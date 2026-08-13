"""AIProvider abstraction (PARTE 6.1). Fase 3 shipped one concrete provider
(Groq); Fase 5 adds a second (OpenAI) plus a free-form ``complete`` method
for the Q&A assistant/insights -- the interface was kept provider-agnostic
from the start so this didn't require touching any Fase 3 call site.
"""

from __future__ import annotations

from typing import Protocol


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
