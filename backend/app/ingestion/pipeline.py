"""Orchestrateur du pipeline d'ingestion.

Traite un document page par page, de façon reprenable (resume) et idempotente.
La progression est persistée en base à chaque page pour un suivi temps réel.
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.ingestion.chunking import chunk_page_text
from app.ingestion.detectors import (
    StructureTracker,
    classify_authorization,
    detect_authorizations,
    detect_tax_tables,
    extract_hs_entries,
    parse_line_taxes,
)
from app.ingestion.detectors.patterns import HS_DOTTED_RE, HS_HEADING_RE
from app.ingestion.embeddings import get_embedding_provider
from app.ingestion.extractors import get_extractor
from app.ingestion.extractors.base import (
    CorruptedDocumentError,
    UnsupportedFormatError,
)
from app.ingestion.ocr import get_ocr_provider
from app.ingestion.types import ExtractedPage, IngestionResult
from app.models.authorization import Authorization
from app.models.document import Document
from app.models.enums import AuthorizationStatus, DocumentStatus, ImportStatus
from app.models.hs_code import HsCode
from app.models.import_history import ImportHistory
from app.models.knowledge import DocumentReference, HsReference, TextChunk
from app.models.tax import Tax

logger = logging.getLogger("ingestion")


def run_ingestion(document_id: uuid.UUID, *, resume: bool = True) -> IngestionResult:
    """Exécute l'ingestion complète d'un document (session dédiée)."""
    db = SessionLocal()
    try:
        return _IngestionRun(db, document_id, resume=resume).execute()
    finally:
        db.close()


class _IngestionRun:
    def __init__(self, db, document_id: uuid.UUID, *, resume: bool) -> None:
        self.db = db
        self.document_id = document_id
        self.resume = resume
        self.result = IngestionResult()
        self.embedder = get_embedding_provider()
        self.ocr = get_ocr_provider()
        self.tracker = StructureTracker()
        # Caches de déduplication (durée de vie = un run).
        self._hs_cache: dict[str, HsCode] = {}
        self._chapters: set[str] = set()
        self._sections: set[str] = set()
        self._tax_codes: set[uuid.UUID] = set()
        self._auth_codes: set[uuid.UUID] = set()
        self._started_at = time.perf_counter()

    # -- utilitaires --
    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _add_error(self, page: int | None, message: str) -> None:
        self.result.errors.append({"page": page, "message": message})
        logger.warning("Document %s page %s : %s", self.document_id, page, message)

    def execute(self) -> IngestionResult:
        document = self.db.get(Document, self.document_id)
        if document is None:
            raise ValueError(f"Document introuvable : {self.document_id}")

        import_record = ImportHistory(
            document_id=document.id,
            start_time=self._now(),
            status=ImportStatus.EN_COURS,
            message="Démarrage de l'ingestion",
        )
        self.db.add(import_record)
        document.status = DocumentStatus.EN_TRAITEMENT
        document.error_message = None
        self.db.commit()

        try:
            self._process(document, import_record)
        except (UnsupportedFormatError, CorruptedDocumentError) as exc:
            self._fail(document, import_record, str(exc))
            raise
        except Exception as exc:  # échec inattendu → statut ERREUR
            self._fail(document, import_record, f"Erreur inattendue : {exc}")
            logger.exception("Échec d'ingestion pour %s", self.document_id)
            raise

        return self.result

    def _fail(self, document: Document, import_record: ImportHistory, msg: str) -> None:
        document.status = DocumentStatus.ERREUR
        document.error_message = msg[:2000]
        import_record.status = ImportStatus.ECHOUE
        import_record.end_time = self._now()
        import_record.message = msg[:500]
        import_record.errors = self.result.errors
        import_record.stats = self.result.as_stats()
        self.db.commit()

    def _process(self, document: Document, import_record: ImportHistory) -> None:
        extractor = get_extractor(document.storage_path)

        total = document.number_of_pages or extractor.count_pages(document.storage_path)
        document.number_of_pages = total
        self.result.total_pages = total
        import_record.total_pages = total

        # Point de reprise : nombre de pages déjà traitées.
        start_after = document.processed_pages if self.resume else 0
        if not self.resume:
            self._reset_document_data(document)

        next_chunk_index = self._current_chunk_count(document.id) if self.resume else 0
        self.db.commit()

        for page in extractor.iter_pages(document.storage_path):
            # Maintient la continuité chapitre/section même sur pages déjà traitées.
            self.tracker.update(page.text)
            state = self.tracker.state

            if page.number <= start_after:
                continue  # page déjà ingérée lors d'un run précédent

            page = self._maybe_ocr(document, page)
            if page.error:
                self._add_error(page.number, page.error)

            self._detect_and_store(document, page, state, next_chunk_index)
            next_chunk_index = self._current_chunk_count(document.id)

            self.result.processed_pages += 1
            document.processed_pages = page.number
            import_record.current_page = page.number
            import_record.message = f"Page {page.number}/{total}"
            self.db.commit()

        self._finalize(document, import_record)

    def _maybe_ocr(self, document: Document, page: ExtractedPage) -> ExtractedPage:
        if not page.needs_ocr:
            return page
        document.is_scanned = True
        if not self.ocr.available:
            page.error = (
                page.error
                or "Page scannée : OCR requis mais non configuré (texte ignoré)."
            )
            return page
        outcome = self.ocr.ocr_page(document.storage_path, page.number)
        if outcome.success:
            document.ocr_used = True
            self.result.ocr_pages += 1
            page.text = outcome.text
            page.ocr_used = True
        else:
            page.error = outcome.error or "Échec OCR."
        return page

    def _get_or_create_hs(
        self, code: str, description: str | None, chapter: str | None
    ) -> tuple[HsCode, bool]:
        """Récupère ou crée un code SH (déduplication globale par `code`).

        Si le code existe déjà, on met à jour la description (si meilleure) et le
        chapitre (si absent) plutôt que d'insérer un doublon. Retourne
        `(hs_code, created)`.
        """
        hs = self._hs_cache.get(code)
        if hs is None:
            hs = self.db.execute(
                select(HsCode).where(HsCode.code == code)
            ).scalar_one_or_none()

        if hs is None:
            hs = HsCode(code=code, description_fr=description or code, chapter=chapter)
            self.db.add(hs)
            self.db.flush()  # obtient l'id pour les rattachements (taxes, etc.)
            self._hs_cache[code] = hs
            return hs, True

        # Existant : mise à jour (jamais de doublon). On ne complète la
        # description que si elle est absente/placeholder — une description
        # officielle déjà enregistrée n'est jamais écrasée.
        self._hs_cache[code] = hs
        if description and (not hs.description_fr or hs.description_fr == hs.code):
            hs.description_fr = description
        if chapter and not hs.chapter:
            hs.chapter = chapter
        return hs, False

    def _has_tax(self, hs_id: uuid.UUID) -> bool:
        if hs_id in self._tax_codes:
            return True
        exists = self.db.execute(
            select(Tax.id).where(Tax.hs_code_id == hs_id).limit(1)
        ).first() is not None
        if exists:
            self._tax_codes.add(hs_id)
        return exists

    def _has_auth(self, hs_id: uuid.UUID) -> bool:
        if hs_id in self._auth_codes:
            return True
        exists = self.db.execute(
            select(Authorization.id).where(Authorization.hs_code_id == hs_id).limit(1)
        ).first() is not None
        if exists:
            self._auth_codes.add(hs_id)
        return exists

    @staticmethod
    def _chapter_of(code: str) -> str | None:
        """Chapitre déduit du CODE lui-même (« 3103.11 » → « Chapitre 31 »).

        Autorité de la source : le chapitre d'un code SH est encodé dans ses
        deux premiers chiffres. On ne dépend donc jamais d'un suivi « collant »
        de chapitre susceptible de déborder d'un chapitre à l'autre.
        """
        digits = "".join(ch for ch in code if ch.isdigit())
        return f"Chapitre {int(digits[:2])}" if len(digits) >= 2 else None

    def _store_authorizations(self, document, page, state, text: str) -> None:
        """Rattache une autorisation à un code SH figurant sur la même ligne.

        Fidélité stricte : uniquement lorsqu'un code SH et une mention
        d'autorisation apparaissent ensemble ; jamais inventé.
        """
        if not detect_authorizations(text).detected:
            return
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = HS_DOTTED_RE.search(line) or HS_HEADING_RE.search(line)
            if match is None:
                continue
            auth = classify_authorization(line)
            if not auth:
                continue
            code = match.group(1)
            status_str, ministry = auth
            hs, _ = self._get_or_create_hs(code, None, self._chapter_of(code))
            if not self._has_auth(hs.id):
                self.db.add(
                    Authorization(
                        hs_code_id=hs.id,
                        status=AuthorizationStatus(status_str),
                        ministry=ministry,
                        description_fr=line[:2000],
                    )
                )
                self._auth_codes.add(hs.id)
                self.result.authorizations_created += 1

    def _detect_and_store(self, document, page, state, start_index: int) -> None:
        text = page.text or ""
        if state.chapter:
            self._chapters.add(state.chapter)
        if state.section:
            self._sections.add(state.section)

        # Table tarifaire → codes SH + description hiérarchique + droit d'importation.
        # HsCode (opérationnel, dédupliqué), HsReference et DocumentReference
        # (traçabilité citable), Tax (colonne « Droit d'Importation »).
        entries = extract_hs_entries(text)
        for entry in entries:
            chapter = self._chapter_of(entry.code)  # chapitre issu du CODE (anti-bleed)
            hs, created = self._get_or_create_hs(entry.code, entry.description, chapter)
            if created:
                self.result.hs_codes_created += 1
            else:
                self.result.duplicates += 1
            if entry.description:
                self.result.descriptions_found += 1
            else:
                self.result.warnings.append({
                    "page": page.number,
                    "message": f"Code SH {entry.code} sans description sur la page.",
                })

            self.db.add(
                HsReference(
                    document_id=document.id,
                    hs_code=entry.code,
                    page=page.number,
                    chapter=chapter,
                    section=state.section,
                    description=entry.description,
                )
            )
            citation = " — ".join(
                p for p in (document.title, chapter, f"Page {page.number}") if p
            )
            self.db.add(
                DocumentReference(
                    product_id=None,
                    document_id=document.id,
                    page=page.number,
                    paragraph=entry.description,
                    citation=citation[:500],
                )
            )
            self.result.references_created += 1

            # Droit d'importation lu dans la colonne tarifaire → Tax.
            if entry.import_duty is not None and not self._has_tax(hs.id):
                self.db.add(
                    Tax(
                        hs_code_id=hs.id,
                        import_duty=entry.import_duty,
                        vat=entry.vat,
                        notes_fr=(entry.description or entry.code)[:2000],
                    )
                )
                self._tax_codes.add(hs.id)
                self.result.taxes_created += 1
        self.result.hs_codes_found += len(entries)
        if detect_tax_tables(text).detected:
            self.result.tax_tables_found += 1

        # Autorisations rattachées à un code SH (fidélité stricte).
        self._store_authorizations(document, page, state, text)

        # Découpage + embeddings
        drafts = chunk_page_text(
            text,
            page=page.number,
            chapter=state.chapter,
            section=state.section,
            start_index=start_index,
        )
        if drafts:
            vectors = self.embedder.embed([d.text for d in drafts])
            for draft, vector in zip(drafts, vectors):
                self.db.add(
                    TextChunk(
                        document_id=document.id,
                        chunk_index=draft.chunk_index,
                        page=draft.page,
                        chapter=draft.chapter,
                        section=draft.section,
                        chunk_text=draft.text,
                        embedding=vector,
                    )
                )
            self.result.chunks_created += len(drafts)

    def _finalize(self, document: Document, import_record: ImportHistory) -> None:
        self.result.chapters_count = len(self._chapters)
        self.result.sections_count = len(self._sections)
        self.result.execution_ms = int((time.perf_counter() - self._started_at) * 1000)
        has_errors = bool(self.result.errors)
        document.status = (
            DocumentStatus.PARTIEL if has_errors else DocumentStatus.TERMINE
        )
        import_record.status = (
            ImportStatus.PARTIEL if has_errors else ImportStatus.REUSSI
        )
        import_record.end_time = self._now()
        import_record.current_page = document.number_of_pages
        import_record.message = "Ingestion terminée"
        import_record.errors = self.result.errors
        import_record.stats = self.result.as_stats()
        self.db.commit()

    def _current_chunk_count(self, document_id: uuid.UUID) -> int:
        return int(
            self.db.execute(
                select(func.count())
                .select_from(TextChunk)
                .where(TextChunk.document_id == document_id)
            ).scalar_one()
        )

    def _reset_document_data(self, document: Document) -> None:
        """Réimport complet : purge les données extraites propres à ce document.

        Les codes SH opérationnels (HsCode) et leurs taxes/autorisations sont
        partagés et dédupliqués : ils ne sont pas supprimés mais ré-actualisés
        lors du réimport (upsert), afin de ne pas détruire des connaissances
        rattachées à d'autres documents.
        """
        for model in (TextChunk, HsReference, DocumentReference):
            self.db.query(model).filter(model.document_id == document.id).delete()
        document.processed_pages = 0
        document.is_scanned = False
        document.ocr_used = False
        self.db.commit()
