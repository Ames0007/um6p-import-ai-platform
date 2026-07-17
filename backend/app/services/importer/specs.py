"""Spécifications d'import par ressource : champs cibles, résolution des
clés étrangères par clé naturelle, normalisation, détection de doublons.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.authorization import Authorization
from app.models.country import Country
from app.models.enums import AuthorizationStatus, ProductStatus
from app.models.hs_code import HsCode
from app.models.product import Product
from app.models.product_alias import ProductAlias
from app.models.purchase_history import PurchaseHistory
from app.models.supplier import Supplier
from app.models.tax import Tax
from app.schemas.importer import TargetField
from app.services.importer.parsing import (
    norm_date,
    norm_datetime,
    norm_float,
    norm_int,
    norm_keywords,
    norm_str,
)


# ----------------- résolveurs de clés naturelles -----------------
def _resolve_country(db: Session, value) -> Any:
    v = norm_str(value)
    if not v:
        return None
    row = db.execute(
        select(Country).where(func.lower(Country.code) == v.lower())
    ).scalar_one_or_none()
    if row is None:
        row = db.execute(
            select(Country).where(func.lower(Country.name_fr) == v.lower())
        ).scalar_one_or_none()
    if row is None:
        raise ValueError(f"Pays inconnu : « {value} »")
    return row.id


def _resolve_hs(db: Session, value) -> Any:
    v = norm_str(value)
    if not v:
        return None
    row = db.execute(select(HsCode).where(HsCode.code == v)).scalar_one_or_none()
    if row is None:
        raise ValueError(f"Code SH inconnu : « {value} »")
    return row.id


def _resolve_supplier(db: Session, value) -> Any:
    v = norm_str(value)
    if not v:
        return None
    row = db.execute(
        select(Supplier).where(func.lower(Supplier.name) == v.lower())
    ).scalar_one_or_none()
    if row is None:
        raise ValueError(f"Fournisseur inconnu : « {value} »")
    return row.id


def _resolve_product(db: Session, ref, name) -> Any:
    ref = norm_str(ref)
    name = norm_str(name)
    row = None
    if ref:
        row = db.execute(
            select(Product).where(Product.reference == ref)
        ).scalar_one_or_none()
    if row is None and name:
        row = db.execute(
            select(Product).where(func.lower(Product.name) == name.lower())
        ).scalar_one_or_none()
    if row is None:
        raise ValueError(f"Produit inconnu : « {ref or name} »")
    return row.id


def _product_status(value) -> ProductStatus:
    v = (norm_str(value) or "actif").lower()
    mapping = {
        "actif": ProductStatus.ACTIF,
        "inactif": ProductStatus.INACTIF,
        "archive": ProductStatus.ARCHIVE,
        "archivé": ProductStatus.ARCHIVE,
    }
    return mapping.get(v, ProductStatus.ACTIF)


def _auth_status(value) -> AuthorizationStatus:
    v = (norm_str(value) or "non_requise").lower()
    mapping = {
        "requise": AuthorizationStatus.REQUISE,
        "non_requise": AuthorizationStatus.NON_REQUISE,
        "non requise": AuthorizationStatus.NON_REQUISE,
        "conditionnelle": AuthorizationStatus.CONDITIONNELLE,
    }
    return mapping.get(v, AuthorizationStatus.NON_REQUISE)


# ----------------- spécification -----------------
@dataclass
class ImportSpec:
    resource: str
    model: type
    target_fields: list[TargetField]
    build: Callable[[Session, dict], dict]
    dedup_field: str | None = None
    find_existing: Callable[[Session, dict], Any] | None = None

    def suggest_mapping(self, columns: list[str]) -> dict[str, str]:
        """Propose une correspondance colonne→champ par similarité de nom."""
        targets = {tf.name: tf for tf in self.target_fields}
        mapping: dict[str, str] = {}
        for col in columns:
            key = col.strip().lower().replace(" ", "_").replace("-", "_")
            if key in targets:
                mapping[col] = key
            else:
                for name in targets:
                    if key == name or key in name or name in key:
                        mapping[col] = name
                        break
        return mapping


def _tf(name: str, label: str, required: bool = False) -> TargetField:
    return TargetField(name=name, label=label, required=required)


# ----------------- builders par ressource -----------------
def _build_country(db, v) -> dict:
    return {"code": norm_str(v.get("code")), "name_fr": norm_str(v.get("name_fr"))}


def _build_hs(db, v) -> dict:
    return {
        "code": norm_str(v.get("code")),
        "description_fr": norm_str(v.get("description_fr")),
        "chapter": norm_str(v.get("chapter")),
    }


def _build_supplier(db, v) -> dict:
    return {
        "name": norm_str(v.get("name")),
        "country_id": _resolve_country(db, v.get("country")),
        "website": norm_str(v.get("website")),
        "contact_name": norm_str(v.get("contact_name")),
        "email": norm_str(v.get("email")),
        "phone": norm_str(v.get("phone")),
        "lead_time_days": norm_int(v.get("lead_time_days")),
    }


def _build_product(db, v) -> dict:
    return {
        "reference": norm_str(v.get("reference")),
        "name": norm_str(v.get("name")),
        "manufacturer": norm_str(v.get("manufacturer")),
        "brand": norm_str(v.get("brand")),
        "category": norm_str(v.get("category")),
        "description_fr": norm_str(v.get("description_fr")),
        "keywords": norm_keywords(v.get("keywords")),
        "country_of_origin_id": _resolve_country(db, v.get("country_of_origin")),
        "preferred_supplier_id": _resolve_supplier(db, v.get("preferred_supplier")),
        "hs_code_id": _resolve_hs(db, v.get("hs_code")),
        "status": _product_status(v.get("status")),
        "notes": norm_str(v.get("notes")),
    }


def _build_alias(db, v) -> dict:
    return {
        "product_id": _resolve_product(db, v.get("product_reference"), v.get("product_name")),
        "alias": norm_str(v.get("alias")),
    }


def _build_tax(db, v) -> dict:
    return {
        "hs_code_id": _resolve_hs(db, v.get("hs_code")),
        "country_id": _resolve_country(db, v.get("country")),
        "import_duty": norm_float(v.get("import_duty")),
        "vat": norm_float(v.get("vat")),
        "parafiscal_tax": norm_float(v.get("parafiscal_tax")),
        "effective_date": norm_date(v.get("effective_date")),
        "notes_fr": norm_str(v.get("notes_fr")),
    }


def _build_authorization(db, v) -> dict:
    return {
        "hs_code_id": _resolve_hs(db, v.get("hs_code")),
        "status": _auth_status(v.get("status")),
        "organization": norm_str(v.get("organization")),
        "ministry": norm_str(v.get("ministry")),
        "legal_reference": norm_str(v.get("legal_reference")),
        "processing_time_days": norm_int(v.get("processing_time_days")),
        "comments": norm_str(v.get("comments")),
        "description_fr": norm_str(v.get("description_fr")),
    }


def _build_purchase(db, v) -> dict:
    unit_price = norm_float(v.get("unit_price"))
    if unit_price is None:
        raise ValueError("Prix unitaire manquant")
    purchased_at = norm_datetime(v.get("purchased_at"))
    if purchased_at is None:
        raise ValueError("Date d'achat manquante")
    return {
        "product_id": _resolve_product(db, v.get("product_reference"), v.get("product_name")),
        "supplier_id": _resolve_supplier(db, v.get("supplier")),
        "country_id": _resolve_country(db, v.get("country")),
        "invoice_number": norm_str(v.get("invoice_number")),
        "unit_price": unit_price,
        "currency": norm_str(v.get("currency")) or "MAD",
        "quantity": norm_int(v.get("quantity")) or 1,
        "incoterm": norm_str(v.get("incoterm")),
        "purchased_at": purchased_at,
    }


# ----------------- registre des specs -----------------
SPECS: dict[str, ImportSpec] = {
    "countries": ImportSpec(
        "countries", Country,
        [_tf("code", "Code ISO", True), _tf("name_fr", "Nom (FR)", True)],
        _build_country, dedup_field="code",
    ),
    "hs_codes": ImportSpec(
        "hs_codes", HsCode,
        [_tf("code", "Code SH", True), _tf("description_fr", "Description", True),
         _tf("chapter", "Chapitre")],
        _build_hs, dedup_field="code",
    ),
    "suppliers": ImportSpec(
        "suppliers", Supplier,
        [_tf("name", "Nom", True), _tf("country", "Pays (code/nom)"),
         _tf("website", "Site web"), _tf("contact_name", "Contact"),
         _tf("email", "Email"), _tf("phone", "Téléphone"),
         _tf("lead_time_days", "Délai (jours)")],
        _build_supplier, dedup_field="name",
    ),
    "products": ImportSpec(
        "products", Product,
        [_tf("reference", "Référence interne"), _tf("name", "Nom", True),
         _tf("manufacturer", "Fabricant"), _tf("brand", "Marque"),
         _tf("category", "Catégorie"), _tf("description_fr", "Description"),
         _tf("keywords", "Mots-clés"), _tf("country_of_origin", "Pays d'origine"),
         _tf("preferred_supplier", "Fournisseur privilégié"),
         _tf("hs_code", "Code SH"), _tf("status", "Statut"), _tf("notes", "Notes")],
        _build_product, dedup_field="reference",
    ),
    "product_aliases": ImportSpec(
        "product_aliases", ProductAlias,
        [_tf("product_reference", "Réf. produit"), _tf("product_name", "Nom produit"),
         _tf("alias", "Alias", True)],
        _build_alias,
        find_existing=lambda db, k: db.execute(
            select(ProductAlias).where(
                ProductAlias.product_id == k["product_id"],
                func.lower(ProductAlias.alias) == (k["alias"] or "").lower(),
            )
        ).scalar_one_or_none(),
    ),
    "taxes": ImportSpec(
        "taxes", Tax,
        [_tf("hs_code", "Code SH", True), _tf("country", "Pays"),
         _tf("import_duty", "Droit d'importation %"), _tf("vat", "TVA %"),
         _tf("parafiscal_tax", "Taxe parafiscale %"),
         _tf("effective_date", "Date d'effet"), _tf("notes_fr", "Notes")],
        _build_tax,
        find_existing=lambda db, k: db.execute(
            select(Tax).where(
                Tax.hs_code_id == k["hs_code_id"],
                Tax.effective_date == k.get("effective_date"),
            )
        ).scalar_one_or_none(),
    ),
    "authorizations": ImportSpec(
        "authorizations", Authorization,
        [_tf("hs_code", "Code SH", True), _tf("status", "Statut"),
         _tf("organization", "Organisme"), _tf("ministry", "Ministère"),
         _tf("legal_reference", "Référence légale"),
         _tf("processing_time_days", "Délai (jours)"),
         _tf("comments", "Commentaires"), _tf("description_fr", "Description")],
        _build_authorization,
        find_existing=lambda db, k: db.execute(
            select(Authorization).where(Authorization.hs_code_id == k["hs_code_id"])
        ).scalar_one_or_none(),
    ),
    "purchase_history": ImportSpec(
        "purchase_history", PurchaseHistory,
        [_tf("product_reference", "Réf. produit"), _tf("product_name", "Nom produit"),
         _tf("supplier", "Fournisseur"), _tf("country", "Pays"),
         _tf("invoice_number", "Facture"), _tf("unit_price", "Prix unitaire", True),
         _tf("currency", "Devise"), _tf("quantity", "Quantité"),
         _tf("incoterm", "Incoterm"), _tf("purchased_at", "Date d'achat", True)],
        _build_purchase,
        find_existing=lambda db, k: (
            db.execute(
                select(PurchaseHistory).where(
                    PurchaseHistory.product_id == k["product_id"],
                    PurchaseHistory.invoice_number == k.get("invoice_number"),
                )
            ).scalar_one_or_none()
            if k.get("invoice_number")
            else None
        ),
    ),
}


def get_spec(resource: str) -> ImportSpec:
    if resource not in SPECS:
        raise KeyError(f"Ressource d'import inconnue : {resource}")
    return SPECS[resource]
