"""End-to-end: real bridge (mocked Syncron) -> real OFX upload -> mocked
Groq classification -> real filtered reads. Exercises the full stack the
same way a real frontend session would, not just individual units.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient

from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL
from tests.fixtures.mock_syncron import mock_valid

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"


def _groq_response(category: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": category}}]})


def _mock_groq_sequence(categories: list[str]) -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(side_effect=[_groq_response(c) for c in categories])


def _bridge_and_get_headers(client: TestClient) -> dict:
    with respx.mock:
        mock_valid(respx, email="tester@example.com")
        response = client.post("/auth/bridge", json={"token": "valid-token"})
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@respx.mock
def test_upload_parses_classifies_and_stores_in_workspace(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)

    # 3 transactions in the fixture -> 3 Groq calls, in file order.
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])

    with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
        response = client.post(
            "/workspace/upload",
            headers=headers,
            files={"files": ("valid_statement.ofx", fh, "application/octet-stream")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total_transactions"] == 3
    assert body["files"] == [{"filename": "valid_statement.ofx", "status": "ok", "rows_parsed": 3, "error": None}]
    assert body["months"] == ["2026-02", "2026-01"]


@respx.mock
def test_upload_with_one_malformed_file_reports_both_outcomes(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])

    with open(FIXTURES / "valid_statement.ofx", "rb") as valid_fh, open(FIXTURES / "malformed_statement.ofx", "rb") as bad_fh:
        response = client.post(
            "/workspace/upload",
            headers=headers,
            files=[
                ("files", ("valid_statement.ofx", valid_fh, "application/octet-stream")),
                ("files", ("malformed_statement.ofx", bad_fh, "application/octet-stream")),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total_transactions"] == 3  # only the valid file's rows
    statuses = {f["filename"]: f["status"] for f in body["files"]}
    assert statuses == {"valid_statement.ofx": "ok", "malformed_statement.ofx": "failed"}


@respx.mock
def test_transactions_and_trend_and_summary_reflect_uploaded_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])

    with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
        client.post("/workspace/upload", headers=headers, files={"files": ("valid_statement.ofx", fh, "application/octet-stream")})

    months = client.get("/workspace/months", headers=headers).json()
    assert months["months"] == ["2026-02", "2026-01"]
    assert months["years"] == ["2026"]

    # period-filtered: only January's 2 transactions
    jan = client.get("/workspace/transactions", headers=headers, params={"month": "2026-01"}).json()
    assert jan["count"] == 2

    # category-only trend view spans both months
    trend_mercado = client.get("/workspace/trend", headers=headers, params={"categories": ["Mercado"]}).json()
    assert trend_mercado["count"] == 1

    summary = client.get("/workspace/summary", headers=headers, params={"month": "2026-01"}).json()
    assert summary["summary"]["income"] == 3000.0
    assert summary["summary"]["transaction_count"] == 2
    assert len(summary["monthly_series"]) == 2  # Jan and Feb both present in the trend dataset


@respx.mock
def test_reading_workspace_without_ever_uploading_is_work_session_expired(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)

    response = client.get("/workspace/transactions", headers=headers, params={"month": "2026-01"})

    assert response.status_code == 410
    assert response.json()["detail"]["error_code"] == "work_session_expired"


def test_upload_without_auth_is_401(client: TestClient) -> None:
    with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
        response = client.post("/workspace/upload", files={"files": ("valid_statement.ofx", fh, "application/octet-stream")})
    assert response.status_code == 401
