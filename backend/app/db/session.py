"""Moteur SQLAlchemy et fabrique de sessions."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,                       # revalide les connexions mortes
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,    # évite les sockets fermés côté serveur
    pool_timeout=settings.DB_POOL_TIMEOUT,
    connect_args={"connect_timeout": settings.DB_CONNECT_TIMEOUT},
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, class_=Session
)


def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI : fournit une session par requête."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
