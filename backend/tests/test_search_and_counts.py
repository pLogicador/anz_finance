"""GET /workspace/search (global, all months) and GET /workspace/category-counts
(backs the filter chips' live counts) -- Fase 6.
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


@respx.mock
def test_search_finds_a_transaction_regardless_of_which_month_its_in(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    # valid_statement.ofx's fixture descriptions are asserted indirectly here --
    # search for a term broad enough to hit at least one real row.
    response = client.get("/workspace/search", headers=headers, params={"q": "a"})
    assert response.status_code == 200
    assert response.json()["count"] >= 1


@respx.mock
def test_search_requires_a_non_empty_query(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    response = client.get("/workspace/search", headers=headers, params={"q": ""})
    assert response.status_code == 422  # min_length=1


@respx.mock
def test_search_with_no_matches_returns_an_empty_list_not_an_error(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    response = client.get("/workspace/search", headers=headers, params={"q": "termo-que-nao-existe-em-lugar-nenhum-xyz"})
    assert response.status_code == 200
    assert response.json() == {"transactions": [], "count": 0}


def test_search_requires_auth(client: TestClient) -> None:
    assert client.get("/workspace/search", params={"q": "a"}).status_code == 401


@respx.mock
def test_category_counts_reflect_the_selected_month_only(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    jan = client.get("/workspace/category-counts", headers=headers, params={"month": "2026-01"}).json()
    feb = client.get("/workspace/category-counts", headers=headers, params={"month": "2026-02"}).json()

    assert sum(jan["counts"].values()) == 2  # January has 2 transactions in the fixture
    assert sum(feb["counts"].values()) == 1  # February has 1
