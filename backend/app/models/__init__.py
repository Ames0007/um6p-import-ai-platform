"""Agrégation des modèles.

Importer ce module garantit que tous les modèles sont enregistrés sur la
métadonnée de `Base` (nécessaire pour Alembic autogenerate).
"""
from app.db.base_class import Base
from app.models.ai_request_log import AiRequestLog
from app.models.audit_log import AuditLog
from app.models.authorization import Authorization
from app.models.compliance import (
    AnalysisReport,
    ComplianceFinding,
    ImportAnalysis,
    ImportAnalysisItem,
    OCRResult,
    PriceAlert,
    ProductCandidate,
)
from app.models.conversation import Conversation, Message
from app.models.country import Country
from app.models.document import Document
from app.models.hs_code import HsCode
from app.models.import_history import ImportHistory
from app.models.invoice import Invoice
from app.models.knowledge import DocumentReference, HsReference, TextChunk
from app.models.knowledge_index import KnowledgeIndex
from app.models.product import Product
from app.models.product_alias import ProductAlias
from app.models.purchase_history import PurchaseHistory
from app.models.supplier import Supplier
from app.models.tax import Tax

__all__ = [
    "Base",
    "AiRequestLog",
    "AnalysisReport",
    "AuditLog",
    "Authorization",
    "ComplianceFinding",
    "ImportAnalysis",
    "ImportAnalysisItem",
    "OCRResult",
    "PriceAlert",
    "ProductCandidate",
    "Conversation",
    "Message",
    "Country",
    "Document",
    "DocumentReference",
    "HsCode",
    "HsReference",
    "ImportHistory",
    "Invoice",
    "KnowledgeIndex",
    "Product",
    "ProductAlias",
    "PurchaseHistory",
    "Supplier",
    "Tax",
    "TextChunk",
]
