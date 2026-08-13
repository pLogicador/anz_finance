"""Proves the Fase 3 concurrency fix: the legacy Categorizer.classify called
Groq once per transaction in a sequential loop
(legacy_streamlit/modules/llm/categorizer.py:54-64) -- for N transactions
each taking ~t seconds, that's N*t wall-clock time. GroqProvider bounds
concurrency at DEFAULT_CONCURRENCY (8) instead, so N transactions take
roughly ceil(N/8)*t.

This mocks Groq's HTTP endpoint with an artificial per-call delay (via
respx's async side_effect) rather than hitting the real API -- the point is
proving the concurrency *mechanism*, independent of real network calls.
"""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest
import respx

from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL, GroqProvider

CALL_DELAY_SECONDS = 0.2
NUM_DESCRIPTIONS = 16


async def _delayed_response(request: httpx.Request) -> httpx.Response:
    await asyncio.sleep(CALL_DELAY_SECONDS)
    return httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]})


@pytest.mark.asyncio
@respx.mock
async def test_classification_runs_concurrently_not_sequentially() -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(side_effect=_delayed_response)

    provider = GroqProvider(api_key="test-key", concurrency=8)
    descriptions = [f"transacao {i}" for i in range(NUM_DESCRIPTIONS)]

    started = time.monotonic()
    results = await provider.classify(descriptions)
    elapsed = time.monotonic() - started

    assert results == ["Mercado"] * NUM_DESCRIPTIONS

    sequential_would_take = NUM_DESCRIPTIONS * CALL_DELAY_SECONDS  # 3.2s
    concurrent_expected = (NUM_DESCRIPTIONS / 8) * CALL_DELAY_SECONDS  # 0.4s
    # Generous margin for test-runner scheduling jitter, but still nowhere
    # near the sequential-loop time -- this is the actual regression guard.
    assert elapsed < concurrent_expected * 3
    assert elapsed < sequential_would_take / 2


@pytest.mark.asyncio
@respx.mock
async def test_a_single_failed_call_becomes_error_without_aborting_the_batch() -> None:
    """Matches the legacy per-item failure contract exactly: one bad
    transaction never aborts the whole batch (legacy_streamlit/modules/llm/categorizer.py:61-63)."""
    call_count = 0

    def _flaky(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            return httpx.Response(500, json={"error": "boom"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "Saúde"}}]})

    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(side_effect=_flaky)

    provider = GroqProvider(api_key="test-key", concurrency=1)  # concurrency=1 to make call order deterministic
    results = await provider.classify(["a", "b", "c"])

    assert results == ["Saúde", "Error", "Saúde"]
