"""Prompt-mestre "Maestro + ANZ Finance" §17, test item #18/20: balance
validation (SUM(transactions) vs. reported LEDGERBAL), never hidden when
it diverges.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import respx
from fastapi.testclient import TestClient

from app.pipeline.balance import validate_balance
from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL
from app.pipeline.ofx_parser import AccountBalance
from tests.fixtures.mock_syncron import mock_valid

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"


def _df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_matching_balance_is_reported_as_matching():
    df = _df([{"Conta": "123456", "Valor": -150.0}, {"Conta": "123456", "Valor": 3000.0}, {"Conta": "123456", "Valor": -89.90}])
    balances = [AccountBalance(account="123456", reported_balance=2760.10, source_filename="a.ofx")]

    checks = validate_balance(df, balances)

    assert len(checks) == 1
    assert checks[0].matches is True
    assert checks[0].computed_balance == 2760.10
    assert checks[0].difference == 0.0
    assert checks[0].assumption  # never silent -- the caveat is always present, match or not


def test_real_divergence_is_surfaced_never_hidden():
    """§17: 'detectar; registrar; informar; não esconder o problema'."""
    df = _df([{"Conta": "123456", "Valor": -150.0}, {"Conta": "123456", "Valor": 3000.0}])  # missing the -89.90 transaction
    balances = [AccountBalance(account="123456", reported_balance=2760.10, source_filename="a.ofx")]

    checks = validate_balance(df, balances)

    assert checks[0].matches is False
    assert checks[0].computed_balance == 2850.0
    assert round(checks[0].difference, 2) == 89.90


def test_float_rounding_within_tolerance_still_matches():
    df = _df([{"Conta": "123456", "Valor": 100.004}])
    balances = [AccountBalance(account="123456", reported_balance=100.0, source_filename="a.ofx")]

    checks = validate_balance(df, balances)

    assert checks[0].matches is True  # 0.004 is within the 1-cent tolerance


def test_account_with_no_reported_balance_produces_no_check():
    df = _df([{"Conta": "999999", "Valor": 10.0}])

    checks = validate_balance(df, [])

    assert checks == []


def test_multiple_reported_balances_for_the_same_account_uses_the_latest():
    df = _df([{"Conta": "123456", "Valor": 100.0}])
    balances = [
        AccountBalance(account="123456", reported_balance=50.0, source_filename="janeiro.ofx"),
        AccountBalance(account="123456", reported_balance=100.0, source_filename="fevereiro.ofx"),
    ]

    checks = validate_balance(df, balances)

    assert len(checks) == 1
    assert checks[0].reported_balance == 100.0
    assert checks[0].source_filename == "fevereiro.ofx"
    assert checks[0].matches is True


# ===== integration: GET /workspace/balance-validation =====


def _groq_response(category: str):
    import httpx

    return httpx.Response(200, json={"choices": [{"message": {"content": category}}]})


def _bridge_and_get_headers(client: TestClient) -> dict:
    with respx.mock:
        mock_valid(respx, email="tester@example.com")
        response = client.post("/auth/bridge", json={"token": "valid-token"})
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@respx.mock
def test_balance_validation_endpoint_reflects_uploaded_statement(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(
        side_effect=[_groq_response(c) for c in ["Mercado", "Receitas", "Moradia"]]
    )

    with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
        client.post("/workspace/upload", headers=headers, files={"files": ("valid_statement.ofx", fh, "application/octet-stream")})

    response = client.get("/workspace/balance-validation", headers=headers)

    assert response.status_code == 200
    checks = response.json()["checks"]
    assert len(checks) == 1
    assert checks[0]["account"] == "123456"
    assert checks[0]["reported_balance"] == 2760.10
    assert checks[0]["matches"] is True
    assert checks[0]["assumption"]  # caveat always present in the API response too
