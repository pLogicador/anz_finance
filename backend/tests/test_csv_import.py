"""POST /workspace/import/csv/{preview,commit} -- Fase 7. Preview never
touches the workspace store (just reads headers/sample rows); commit
parses via the user's column mapping, classifies, and APPENDS to whatever
is already in the workspace (unlike OFX upload, which replaces).
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient

from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL
from app.pipeline.csv_import import CsvImportError, apply_column_mapping, preview_csv
from tests.fixtures.mock_syncron import mock_valid

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"

SAMPLE_CSV = b"Data da compra,Valor pago,Estabelecimento\n2026-03-05,150.00,PADARIA CENTRAL\n2026-03-10,-45.00,FARMACIA POPULAR\n"
MALFORMED_CSV = b"col_a,col_b\nx,y\n"


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


# -- Unit: csv_import.py -------------------------------------------------


def test_preview_returns_columns_and_sample_rows() -> None:
    preview = preview_csv(SAMPLE_CSV)
    assert preview.columns == ["Data da compra", "Valor pago", "Estabelecimento"]
    assert preview.row_count == 2
    assert len(preview.sample_rows) == 2


def test_preview_rejects_an_empty_file() -> None:
    import pytest

    with pytest.raises(CsvImportError):
        preview_csv(b"col_a,col_b\n")


def test_apply_column_mapping_produces_the_expected_shape() -> None:
    df = apply_column_mapping(SAMPLE_CSV, date_column="Data da compra", valor_column="Valor pago", description_column="Estabelecimento")
    assert list(df.columns) == ["Data", "Valor", "Descrição"]
    assert len(df) == 2
    assert df.iloc[0]["Valor"] == 150.00


def test_apply_column_mapping_does_not_corrupt_unambiguous_iso_dates() -> None:
    """Regression guard: an early draft parsed dates with `dayfirst=True`
    unconditionally, which silently swapped month/day on ISO-formatted
    dates ("2026-03-05" became May 3rd instead of March 5th) -- caught by
    hand-checking pandas' actual behavior, not by assumption."""
    df = apply_column_mapping(SAMPLE_CSV, date_column="Data da compra", valor_column="Valor pago", description_column="Estabelecimento")
    assert list(df["Data"]) == [date(2026, 3, 5), date(2026, 3, 10)]


def test_apply_column_mapping_rejects_an_unknown_column() -> None:
    import pytest

    with pytest.raises(CsvImportError):
        apply_column_mapping(SAMPLE_CSV, date_column="Coluna Inexistente", valor_column="Valor pago", description_column="Estabelecimento")


# -- Routes: /preview -----------------------------------------------------


def test_import_preview_requires_auth(client: TestClient) -> None:
    response = client.post("/workspace/import/csv/preview", files={"file": ("sample.csv", BytesIO(SAMPLE_CSV), "text/csv")})
    assert response.status_code == 401


@respx.mock
def test_import_preview_does_not_require_uploaded_data(client: TestClient) -> None:
    """Preview is how you might START a session, not something gated on already having data."""
    headers = _bridge_and_get_headers(client)
    response = client.post("/workspace/import/csv/preview", headers=headers, files={"file": ("sample.csv", BytesIO(SAMPLE_CSV), "text/csv")})
    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 2
    assert "Data da compra" in body["columns"]


@respx.mock
def test_import_preview_rejects_a_malformed_or_empty_file(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    response = client.post("/workspace/import/csv/preview", headers=headers, files={"file": ("empty.csv", BytesIO(b"a,b\n"), "text/csv")})
    assert response.status_code == 400


# -- Routes: /commit ------------------------------------------------------


@respx.mock
def test_import_commit_creates_a_fresh_workspace_when_nothing_was_uploaded(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Compras", "Saúde"])

    response = client.post(
        "/workspace/import/csv/commit",
        headers=headers,
        data={"date_column": "Data da compra", "valor_column": "Valor pago", "description_column": "Estabelecimento"},
        files={"file": ("sample.csv", BytesIO(SAMPLE_CSV), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["imported_rows"] == 2
    assert body["total_transactions"] == 2
    assert body["months"] == ["2026-03"]


@respx.mock
def test_import_commit_appends_to_existing_ofx_data_instead_of_replacing_it(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])  # 3 OFX transactions
    _upload_valid_statement(client, headers)

    _mock_groq_sequence(["Compras", "Saúde"])  # 2 CSV transactions
    response = client.post(
        "/workspace/import/csv/commit",
        headers=headers,
        data={"date_column": "Data da compra", "valor_column": "Valor pago", "description_column": "Estabelecimento"},
        files={"file": ("sample.csv", BytesIO(SAMPLE_CSV), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["imported_rows"] == 2
    assert body["total_transactions"] == 5  # 3 (OFX) + 2 (CSV), appended not replaced

    months = client.get("/workspace/months", headers=headers).json()
    assert set(months["months"]) == {"2026-01", "2026-02", "2026-03"}


@respx.mock
def test_import_commit_preserves_existing_snapshots(client: TestClient) -> None:
    """A real bug caught during Fase 7 development: both upload.py and
    import_csv.py build a brand-new WorkspacePayload on write -- without
    explicitly carrying `snapshots` forward, a re-upload/import would
    silently wipe any snapshot the user had saved (Fase 6)."""
    headers = _bridge_and_get_headers(client)
    _mock_groq_sequence(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    client.post("/workspace/snapshots", headers=headers, json={"label": "Minha view", "month": "2026-01", "categories": [], "type": "Todas"})

    _mock_groq_sequence(["Compras", "Saúde"])
    client.post(
        "/workspace/import/csv/commit",
        headers=headers,
        data={"date_column": "Data da compra", "valor_column": "Valor pago", "description_column": "Estabelecimento"},
        files={"file": ("sample.csv", BytesIO(SAMPLE_CSV), "text/csv")},
    )

    snapshots = client.get("/workspace/snapshots", headers=headers).json()
    assert len(snapshots["snapshots"]) == 1
    assert snapshots["snapshots"][0]["label"] == "Minha view"


@respx.mock
def test_import_commit_with_unmapped_column_is_400(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    response = client.post(
        "/workspace/import/csv/commit",
        headers=headers,
        data={"date_column": "Coluna Que Nao Existe", "valor_column": "Valor pago", "description_column": "Estabelecimento"},
        files={"file": ("sample.csv", BytesIO(SAMPLE_CSV), "text/csv")},
    )
    assert response.status_code == 400


def test_import_commit_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/workspace/import/csv/commit",
        data={"date_column": "a", "valor_column": "b", "description_column": "c"},
        files={"file": ("sample.csv", BytesIO(SAMPLE_CSV), "text/csv")},
    )
    assert response.status_code == 401
