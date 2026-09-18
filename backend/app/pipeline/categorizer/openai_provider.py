"""Second real provider (Fase 5's "multi-modelo" requirement). Deliberately
NOT a second vendor chosen at random -- OpenAI's Chat Completions API is
wire-compatible with Groq's (same request/response shape, both modeled on
the same spec), so this is a genuine, independently-reachable provider with
almost no new code, rather than a placeholder/fake provider standing in for
"multiple models" without actually being able to serve a real request.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import httpx

from app.pipeline.categorizer.labels import build_prompt

DEFAULT_MODEL = "gpt-4o-mini"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_CONCURRENCY = 8
DEFAULT_TIMEOUT_SECONDS = 20.0
# Ver o mesmo comentário em groq_provider.py -- Q&A livre (complete/stream)
# precisa de mais fôlego que classificar uma única transação. Dobrado de
# 45s pra 90s em 2026-09-18 (usuário confirmou ao vivo que 45s ainda
# cortava um relatório mais longo sobre "Todos os meses").
QA_TIMEOUT_SECONDS = 90.0


class OpenAIProviderError(Exception):
    pass


_DEFAULT_RETRY_DELAY_SECONDS = 0.6
_RATE_LIMIT_DEFAULT_DELAY_SECONDS = 5.0
_RATE_LIMIT_MAX_DELAY_SECONDS = 20.0


def _retry_delay_seconds(exc: Exception) -> float | None:
    """Ver o mesmo comentário em groq_provider.py -- só falha transitória
    vale retry (um 401/400 definitivo falharia idêntico numa 2ª
    tentativa); 429 respeita `Retry-After` quando presente, já que uma
    janela de rate-limit por MINUTO nunca libera em menos de 1 segundo."""
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return _DEFAULT_RETRY_DELAY_SECONDS
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 429:
            retry_after = exc.response.headers.get("retry-after")
            if retry_after:
                try:
                    return min(float(retry_after), _RATE_LIMIT_MAX_DELAY_SECONDS)
                except ValueError:
                    pass
            return _RATE_LIMIT_DEFAULT_DELAY_SECONDS
        if status >= 500:
            return _DEFAULT_RETRY_DELAY_SECONDS
    return None


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
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=QA_TIMEOUT_SECONDS) as client:
                    return (await self._chat(client, user, system=system)).strip()
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                delay = _retry_delay_seconds(exc)
                if attempt == 0 and delay is not None:
                    await asyncio.sleep(delay)
                    continue
                raise OpenAIProviderError(str(exc)) from exc
        raise OpenAIProviderError(str(last_exc))

    async def stream(self, *, system: str, user: str) -> AsyncIterator[str]:
        """Fase 4 do plano de streaming real -- mesmo racional/contrato do
        GroqProvider.stream (as duas APIs são compatíveis no formato de
        Chat Completions, incluindo o shape do SSE)."""
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        for attempt in range(2):
            emitted_any = False
            try:
                async with httpx.AsyncClient(timeout=QA_TIMEOUT_SECONDS) as client:
                    async with client.stream(
                        "POST",
                        OPENAI_CHAT_COMPLETIONS_URL,
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
                                emitted_any = True
                                yield delta
                return
            except httpx.HTTPStatusError as exc:
                delay = _retry_delay_seconds(exc)
                if not emitted_any and attempt == 0 and delay is not None:
                    await asyncio.sleep(delay)
                    continue
                raise OpenAIProviderError(f"OpenAI respondeu {exc.response.status_code}") from exc
            except httpx.TimeoutException as exc:
                if not emitted_any and attempt == 0:
                    await asyncio.sleep(_DEFAULT_RETRY_DELAY_SECONDS)
                    continue
                raise OpenAIProviderError("OpenAI não respondeu a tempo") from exc
            except httpx.TransportError as exc:
                if not emitted_any and attempt == 0:
                    await asyncio.sleep(_DEFAULT_RETRY_DELAY_SECONDS)
                    continue
                raise OpenAIProviderError(str(exc)) from exc

    async def test_connection(self) -> bool:
        try:
            result = await self.classify(["teste de conexão"])
            return result[0] != "Error"
        except Exception:  # noqa: BLE001
            return False
