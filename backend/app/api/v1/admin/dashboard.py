"""Endpoint du tableau de bord."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Admin · Tableau de bord"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    return dashboard_service.build(db)
