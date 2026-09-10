"""Route-level coverage for Fase 5: model listing, test-connection (incl.
"own key overrides default" and "key never logged/echoed", same rigor as
test_no_token_logging.py), deterministic insights over real uploaded data,
and the grounded Q&A assistant (incl. that the exact real numbers -- not
fabricated ones -- reach the provider, and that a provider failure degrades
to a 502 instead of a 500 or a fabricated answer).
"""

from __future__ import annotations

import logging
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


def _mock_groq_classify_then(categories: list[str], *, then_returns: str | None = None) -> respx.Route:
    """Returns the respx Route so callers can keep using the SAME route
    object for later assertions/re-mocking -- calling ``respx.post(url)``
    again elsewhere would register a second, unmocked route matching the
    same URL and shadow this one (an easy respx footgun: an unmocked route
    added later intercepts the call and makes it fail as if the provider
    were down, rather than falling through to this working mock)."""
    calls = {"n": 0}

    def _responder(request: httpx.Request) -> httpx.Response:
        idx = calls["n"]
        calls["n"] += 1
        if idx < len(categories):
            return httpx.Response(200, json={"choices": [{"message": {"content": categories[idx]}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": then_returns or "ok"}}]})

    return respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(side_effect=_responder)


def _upload_valid_statement(client: TestClient, headers: dict) -> None:
    with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
        response = client.post("/workspace/upload", headers=headers, files={"files": ("valid_statement.ofx", fh, "application/octet-stream")})
    assert response.status_code == 200


# -- GET /ai/models -----------------------------------------------------


def test_list_models_requires_auth(client: TestClient) -> None:
    assert client.get("/ai/models").status_code == 401


@respx.mock
def test_list_models_returns_both_providers(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    body = client.get("/ai/models", headers=headers).json()
    providers = {m["provider"] for m in body["models"]}
    assert providers == {"groq", "openai"}


# -- POST /ai/settings/test-connection -----------------------------------


def test_test_connection_requires_auth(client: TestClient) -> None:
    assert client.post("/ai/settings/test-connection", json={"provider": "groq"}).status_code == 401


@respx.mock
def test_test_connection_reports_success_and_failure(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)

    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}))
    ok_response = client.post("/ai/settings/test-connection", headers=headers, json={"provider": "groq"})
    assert ok_response.status_code == 200
    assert ok_response.json() == {"ok": True}

    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(401, json={"error": "bad key"}))
    fail_response = client.post("/ai/settings/test-connection", headers=headers, json={"provider": "groq"})
    assert fail_response.status_code == 200
    assert fail_response.json() == {"ok": False}


@respx.mock
def test_test_connection_uses_the_users_own_key_not_the_operator_default(client: TestClient) -> None:
    """test_settings (conftest) sets a default groq_api_key -- a request
    that supplies its own key must use THAT key against the provider, not
    silently fall back to the operator default."""
    headers = _bridge_and_get_headers(client)
    route = respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}))

    client.post("/ai/settings/test-connection", headers=headers, json={"provider": "groq", "api_key": "user-own-key-xyz"})

    sent_auth = route.calls.last.request.headers["Authorization"]
    assert sent_auth == "Bearer user-own-key-xyz"
    assert "test-groq-key" not in sent_auth  # the operator default was not used


@respx.mock
def test_test_connection_never_echoes_or_logs_the_users_own_key(client: TestClient, caplog) -> None:
    headers = _bridge_and_get_headers(client)
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}))
    secret_key = "sk-super-secret-should-never-appear-anywhere-abc123"

    with caplog.at_level(logging.DEBUG):
        response = client.post("/ai/settings/test-connection", headers=headers, json={"provider": "groq", "api_key": secret_key})

    assert secret_key not in response.text
    assert secret_key not in caplog.text


def test_test_connection_unknown_provider_is_400(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    response = client.post("/ai/settings/test-connection", headers=headers, json={"provider": "anthropic"})
    assert response.status_code == 400


# -- GET /ai/insights -----------------------------------------------------


@respx.mock
def test_insights_requires_uploaded_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    response = client.get("/ai/insights", headers=headers, params={"month": "2026-01"})
    # Fase 13: a freshly-bridged, never-uploaded session is `no_data_yet`
    # (404), not `work_session_expired` (410) -- see workspace/deps.py.
    assert response.status_code == 404


@respx.mock
def test_insights_reflect_real_uploaded_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_classify_then(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    response = client.get("/ai/insights", headers=headers, params={"month": "2026-01"})
    assert response.status_code == 200
    insights = response.json()["insights"]
    assert len(insights) >= 1
    assert all(i["kind"] in {"positive", "negative", "neutral"} for i in insights)


# -- POST /ai/ask -----------------------------------------------------


def test_ask_requires_auth(client: TestClient) -> None:
    response = client.post("/ai/ask", json={"question": "qual foi minha maior categoria?", "month": "2026-01"})
    assert response.status_code == 401


@respx.mock
def test_ask_requires_uploaded_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    response = client.post("/ai/ask", headers=headers, json={"question": "qual foi minha maior categoria?", "month": "2026-01"})
    assert response.status_code == 404


@respx.mock
def test_ask_grounds_the_prompt_in_the_real_session_numbers(client: TestClient) -> None:
    """Jan 2026 has income R$ 3000.00 in the fixture (asserted already by
    test_workspace_api.py) -- the exact figure must reach the provider
    verbatim, proving the assistant is grounded in this session's real data
    and not just forwarding the bare question."""
    headers = _bridge_and_get_headers(client)
    # 2026-09-02: as 3 descrições do fixture (SUPERMERCADO ABC/SALARIO
    # EMPRESA XYZ/CONTA DE LUZ) agora são todas resolvidas por regra
    # determinística (app/pipeline/categorizer/rules.py, prompt-mestre
    # §14) -- zero chamada real de classificação acontece no upload, então
    # a 1ª (e única) chamada HTTP real ao "Groq" é a própria pergunta do
    # /ai/ask. `categories=[]` deixa isso explícito (antes, uma lista de 3
    # itens desalinhava o índice do side_effect e a resposta da pergunta
    # "roubava" a resposta que seria da 1ª classificação).
    route = _mock_groq_classify_then([], then_returns="Você recebeu R$ 3000,00 em janeiro.")
    _upload_valid_statement(client, headers)

    response = client.post("/ai/ask", headers=headers, json={"question": "quanto recebi em janeiro?", "month": "2026-01"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Você recebeu R$ 3000,00 em janeiro."

    sent_body = route.calls.last.request.content.decode()
    assert "R$ 3000.00" in sent_body  # real number, not fabricated
    # the grounding/refusal instruction must be part of what's sent, every time
    assert "não possui essa informação" in sent_body


@respx.mock
def test_ask_degrades_to_502_when_the_provider_fails_instead_of_crashing(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    _mock_groq_classify_then(["Mercado", "Receitas", "Moradia"])
    _upload_valid_statement(client, headers)

    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(500, json={"error": "boom"}))
    response = client.post("/ai/ask", headers=headers, json={"question": "e agora?", "month": "2026-01"})

    assert response.status_code == 502
    assert "message" in response.json()["detail"]
