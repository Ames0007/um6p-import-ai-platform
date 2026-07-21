"""Configuration centralisée de l'application (variables d'environnement)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de l'application, chargés depuis l'environnement / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    APP_NAME: str = "Assistant IA Import UM6P"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # --- Sécurité / JWT (préparation SSO) ---
    SECRET_KEY: str = "change-me-super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- CORS ---
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3005"
    # Regex optionnel d'origines autorisées (ex. previews Vercel).
    # Vide = désactivé. Ex. : r"https://.*\.vercel\.app"
    BACKEND_CORS_ORIGIN_REGEX: str = ""

    # --- Observabilité / journalisation (Phase 8) ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json | text

    # --- PostgreSQL ---
    POSTGRES_USER: str = "um6p"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "um6p_import"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # --- Pool de connexions SQLAlchemy (Phase 3/6) ---
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800   # recycle les connexions après 30 min
    DB_POOL_TIMEOUT: int = 30
    DB_CONNECT_TIMEOUT: int = 10

    # --- Index de connaissance (Phase 7) ---
    # Intervalle de réconciliation en arrière-plan (rebuild si « sale »).
    KI_REFRESH_INTERVAL_SECONDS: int = 20

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Uploads ---
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 25

    # --- Claude API ---
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-opus-4-8"
    AI_MAX_TOKENS: int = 1024
    AI_TEMPERATURE: float = 0.0  # factuel : pas de créativité
    AI_MAX_RETRIES: int = 2
    AI_HISTORY_TURNS: int = 8  # nombre de messages d'historique conservés

    # --- Ingestion documentaire (Phase 2) ---
    DOCUMENTS_DIR: str = "./storage/documents"
    INGESTION_QUEUE_NAME: str = "ingestion"
    # True : files d'attente RQ (worker séparé, durable). False : thread d'arrière-plan.
    USE_TASK_QUEUE: bool = False
    JOB_TIMEOUT_SECONDS: int = 60 * 60 * 6  # documents pouvant dépasser 1000 pages
    # Repli en thread si l'enfilement dans RQ échoue (Redis indisponible).
    INGESTION_INLINE_FALLBACK: bool = True
    # Taille cible d'un chunk de texte (caractères) et chevauchement.
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 150
    # En dessous de ce nombre de caractères extraits, une page est considérée
    # comme scannée (candidate à l'OCR).
    OCR_MIN_CHARS_PER_PAGE: int = 40
    OCR_ENABLED: bool = False          # active un fournisseur OCR réel (hook)
    EMBEDDINGS_ENABLED: bool = False   # active la génération d'embeddings (hook)
    EMBEDDING_DIM: int = 1536

    # --- Conformité à l'import (Phase 5) ---
    # pdf_text | tesseract | azure | google | noop
    OCR_PROVIDER: str = "pdf_text"
    AZURE_DOCUMENT_ENDPOINT: str = ""
    AZURE_DOCUMENT_KEY: str = ""
    GOOGLE_DOCUMENT_PROJECT: str = ""
    GOOGLE_DOCUMENT_PROCESSOR: str = ""
    # Seuil d'alerte d'écart de prix (en %) vs prix moyen historique.
    PRICE_ALERT_THRESHOLD_PERCENT: float = 15.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        """URL SQLAlchemy (driver psycopg 3)."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.APP_ENV.strip().lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Instance mise en cache des paramètres (singleton)."""
    return Settings()


settings = get_settings()
