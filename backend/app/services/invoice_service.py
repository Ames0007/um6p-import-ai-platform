"""Service Factures : enregistrement du fichier importé.

L'extraction/analyse par l'IA n'est pas implémentée à ce stade ; le service se
limite à persister le fichier et son métadonnées.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import InvoiceStatus
from app.models.invoice import Invoice
from app.services.base import BaseService


class InvoiceService(BaseService[Invoice]):
    def __init__(self) -> None:
        super().__init__(Invoice)

    def _upload_dir(self) -> Path:
        path = Path(settings.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_upload(self, db: Session, file: UploadFile) -> Invoice:
        """Persiste le fichier sur disque et crée l'enregistrement Facture."""
        stored_name = f"{uuid.uuid4()}_{file.filename}"
        target = self._upload_dir() / stored_name

        size = 0
        with target.open("wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                buffer.write(chunk)

        invoice = Invoice(
            filename=file.filename or stored_name,
            stored_path=str(target),
            mime_type=file.content_type,
            size_bytes=size,
            status=InvoiceStatus.RECUE,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice


invoice_service = InvoiceService()
