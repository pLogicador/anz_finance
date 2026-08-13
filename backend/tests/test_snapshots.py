"""POST/GET/DELETE /workspace/snapshots -- filter-combination bookmarks
stored on the same workspace TTL entry as the uploaded data (Fase 6).
"""

from __future__ import annotations

from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient

from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL
from tests.fixtures.mock_syncron import mock_valid

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"


def _bridge_and_get_headers(client: TestClient) -> dict:
    with respx.mock:
        mock_valid(respx, email="tester@example.com")
        response = client.post("/auth/bridge", json={"token": "valid-token"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _mock_groq_sequence(categories: list[str]) -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(side_effect=[httpx.Response(200, json={"choices": [{"message": {"content": c}}]}) for c in categories])


def _upload_valid_statement(client: TestClient, headers: dict) -> None:
    with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
        response = client.post("/workspace/upload", headers=headers, files={"files": ("valid_statement.ofx", fh, "application/octet-stream")})
    assert response.status_code == 200


def test_snapshots_require_auth(client: TestClient) -> None:
    assert client.get("/workspace/snapshots").status_code == 401


@respx.mock
def test_snapshots_require_uploaded_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    assert client.get("/workspace/snapshots", headers=headers).status_code == 404


@respx.mock
def test_create_list_and_delete_a_snapshot(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    empty = client.get("/workspace/snapshots", headers=headers).json()
    assert empty["snapshots"] == []

    created = client.post(
        "/workspace/snapshots",
        headers=headers,
        json={"label": "Gastos de janeiro", "month": "2026-01", "categories": ["Mercado"], "type": "Despesas"},
    )
    assert created.status_code == 200
    snapshots = created.json()["snapshots"]
    assert len(snapshots) == 1
    assert snapshots[0]["label"] == "Gastos de janeiro"
    snapshot_id = snapshots[0]["id"]

    listed = client.get("/workspace/snapshots", headers=headers).json()
    assert len(listed["snapshots"]) == 1

    deleted = client.delete(f"/workspace/snapshots/{snapshot_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["snapshots"] == []


@respx.mock
def test_deleting_an_unknown_snapshot_is_404(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    response = client.delete("/workspace/snapshots/does-not-exist", headers=headers)
    assert response.status_code == 404


@respx.mock
def test_a_blank_label_falls_back_to_the_month(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    created = client.post("/workspace/snapshots", headers=headers, json={"label": "   ", "month": "2026-01"})
    assert created.json()["snapshots"][0]["label"] == "2026-01"
