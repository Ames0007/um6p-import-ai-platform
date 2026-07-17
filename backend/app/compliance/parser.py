"""Extraction structurée d'une facture à partir du texte OCR.

Purement déterministe (regex/heuristiques) : n'invente rien, se contente de
repérer les informations présentes dans le texte. Les lignes non reconnues ne
sont pas fabriquées.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from app.services.importer.parsing import norm_date, norm_float

INCOTERMS = [
    "EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP",
    "DAP", "DPU", "DDP", "DAT",
]

_INVOICE_NO_RE = re.compile(
    r"(?:facture|invoice|n[°o]|no|ref(?:erence)?)\s*[:#.\-]?\s*([A-Za-z0-9][A-Za-z0-9/_\-]{2,})",
    re.IGNORECASE,
)
_DATE_RE = re.compile(r"\b(\d{1,4}[/\-.]\d{1,2}[/\-.]\d{1,4})\b")
_INCOTERM_RE = re.compile(r"\b(" + "|".join(INCOTERMS) + r")\b")
_NUMBER_RE = re.compile(r"\d[\d\s]*(?:[.,]\d+)?")
# Colonnes numériques en fin de ligne (qté / prix unitaire / total), séparées
# par des espaces — évite de couper un nom contenant des chiffres (« DM750 »).
_TRAILING_RE = re.compile(
    r"^(?P<name>.*?\S)\s{2,}"
    r"(?P<nums>\d[\d\s]*(?:[.,]\d+)?(?:\s+\d[\d\s]*(?:[.,]\d+)?){0,3})\s*$"
)
_SINGLE_TRAILING_RE = re.compile(
    r"^(?P<name>.*?[A-Za-zÀ-ÿ]\S*)\s+(?P<nums>\d[\d ]*(?:[.,]\d+)?)\s*$"
)
_SUPPLIER_HINT_RE = re.compile(
    r"(?:fournisseur|supplier|vendor|sold by|emetteur|vendeur)\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)
_HEADER_RE = re.compile(
    r"^\s*(total|sous[\-\s]?total|tva|montant|net\s|designation|description|"
    r"reference|ref\.|qte|quantite|prix|incoterm|date|facture|invoice|client|"
    r"adresse|page|devise|remise)\b",
    re.IGNORECASE,
)


@dataclass
class ParsedLine:
    line_number: int
    raw_text: str
    product_name: str
    quantity: float | None = None
    unit_price: float | None = None
    currency: str | None = None


@dataclass
class ParsedInvoice:
    supplier_name: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    currency: str | None = None
    incoterm: str | None = None
    lines: list[ParsedLine] = field(default_factory=list)


def _detect_currency(text: str) -> str | None:
    upper = text.upper()
    if "€" in text or re.search(r"\bEUR\b", upper):
        return "EUR"
    if "$" in text or re.search(r"\bUSD\b|\bUS ?D\b", upper):
        return "USD"
    if re.search(r"\bMAD\b|\bDHS?\b|DIRHAM", upper):
        return "MAD"
    return None


class InvoiceParser:
    def parse(self, text: str) -> ParsedInvoice:
        invoice = ParsedInvoice()
        if not text or not text.strip():
            return invoice

        invoice.currency = _detect_currency(text)

        m = _INVOICE_NO_RE.search(text)
        if m:
            invoice.invoice_number = m.group(1).strip()

        dm = _DATE_RE.search(text)
        if dm:
            try:
                invoice.invoice_date = norm_date(dm.group(1))
            except ValueError:
                invoice.invoice_date = None

        im = _INCOTERM_RE.search(text.upper())
        if im:
            invoice.incoterm = im.group(1)

        invoice.supplier_name = self._detect_supplier(text)
        invoice.lines = self._detect_lines(text, invoice.currency)
        return invoice

    def _detect_supplier(self, text: str) -> str | None:
        for line in text.splitlines():
            m = _SUPPLIER_HINT_RE.search(line)
            if m and m.group(1).strip():
                return m.group(1).strip()[:200]
        # À défaut : première ligne « nom propre » (lettres, peu de chiffres).
        for line in text.splitlines():
            s = line.strip()
            if len(s) >= 3 and sum(c.isalpha() for c in s) >= len(s) * 0.6:
                if not _HEADER_RE.match(s):
                    return s[:200]
        return None

    def _detect_lines(self, text: str, default_currency: str | None) -> list[ParsedLine]:
        lines: list[ParsedLine] = []
        counter = 0
        for raw in text.splitlines():
            s = raw.strip()
            if len(s) < 3 or _HEADER_RE.match(s):
                continue

            match = _TRAILING_RE.match(s) or _SINGLE_TRAILING_RE.match(s)
            if not match:
                continue
            name = match.group("name").strip(" .:-\t|")
            if sum(c.isalpha() for c in name) < 3:
                continue

            numbers = [
                norm_float(tok)
                for tok in match.group("nums").split()
                if tok.strip()
            ]
            numbers = [n for n in numbers if n is not None]
            if not numbers:
                continue

            counter += 1
            quantity: float | None = None
            unit_price: float | None = numbers[-1]
            if len(numbers) >= 2 and numbers[0] <= 100000:
                quantity = numbers[0]

            lines.append(
                ParsedLine(
                    line_number=counter,
                    raw_text=s,
                    product_name=name,
                    quantity=quantity,
                    unit_price=unit_price,
                    currency=_detect_currency(s) or default_currency,
                )
            )
        return lines


invoice_parser = InvoiceParser()
