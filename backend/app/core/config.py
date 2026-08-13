"""Centralized backend configuration.

Replaces the legacy app's pattern of reading `API_BASE`/`API_HUB` via bare
`os.getenv(...)` calls scattered outside `config.py` (see
`legacy_streamlit/run_dashboard.py:12-13`). Every environment-derived value
the backend needs lives here, loaded once at import time.

No value here is ever persisted anywhere beyond process memory — this module
itself does not read/write any file other than `.env` at startup.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # -- Syncron integration (subscription_access_api) -----------------
    # Base URL of the central Syncron auth/subscription service. This
    # backend only ever calls it over HTTP (POST /validate-agendador-token)
    # -- subscription_access_api's own repo is never modified from here.
    syncron_api_base: str = Field(
        default="http://localhost:8000",
        description="Base URL of subscription_access_api.",
    )
    syncron_validate_timeout_seconds: float = 5.0

    # -- ANZ's own session (see backend/app/access/security.py) --------
    # Independent from subscription_access_api's own JWT secret by design
    # (guardrail: ANZ never assumes authority over Syncron identity -- this
    # key only signs ANZ's own short-lived technical session token).
    secret_key: str = Field(
        default="dev-only-insecure-secret-change-me",
        description="Signing key for ANZ's own session JWT. Must be overridden in every real environment.",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # -- PARTE 4 workspace (in-memory, TTL, no persistence) -------------
    workspace_ttl_minutes: int = 60

    # -- AI classification (Fase 3: Groq is the first provider; Fase 5 adds
    # OpenAI as a second, real, independently-reachable provider) ---------
    # Session-only alternative (the user's own key, PARTE 6.2) is handled
    # per-request in Fase 5 (see pipeline/categorizer/registry.py) -- these
    # are only the operator-provided defaults, used when the caller doesn't
    # supply their own key.
    groq_api_key: str = Field(default="", description="Default Groq API key, used when the user hasn't supplied their own.")
    openai_api_key: str = Field(default="", description="Default OpenAI API key, used when the user hasn't supplied their own.")

    # -- CORS ------------------------------------------------------------
    frontend_url: str = Field(
        default="http://localhost:5173",
        description="Origin of the deployed/dev frontend, used for CORS allow_origins.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
