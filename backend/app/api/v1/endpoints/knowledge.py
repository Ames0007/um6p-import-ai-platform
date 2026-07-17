"""Endpoints de recherche dans la base de connaissances officielle."""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.knowledge_index import KI_CHAPTER, KI_HS_CODE, KnowledgeIndex
from app.schemas.knowledge_index import (
    KnowledgeResult,
    LookupResponse,
    Suggestion,
    SuggestResponse,
)
from app.schemas.search import SearchResponse
from app.services.knowledge_index import knowledge_index_search
from app.services.knowledge_service import knowledge_service
from app.services.search_service import search_service

router = APIRouter(prefix="/knowledge", tags=["Base de connaissances"])

# Détection de mode (côté serveur, sans IA) — code SH exact ou chapitre.
_HS_EXACT_RE = re.compile(r"^\d{4}\.\d{2}(?:\.\d{2}){0,2}$")
_CHAPTER_RE = re.compile(r"^\s*(?:chapitre\s*)?(\d{1,2})\s*$", re.IGNORECASE)
_CHAPTER_WORD_RE = re.compile(r"chapitre\s*(\d{1,2})", re.IGNORECASE)


def _to_result(hit) -> KnowledgeResult:
    return KnowledgeResult(
        id=hit.id, type=hit.type, reference=hit.reference, title=hit.title,
        chapter=hit.chapter, section=hit.section,
        document_id=str(hit.document_id) if hit.document_id else None,
        document_title=hit.document_title, page=hit.page,
        description=hit.description, taxes=hit.taxes,
        authorizations=hit.authorizations, source_table=hit.source_table,
        source_pk=hit.source_pk, score=hit.score,
    )


def _chapter_codes(db: Session, chapter: str) -> list[KnowledgeResult]:
    rows = db.execute(
        select(KnowledgeIndex)
        .where(KnowledgeIndex.type == KI_HS_CODE, KnowledgeIndex.chapter == chapter)
        .order_by(KnowledgeIndex.reference)
        .limit(200)
    ).scalars().all()
    return [
        KnowledgeResult(
            id=str(r.id), type=r.type, reference=r.reference, title=r.title,
            chapter=r.chapter, section=r.section,
            document_id=str(r.document_id) if r.document_id else None,
            document_title=r.document_title, page=r.page, description=r.description,
            taxes=r.taxes, authorizations=r.authorizations,
            source_table=r.source_table, source_pk=r.source_pk, score=0.0,
        )
        for r in rows
    ]


@router.get("/lookup", response_model=LookupResponse)
def knowledge_lookup(
    q: str = Query(..., min_length=1, description="Terme, code SH, chapitre, produit…"),
    limit: int = Query(default=8, le=50),
    db: Session = Depends(get_db),
) -> LookupResponse:
    """Recherche instantanée par CONCEPT dans l'Index de connaissance (sans IA).

    Sélection de mode automatique : code SH exact → l'enregistrement précis ;
    chapitre → aperçu du chapitre (ses codes SH) ; sinon → résultats classés.
    Ne fait qu'interroger `knowledge_index` (PostgreSQL reste la source de vérité).
    """
    # Phase 7 : lecture seule — aucun rebuild sur le chemin de recherche.
    query = q.strip()

    # 1) Code SH exact -> renvoi immédiat.
    if _HS_EXACT_RE.match(query):
        hit = knowledge_index_search.by_reference(db, KI_HS_CODE, query)
        if hit is not None:
            return LookupResponse(query=query, mode="exact_hs", results=[_to_result(hit)])

    # 2) Chapitre (« Chapitre 31 » ou « 31 ») -> aperçu du chapitre.
    m = _CHAPTER_RE.match(query) or _CHAPTER_WORD_RE.search(query)
    if m:
        num = m.group(1)
        hit = knowledge_index_search.by_reference(db, KI_CHAPTER, num)
        if hit is not None:
            return LookupResponse(
                query=query, mode="chapter", results=[_to_result(hit)],
                chapter_codes=_chapter_codes(db, hit.chapter or hit.title or ""),
            )

    # 3) Recherche classée générale.
    hits = knowledge_index_search.search(db, query, limit=limit)
    if not hits:
        return LookupResponse(query=query, mode="empty", results=[])
    mode = {
        "HS_CODE": "hs_code", "PRODUCT": "product", "DOCUMENT": "document",
        "CHAPTER": "chapter",
    }.get(hits[0].type, "ranked")
    results = [_to_result(h) for h in hits]
    chapter_codes: list[KnowledgeResult] = []
    if hits[0].type == KI_CHAPTER and hits[0].chapter:
        chapter_codes = _chapter_codes(db, hits[0].chapter)
    return LookupResponse(query=query, mode=mode, results=results, chapter_codes=chapter_codes)


@router.get("/suggest", response_model=SuggestResponse)
def knowledge_suggest(
    q: str = Query(..., min_length=1, description="Préfixe pour l'autocomplétion"),
    limit: int = Query(default=8, le=20),
    db: Session = Depends(get_db),
) -> SuggestResponse:
    """Suggestions d'autocomplétion (sans IA) issues de l'Index de connaissance."""
    # Phase 7 : lecture seule — aucun rebuild sur le chemin de recherche.
    hits = knowledge_index_search.search(db, q.strip(), limit=limit)
    suggestions = [
        Suggestion(
            label=h.title or h.reference or "",
            sublabel=h.reference if h.type == KI_HS_CODE else (h.chapter or h.type.title()),
            type=h.type, reference=h.reference,
        )
        for h in hits
    ]
    return SuggestResponse(query=q.strip(), suggestions=suggestions)


@router.get("/search", response_model=SearchResponse)
def search_knowledge(
    q: str = Query(..., min_length=1, description="Terme recherché (ex. « centrifuge »)"),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Recherche un terme dans les documents officiels et renvoie les passages
    correspondants avec leur traçabilité (document, chapitre, page, codes SH)."""
    return search_service.search(db, q, limit=limit)


@router.get("/coverage")
def knowledge_coverage(db: Session = Depends(get_db)) -> dict:
    """Tableau de couverture des connaissances : chapitres 01–97 importés."""
    return knowledge_service.coverage(db)


@router.get("/health")
def knowledge_health(db: Session = Depends(get_db)) -> dict:
    """Tableau de santé de la base de connaissances (indicateurs agrégés)."""
    return knowledge_service.health(db)


@router.get("/quality")
def knowledge_quality(db: Session = Depends(get_db)) -> dict:
    """Rapport de contrôle qualité (descriptions, citations, chapitres vides…)."""
    return knowledge_service.quality(db)


@router.get("/search-tests")
def knowledge_search_tests(db: Session = Depends(get_db)) -> dict:
    """Tests de recherche automatiques (PASS/FAIL) sur des requêtes de référence."""
    return knowledge_service.run_search_tests(db)
