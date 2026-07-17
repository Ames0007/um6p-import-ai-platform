"""Service de l'index de connaissance unifié (couche de recherche unique).

Deux responsabilités :
1. CONSTRUCTION (`rebuild`/`ensure_fresh`) — (re)matérialise `knowledge_index`
   à partir des tables relationnelles de PostgreSQL. Aucune logique métier n'est
   dupliquée : on lit des données déjà calculées (codes SH, descriptions, taxes…)
   et on en dérive uniquement une représentation de recherche normalisée.
   Le rafraîchissement est automatique : des déclencheurs SQL marquent l'index
   « sale » dès qu'une table source change (import de document/produit, mise à
   jour de taxe/autorisation) ; `ensure_fresh` reconstruit alors à la volée.
2. RECHERCHE (`search`, `by_reference`, `by_chapter`) — interroge UNIQUEMENT
   `knowledge_index` et renvoie des enregistrements légers (dont la clé
   `source_table`/`source_pk`) que le retriever recharge ensuite en entier
   depuis PostgreSQL (seule source de vérité).
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import delete, func, insert, select, text
from sqlalchemy.orm import Session

from app.models.authorization import Authorization
from app.models.document import Document
from app.models.hs_code import HsCode
from app.models.knowledge import HsReference
from app.models.knowledge_index import (
    KI_AUTHORIZATION,
    KI_CHAPTER,
    KI_DOCUMENT,
    KI_HS_CODE,
    KI_PRODUCT,
    KI_SECTION,
    KI_SUPPLIER,
    KI_TAX,
    KnowledgeIndex,
)
from app.models.product import Product
from app.models.product_alias import ProductAlias
from app.models.supplier import Supplier
from app.models.tax import Tax

SEARCH_CANDIDATES = 80  # candidats ramenés par le GIN avant reclassement fin
DEFAULT_LIMIT = 5

# Mots vides français : exclus de la requête plein-texte pour ne pas polluer le
# classement (« de », « du », « le »… apparaissent partout).
_STOPWORDS = {
    "de", "du", "des", "la", "le", "les", "un", "une", "en", "et", "ou", "au",
    "aux", "pour", "avec", "sur", "dans", "par", "est", "quel", "quelle",
    "quels", "quelles", "sont", "d", "l",
}


# ----------------------------- normalisation -----------------------------
def normalize(text_in: str | None) -> str:
    """Minuscule + suppression des accents + ponctuation→espace + espaces."""
    s = unicodedata.normalize("NFKD", (text_in or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^0-9a-z]+", " ", s)
    return " ".join(s.split())


def singularize(token: str) -> str:
    """Singularisation heuristique française (chevaux→cheval, engrais→engrai…)."""
    if len(token) > 4 and token.endswith("aux"):
        return token[:-3] + "al"
    if len(token) > 3 and token.endswith(("s", "x")):
        return token[:-1]
    return token


def _digits(s: str | None) -> str:
    return "".join(c for c in (s or "") if c.isdigit())


def _build_search(*chunks) -> str:
    """Texte recherchable : normalisé, tokens + formes singulières."""
    parts: list[str] = []
    for ch in chunks:
        if not ch:
            continue
        if isinstance(ch, (list, tuple, set)):
            parts.extend(str(x) for x in ch if x)
        else:
            parts.append(str(ch))
    norm = normalize(" ".join(parts))
    tokens = norm.split()
    extra = [singularize(t) for t in tokens]
    seen: dict[str, None] = {}
    for t in tokens + extra:
        seen.setdefault(t, None)
    return " ".join(seen.keys())


def _fmt(value) -> str:
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return str(value)


def _tax_summary(taxes: list[Tax]) -> str | None:
    if not taxes:
        return None
    t = taxes[0]
    parts = []
    if t.import_duty is not None:
        parts.append(f"DI {_fmt(t.import_duty)}%")
    if t.vat is not None:
        parts.append(f"TVA {_fmt(t.vat)}%")
    if t.parafiscal_tax:
        parts.append(f"parafiscale {_fmt(t.parafiscal_tax)}%")
    return ", ".join(parts) or None


def _auth_summary(auths: list[Authorization]) -> str | None:
    if not auths:
        return None
    a = auths[0]
    bits = [a.status.value if a.status else None, a.ministry or a.organization]
    return " — ".join(b for b in bits if b) or None


def _segments(description: str | None) -> list[str]:
    """Découpe une description hiérarchique « position — groupe — feuille »."""
    return [s.strip() for s in re.split(r"\s[—–]\s", description or "") if s.strip()]


# ----------------------------- construction -----------------------------
@dataclass
class KnowledgeIndexBuilder:
    def _hs_rows(self, db: Session) -> list[dict]:
        tax_map: dict = defaultdict(list)
        for t in db.execute(select(Tax)).scalars():
            tax_map[t.hs_code_id].append(t)
        auth_map: dict = defaultdict(list)
        for a in db.execute(select(Authorization)).scalars():
            auth_map[a.hs_code_id].append(a)
        prod_map: dict = defaultdict(list)
        for p in db.execute(
            select(Product).where(Product.hs_code_id.isnot(None))
        ).scalars():
            prod_map[p.hs_code_id].append(p)
        ref_map: dict[str, HsReference] = {}
        for r in db.execute(select(HsReference)).scalars():
            ref_map.setdefault(r.hs_code, r)
        doc_titles = {
            d.id: d.title for d in db.execute(select(Document)).scalars()
        }

        rows: list[dict] = []
        for hs in db.execute(select(HsCode)).scalars():
            segs = _segments(hs.description_fr)
            description = segs[0] if segs else (hs.description_fr or "")
            title = segs[-1] if len(segs) > 1 else description
            num = _digits(hs.chapter)
            taxes = tax_map.get(hs.id, [])
            auths = auth_map.get(hs.id, [])
            products = prod_map.get(hs.id, [])
            ref = ref_map.get(hs.code)
            doc_title = doc_titles.get(ref.document_id) if ref else None
            prod_terms = []
            for p in products:
                prod_terms += [p.name, p.brand, p.manufacturer, p.category]
                prod_terms += list(p.keywords or [])
            rows.append(
                {
                    "type": KI_HS_CODE,
                    "reference": hs.code,
                    "title": title,
                    "normalized_title": normalize(title),
                    "chapter": hs.chapter,
                    "section": ref.section if ref else None,
                    "document_id": ref.document_id if ref else None,
                    "document_title": doc_title,
                    "page": ref.page if ref else None,
                    "description": description,
                    "taxes": _tax_summary(taxes),
                    "authorizations": _auth_summary(auths),
                    "searchable_text": _build_search(
                        hs.code,
                        hs.code.replace(".", " "),
                        segs or [hs.description_fr],
                        hs.chapter,
                        num,
                        f"chapitre {num}" if num else None,
                        ref.section if ref else None,
                        doc_title,
                        prod_terms,
                        "droit importation tva" if taxes else None,
                    ),
                    "source_table": "hs_codes",
                    "source_pk": str(hs.id),
                }
            )
        return rows

    def _product_rows(self, db: Session) -> list[dict]:
        alias_map: dict = defaultdict(list)
        for al in db.execute(select(ProductAlias)).scalars():
            alias_map[al.product_id].append(al.alias)
        hs_map = {h.id: h for h in db.execute(select(HsCode)).scalars()}
        rows: list[dict] = []
        for p in db.execute(select(Product)).scalars():
            hs = hs_map.get(p.hs_code_id) if p.hs_code_id else None
            aliases = alias_map.get(p.id, [])
            rows.append(
                {
                    "type": KI_PRODUCT,
                    "reference": p.reference or None,
                    "title": p.name,
                    "normalized_title": normalize(p.name),
                    "chapter": hs.chapter if hs else None,
                    "section": None,
                    "document_id": None,
                    "document_title": None,
                    "page": None,
                    "description": p.description_fr,
                    "taxes": None,
                    "authorizations": None,
                    "searchable_text": _build_search(
                        p.name, p.reference, p.brand, p.manufacturer, p.category,
                        list(p.keywords or []), aliases, p.description_fr,
                        hs.code if hs else None, hs.description_fr if hs else None,
                    ),
                    "source_table": "products",
                    "source_pk": str(p.id),
                }
            )
        return rows

    def _chapter_rows(self, db: Session) -> list[dict]:
        chapters = db.execute(
            select(HsCode.chapter).where(HsCode.chapter.isnot(None)).distinct()
        ).scalars().all()
        rows: list[dict] = []
        for ch in chapters:
            num = _digits(ch)
            rows.append(
                {
                    "type": KI_CHAPTER,
                    "reference": num or ch,
                    "title": ch,
                    "normalized_title": normalize(ch),
                    "chapter": ch,
                    "section": None,
                    "document_id": None,
                    "document_title": None,
                    "page": None,
                    "description": None,
                    "taxes": None,
                    "authorizations": None,
                    "searchable_text": _build_search(ch, num, f"chapitre {num}"),
                    "source_table": "chapter",
                    "source_pk": ch,
                }
            )
        return rows

    def _section_rows(self, db: Session) -> list[dict]:
        sections = db.execute(
            select(HsReference.section).where(HsReference.section.isnot(None)).distinct()
        ).scalars().all()
        rows: list[dict] = []
        for sec in sections:
            rows.append(
                {
                    "type": KI_SECTION,
                    "reference": sec,
                    "title": sec,
                    "normalized_title": normalize(sec),
                    "chapter": None,
                    "section": sec,
                    "document_id": None,
                    "document_title": None,
                    "page": None,
                    "description": None,
                    "taxes": None,
                    "authorizations": None,
                    "searchable_text": _build_search(sec),
                    "source_table": "section",
                    "source_pk": sec,
                }
            )
        return rows

    def _document_rows(self, db: Session) -> list[dict]:
        chap_map: dict = defaultdict(set)
        for r in db.execute(
            select(HsReference.document_id, HsReference.chapter).where(
                HsReference.chapter.isnot(None)
            )
        ):
            chap_map[r[0]].add(r[1])
        rows: list[dict] = []
        for d in db.execute(select(Document)).scalars():
            chapters = sorted(chap_map.get(d.id, set()))
            rows.append(
                {
                    "type": KI_DOCUMENT,
                    "reference": (d.title or "")[:120],
                    "title": d.title,
                    "normalized_title": normalize(d.title),
                    "chapter": chapters[0] if chapters else None,
                    "section": None,
                    "document_id": d.id,
                    "document_title": d.title,
                    "page": None,
                    "description": None,
                    "taxes": None,
                    "authorizations": None,
                    "searchable_text": _build_search(
                        d.title, d.category.value if d.category else None,
                        chapters, "document",
                    ),
                    "source_table": "documents",
                    "source_pk": str(d.id),
                }
            )
        return rows

    def _supplier_rows(self, db: Session) -> list[dict]:
        rows: list[dict] = []
        for s in db.execute(select(Supplier)).scalars():
            rows.append(
                {
                    "type": KI_SUPPLIER,
                    "reference": None,
                    "title": s.name,
                    "normalized_title": normalize(s.name),
                    "chapter": None,
                    "section": None,
                    "document_id": None,
                    "document_title": None,
                    "page": None,
                    "description": None,
                    "taxes": None,
                    "authorizations": None,
                    "searchable_text": _build_search(
                        s.name, s.contact_name, s.website, "fournisseur"
                    ),
                    "source_table": "suppliers",
                    "source_pk": str(s.id),
                }
            )
        return rows

    def _authorization_rows(self, db: Session) -> list[dict]:
        code_map = {h.id: h.code for h in db.execute(select(HsCode)).scalars()}
        rows: list[dict] = []
        for a in db.execute(select(Authorization)).scalars():
            code = code_map.get(a.hs_code_id)
            title = a.organization or a.ministry or "Autorisation"
            rows.append(
                {
                    "type": KI_AUTHORIZATION,
                    "reference": code,
                    "title": title,
                    "normalized_title": normalize(title),
                    "chapter": None,
                    "section": None,
                    "document_id": None,
                    "document_title": None,
                    "page": None,
                    "description": a.description_fr,
                    "taxes": None,
                    "authorizations": a.status.value if a.status else None,
                    "searchable_text": _build_search(
                        "autorisation licence", a.status.value if a.status else None,
                        a.organization, a.ministry, a.description_fr, code,
                    ),
                    "source_table": "authorizations",
                    "source_pk": str(a.id),
                }
            )
        return rows

    def _tax_rows(self, db: Session) -> list[dict]:
        code_map = {h.id: h.code for h in db.execute(select(HsCode)).scalars()}
        rows: list[dict] = []
        for t in db.execute(select(Tax)).scalars():
            code = code_map.get(t.hs_code_id)
            summ = _tax_summary([t])
            rows.append(
                {
                    "type": KI_TAX,
                    "reference": code,
                    "title": f"Taxes {code}" if code else "Taxes",
                    "normalized_title": normalize(f"taxes {code}"),
                    "chapter": None,
                    "section": None,
                    "document_id": None,
                    "document_title": None,
                    "page": None,
                    "description": summ,
                    "taxes": summ,
                    "authorizations": None,
                    "searchable_text": _build_search(
                        "droit importation tva taxe douane", code, summ,
                    ),
                    "source_table": "taxes",
                    "source_pk": str(t.id),
                }
            )
        return rows

    def rebuild(self, db: Session) -> int:
        """Reconstruit intégralement l'index depuis PostgreSQL."""
        db.execute(delete(KnowledgeIndex))
        rows: list[dict] = []
        rows += self._hs_rows(db)
        rows += self._product_rows(db)
        rows += self._chapter_rows(db)
        rows += self._section_rows(db)
        rows += self._document_rows(db)
        rows += self._supplier_rows(db)
        rows += self._authorization_rows(db)
        rows += self._tax_rows(db)
        if rows:
            db.execute(insert(KnowledgeIndex), rows)
        db.execute(
            text(
                "UPDATE knowledge_index_state SET dirty = false, "
                "last_built_at = now() WHERE id = 1"
            )
        )
        db.commit()
        return len(rows)

    def ensure_fresh(self, db: Session) -> None:
        """Reconstruit si l'index est marqué « sale » (ou vide)."""
        try:
            dirty_row = db.execute(
                text("SELECT dirty FROM knowledge_index_state WHERE id = 1")
            ).first()
        except Exception:
            dirty_row = None
        count = db.execute(select(func.count()).select_from(KnowledgeIndex)).scalar()
        if dirty_row is None or dirty_row[0] or not count:
            self.rebuild(db)


