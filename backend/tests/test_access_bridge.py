"""POST /auth/bridge -- happy path plus the 3 distinct failure states.

This is the fix for the legacy app's behavior (collapsing token-invalid,
plan-expired, and service-unavailable into one generic "Sessão expirada"
message) -- PARTE 5.6 requires these to be visibly distinguishable, and
that starts with the backend returning distinguishable ``error_code``s.
"""

from __future__ import annotations

import respx
from fastapi.testclient import TestClient

from app.access.security import decode_session_token
from tests.fixtures.mock_syncron import mock_plan_expired, mock_service_down, mock_timeout, mock_token_invalid, mock_valid


@respx.mock
def test_bridge_success_issues_a_session_jwt(client: TestClient, test_settings) -> None:
    mock_valid(respx, email="premium.user@example.com")

    response = client.post("/auth/bridge", json={"token": "valid-token-abc"})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "premium.user@example.com"
    assert body["token_type"] == "bearer"
    assert "workspace_id" in body

    claims = decode_session_token(body["access_token"], test_settings)
    assert claims.sub == "premium.user@example.com"
    assert claims.workspace_id == body["workspace_id"]


@respx.mock
def test_bridge_free_active_plan_is_also_authorized(client: TestClient) -> None:
    """PARTE 5.3: free plan (active) must be allowed in, same as premium."""
    mock_valid(respx, email="free.user@example.com")

    response = client.post("/auth/bridge", json={"token": "valid-free-plan-token"})

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "free.user@example.com"


@respx.mock
def test_bridge_plan_expired_returns_distinct_403(client: TestClient) -> None:
    mock_plan_expired(respx)

    response = client.post("/auth/bridge", json={"token": "expired-plan-token"})

    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "plan_expired"


@respx.mock
def test_bridge_invalid_token_returns_distinct_401(client: TestClient) -> None:
    mock_token_invalid(respx)

    response = client.post("/auth/bridge", json={"token": "garbage-token"})

    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "token_invalid_or_missing"


@respx.mock
def test_bridge_service_down_returns_distinct_503(client: TestClient) -> None:
    mock_service_down(respx)

    response = client.post("/auth/bridge", json={"token": "some-token"})

    assert response.status_code == 503
    assert response.json()["detail"]["error_code"] == "auth_service_unavailable"


@respx.mock
def test_bridge_timeout_returns_distinct_503(client: TestClient) -> None:
    mock_timeout(respx)

    response = client.post("/auth/bridge", json={"token": "some-token"})

    assert response.status_code == 503
    assert response.json()["detail"]["error_code"] == "auth_service_unavailable"


def test_bridge_empty_token_never_calls_syncron_at_all(client: TestClient) -> None:
    """An empty token is rejected locally -- no reason to spend a network call on it."""
    with respx.mock:
        # No routes registered: if the app tried to call out, respx raises.
        response = client.post("/auth/bridge", json={"token": "   "})

    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "token_invalid_or_missing"
