"""Architecture de fournisseurs OCR (configurable) pour l'extraction de factures.

Fournisseurs :
- pdf_text  : extraction texte native (PDF/DOCX/XLSX/CSV via les extracteurs Phase 2)
- tesseract : OCR local (images + PDF scannés) — hook, dépendances optionnelles
- azure     : Azure Document Intelligence — hook, SDK + identifiants requis
- google    : Google Document AI — hook, SDK + identifiants requis
- noop      : aucun OCR

Sélection via `settings.OCR_PROVIDER`. Repli automatique sur Tesseract pour les
images / PDF scannés lorsque l'extraction native ne renvoie rien.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.ingestion.extractors import get_extractor
from app.ingestion.extractors.base import (
    CorruptedDocumentError,
    UnsupportedFormatError,
)

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


@dataclass
class OcrExtraction:
    text: str
    pages: int
    provider: str
    confidence: float | None = None
    error: str | None = None


class DocumentOcrProvider(abc.ABC):
    name: str = "base"

    @property
    @abc.abstractmethod
    def available(self) -> bool:
        ...

    @abc.abstractmethod
    def extract(self, path: str | Path) -> OcrExtraction:
        ...


class PdfTextProvider(DocumentOcrProvider):
    """Extraction texte native (sans OCR). Idéal pour les documents numériques."""

    name = "pdf_text"

    @property
    def available(self) -> bool:
        return True

    def extract(self, path: str | Path) -> OcrExtraction:
        suffix = Path(path).suffix.lower()
        if suffix in IMAGE_SUFFIXES:
            return OcrExtraction(
                text="", pages=0, provider=self.name,
                error="Image : nécessite un OCR (pdf_text ne traite pas les images).",
            )
        try:
            extractor = get_extractor(path)
        except UnsupportedFormatError as exc:
            return OcrExtraction(text="", pages=0, provider=self.name, error=str(exc))
        try:
            pages = list(extractor.iter_pages(path))
        except CorruptedDocumentError as exc:
            return OcrExtraction(text="", pages=0, provider=self.name, error=str(exc))
        text = "\n".join(p.text for p in pages if p.text)
        return OcrExtraction(text=text, pages=len(pages), provider=self.name)


class TesseractProvider(DocumentOcrProvider):
    """OCR local Tesseract (images + PDF scannés). Dépendances optionnelles."""

    name = "tesseract"

    def __init__(self, lang: str = "fra+eng") -> None:
        self.lang = lang
        self._ready = False
        try:
            import pytesseract  # noqa: F401
            from PIL import Image  # noqa: F401

            self._ready = True
        except ImportError:
            self._ready = False

    @property
    def available(self) -> bool:
        return self._ready

    def extract(self, path: str | Path) -> OcrExtraction:
        if not self._ready:
            return OcrExtraction(
                text="", pages=0, provider=self.name,
                error="Dépendances OCR absentes (pytesseract / Pillow).",
            )
        suffix = Path(path).suffix.lower()
        try:
            import pytesseract
            from PIL import Image

            if suffix in IMAGE_SUFFIXES:
                text = pytesseract.image_to_string(Image.open(path), lang=self.lang)
                return OcrExtraction(text=text, pages=1, provider=self.name)

            # PDF scanné → rendu en images via pdf2image, puis OCR page par page.
            import pdf2image

            images = pdf2image.convert_from_path(str(path), dpi=200)
            parts = [
                pytesseract.image_to_string(img, lang=self.lang) for img in images
            ]
            return OcrExtraction(
                text="\n".join(parts), pages=len(images), provider=self.name
            )
        except Exception as exc:  # OCR non bloquant
            return OcrExtraction(
                text="", pages=0, provider=self.name, error=f"Échec OCR : {exc}"
            )


class AzureDocumentProvider(DocumentOcrProvider):
    """Azure Document Intelligence (hook). Requiert le SDK + identifiants."""

    name = "azure"

    @property
    def available(self) -> bool:
        if not (settings.AZURE_DOCUMENT_ENDPOINT and settings.AZURE_DOCUMENT_KEY):
            return False
        try:
            import azure.ai.formrecognizer  # noqa: F401

            return True
        except ImportError:
            return False

    def extract(self, path: str | Path) -> OcrExtraction:
        if not self.available:
            return OcrExtraction(
                text="", pages=0, provider=self.name,
                error="Azure Document Intelligence non configuré.",
            )
        try:  # pragma: no cover - dépend d'un service externe
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential

            client = DocumentAnalysisClient(
                settings.AZURE_DOCUMENT_ENDPOINT,
                AzureKeyCredential(settings.AZURE_DOCUMENT_KEY),
            )
            with open(path, "rb") as fh:
                poller = client.begin_analyze_document("prebuilt-read", fh)
            result = poller.result()
            return OcrExtraction(
                text=result.content or "",
                pages=len(result.pages or []),
                provider=self.name,
            )
        except Exception as exc:  # pragma: no cover
            return OcrExtraction(
                text="", pages=0, provider=self.name, error=f"Échec Azure : {exc}"
            )


class GoogleDocumentProvider(DocumentOcrProvider):
    """Google Document AI (hook). Requiert le SDK + identifiants."""

    name = "google"

    @property
    def available(self) -> bool:
        if not (settings.GOOGLE_DOCUMENT_PROJECT and settings.GOOGLE_DOCUMENT_PROCESSOR):
            return False
        try:
            import google.cloud.documentai  # noqa: F401

            return True
        except ImportError:
            return False

    def extract(self, path: str | Path) -> OcrExtraction:
        # Intégration à compléter lors de l'activation (SDK + processeur).
        return OcrExtraction(
            text="", pages=0, provider=self.name,
            error="Google Document AI non configuré.",
        )


class NoOpProvider(DocumentOcrProvider):
    name = "noop"

    @property
    def available(self) -> bool:
        return False

    def extract(self, path: str | Path) -> OcrExtraction:
        return OcrExtraction(text="", pages=0, provider=self.name, error="OCR désactivé.")


_PROVIDERS: dict[str, type[DocumentOcrProvider]] = {
    "pdf_text": PdfTextProvider,
    "tesseract": TesseractProvider,
    "azure": AzureDocumentProvider,
    "google": GoogleDocumentProvider,
    "noop": NoOpProvider,
}


def get_provider(name: str | None = None) -> DocumentOcrProvider:
    key = (name or settings.OCR_PROVIDER or "pdf_text").lower()
    return _PROVIDERS.get(key, PdfTextProvider)()


def extract_document(path: str | Path, provider_name: str | None = None) -> OcrExtraction:
    """Extrait le texte avec le fournisseur configuré ; repli OCR si besoin."""
    provider = get_provider(provider_name)
    extraction = provider.extract(path)

    needs_ocr = (not extraction.text.strip()) and provider.name != "tesseract"
    if needs_ocr:
        tesseract = TesseractProvider()
        if tesseract.available:
            fallback = tesseract.extract(path)
            if fallback.text.strip():
                return fallback
    return extraction
