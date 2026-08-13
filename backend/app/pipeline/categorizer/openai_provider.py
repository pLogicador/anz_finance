"""Second real provider (Fase 5's "multi-modelo" requirement). Deliberately
NOT a second vendor chosen at random -- OpenAI's Chat Completions API is
wire-compatible with Groq's (same request/response shape, both modeled on
the same spec), so this is a genuine, independently-reachable provider with
almost no new code, rather than a placeholder/fake provider standing in for
"multiple models" without actually being able to serve a real request.
"""

from __future__ import annotations

import asyncio

import httpx

from app.pipeline.categorizer.labels import build_prompt

DEFAULT_MODEL = "gpt-4o-mini"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_CONCURRENCY = 8
DEFAULT_TIMEOUT_SECONDS = 20.0


class OpenAIProviderError(Exception):
    pass


class OpenAIProvider:
    provider_id = "openai"

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
            except Exception:  # noqa: BLE001 -- same per-item failure contract as GroqProvider
                return "Error"

    async def _chat(self, client: httpx.AsyncClient, prompt: str, *, system: str | None = None) -> str:
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        response = await client.post(
            OPENAI_CHAT_COMPLETIONS_URL,
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
            raise OpenAIProviderError(str(exc)) from exc

    async def test_connection(self) -> bool:
        try:
            result = await self.classify(["teste de conexão"])
            return result[0] != "Error"
        except Exception:  # noqa: BLE001
            return False
