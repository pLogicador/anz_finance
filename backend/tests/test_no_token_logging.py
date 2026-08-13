"""PARTE 5.5: "Nunca logar o token." Confirmed by grep-over-captured-logs,
not by reading the code and hoping -- this is exactly the class of bug the
legacy app had (``legacy_streamlit/run_dashboard.py:65``,
``logger.info("Token recebido (raw): %s", token)``).
"""

from __future__ import annotations

import logging

import respx
from fastapi.testclient import TestClient

from tests.fixtures.mock_syncron import mock_plan_expired, mock_service_down, mock_token_invalid, mock_valid

SECRET_TOKEN = "super-secret-agendador-token-should-never-be-logged-9f8e7d"


@respx.mock
def test_raw_token_never_appears_in_logs_on_success(client: TestClient, caplog) -> None:
    mock_valid(respx)
    with caplog.at_level(logging.DEBUG):
        client.post("/auth/bridge", json={"token": SECRET_TOKEN})
    assert SECRET_TOKEN not in caplog.text


@respx.mock
def test_raw_token_never_appears_in_logs_on_plan_expired(client: TestClient, caplog) -> None:
    mock_plan_expired(respx)
    with caplog.at_level(logging.DEBUG):
        client.post("/auth/bridge", json={"token": SECRET_TOKEN})
    assert SECRET_TOKEN not in caplog.text


@respx.mock
def test_raw_token_never_appears_in_logs_on_invalid(client: TestClient, caplog) -> None:
    mock_token_invalid(respx)
    with caplog.at_level(logging.DEBUG):
        client.post("/auth/bridge", json={"token": SECRET_TOKEN})
    assert SECRET_TOKEN not in caplog.text


@respx.mock
def test_raw_token_never_appears_in_logs_when_service_is_down(client: TestClient, caplog) -> None:
    mock_service_down(respx)
    with caplog.at_level(logging.DEBUG):
        client.post("/auth/bridge", json={"token": SECRET_TOKEN})
    assert SECRET_TOKEN not in caplog.text
