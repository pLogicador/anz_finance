from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from app.workspace.store import WorkspaceStore, get_workspace_store

SYNCRON_API_BASE = "http://syncron.test"


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        syncron_api_base=SYNCRON_API_BASE,
        syncron_validate_timeout_seconds=5.0,
        secret_key="test-secret-key-not-for-real-use",
        algorithm="HS256",
        access_token_expire_minutes=30,
        workspace_ttl_minutes=60,
        frontend_url="http://localhost:5173",
        # Fase 5's registry.resolve_api_key() requires *some* key (own or
        # default) before building a provider -- these stand in for the
        # operator-configured defaults every real deployment would set.
        groq_api_key="test-groq-key",
        openai_api_key="test-openai-key",
    )


@pytest.fixture
def workspace_store() -> WorkspaceStore:
    return WorkspaceStore(ttl_minutes=60)


@pytest.fixture
def client(test_settings: Settings, workspace_store: WorkspaceStore) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_workspace_store] = lambda: workspace_store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
