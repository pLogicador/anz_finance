"""Fase 9: baseline security headers on every response, and a file-size
ceiling on both ingestion routes (OFX upload, CSV import) -- before this,
neither enforced any limit, so an arbitrarily large upload could exhaust
worker memory (`UploadFile.read()` loads the whole file regardless).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import respx
from fastapi.testclient import TestClient

from tests.fixtures.mock_syncron import mock_valid

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"


def _bridge_and_get_headers(client: TestClient) -> dict:
    with respx.mock:
        mock_valid(respx, email="tester@example.com")
        response = client.post("/auth/bridge", json={"token": "valid-token"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_security_headers_present_on_a_plain_public_route(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


@respx.mock
def test_security_headers_present_on_an_authenticated_route(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    response = client.get("/auth/me", headers=headers)
    assert response.headers["x-content-type-options"] == "nosniff"


@respx.mock
def test_oversized_ofx_file_fails_that_file_without_aborting_the_batch(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    with patch("app.pipeline.ofx_parser.MAX_UPLOAD_FILE_BYTES", 10):  # tiny limit, easy to exceed in a test
        with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
            response = client.post("/workspace/upload", headers=headers, files={"files": ("valid_statement.ofx", fh, "application/octet-stream")})

    assert response.status_code == 200  # the request itself still succeeds
    body = response.json()
    assert body["files"][0]["status"] == "failed"
    assert "limite" in body["files"][0]["error"].lower()
    assert body["total_transactions"] == 0


@respx.mock
def test_oversized_csv_preview_is_rejected_with_a_clear_400(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    with patch("app.routes.import_csv.MAX_UPLOAD_FILE_BYTES", 10):
        response = client.post(
            "/workspace/import/csv/preview",
            headers=headers,
            files={"file": ("big.csv", BytesIO(b"a,b\n1,2\n3,4\n5,6\n"), "text/csv")},
        )
    assert response.status_code == 400
    assert "limite" in response.json()["detail"]["message"].lower()


@respx.mock
def test_oversized_csv_commit_is_rejected_with_a_clear_400(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    with patch("app.routes.import_csv.MAX_UPLOAD_FILE_BYTES", 10):
        response = client.post(
            "/workspace/import/csv/commit",
            headers=headers,
            data={"date_column": "a", "valor_column": "b", "description_column": "a"},
            files={"file": ("big.csv", BytesIO(b"a,b\n1,2\n3,4\n5,6\n"), "text/csv")},
        )
    assert response.status_code == 400
