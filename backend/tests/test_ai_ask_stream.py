"""POST /ai/ask/stream (Fase 4 do plano de streaming real, 2026-09-15,
syncron_core/docs/maestro-respostas-reais-streaming-plano.md) -- confirma
que a resposta chega em múltiplos eventos SSE reais (não um único evento
com o texto inteiro), que o grounding é o MESMO usado por `POST /ai/ask`
(mesmos dados reais da sessão chegando ao provedor), e que uma falha do
provedor no meio do stream vira um evento `error` nomeado em vez de
derrubar a conexão sem explicação.
"""

from __future__ import annotations

import json
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


def _upload_valid_statement(client: TestClient, headers: dict) -> None:
    with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
        response = client.post("/workspace/upload", headers=headers, files={"files": ("valid_statement.ofx", fh, "application/octet-stream")})
    assert response.status_code == 200


def _sse_chunk(content: str) -> bytes:
    payload = json.dumps({"id": "x", "choices": [{"delta": {"content": content}}]})
    return f"data: {payload}\n\n".encode()


def _groq_sse_body(pieces: list[str]) -> bytes:
    body = b"".join(_sse_chunk(p) for p in pieces)
    return body + b"data: [DONE]\n\n"


def _parse_sse_events(raw_text: str) -> list[dict]:
    events = []
    for block in raw_text.strip().split("\n\n"):
        if not block.strip():
            continue
        event_name = None
        data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                event_name = line[len("event: ") :]
            elif line.startswith("data: "):
                data = line[len("data: ") :]
        if event_name is not None:
            events.append({"event": event_name, "data": json.loads(data) if data else None})
    return events


def test_ask_stream_requires_uploaded_data(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    response = client.post("/ai/ask/stream", headers=headers, json={"question": "quanto gastei?", "month": "2026-01"})
    # Mesma validação de `ask()` -- roda ANTES de o gerador SSE começar,
    # então ainda é um 404 normal, não um stream com um evento de erro.
    assert response.status_code == 404


def test_ask_stream_unknown_provider_is_400_before_any_byte_of_the_stream(client: TestClient) -> None:
    headers = _bridge_and_get_headers(client)
    with respx.mock:
        mock_valid(respx, email="tester@example.com")
        _upload_valid_statement(client, headers)
        response = client.post(
            "/ai/ask/stream",
            headers=headers,
            json={"question": "quanto gastei?", "month": "2026-01", "provider": "anthropic"},
        )
    assert response.status_code == 400
    assert not response.headers.get("content-type", "").startswith("text/event-stream")


def test_ask_stream_delivers_multiple_real_delta_events_grounded_in_real_session_numbers(client: TestClient) -> None:
    """Jan 2026 tem receita real de R$ 3000,00 no fixture (já confirmado em
    test_ai_routes.py) -- o número real precisa chegar ao provedor, e a
    resposta precisa voltar em MAIS DE UM evento `delta` (prova de que é
    streaming de verdade, não um único chunk fingindo ser vários)."""
    headers = _bridge_and_get_headers(client)
    with respx.mock:
        mock_valid(respx, email="tester@example.com")
        _upload_valid_statement(client, headers)

        route = respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(
            return_value=httpx.Response(200, content=_groq_sse_body(["Você ", "recebeu ", "R$ 3000,00 ", "em janeiro."]))
        )

        response = client.post(
            "/ai/ask/stream", headers=headers, json={"question": "quanto recebi em janeiro?", "month": "2026-01"}
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse_events(response.text)
    delta_events = [e for e in events if e["event"] == "delta"]
    assert len(delta_events) == 4  # streaming real, não um único evento com o texto inteiro
    assert "".join(e["data"]["delta"] for e in delta_events) == "Você recebeu R$ 3000,00 em janeiro."
    assert events[-1]["event"] == "done"

    sent_body = route.calls.last.request.content.decode()
    assert "R$ 3000.00" in sent_body  # número real da sessão, não fabricado
    assert '"stream":true' in sent_body


def test_ask_stream_degrades_to_an_error_event_when_the_provider_fails_mid_stream(client: TestClient) -> None:
    """Diferente de `POST /ai/ask` (que ainda pode responder 502 -- nenhum
    byte foi mandado ainda), aqui o header 200/`text/event-stream` já saiu
    antes de a falha do provedor acontecer -- não dá mais pra trocar o
    status HTTP, então a falha vira um evento `error` nomeado."""
    headers = _bridge_and_get_headers(client)
    with respx.mock:
        mock_valid(respx, email="tester@example.com")
        _upload_valid_statement(client, headers)

        respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(500, json={"error": "boom"}))

        response = client.post("/ai/ask/stream", headers=headers, json={"question": "e agora?", "month": "2026-01"})

    assert response.status_code == 200  # os headers já saíram como sucesso
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse_events(response.text)
    assert events == [{"event": "error", "data": {"message": "O provedor de IA não respondeu. Tente novamente em instantes."}}]


def test_ask_stream_never_echoes_or_logs_the_users_own_key(client: TestClient, caplog) -> None:
    headers = _bridge_and_get_headers(client)
    secret_key = "sk-super-secret-should-never-appear-anywhere-abc123"
    with respx.mock:
        mock_valid(respx, email="tester@example.com")
        _upload_valid_statement(client, headers)
        respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(200, content=_groq_sse_body(["ok"])))

        with caplog.at_level(logging.DEBUG):
            response = client.post(
                "/ai/ask/stream",
                headers=headers,
                json={"question": "e agora?", "month": "2026-01", "api_key": secret_key},
            )

    assert secret_key not in response.text
    assert secret_key not in caplog.text