# ----------------------------- recherche -----------------------------
@dataclass
class KnowledgeIndexHit:
    id: str
    type: str
    reference: str | None
    title: str | None
    normalized_title: str | None
    chapter: str | None
    section: str | None
    document_id: object
    document_title: str | None
    page: int | None
    description: str | None
    taxes: str | None
    authorizations: str | None
    source_table: str
    source_pk: str | None
    score: float


_SEARCH_SQL = text(
    """
    SELECT id, type, reference, title, normalized_title, chapter, section,
           document_id, document_title, page, description, taxes, authorizations,
           source_table, source_pk, searchable_text,
           ts_rank_cd(to_tsvector('simple', searchable_text),
                      to_tsquery('simple', :tsq)) AS rank
    FROM knowledge_index
    WHERE to_tsvector('simple', searchable_text) @@ to_tsquery('simple', :tsq)
    ORDER BY rank DESC
    LIMIT :lim
    """
)


class KnowledgeIndexSearch:
    def _tokens(self, query: str) -> list[str]:
        out: list[str] = []
        for t in normalize(query).split():
            if len(t) < 2 or t in _STOPWORDS:
                continue
            out.append(singularize(t))
        return out

    def search(
        self, db: Session, query: str, *, limit: int = DEFAULT_LIMIT
    ) -> list[KnowledgeIndexHit]:
        """Recherche plein-texte (GIN) + reclassement fin. Renvoie ≤ limit hits."""
        tokens = self._tokens(query)
        if not tokens:
            return []
        nq = " ".join(tokens)
        tsq = " | ".join(f"{t}:*" for t in tokens)
        rows = db.execute(
            _SEARCH_SQL, {"tsq": tsq, "lim": SEARCH_CANDIDATES}
        ).mappings().all()

        scored: list[KnowledgeIndexHit] = []
        qset = set(tokens)
        for r in rows:
            st = r["searchable_text"] or ""
            words = set(st.split())
            ntitle = r["normalized_title"] or ""
            score = float(r["rank"]) * 10.0
            if ntitle == nq:
                score += 100          # concept exact
            elif nq and ntitle.startswith(nq):
                score += 55           # le titre commence par la requête
            elif nq and nq in ntitle:
                score += 45           # requête contenue dans le titre
            elif nq and nq in st:
                score += 30           # phrase présente dans le texte
            score += 6 * sum(1 for t in qset if t in words)  # recouvrement de termes
            # légère préférence pour les concepts de fond (SH/produit/chapitre/doc)
            score += {KI_HS_CODE: 3, KI_PRODUCT: 3, KI_CHAPTER: 2,
                      KI_DOCUMENT: 2}.get(r["type"], 0)
            scored.append(
                KnowledgeIndexHit(
                    id=str(r["id"]), type=r["type"], reference=r["reference"],
                    title=r["title"], normalized_title=ntitle,
                    chapter=r["chapter"], section=r["section"],
                    document_id=r["document_id"], document_title=r["document_title"],
                    page=r["page"], description=r["description"],
                    taxes=r["taxes"], authorizations=r["authorizations"],
                    source_table=r["source_table"], source_pk=r["source_pk"],
                    score=round(score, 3),
                )
            )
        scored.sort(
            key=lambda h: (-h.score, len(h.reference or "zzzzz"), h.reference or "")
        )
        return scored[:limit]

    def by_reference(
        self, db: Session, ki_type: str, reference: str
    ) -> KnowledgeIndexHit | None:
        """Recherche EXACTE par référence (code SH, n° de chapitre…)."""
        r = db.execute(
            select(KnowledgeIndex)
            .where(KnowledgeIndex.type == ki_type, KnowledgeIndex.reference == reference)
            .limit(1)
        ).scalar_one_or_none()
        if r is None:
            return None
        return KnowledgeIndexHit(
            id=str(r.id), type=r.type, reference=r.reference, title=r.title,
            normalized_title=r.normalized_title, chapter=r.chapter, section=r.section,
            document_id=r.document_id, document_title=r.document_title, page=r.page,
            description=r.description, taxes=r.taxes, authorizations=r.authorizations,
            source_table=r.source_table, source_pk=r.source_pk, score=1000.0,
        )


knowledge_index_builder = KnowledgeIndexBuilder()
knowledge_index_search = KnowledgeIndexSearch()
