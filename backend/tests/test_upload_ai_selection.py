"""Fase 5's provider/model/own-key form fields on POST /workspace/upload --
including the regression guard for Fase 4's validated behavior: no API key
configured must degrade each transaction gracefully, never block the whole
upload (that graceful-degradation path was previously only checked by hand
in a browser; codified here as an automated test now that Fase 5 could have
regressed it).
"""

from __future__ import annotations

from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient

from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL
from app.pipeline.categorizer.openai_provider import OPENAI_CHAT_COMPLETIONS_URL
from tests.fixtures.mock_syncron import mock_valid

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"


def _bridge_and_get_headers(client: TestClient) -> dict:
    with respx.mock:
        mock_valid(respx, email="tester@example.com")
        response = client.post("/auth/bridge", json={"token": "valid-token"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _upload(client: TestClient, headers: dict, data: dict | None = None):
    with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
        return client.post(
            "/workspace/upload",
            headers=headers,
            data=data or {},
            files={"files": ("valid_statement.ofx", fh, "application/octet-stream")},
        )


@respx.mock
def test_upload_with_no_key_configured_anywhere_still_succeeds_with_degraded_classification(client: TestClient, test_settings) -> None:
    from app.core.config import get_settings
    from app.main import app

    headers = _bridge_and_get_headers(client)  # bridge first, with the client fixture's normal (keyed) settings still in place

    # THEN simulate an operator deployment with no default key configured at
    # all -- keep every other setting (syncron_api_base/secret_key/...)
    # identical to the fixture's, only the AI keys change, so the already-
    # minted session token still decodes correctly.
    app.dependency_overrides[get_settings] = lambda: test_settings.model_copy(update={"groq_api_key": "", "openai_api_key": ""})
    try:
        respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(401, json={"error": "no api key"}))
        response = _upload(client, headers)
    finally:
        app.dependency_overrides[get_settings] = lambda: test_settings

    assert response.status_code == 200
    assert response.json()["total_transactions"] == 3  # upload itself never blocked


@respx.mock
def test_upload_routes_to_openai_when_provider_is_selected(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    route = respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}))

    response = _upload(client, headers, {"provider": "openai", "model": "gpt-4o"})

    assert response.status_code == 200
    assert route.called


@respx.mock
def test_upload_uses_the_users_own_key_when_supplied(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    route = respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}))

    _upload(client, headers, {"provider": "groq", "api_key": "user-own-key-upload"})

    assert route.calls.last.request.headers["Authorization"] == "Bearer user-own-key-upload"


@respx.mock
def test_upload_with_unknown_provider_is_400(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    response = _upload(client, headers, {"provider": "anthropic"})
    assert response.status_code == 400
