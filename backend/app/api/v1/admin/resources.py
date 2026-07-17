"""Registre des ressources de l'administration (config CRUD générique)."""
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from app.models.authorization import Authorization
from app.models.country import Country
from app.models.hs_code import HsCode
from app.models.product import Product
from app.models.product_alias import ProductAlias
from app.models.purchase_history import PurchaseHistory
from app.models.supplier import Supplier
from app.models.tax import Tax
from app.schemas import admin as S
from app.services.crud import CRUDService


@dataclass
class ResourceConfig:
    name: str  # segment d'URL (ex. "products")
    tag: str  # étiquette OpenAPI (FR)
    crud: CRUDService
    create_schema: type[BaseModel]
    update_schema: type[BaseModel]
    read_schema: type[BaseModel]


RESOURCES: list[ResourceConfig] = [
    ResourceConfig(
        "countries", "Admin · Pays",
        CRUDService(Country, entity_type="countries",
                    search_fields=["code", "name_fr"],
                    sortable_fields=["code", "name_fr"], default_sort="name_fr"),
        S.CountryCreate, S.CountryUpdate, S.CountryRead,
    ),
    ResourceConfig(
        "hs-codes", "Admin · Codes SH",
        CRUDService(HsCode, entity_type="hs_codes",
                    search_fields=["code", "description_fr", "chapter"],
                    sortable_fields=["code", "chapter"], default_sort="code"),
        S.HsCodeCreate, S.HsCodeUpdate, S.HsCodeRead,
    ),
    ResourceConfig(
        "taxes", "Admin · Taxes",
        CRUDService(Tax, entity_type="taxes",
                    search_fields=["notes_fr"],
                    sortable_fields=["effective_date", "import_duty", "vat"],
                    default_sort="effective_date"),
        S.TaxCreate, S.TaxUpdate, S.TaxRead,
    ),
    ResourceConfig(
        "authorizations", "Admin · Autorisations",
        CRUDService(Authorization, entity_type="authorizations",
                    search_fields=["organization", "ministry", "legal_reference"],
                    sortable_fields=["status", "processing_time_days"],
                    default_sort="created_at"),
        S.AuthorizationCreate, S.AuthorizationUpdate, S.AuthorizationRead,
    ),
    ResourceConfig(
        "suppliers", "Admin · Fournisseurs",
        CRUDService(Supplier, entity_type="suppliers",
                    search_fields=["name", "email", "contact_name"],
                    sortable_fields=["name", "lead_time_days"], default_sort="name"),
        S.SupplierCreate, S.SupplierUpdate, S.SupplierRead,
    ),
    ResourceConfig(
        "products", "Admin · Produits",
        CRUDService(Product, entity_type="products",
                    search_fields=["name", "reference", "brand", "manufacturer",
                                   "category"],
                    sortable_fields=["name", "reference", "category", "status"],
                    default_sort="name"),
        S.ProductCreate, S.ProductUpdate, S.ProductRead,
    ),
    ResourceConfig(
        "product-aliases", "Admin · Alias Produits",
        CRUDService(ProductAlias, entity_type="product_aliases",
                    search_fields=["alias"], sortable_fields=["alias"],
                    default_sort="alias"),
        S.ProductAliasCreate, S.ProductAliasUpdate, S.ProductAliasRead,
    ),
    ResourceConfig(
        "purchase-history", "Admin · Historique des achats",
        CRUDService(PurchaseHistory, entity_type="purchase_history",
                    search_fields=["invoice_number", "incoterm"],
                    sortable_fields=["purchased_at", "unit_price", "quantity"],
                    default_sort="purchased_at"),
        S.PurchaseCreate, S.PurchaseUpdate, S.PurchaseRead,
    ),
]

RESOURCE_BY_NAME = {r.name: r for r in RESOURCES}

# Filtres d'égalité autorisés en query string (ignorés si absents du modèle).
ALLOWED_FILTERS = (
    "status",
    "category",
    "hs_code_id",
    "country_id",
    "supplier_id",
    "product_id",
    "country_of_origin_id",
    "preferred_supplier_id",
)
