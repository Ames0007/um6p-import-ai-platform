"""Service de la bibliothèque documentaire et de l'orchestration d'import."""
from __future__ import annotations

import logging
import shutil
import tempfile
import uuid
import zipfile
from datetime import date
from pathlib import Path
from typing import Sequence

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingestion.checksum import sha256_of_file
from app.ingestion.extractors import get_extractor
from app.ingestion.extractors.base import UnsupportedFormatError
from app.models.document import Document
from app.models.enums import DocumentCategory, DocumentStatus
from app.models.import_history import ImportHistory
from app.models.knowledge import HsReference, TextChunk
from app.schemas.document import (
    DocumentRead,
    DocumentUpdateMeta,
    ImportRunRead,
)
from app.workers import dispatch_ingestion

logger = logging.getLogger("documents")

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".xlsx", ".csv"}

# Mots-clés → catégorie (déduction à partir du nom de fichier).
_CATEGORY_HINTS: list[tuple[str, DocumentCategory]] = [
    ("code des douanes", DocumentCategory.CODE_DES_DOUANES),
    ("code_des_douanes", DocumentCategory.CODE_DES_DOUANES),
    ("nomenclature", DocumentCategory.NOMENCLATURE),
    ("chimiq", DocumentCategory.PRODUITS_CHIMIQUES),
    ("engrais", DocumentCategory.ENGRAIS),
    ("machine", DocumentCategory.MACHINES),
    ("plastiq", DocumentCategory.MATIERES_PLASTIQUES),
    ("controle", DocumentCategory.PRODUITS_CONTROLES),
    ("contrôlé", DocumentCategory.PRODUITS_CONTROLES),
    ("circulaire", DocumentCategory.CIRCULAIRES),
    ("annexe", DocumentCategory.ANNEXES),
]


class DuplicateDocumentError(Exception):
    """Un document au contenu identique (même checksum) existe déjà."""

    def __init__(self, existing: Document) -> None:
        self.existing = existing
        super().__init__(f"Document déjà présent : {existing.title}")


def _guess_category(filename: str) -> DocumentCategory:
    lower = filename.lower()
    for hint, category in _CATEGORY_HINTS:
        if hint in lower:
            return category
    return DocumentCategory.AUTRE


