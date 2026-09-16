"""Groq provider -- ports legacy_streamlit/modules/llm/categorizer.py's
behavior, with the concurrency fix the plan calls out explicitly (Fase 3):
the legacy ``Categorizer.classify`` called Groq once per transaction in a
plain sequential ``for`` loop -- "large statements are slow and make many
API calls" per that module's own docstring. Here, calls run concurrently
(bounded by a semaphore) via direct httpx calls to Groq's REST API instead
of through LangChain -- LangChain's only role in the legacy code was piping
a prompt template into a chat model, which a plain f-string + httpx call
does just as well with less dependency weight and much simpler concurrency
control (decision authorized by the plan's Fase 3 notes: drop
`langchain-openai`, reconsider the LangChain layer).

Per-item failure contract preserved exactly: a failed call (network error,
bad response, timeout) appends "Error" for that item, exactly like
legacy's `except Exception: categories.append("Error")` -- never aborts
the batch.

Fase 5 adds ``complete()`` (free-form chat, for the Q&A assistant) --
reuses the same chat-completions endpoint/auth, but raises on failure
instead of swallowing it, since there's no batch to keep alive.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import httpx

from app.pipeline.categorizer.labels import build_prompt

DEFAULT_MODEL = "llama-3.1-8b-instant"
GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_CONCURRENCY = 8
DEFAULT_TIMEOUT_SECONDS = 20.0


class GroqProviderError(Exception):
    """Raised by ``complete()``/``test_connection()`` on any failure -- never raised by ``classify()``."""


class GroqProvider:
    provider_id = "groq"

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_MODEL,
        concurrency: int = DEFAULT_CONCURRENCY,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._semaphore = asyncio.Semaphore(concurrency)
        self._timeout_seconds = timeout_seconds

    async def classify(self, descriptions: list[str]) -> list[str]:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            tasks = [self._classify_one(client, description) for description in descriptions]
            return await asyncio.gather(*tasks)

    async def _classify_one(self, client: httpx.AsyncClient, description: str) -> str:
        async with self._semaphore:
            try:
                content = await self._chat(client, build_prompt(description))
                return content.strip()
            except Exception:  # noqa: BLE001 -- one bad transaction must not abort the batch
                return "Error"

    async def _chat(self, client: httpx.AsyncClient, prompt: str, *, system: str | None = None) -> str:
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        response = await client.post(
            GROQ_CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages, "temperature": 0},
        )
        response.raise_for_status()
        body = response.json()
        return body["choices"][0]["message"]["content"]

    async def complete(self, *, system: str, user: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                return (await self._chat(client, user, system=system)).strip()
        except Exception as exc:  # noqa: BLE001
            raise GroqProviderError(str(exc)) from exc

    async def stream(self, *, system: str, user: str) -> AsyncIterator[str]:
        """Fase 4 do plano de streaming real -- mesmo endpoint/auth de
        ``_chat`` só com `stream: true`, consumindo o SSE nativo da própria
        Groq (o formato Chat Completions padrão: `data: {...}\\n\\n` por
        chunk, terminado por `data: [DONE]\\n\\n`) em vez de esperar o corpo
        inteiro. Levanta em qualquer falha, inclusive uma que só aparece NO
        MEIO da iteração (conexão cai depois de já ter mandado alguns
        deltas) -- mesmo contrato de `complete()`, o chamador decide o que
        fazer com o texto parcial já recebido até ali."""
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                async with client.stream(
                    "POST",
                    GROQ_CHAT_COMPLETIONS_URL,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "messages": messages, "temperature": 0, "stream": True},
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        raw = line[len("data:") :].strip()
                        if raw == "[DONE]":
                            return
                        try:
                            chunk = json.loads(raw)
                        except ValueError:
                            continue
                        choices = chunk.get("choices") or []
                        delta = (choices[0].get("delta") or {}).get("content") if choices else None
                        if delta:
                            yield delta
        except httpx.HTTPStatusError as exc:
            raise GroqProviderError(f"Groq respondeu {exc.response.status_code}") from exc
        except httpx.TimeoutException as exc:
            raise GroqProviderError("Groq não respondeu a tempo") from exc
        except httpx.TransportError as exc:
            raise GroqProviderError(str(exc)) from exc

    async def test_connection(self) -> bool:
        try:
            result = await self.classify(["teste de conexão"])
            return result[0] != "Error"
        except Exception:  # noqa: BLE001
            return False
