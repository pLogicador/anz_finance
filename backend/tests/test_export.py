"""GET /workspace/export/{csv,pdf} -- both must respect active filters
(the real gap the legacy app's single unfiltered export button had).
"""

from __future__ import annotations

from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient

from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL
from app.pipeline.csv_export import build_csv
from app.pipeline.pdf_report import build_pdf_report
from app.pipeline.metrics import PeriodSummary
from tests.fixtures.mock_syncron import mock_valid
import pandas as pd

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


# -- Unit: csv_export -------------------------------------------------


def test_build_csv_contains_only_expected_columns_in_order() -> None:
    df = pd.DataFrame([{"Data": "2026-01-01", "Descrição": "a", "Categorias": "Mercado", "Valor": -10.0, "Mês": "2026-01"}])
    text = build_csv(df)
    header = text.splitlines()[0]
    assert header == "Data,Descrição,Categorias,Valor"


def test_build_csv_on_empty_df_still_has_a_header() -> None:
    text = build_csv(pd.DataFrame(columns=["Data", "Descrição", "Categorias", "Valor", "Mês"]))
    assert text.strip() == "Data,Descrição,Categorias,Valor"


# -- Unit: pdf_report ---------------------------------------------------


def test_build_pdf_report_escapes_unbalanced_markup_in_user_controlled_filters() -> None:
    """Regression guard for a real bug found during the Fase 9 security
    pass: `month`/`categories`/`type_filter` come straight from request
    query params and previously went unescaped into a reportlab
    `Paragraph` (which parses a small XML-like markup subset) -- an
    unbalanced `<` crashed report generation with an unhandled ValueError,
    confirmed by hand before fixing."""
    summary = PeriodSummary(income=0.0, expense=0.0, net=0.0, transaction_count=0, top_category=None, top_category_amount=0.0)
    breakdown = pd.DataFrame(columns=["Categorias", "Valor"])
    pdf_bytes = build_pdf_report(
        month="2026-01 <script>alert(1)</script> <unbalanced",
        categories=["<b>injected</b>"],
        type_filter="Todas & mais",
        summary=summary,
        category_breakdown=breakdown,
    )
    assert pdf_bytes.startswith(b"%PDF")


def test_build_pdf_report_produces_a_real_pdf_byte_stream() -> None:
    summary = PeriodSummary(income=1000.0, expense=-200.0, net=800.0, transaction_count=3, top_category="Mercado", top_category_amount=200.0)
    breakdown = pd.DataFrame([{"Categorias": "Mercado", "Valor": 200.0}])
    pdf_bytes = build_pdf_report(month="2026-01", categories=[], type_filter="Todas", summary=summary, category_breakdown=breakdown)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500  # a real multi-element document, not an empty shell


# -- Routes ---------------------------------------------------------------


def test_export_csv_requires_auth(client: TestClient) -> None:
    assert client.get("/workspace/export/csv", params={"month": "2026-01"}).status_code == 401


@respx.mock
def test_export_csv_requires_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    assert client.get("/workspace/export/csv", headers=headers, params={"month": "2026-01"}).status_code == 404


@respx.mock
def test_export_csv_respects_the_month_filter(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    jan = client.get("/workspace/export/csv", headers=headers, params={"month": "2026-01"})
    assert jan.status_code == 200
    assert jan.headers["content-type"].startswith("text/csv")
    assert 'filename="anz-finance-2026-01.csv"' in jan.headers["content-disposition"]
    jan_rows = [line for line in jan.text.strip().splitlines()[1:] if line]
    assert len(jan_rows) == 2  # January has 2 transactions in the fixture

    feb = client.get("/workspace/export/csv", headers=headers, params={"month": "2026-02"})
    feb_rows = [line for line in feb.text.strip().splitlines()[1:] if line]
    assert len(feb_rows) == 1


@respx.mock
def test_export_csv_respects_the_type_filter(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    despesas = client.get("/workspace/export/csv", headers=headers, params={"month": "2026-01", "type": "Despesas"})
    rows = [line for line in despesas.text.strip().splitlines()[1:] if line]
    assert len(rows) == 1  # only the one expense row in January


@respx.mock
def test_export_pdf_requires_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    assert client.get("/workspace/export/pdf", headers=headers, params={"month": "2026-01"}).status_code == 404


@respx.mock
def test_export_pdf_does_not_crash_on_a_malicious_month_query_param(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    response = client.get("/workspace/export/pdf", headers=headers, params={"month": "2026-01 <unbalanced"})
    # A month that doesn't match any real data just yields an empty-period
    # report (200) -- the point of this test is that it does NOT 500.
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


@respx.mock
def test_export_pdf_returns_a_real_pdf(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    response = client.get("/workspace/export/pdf", headers=headers, params={"month": "2026-01"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