class DocumentService:
    # -- stockage --
    def _storage_dir(self) -> Path:
        path = Path(settings.DOCUMENTS_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    # -- lecture / bibliothèque --
    def get(self, db: Session, document_id: uuid.UUID) -> Document | None:
        return db.get(Document, document_id)

    def list(self, db: Session, *, skip: int = 0, limit: int = 100) -> Sequence[Document]:
        stmt = (
            select(Document)
            .order_by(Document.upload_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return db.execute(stmt).scalars().all()

    def to_read(self, db: Session, document: Document) -> DocumentRead:
        """Construit le schéma de lecture avec les champs calculés."""
        hs_count = int(
            db.execute(
                select(func.count())
                .select_from(HsReference)
                .where(HsReference.document_id == document.id)
            ).scalar_one()
        )
        last_import = db.execute(
            select(ImportHistory)
            .where(ImportHistory.document_id == document.id)
            .order_by(ImportHistory.start_time.desc().nullslast())
            .limit(1)
        ).scalar_one_or_none()

        errors_count = 0
        processing_time = None
        last_import_read = None
        if last_import is not None:
            errors_count = len(last_import.errors or [])
            processing_time = last_import.duration_seconds
            last_import_read = ImportRunRead.model_validate(
                {
                    **{
                        k: getattr(last_import, k)
                        for k in (
                            "id",
                            "status",
                            "start_time",
                            "end_time",
                            "current_page",
                            "total_pages",
                            "message",
                            "errors",
                            "stats",
                        )
                    },
                    "duration_seconds": last_import.duration_seconds,
                }
            )

        progress = 0.0
        if document.number_of_pages:
            progress = round(
                100 * document.processed_pages / document.number_of_pages, 1
            )

        data = DocumentRead.model_validate(document)
        data.extracted_hs_count = hs_count
        data.extraction_errors_count = errors_count
        data.processing_time_seconds = processing_time
        data.progress_percent = min(progress, 100.0)
        data.last_import = last_import_read
        return data

    # -- création / import --
    def _persist_file(self, source: Path, original_name: str) -> tuple[Path, str, int]:
        checksum = sha256_of_file(source)
        stored_name = f"{checksum[:16]}_{original_name}"
        target = self._storage_dir() / stored_name
        if not target.exists():
            shutil.copyfile(source, target)
        return target, checksum, target.stat().st_size

    def _find_by_checksum(self, db: Session, checksum: str) -> Document | None:
        return db.execute(
            select(Document).where(Document.checksum == checksum).limit(1)
        ).scalar_one_or_none()

    def _count_pages_safe(self, path: Path) -> int:
        try:
            return get_extractor(path).count_pages(path)
        except Exception:  # comptage best-effort ; le pipeline recomptera
            return 0

    def create_document(
        self,
        db: Session,
        *,
        source_path: Path,
        original_name: str,
        meta: DocumentUpdateMeta | None = None,
        allow_duplicate: bool = False,
    ) -> Document:
        """Crée un document à partir d'un fichier déjà présent sur disque."""
        suffix = Path(original_name).suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            raise UnsupportedFormatError(f"Format non pris en charge : {suffix}")

        stored_path, checksum, size = self._persist_file(source_path, original_name)

        existing = self._find_by_checksum(db, checksum)
        if existing and not allow_duplicate:
            raise DuplicateDocumentError(existing)

        meta = meta or DocumentUpdateMeta()
        document = Document(
            title=meta.title or Path(original_name).stem,
            filename=original_name,
            category=meta.category or _guess_category(original_name),
            version=meta.version,
            publication_date=meta.publication_date,
            language=meta.language or "fr",
            number_of_pages=self._count_pages_safe(stored_path),
            status=DocumentStatus.EN_ATTENTE,
            checksum=checksum,
            storage_path=str(stored_path),
            mime_type=None,
            size_bytes=size,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    def _iter_zip_pdfs(self, zip_path: Path):
        """Extrait les PDF d'une archive ZIP vers un répertoire temporaire."""
        tmp_dir = Path(tempfile.mkdtemp(prefix="um6p_zip_"))
        with zipfile.ZipFile(zip_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = Path(info.filename).name
                if Path(name).suffix.lower() != ".pdf":
                    continue
                extracted = tmp_dir / name
                with archive.open(info) as src, extracted.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                yield extracted, name

    def ingest_upload(
        self,
        db: Session,
        file: UploadFile,
        *,
        meta: DocumentUpdateMeta | None = None,
        allow_duplicate: bool = False,
    ) -> tuple[list[Document], list[str], str]:
        """Persiste un upload (fichier unique ou ZIP), crée les documents et
        planifie leur ingestion. Retourne (documents, doublons, mode)."""
        tmp = Path(tempfile.mkdtemp(prefix="um6p_up_"))
        tmp_file = tmp / (file.filename or "document")
        with tmp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        created: list[Document] = []
        duplicates: list[str] = []

        try:
            if tmp_file.suffix.lower() == ".zip":
                for member_path, member_name in self._iter_zip_pdfs(tmp_file):
                    self._create_or_record_duplicate(
                        db, member_path, member_name, meta, allow_duplicate,
                        created, duplicates,
                    )
            else:
                self._create_or_record_duplicate(
                    db, tmp_file, file.filename or tmp_file.name, meta,
                    allow_duplicate, created, duplicates,
                )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        mode = "inline"
        for document in created:
            mode = dispatch_ingestion(document.id, resume=True)

        return created, duplicates, mode

    def _create_or_record_duplicate(
        self, db, path, name, meta, allow_duplicate, created, duplicates
    ) -> None:
        try:
            document = self.create_document(
                db,
                source_path=path,
                original_name=name,
                meta=meta,
                allow_duplicate=allow_duplicate,
            )
            created.append(document)
        except DuplicateDocumentError:
            duplicates.append(name)

    # -- réimport / suppression --
    def reimport(self, db: Session, document: Document) -> str:
        """Relance une ingestion complète (purge des données extraites)."""
        document.status = DocumentStatus.EN_ATTENTE
        document.processed_pages = 0
        document.error_message = None
        db.commit()
        return dispatch_ingestion(document.id, resume=False)

    def delete(self, db: Session, document: Document) -> None:
        stored = Path(document.storage_path)
        db.delete(document)  # cascade sur chunks / hs_refs / imports
        db.commit()
        try:
            if stored.exists():
                stored.unlink()
        except OSError:
            logger.warning("Fichier non supprimé : %s", stored)

    # -- reprise après interruption --
    def resume_interrupted(self, db: Session) -> int:
        """Relance les documents laissés « en_traitement » (redémarrage/panne)."""
        stmt = select(Document).where(
            Document.status == DocumentStatus.EN_TRAITEMENT
        )
        stuck = db.execute(stmt).scalars().all()
        for document in stuck:
            logger.info("Reprise de l'ingestion interrompue : %s", document.id)
            dispatch_ingestion(document.id, resume=True)
        return len(stuck)


document_service = DocumentService()
