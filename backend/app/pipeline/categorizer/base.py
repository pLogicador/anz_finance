"""AIProvider abstraction (PARTE 6.1). Fase 3 shipped one concrete provider
(Groq); Fase 5 adds a second (OpenAI) plus a free-form ``complete`` method
for the Q&A assistant/insights -- the interface was kept provider-agnostic
from the start so this didn't require touching any Fase 3 call site.

Fase 4 do plano de streaming real (2026-09-15, syncron_core/docs/maestro-
respostas-reais-streaming-plano.md) adds ``stream()`` -- same grounded Q&A
contract as ``complete()``, but yielding the answer as real deltas (native
Server-Sent Events from the provider's own Chat Completions API, `stream:
true`), instead of blocking on the full response. Kept as a SEPARATE method
(not a `stream: bool` flag on `complete`) so the non-streaming call sites
already wired (test-connection, `POST /ai/ask`) are untouched -- zero risk
of regressing them while adding this.
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol


class AIProvider(Protocol):
    """Every provider (Groq, OpenAI) implements this."""

    async def classify(self, descriptions: list[str]) -> list[str]:
        """Returns one raw label string per description, same order, same length.

        A per-item failure must not raise -- it appends the literal string
        "Error" for that item (matches the legacy contract exactly, see
        legacy_streamlit/modules/llm/categorizer.py:54-64) so one bad
        transaction never aborts the whole batch.
        """
        ...

    async def test_connection(self) -> bool:
        """Backs `POST /ai/settings/test-connection`."""
        ...

    async def complete(self, *, system: str, user: str) -> str:
        """Free-form chat completion -- backs the Q&A assistant and the
        (currently unused by the deterministic insight engine, but kept
        available for a future LLM-authored insight) narrative surfaces.
        Must raise on failure (unlike ``classify``, there's no single-item
        batch to keep alive) so callers can distinguish "provider is down"
        from "provider answered".
        """
        ...

    def stream(self, *, system: str, user: str) -> AsyncIterator[str]:
        """Same free-form chat completion as ``complete()``, but yielding
        each new text delta as it arrives from the provider's own SSE
        stream (never a fake/simulated stream over an already-complete
        answer). Must raise on failure -- same contract as ``complete()``,
        just possibly mid-iteration if the connection drops after some
        deltas already arrived (the caller decides what to do with the
        partial text already yielded)."""
        ...
