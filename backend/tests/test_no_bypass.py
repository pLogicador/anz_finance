"""Anti-bypass suite for PARTE 5.

PARTE 22's audit checklist asks explicitly: "Existe alguma rota, estado ou
fallback que permita acesso sem passar pela Syncron? (se existir, é um bug
crítico)". This file is that check, automated: every way a caller might try
to reach an authorized state without a real, successful call to
subscription_access_api must fail.
"""

from __future__ import annotations

import respx
from fastapi.testclient import TestClient

from tests.fixtures.mock_syncron import mock_token_invalid


@respx.mock
def test_missing_token_field_is_rejected(client: TestClient) -> None:
    response = client.post("/auth/bridge", json={})
    assert response.status_code == 422  # pydantic validation, not even reaching syncron_client


@respx.mock
def test_null_token_is_rejected(client: TestClient) -> None:
    response = client.post("/auth/bridge", json={"token": None})
    assert response.status_code == 422


@respx.mock
def test_whitespace_only_token_is_rejected_without_a_network_call(client: TestClient) -> None:
    with respx.mock:  # no routes registered -- a real call would raise
        response = client.post("/auth/bridge", json={"token": "\t\n  "})
    assert response.status_code == 401


@respx.mock
def test_bearer_prefixed_token_is_stripped_then_still_validated(client: TestClient) -> None:
    """Mirrors legacy_streamlit/run_dashboard.py:47-49's defensive stripping."""
    mock_token_invalid(respx)  # doesn't matter which outcome -- what matters is a call happens
    response = client.post("/auth/bridge", json={"token": "Bearer some-token"})
    assert response.status_code == 401
    assert respx.calls.call_count == 1


def test_me_without_any_authorization_header_is_401(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "token_invalid_or_missing"


def test_me_with_garbage_bearer_token_is_401(client: TestClient) -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert response.status_code == 401


def test_me_with_a_jwt_signed_by_a_different_key_is_rejected(client: TestClient, test_settings) -> None:
    """A forged/foreign JWT (e.g. signed with a guessed or leaked different
    key) must never be accepted -- proves the signature is actually checked,
    not just the shape of the token."""
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    forged = jwt.encode(
        {
            "sub": "attacker@example.com",
            "workspace_id": "forged-workspace",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(minutes=30)).timestamp()),
        },
        "a-completely-different-secret",
        algorithm=test_settings.algorithm,
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


def test_me_with_an_expired_jwt_is_rejected(client: TestClient, test_settings) -> None:
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    expired = jwt.encode(
        {
            "sub": "user@example.com",
            "workspace_id": "some-workspace",
            "iat": int((datetime.now(UTC) - timedelta(hours=2)).timestamp()),
            "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
        },
        test_settings.secret_key,
        algorithm=test_settings.algorithm,
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401


@respx.mock
def test_a_401_or_403_from_syncron_never_still_issues_a_session(client: TestClient) -> None:
    """Belt-and-suspenders: even if the route logic had a bug, a session
    token must never come back on a non-2xx bridge response."""
    mock_token_invalid(respx)
    response = client.post("/auth/bridge", json={"token": "bad-token"})
    assert "access_token" not in response.json()
