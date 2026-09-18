"""Mirrors test_categorizer_concurrency.py's rigor for the second provider --
same per-item failure contract, same concurrency mechanism, plus the new
``complete()`` method (raises on failure, unlike ``classify()``)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.pipeline.categorizer.openai_provider import (
    OPENAI_CHAT_COMPLETIONS_URL,
    OpenAIProvider,
    OpenAIProviderError,
    _retry_delay_seconds,
)


@pytest.mark.asyncio
@respx.mock
async def test_classify_returns_one_label_per_description_same_order() -> None:
    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(
        side_effect=[
            httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}),
            httpx.Response(200, json={"choices": [{"message": {"content": "Receitas"}}]}),
        ]
    )
    provider = OpenAIProvider(api_key="test-key", concurrency=1)
    result = await provider.classify(["a", "b"])
    assert result == ["Mercado", "Receitas"]


@pytest.mark.asyncio
@respx.mock
async def test_a_failed_classify_call_becomes_error_without_raising() -> None:
    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(500, json={"error": "boom"}))
    provider = OpenAIProvider(api_key="test-key")
    result = await provider.classify(["a"])
    assert result == ["Error"]


@pytest.mark.asyncio
@respx.mock
async def test_complete_returns_the_message_content() -> None:
    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Sua maior categoria foi Mercado."}}]})
    )
    provider = OpenAIProvider(api_key="test-key")
    answer = await provider.complete(system="seja breve", user="qual foi minha maior categoria?")
    assert answer == "Sua maior categoria foi Mercado."


@pytest.mark.asyncio
@respx.mock
async def test_complete_raises_instead_of_swallowing_failures() -> None:
    """Unlike classify(), complete() has no batch to keep alive -- a failed
    call must be visible to the caller (routes/ai.py turns it into a 502),
    not silently become an empty/garbage answer."""
    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(500, json={"error": "boom"}))
    provider = OpenAIProvider(api_key="test-key")
    with pytest.raises(OpenAIProviderError):
        await provider.complete(system="s", user="u")


# ===== Retry em falha transitória (achado real, usuário, 2026-09-18: =====
# ===== "provedor de IA não respondeu" reapareceu mesmo depois do timeout =====
# ===== maior -- parte do sintoma é uma falha transitória de verdade). =====


@pytest.mark.asyncio
@respx.mock
async def test_complete_retries_once_and_succeeds_after_a_transient_500() -> None:
    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(
        side_effect=[
            httpx.Response(500, json={"error": "boom"}),
            httpx.Response(200, json={"choices": [{"message": {"content": "Sua maior categoria foi Mercado."}}]}),
        ]
    )
    provider = OpenAIProvider(api_key="test-key")
    answer = await provider.complete(system="s", user="u")
    assert answer == "Sua maior categoria foi Mercado."


@pytest.mark.asyncio
@respx.mock
async def test_complete_never_retries_a_definitive_401() -> None:
    """Um único mock na fila -- se `complete()` tentasse de novo, o respx
    ficaria sem resposta configurada pra devolver e o teste falharia com
    um erro diferente de `OpenAIProviderError` (prova indireta de que só
    UMA chamada real aconteceu)."""
    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(401, json={"error": "bad key"}))
    provider = OpenAIProvider(api_key="bad")
    with pytest.raises(OpenAIProviderError):
        await provider.complete(system="s", user="u")


@pytest.mark.asyncio
@respx.mock
async def test_stream_retries_once_and_succeeds_when_nothing_was_emitted_yet() -> None:
    sse_body = 'data: {"choices":[{"delta":{"content":"Olá"}}]}\n\ndata: [DONE]\n\n'
    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(
        side_effect=[httpx.Response(500, json={"error": "boom"}), httpx.Response(200, content=sse_body)]
    )
    provider = OpenAIProvider(api_key="test-key")
    deltas = [chunk async for chunk in provider.stream(system="s", user="u")]
    assert deltas == ["Olá"]


@pytest.mark.asyncio
@respx.mock
async def test_stream_never_retries_a_definitive_401() -> None:
    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(401, json={"error": "bad key"}))
    provider = OpenAIProvider(api_key="bad")
    with pytest.raises(OpenAIProviderError):
        async for _ in provider.stream(system="s", user="u"):
            pass


# ===== _retry_delay_seconds: decisão pura, sem rede/sleep real =====


def _http_error(status: int, headers: dict | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", OPENAI_CHAT_COMPLETIONS_URL)
    response = httpx.Response(status, headers=headers or {}, request=request)
    return httpx.HTTPStatusError("boom", request=request, response=response)


def test_retry_delay_honors_a_real_retry_after_header() -> None:
    assert _retry_delay_seconds(_http_error(429, {"retry-after": "3"})) == 3.0


def test_retry_delay_caps_an_absurdly_long_retry_after() -> None:
    assert _retry_delay_seconds(_http_error(429, {"retry-after": "9999"})) == 20.0


def test_retry_delay_falls_back_to_a_realistic_default_without_the_header() -> None:
    assert _retry_delay_seconds(_http_error(429)) == 5.0


def test_retry_delay_for_a_5xx_stays_the_short_transient_default() -> None:
    assert _retry_delay_seconds(_http_error(503)) == 0.6


def test_retry_delay_is_none_for_a_definitive_client_error() -> None:
    assert _retry_delay_seconds(_http_error(401)) is None
    assert _retry_delay_seconds(_http_error(400)) is None


@pytest.mark.asyncio
@respx.mock
async def test_test_connection_true_on_success_false_on_failure() -> None:
    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}))
    assert await OpenAIProvider(api_key="k").test_connection() is True

    respx.post(OPENAI_CHAT_COMPLETIONS_URL).mock(return_value=httpx.Response(401, json={"error": "bad key"}))
    assert await OpenAIProvider(api_key="bad").test_connection() is False
