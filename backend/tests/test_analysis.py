"""Unit tests for app/pipeline/analysis.py (deterministic, no mocking) plus
route-level coverage for GET /analysis/anomalies and GET /analysis/compare.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import respx
from fastapi.testclient import TestClient

from app.pipeline.analysis import compare_periods, detect_anomalies
from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL
from tests.fixtures.mock_syncron import mock_valid

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"


def _df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


# -- detect_anomalies ---------------------------------------------------


def test_no_anomaly_when_category_has_too_few_transactions() -> None:
    df = _df(
        [
            {"Data": date(2026, 1, 1), "Valor": -50.0, "Descrição": "a", "Categorias": "Mercado", "Mês": "2026-01"},
            {"Data": date(2026, 1, 2), "Valor": -500.0, "Descrição": "b", "Categorias": "Mercado", "Mês": "2026-01"},
        ]
    )
    assert detect_anomalies(df) == []  # only 2 transactions in the category, below the min-size threshold


def test_flags_a_transaction_far_above_its_category_average() -> None:
    df = _df(
        [
            {"Data": date(2026, 1, 1), "Valor": -50.0, "Descrição": "normal 1", "Categorias": "Mercado", "Mês": "2026-01"},
            {"Data": date(2026, 1, 2), "Valor": -55.0, "Descrição": "normal 2", "Categorias": "Mercado", "Mês": "2026-01"},
            {"Data": date(2026, 1, 3), "Valor": -45.0, "Descrição": "normal 3", "Categorias": "Mercado", "Mês": "2026-01"},
            {"Data": date(2026, 1, 4), "Valor": -900.0, "Descrição": "outlier", "Categorias": "Mercado", "Mês": "2026-01"},
        ]
    )
    anomalies = detect_anomalies(df)
    assert len(anomalies) == 1
    assert anomalies[0].description == "outlier"
    assert anomalies[0].ratio > 2.5


def test_income_rows_are_never_flagged() -> None:
    df = _df([{"Data": date(2026, 1, i), "Valor": 100.0 * i, "Descrição": f"salario {i}", "Categorias": "Receitas", "Mês": "2026-01"} for i in range(1, 5)])
    assert detect_anomalies(df) == []


def test_empty_df_returns_no_anomalies() -> None:
    assert detect_anomalies(pd.DataFrame(columns=["Data", "Valor", "Descrição", "Categorias", "Mês"])) == []


# -- compare_periods ------------------------------------------------------


def test_compare_periods_computes_correct_deltas() -> None:
    df = _df(
        [
            {"Data": date(2026, 1, 1), "Valor": 1000.0, "Descrição": "salario", "Categorias": "Receitas", "Mês": "2026-01"},
            {"Data": date(2026, 1, 2), "Valor": -200.0, "Descrição": "mercado", "Categorias": "Mercado", "Mês": "2026-01"},
            {"Data": date(2026, 2, 1), "Valor": 1500.0, "Descrição": "salario", "Categorias": "Receitas", "Mês": "2026-02"},
            {"Data": date(2026, 2, 2), "Valor": -300.0, "Descrição": "mercado", "Categorias": "Mercado", "Mês": "2026-02"},
        ]
    )
    result = compare_periods(df, "2026-01", "2026-02")

    assert result.summary_a.income == 1000.0
    assert result.summary_b.income == 1500.0
    assert result.income_change_pct == 50.0
    # Raw, un-inverted delta on the signed value -- -200 -> -300 is a -50%
    # change of the raw number, same "no inversion here, that's a
    # presentation concern" contract as metrics.month_over_month_delta
    # (see its module docstring). The magnitude did grow 50%; the *signed*
    # delta is -50%, and this function intentionally mirrors that contract.
    assert result.expense_change_pct == -50.0

    mercado = next(d for d in result.category_deltas if d.category == "Mercado")
    assert mercado.valor_a == 200.0
    assert mercado.valor_b == 300.0
    assert mercado.delta == 100.0


def test_compare_periods_handles_a_month_with_zero_baseline() -> None:
    df = _df([{"Data": date(2026, 2, 1), "Valor": 500.0, "Descrição": "novo", "Categorias": "Receitas", "Mês": "2026-02"}])
    result = compare_periods(df, "2026-01", "2026-02")
    assert result.income_change_pct is None  # no baseline in 2026-01 to divide by


# -- Routes ---------------------------------------------------------------


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
def test_anomalies_route_requires_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    assert client.get("/analysis/anomalies", headers=headers).status_code == 410


def test_anomalies_route_requires_auth(client: TestClient) -> None:
    assert client.get("/analysis/anomalies").status_code == 401


@respx.mock
def test_anomalies_route_returns_a_list_over_real_uploaded_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    response = client.get("/analysis/anomalies", headers=headers)
    assert response.status_code == 200
    assert "anomalies" in response.json()


@respx.mock
def test_compare_route_rejects_a_month_not_present_in_the_session(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    response = client.get("/analysis/compare", headers=headers, params={"month_a": "2026-01", "month_b": "1999-01"})
    assert response.status_code == 400


@respx.mock
def test_compare_route_returns_both_summaries_for_real_uploaded_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    response = client.get("/analysis/compare", headers=headers, params={"month_a": "2026-01", "month_b": "2026-02"})
    assert response.status_code == 200
    body = response.json()
    assert body["summary_a"]["income"] == 3000.0
    assert body["month_a"] == "2026-01"
    assert body["month_b"] == "2026-02"
