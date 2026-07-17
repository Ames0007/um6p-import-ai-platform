"""Récupération via l'index de connaissance unifié (UNIQUE couche recherchable).

Nouvelle architecture :

    Requête (normalisée par Claude)
        ↓
    knowledge_index   ← seule surface de recherche
        ↓  (clés primaires)
    Chargement des enregistrements complets depuis PostgreSQL (source de vérité)
        ↓
    RetrievalResult → contexte

Le retriever n'interroge JAMAIS directement `hs_codes`, `products`,
`text_chunks` ou `document_references` pour *chercher* : il cherche dans
`knowledge_index`, en retire des clés, puis *charge* les enregistrements
complets depuis PostgreSQL. La forme de `RetrievalResult` est inchangée afin
que la construction de contexte et le pipeline restent identiques.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.intents import Intent
from app.ai.memory import Focus
from app.models.authorization import Authorization
from app.models.hs_code import HsCode
from app.models.knowledge_index import (
    KI_CHAPTER,
    KI_DOCUMENT,
    KI_HS_CODE,
    KI_PRODUCT,
    KnowledgeIndex,
)
from app.models.product import Product
from app.models.purchase_history import PurchaseHistory
from app.models.supplier import Supplier
from app.models.tax import Tax
from app.services.knowledge_index import (
    KnowledgeIndexHit,
    knowledge_index_search,
)

CANDIDATE_LIMIT = 8
DOC_LIMIT = 5
CHAPTER_CODES_LIMIT = 40

# Code SH présent dans la requête (sous-position « 3104.20 » ou position « 31.04 »).
_HS_IN_QUERY_RE = re.compile(r"(?<!\d)(\d{4}\.\d{2}(?:\.\d{2}){0,2}|\d{2}\.\d{2})(?!\d)")
_CHAPTER_Q_RE = re.compile(r"chapitre\s+(\d{1,3})", re.IGNORECASE)


def _is_subheading(reference: str | None) -> bool:
    """Vrai pour une sous-position réelle (« 3104.20 »), faux pour une position
    (« 31.04 ») — cette dernière déclenche un aperçu de chapitre (requête large)."""
    return bool(reference and re.match(r"^\d{4}\.\d{2}", reference))


@dataclass
class DocHit:
    document_title: str
    chapter: str | None
    page: int | None
    excerpt: str


@dataclass
class RetrievalResult:
    intent: Intent
    products: list[Product] = field(default_factory=list)
    resolved_product: Product | None = None
    hs_code: HsCode | None = None
    taxes: list[Tax] = field(default_factory=list)
    authorizations: list[Authorization] = field(default_factory=list)
    purchases: list[PurchaseHistory] = field(default_factory=list)
    purchase_stats: dict | None = None
    supplier: Supplier | None = None
    related_products: list[Product] = field(default_factory=list)
    documents: list[DocHit] = field(default_factory=list)
    # Récupération hiérarchique : aperçu au niveau chapitre pour une requête large.
    is_broad: bool = False
    chapter_name: str | None = None
    chapter_headings: list[str] = field(default_factory=list)
    chapter_codes: list[HsCode] = field(default_factory=list)
    focus: Focus = field(default_factory=Focus)
    # Observabilité : enregistrements de l'index qui ont mené à ce résultat.
    ki_matches: list[KnowledgeIndexHit] = field(default_factory=list)
    loaded_tables: list[str] = field(default_factory=list)

    @property
    def has_structured(self) -> bool:
        return bool(
            self.resolved_product
            or self.hs_code
            or self.taxes
            or self.authorizations
            or self.purchases
            or self.supplier
            or self.chapter_codes
        )

    @property
    def needs_selection(self) -> bool:
        return self.resolved_product is None and len(self.products) > 1


class Retriever:
    def retrieve(
        self, db: Session, *, intent: Intent, query: str, focus: Focus
    ) -> RetrievalResult:
        # Phase 7 : la recherche NE reconstruit PLUS l'index (lecture seule).
        # La fraîcheur est garantie hors du chemin des requêtes par le
        # rafraîchisseur d'arrière-plan (app.services.knowledge_refresher).
        result = RetrievalResult(intent=intent)

        # 1) CODE SH EXPLICITE — recherche par référence exacte dans l'index,
        #    chargement immédiat, arrêt du pipeline (aucun classement).
        for raw in _HS_IN_QUERY_RE.findall(query):
            hit = knowledge_index_search.by_reference(db, KI_HS_CODE, raw)
            if hit and hit.source_pk:
                hs = db.get(HsCode, uuid.UUID(hit.source_pk))
                if hs is not None:
                    self._resolve_hs(db, result, hs, focus, matched=[hit])
                    return result

        # 2) CHAPITRE EXPLICITE — référence exacte → aperçu du chapitre.
        chap = _CHAPTER_Q_RE.search(query)
        if chap:
            hit = knowledge_index_search.by_reference(
                db, KI_CHAPTER, str(int(chap.group(1)))
            )
            if hit is not None:
                self._chapter_overview(db, result, hit.chapter or hit.title, [hit])
                result.focus = self._build_focus(None, None, focus)
                return result

        # 3) RECHERCHE DANS L'INDEX (unique couche recherchable).
        hits = knowledge_index_search.search(db, query, limit=CANDIDATE_LIMIT)
        result.ki_matches = hits

        # 3a) Produits candidats (chargés depuis PostgreSQL).
        products: list[Product] = []
        for h in hits:
            if h.type == KI_PRODUCT and h.source_pk:
                p = db.get(Product, uuid.UUID(h.source_pk))
                if p is not None:
                    products.append(p)
        result.products = products

        resolved: Product | None = None
        if len(products) == 1:
            resolved = products[0]
        elif not products and focus.product_id:
            resolved = db.get(Product, uuid.UUID(focus.product_id))
        if resolved is not None and intent in {
            Intent.DOCUMENT_SEARCH,
            Intent.GENERAL_PROCUREMENT,
        } and len(products) > 1:
            resolved = None
        result.resolved_product = resolved

        # 3b) Résolution du code SH. La requête courante prime : sous-position
        #     précise → code direct ; position (heading) → aperçu chapitre ;
        #     sinon repli sur le focus conversationnel (suivi elliptique).
        hs_code: HsCode | None = None
        if resolved is not None and resolved.hs_code_id:
            hs_code = db.get(HsCode, resolved.hs_code_id)

        if hs_code is None and resolved is None:
            top_hs = next((h for h in hits if h.type == KI_HS_CODE), None)
            if top_hs is not None and top_hs.source_pk and _is_subheading(top_hs.reference):
                hs_code = db.get(HsCode, uuid.UUID(top_hs.source_pk))
            elif top_hs is not None:  # position → requête large
                self._chapter_overview(db, result, top_hs.chapter, [top_hs])
            elif focus.hs_code_id:
                hs_code = db.get(HsCode, uuid.UUID(focus.hs_code_id))

        if hs_code is not None:
            result.hs_code = hs_code
            self._attach_hs_records(db, result, hs_code)
            result.documents = self._doc_refs_for_code(db, hs_code)

        # 3c) Achats / fournisseur (produit résolu) — chargés depuis PostgreSQL.
        if resolved is not None:
            result.purchases = list(
                db.execute(
                    select(PurchaseHistory)
                    .where(PurchaseHistory.product_id == resolved.id)
                    .order_by(PurchaseHistory.purchased_at.desc())
                    .limit(10)
                ).scalars().all()
            )
            result.purchase_stats = self._purchase_stats(db, resolved.id)
            result.supplier = self._supplier(db, resolved, result.purchases)

        # 3d) Documents : à défaut de code résolu et hors mode large, on expose
        #     les concepts DOCUMENT trouvés dans l'index comme sources.
        if not result.is_broad and result.hs_code is None and not result.documents:
            result.documents = [
                DocHit(
                    document_title=h.document_title or h.title or "",
                    chapter=h.chapter,
                    page=h.page,
                    excerpt="",
                )
                for h in hits
                if h.type == KI_DOCUMENT
            ][:DOC_LIMIT]

        result.focus = self._build_focus(resolved, result.hs_code, focus)
        result.loaded_tables = self._loaded_tables(result)
        return result

    # ---------------- chargement / assemblage ----------------
    def _resolve_hs(
        self, db: Session, result: RetrievalResult, hs: HsCode,
        focus: Focus, matched: list[KnowledgeIndexHit],
    ) -> None:
        result.hs_code = hs
        result.ki_matches = matched
        self._attach_hs_records(db, result, hs)
        result.documents = self._doc_refs_for_code(db, hs)
        result.focus = self._build_focus(None, hs, focus)
        result.loaded_tables = self._loaded_tables(result)

    def _attach_hs_records(
        self, db: Session, result: RetrievalResult, hs_code: HsCode
    ) -> None:
        result.taxes = list(
            db.execute(
                select(Tax)
                .where(Tax.hs_code_id == hs_code.id)
                .order_by(Tax.effective_date.desc().nullslast())
            ).scalars().all()
        )
        result.authorizations = list(
            db.execute(
                select(Authorization).where(Authorization.hs_code_id == hs_code.id)
            ).scalars().all()
        )
        result.related_products = list(
            db.execute(
                select(Product)
                .where(Product.hs_code_id == hs_code.id)
                .limit(CANDIDATE_LIMIT)
            ).scalars().all()
        )

    def _doc_refs_for_code(self, db: Session, hs_code: HsCode) -> list[DocHit]:
        """Références documentaires par correspondance EXACTE du code (chargement,
        pas de recherche de chunk/sémantique)."""
        from app.models.document import Document
        from app.models.knowledge import HsReference

        rows = db.execute(
            select(HsReference, Document)
            .join(Document, Document.id == HsReference.document_id)
            .where(HsReference.hs_code == hs_code.code)
            .limit(DOC_LIMIT)
        ).all()
        hits: list[DocHit] = []
        seen: set[tuple] = set()
        for ref, doc in rows:
            key = (doc.title, ref.page)
            if key in seen:
                continue
            seen.add(key)
            hits.append(
                DocHit(document_title=doc.title, chapter=ref.chapter,
                       page=ref.page, excerpt="")
            )
        return hits

    def _chapter_overview(
        self, db: Session, result: RetrievalResult,
        chapter_label: str | None, matched: list[KnowledgeIndexHit],
    ) -> None:
        """Aperçu d'un chapitre : codes SH liés (chargés depuis PostgreSQL) +
        positions + documents, à partir des clés trouvées dans l'index."""
        if not chapter_label:
            return
        ki_codes = db.execute(
            select(KnowledgeIndex)
            .where(
                KnowledgeIndex.type == KI_HS_CODE,
                KnowledgeIndex.chapter == chapter_label,
            )
            .order_by(KnowledgeIndex.reference)
            .limit(CHAPTER_CODES_LIMIT)
        ).scalars().all()
        codes: list[HsCode] = []
        for row in ki_codes:
            if row.source_pk:
                hs = db.get(HsCode, uuid.UUID(row.source_pk))
                if hs is not None:
                    codes.append(hs)
        if not codes:
            return
        result.is_broad = True
        result.chapter_name = chapter_label
        result.chapter_codes = codes
        result.ki_matches = matched
        headings: dict[str, str] = {}
        for hs in codes:
            headings.setdefault(self._heading_of(hs.code), hs.description_fr)
        result.chapter_headings = [f"{h} — {d}" for h, d in headings.items()]

        doc_rows = db.execute(
            select(KnowledgeIndex)
            .where(
                KnowledgeIndex.type == KI_DOCUMENT,
                KnowledgeIndex.chapter == chapter_label,
            )
            .limit(DOC_LIMIT)
        ).scalars().all()
        result.documents = [
            DocHit(document_title=r.document_title or r.title or "",
                   chapter=r.chapter, page=None, excerpt="")
            for r in doc_rows
        ][:DOC_LIMIT]
        result.loaded_tables = self._loaded_tables(result)

    @staticmethod
    def _heading_of(code: str) -> str:
        digits = "".join(ch for ch in code if ch.isdigit())
        return f"{digits[:2]}.{digits[2:4]}" if len(digits) >= 4 else code

    def _purchase_stats(self, db: Session, product_id: uuid.UUID) -> dict | None:
        from sqlalchemy import func

        row = db.execute(
            select(
                func.count(PurchaseHistory.id),
                func.avg(PurchaseHistory.unit_price),
                func.min(PurchaseHistory.unit_price),
                func.max(PurchaseHistory.unit_price),
            ).where(PurchaseHistory.product_id == product_id)
        ).one()
        if not row[0]:
            return None
        return {
            "count": int(row[0]),
            "average_price": float(row[1]) if row[1] is not None else None,
            "min_price": float(row[2]) if row[2] is not None else None,
            "max_price": float(row[3]) if row[3] is not None else None,
        }

    def _supplier(
        self, db: Session, product: Product, purchases: list[PurchaseHistory]
    ) -> Supplier | None:
        if product.preferred_supplier_id:
            return db.get(Supplier, product.preferred_supplier_id)
        for purchase in purchases:
            if purchase.supplier_id:
                return db.get(Supplier, purchase.supplier_id)
        return None

    def _build_focus(
        self, product: Product | None, hs_code: HsCode | None, previous: Focus
    ) -> Focus:
        return Focus(
            product_id=str(product.id) if product else previous.product_id,
            product_name=product.name if product else previous.product_name,
            hs_code_id=str(hs_code.id) if hs_code else previous.hs_code_id,
            hs_code=hs_code.code if hs_code else previous.hs_code,
        )

    @staticmethod
    def _loaded_tables(result: RetrievalResult) -> list[str]:
        tables = ["knowledge_index"]
        if result.hs_code or result.chapter_codes:
            tables.append("hs_codes")
        if result.taxes:
            tables.append("taxes")
        if result.authorizations:
            tables.append("authorizations")
        if result.resolved_product or result.related_products or result.products:
            tables.append("products")
        if result.purchases:
            tables.append("purchase_history")
        if result.supplier:
            tables.append("suppliers")
        if result.documents:
            tables.append("documents")
        return tables


retriever = Retriever()
