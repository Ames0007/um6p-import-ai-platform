"""Services de pilotage de la base de connaissances douanière (production).

Lecture seule : couverture par chapitre, santé globale, contrôle qualité et
tests de recherche automatiques. Aucune donnée inventée — tout est calculé à
partir de ce qui a été réellement importé.
"""
from __future__ import annotations

import unicodedata
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.context import context_builder
from app.ai.intents import detect_intent
from app.ai.memory import Focus
from app.ai.retriever import retriever
from app.models.authorization import Authorization
from app.models.document import Document
from app.models.hs_code import HsCode
from app.models.import_history import ImportHistory
from app.models.knowledge import DocumentReference, HsReference, TextChunk
from app.models.tax import Tax


def _norm(text: str | None) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def _chapter_num(code: str) -> int | None:
    digits = "".join(ch for ch in (code or "") if ch.isdigit())
    return int(digits[:2]) if len(digits) >= 2 else None


def _is_complete_desc(code: str, desc: str | None) -> bool:
    return bool(desc) and desc != code and len(desc.strip()) >= 5


# Tests de recherche par défaut (attendu = code SH partiel ou « Chapitre N »).
DEFAULT_SEARCH_TESTS = [
    {"query": "engrais", "expected": "Chapitre 31"},
    {"query": "chlorure de potassium", "expected": "3104.20"},
    {"query": "urée", "expected": "3102.10"},
    {"query": "superphosphate", "expected": "Chapitre 31"},
    {"query": "phosphate diammonique", "expected": "3105.30"},
]


