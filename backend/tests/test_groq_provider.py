"""Mirrors test_openai_provider.py -- Groq é o provedor default de verdade
usado em produção (DEFAULT_PROVIDER), então merece a mesma cobertura direta
que o OpenAI já tinha, não só via as rotas de /ai/*."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL, GroqProvider, GroqProviderError


@pytest.mark.asyncio
@respx.mock
async def test_classify_returns_one_label_per_description_same_order() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(
        side_effect=[
            httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}),
            httpx.Response(200, json={"choices": [{"message": {"content": "Receitas"}}]}),
        ]
    )
    provider = GroqProvider(api_key="test-key", concurrency=1)
    result = await provider.classify(["a", "b"])
    assert result == ["Mercado", "Receitas"]


@pytest.mark.asyncio
@respx.mock
async def test_a_failed_classify_call_becomes_error_without_raising() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(500, json={"error": "boom"}))
    provider = GroqProvider(api_key="test-key")
    result = await provider.classify(["a"])
    assert result == ["Error"]


@pytest.mark.asyncio
@respx.mock
async def test_complete_returns_the_message_content() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Sua maior categoria foi Mercado."}}]})
    )
    provider = GroqProvider(api_key="test-key")
    answer = await provider.complete(system="seja breve", user="qual foi minha maior categoria?")
    assert answer == "Sua maior categoria foi Mercado."


@pytest.mark.asyncio
@respx.mock
async def test_complete_raises_instead_of_swallowing_failures() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(400, json={"error": "boom"}))
    provider = GroqProvider(api_key="test-key")
    with pytest.raises(GroqProviderError):
        await provider.complete(system="s", user="u")


@pytest.mark.asyncio
@respx.mock
async def test_test_connection_true_on_success_false_on_failure() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}))
    assert await GroqProvider(api_key="k").test_connection() is True

    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(401, json={"error": "bad key"}))
    assert await GroqProvider(api_key="bad").test_connection() is False


# ===== Retry em falha transitória (achado real, usuário, 2026-09-18: =====
# ===== "provedor de IA não respondeu" reapareceu mesmo depois do timeout =====
# ===== maior -- parte do sintoma é uma falha transitória de verdade). =====


@pytest.mark.asyncio
@respx.mock
async def test_complete_retries_once_and_succeeds_after_a_transient_500() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(
        side_effect=[
            httpx.Response(500, json={"error": "boom"}),
            httpx.Response(200, json={"choices": [{"message": {"content": "Sua maior categoria foi Mercado."}}]}),
        ]
    )
    provider = GroqProvider(api_key="test-key")
    answer = await provider.complete(system="s", user="u")
    assert answer == "Sua maior categoria foi Mercado."


@pytest.mark.asyncio
@respx.mock
async def test_complete_retries_once_and_succeeds_after_a_transient_429() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(
        side_effect=[
            httpx.Response(429, json={"error": "rate limited"}),
            httpx.Response(200, json={"choices": [{"message": {"content": "Ok."}}]}),
        ]
    )
    provider = GroqProvider(api_key="test-key")
    answer = await provider.complete(system="s", user="u")
    assert answer == "Ok."


@pytest.mark.asyncio
@respx.mock
async def test_complete_never_retries_a_definitive_401() -> None:
    """Um único mock na fila -- se `complete()` tentasse de novo, o respx
    ficaria sem resposta configurada e o teste falharia de um jeito
    diferente de `GroqProviderError` (prova indireta de só 1 chamada)."""
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(401, json={"error": "bad key"}))
    provider = GroqProvider(api_key="bad")
    with pytest.raises(GroqProviderError):
        await provider.complete(system="s", user="u")


@pytest.mark.asyncio
@respx.mock
async def test_complete_retries_once_on_connection_error_too() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(
        side_effect=[httpx.ConnectError("boom"), httpx.Response(200, json={"choices": [{"message": {"content": "Ok."}}]})]
    )
    provider = GroqProvider(api_key="test-key")
    answer = await provider.complete(system="s", user="u")
    assert answer == "Ok."


@pytest.mark.asyncio
@respx.mock
async def test_stream_retries_once_and_succeeds_when_nothing_was_emitted_yet() -> None:
    sse_body = 'data: {"choices":[{"delta":{"content":"Olá"}}]}\n\ndata: [DONE]\n\n'
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(
        side_effect=[httpx.Response(500, json={"error": "boom"}), httpx.Response(200, content=sse_body)]
    )
    provider = GroqProvider(api_key="test-key")
    deltas = [chunk async for chunk in provider.stream(system="s", user="u")]
    assert deltas == ["Olá"]


@pytest.mark.asyncio
@respx.mock
async def test_stream_never_retries_a_definitive_401() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(401, json={"error": "bad key"}))
    provider = GroqProvider(api_key="bad")
    with pytest.raises(GroqProviderError):
        async for _ in provider.stream(system="s", user="u"):
            pass