class KnowledgeService:
    # ---------------- Couverture par chapitre ----------------
    def coverage(self, db: Session) -> dict:
        codes = db.execute(select(HsCode.code, HsCode.description_fr)).all()
        by_ch_codes: dict[int, list] = defaultdict(list)
        for code, desc in codes:
            n = _chapter_num(code)
            if n:
                by_ch_codes[n].append((code, desc))

        taxes_by_ch = self._count_by_chapter(db, Tax)
        auth_by_ch = self._count_by_chapter(db, Authorization)
        ch_docs, doc_meta = self._chapter_documents(db)
        tested = self._tested_chapters(db)

        chapters = []
        for n in range(1, 98):
            items = by_ch_codes.get(n, [])
            hs_count = len(items)
            desc_count = sum(1 for c, d in items if _is_complete_desc(c, d))
            docs = ch_docs.get(n, set())
            warns = sum(doc_meta.get(d, {}).get("warnings", 0) for d in docs)
            errs = sum(doc_meta.get(d, {}).get("errors", 0) for d in docs)
            last = max((doc_meta.get(d, {}).get("upload_date") for d in docs), default=None)
            status = self._chapter_status(docs, doc_meta)
            chapters.append({
                "chapter": f"Chapitre {n:02d}",
                "imported": hs_count > 0,
                "hs_codes": hs_count,
                "descriptions": desc_count,
                "taxes": taxes_by_ch.get(n, 0),
                "authorizations": auth_by_ch.get(n, 0),
                "last_import_date": last.isoformat() if last else None,
                "validation_status": status,
                "search_tested": n in tested,
                "coverage_percent": round(100 * desc_count / hs_count, 1) if hs_count else 0.0,
                "errors": errs,
                "warnings": warns,
            })
        imported = [c for c in chapters if c["imported"]]
        return {
            "total_chapters": 97,
            "imported_chapters": len(imported),
            "coverage_percent": round(100 * len(imported) / 97, 1),
            "chapters": chapters,
        }

    # ---------------- Santé globale ----------------
    def health(self, db: Session) -> dict:
        def count(model) -> int:
            return int(db.execute(select(func.count()).select_from(model)).scalar_one())

        total_codes = count(HsCode)
        with_desc = int(db.execute(
            select(func.count()).select_from(HsCode)
            .where(HsCode.description_fr != HsCode.code, func.length(HsCode.description_fr) >= 5)
        ).scalar_one())
        refs = count(HsReference)
        distinct_codes = int(db.execute(
            select(func.count(func.distinct(HsReference.hs_code)))
        ).scalar_one())
        chunks = count(TextChunk)
        embeddings = int(db.execute(
            select(func.count()).select_from(TextChunk).where(TextChunk.embedding.isnot(None))
        ).scalar_one())
        pages = int(db.execute(select(func.coalesce(func.sum(Document.number_of_pages), 0))).scalar_one())
        chapters_with_codes = len({
            _chapter_num(c) for (c,) in db.execute(select(HsCode.code)).all() if _chapter_num(c)
        })
        dup_rate = round(100 * (refs - distinct_codes) / refs, 1) if refs else 0.0
        doc_refs = count(DocumentReference)
        valid_citations = int(db.execute(
            select(func.count()).select_from(DocumentReference)
            .where(DocumentReference.citation.isnot(None), DocumentReference.page.isnot(None))
        ).scalar_one())
        desc_score = with_desc / total_codes if total_codes else 0.0
        cite_score = valid_citations / doc_refs if doc_refs else 0.0
        validation_score = round(100 * (0.6 * desc_score + 0.4 * cite_score), 1)
        return {
            "imported_documents": count(Document),
            "imported_chapters": chapters_with_codes,
            "imported_pages": pages,
            "hs_codes": total_codes,
            "taxes": count(Tax),
            "authorizations": count(Authorization),
            "document_references": doc_refs,
            "searchable_chunks": chunks,
            "embeddings": embeddings,
            "coverage_percent": round(100 * chapters_with_codes / 97, 1),
            "duplicate_rate_percent": dup_rate,
            "validation_score": validation_score,
        }

    # ---------------- Contrôle qualité ----------------
    def quality(self, db: Session) -> dict:
        incomplete = db.execute(
            select(HsCode.code, HsCode.description_fr)
            .where((HsCode.description_fr == HsCode.code) | (func.length(HsCode.description_fr) < 5))
            .limit(50)
        ).all()
        no_tax = int(db.execute(
            select(func.count()).select_from(HsCode)
            .where(~HsCode.id.in_(select(Tax.hs_code_id)))
        ).scalar_one())
        no_auth = int(db.execute(
            select(func.count()).select_from(HsCode)
            .where(~HsCode.id.in_(select(Authorization.hs_code_id)))
        ).scalar_one())
        invalid_cit = int(db.execute(
            select(func.count()).select_from(DocumentReference)
            .where((DocumentReference.citation.is_(None)) | (DocumentReference.page.is_(None)))
        ).scalar_one())
        # Chapitres « vides » : présents dans les chunks mais sans code SH.
        chunk_chapters = {
            _chapter_num_from_label(ch) for (ch,) in db.execute(
                select(func.distinct(TextChunk.chapter)).where(TextChunk.chapter.isnot(None))
            ).all()
        }
        code_chapters = {_chapter_num(c) for (c,) in db.execute(select(HsCode.code)).all()}
        empty_chapters = sorted(n for n in chunk_chapters if n and n not in code_chapters)
        # Occurrences dupliquées (informational).
        refs = int(db.execute(select(func.count()).select_from(HsReference)).scalar_one())
        distinct_codes = int(db.execute(select(func.count(func.distinct(HsReference.hs_code)))).scalar_one())
        issues = {
            "incomplete_descriptions": {"count": len(incomplete),
                                        "samples": [c for c, _ in incomplete[:10]]},
            "codes_without_taxes": no_tax,
            "codes_without_authorizations": no_auth,
            "invalid_citations": invalid_cit,
            "empty_chapters": empty_chapters,
            "duplicate_occurrences": max(refs - distinct_codes, 0),
            "broken_document_references": 0,  # garanti par contrainte FK
        }
        critical = len(incomplete) + invalid_cit + len(empty_chapters)
        return {"issues": issues, "critical_issue_count": critical,
                "status": "sain" if critical == 0 else "à vérifier"}

    # ---------------- Tests de recherche ----------------
    def run_search_tests(self, db: Session, tests: list[dict] | None = None) -> dict:
        tests = tests or DEFAULT_SEARCH_TESTS
        results = []
        for t in tests:
            q, expected = t["query"], t["expected"]
            result = retriever.retrieve(db, intent=detect_intent(q), query=q, focus=Focus())
            ctx = context_builder.build(result)
            hay_parts = []
            if result.hs_code:
                hay_parts += [result.hs_code.code, result.hs_code.chapter or "", result.hs_code.description_fr]
            if result.chapter_name:
                hay_parts.append(result.chapter_name)
            hay_parts += [c.code for c in result.chapter_codes]
            hay_parts += [d.document_title for d in result.documents]
            hay = _norm(" ".join(p for p in hay_parts if p))
            passed = _norm(expected) in hay and ctx.confidence != "aucune"
            results.append({
                "query": q, "expected": expected, "passed": passed,
                "confidence": ctx.confidence,
                "resolved": (result.hs_code.code if result.hs_code else result.chapter_name),
                "mode": "chapitre" if result.is_broad else "code",
            })
        passed = sum(1 for r in results if r["passed"])
        return {"total": len(results), "passed": passed, "failed": len(results) - passed,
                "pass_rate_percent": round(100 * passed / len(results), 1) if results else 0.0,
                "results": results}

    # ---------------- helpers ----------------
    def _count_by_chapter(self, db: Session, model) -> dict[int, int]:
        rows = db.execute(
            select(HsCode.code, func.count(model.id)).join(model, model.hs_code_id == HsCode.id)
            .group_by(HsCode.code)
        ).all()
        out: dict[int, int] = defaultdict(int)
        for code, n in rows:
            ch = _chapter_num(code)
            if ch:
                out[ch] += int(n)
        return out

    def _chapter_documents(self, db: Session):
        pairs = db.execute(
            select(func.distinct(HsReference.hs_code), HsReference.document_id)
        ).all()
        ch_docs: dict[int, set] = defaultdict(set)
        for code, doc_id in pairs:
            ch = _chapter_num(code)
            if ch and doc_id:
                ch_docs[ch].add(doc_id)
        doc_meta: dict = {}
        for doc in db.execute(select(Document)).scalars().all():
            latest = db.execute(
                select(ImportHistory).where(ImportHistory.document_id == doc.id)
                .order_by(ImportHistory.start_time.desc()).limit(1)
            ).scalar_one_or_none()
            stats = (latest.stats if latest and latest.stats else {}) or {}
            doc_meta[doc.id] = {
                "status": doc.status.value if doc.status else None,
                "upload_date": doc.upload_date,
                "warnings": int(stats.get("warnings", 0)),
                "errors": int(stats.get("errors", 0)),
            }
        return ch_docs, doc_meta

    def _chapter_status(self, docs, doc_meta) -> str:
        statuses = {doc_meta.get(d, {}).get("status") for d in docs}
        if not statuses:
            return "non_importe"
        if "erreur" in statuses:
            return "erreur"
        if "partiel" in statuses:
            return "partiel"
        if "termine" in statuses:
            return "termine"
        return next(iter(statuses)) or "non_importe"

    def _tested_chapters(self, db: Session) -> set[int]:
        # Chapitres couverts par les tests de recherche qui passent.
        tested: set[int] = set()
        try:
            report = self.run_search_tests(db)
        except Exception:
            return tested
        for r in report["results"]:
            if not r["passed"]:
                continue
            resolved = r.get("resolved") or ""
            n = _chapter_num(resolved) or _chapter_num_from_label(resolved)
            if n:
                tested.add(n)
        return tested


def _chapter_num_from_label(label: str | None) -> int | None:
    if not label:
        return None
    digits = "".join(ch for ch in label if ch.isdigit())
    return int(digits[:2]) if len(digits) >= 2 else None


knowledge_service = KnowledgeService()
