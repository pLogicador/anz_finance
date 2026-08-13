"""Pluggable provider/model registry (PARTE 6.1/6.2) -- the one place that
knows which providers exist, which models each offers, and how to resolve
an API key for a given provider (operator default vs. the user's own,
session-only key). Every route that needs a live `AIProvider` instance
(upload/classify, insights, ask, test-connection) goes through
``build_provider`` instead of constructing ``GroqProvider``/``OpenAIProvider``
directly, so adding a third provider later is a one-place change.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.pipeline.categorizer.base import AIProvider
from app.pipeline.categorizer.groq_provider import DEFAULT_MODEL as GROQ_DEFAULT_MODEL
from app.pipeline.categorizer.groq_provider import GroqProvider
from app.pipeline.categorizer.openai_provider import DEFAULT_MODEL as OPENAI_DEFAULT_MODEL
from app.pipeline.categorizer.openai_provider import OpenAIProvider


class UnknownProvider(ValueError):
    pass


class MissingApiKey(ValueError):
    """Neither a user-supplied key nor an operator default is available for this provider."""


@dataclass(frozen=True)
class ModelOption:
    provider: str
    model: str
    label: str


AVAILABLE_MODELS: tuple[ModelOption, ...] = (
    ModelOption(provider="groq", model="llama-3.1-8b-instant", label="Groq · Llama 3.1 8B Instant (rápido)"),
    ModelOption(provider="groq", model="llama-3.3-70b-versatile", label="Groq · Llama 3.3 70B Versatile (mais preciso)"),
    ModelOption(provider="openai", model="gpt-4o-mini", label="OpenAI · GPT-4o mini (rápido)"),
    ModelOption(provider="openai", model="gpt-4o", label="OpenAI · GPT-4o (mais preciso)"),
)

DEFAULT_PROVIDER = "groq"


def resolve_api_key(provider: str, settings: Settings, own_key: str | None) -> str:
    """Soft resolution, used by the classification pipeline
    (``routes/upload.py``): the user's own key (never persisted -- it only
    ever lives for the duration of one request) wins over the operator
    default, but if NEITHER is configured this returns ``""`` instead of
    raising. An empty key isn't silently "fine" -- ``GroqProvider``/
    ``OpenAIProvider`` will fail every call with it -- but that failure
    already has a well-defined, validated outcome: each per-item failure
    becomes the literal "Error" -> normalized to "Erro na classificação"
    (see ``labels.py``), so the whole upload still completes instead of
    being blocked outright. This matches Fase 4's validated behavior
    (pipeline degrades gracefully with no key configured, doesn't hard-fail
    the upload) and must not regress it.
    """
    if own_key:
        return own_key
    return {"groq": settings.groq_api_key, "openai": settings.openai_api_key}.get(provider, "")


def require_api_key(provider: str, settings: Settings, own_key: str | None) -> str:
    """Strict resolution, used by the explicit AI actions in
    ``routes/ai.py`` (test-connection/ask): here there's no batch to
    degrade gracefully -- a deliberate user action ("test my connection",
    "answer this question") deserves an immediate, honest 400 when no key
    is configured at all, rather than a confusing downstream provider
    failure.
    """
    key = resolve_api_key(provider, settings, own_key)
    if not key:
        raise MissingApiKey(f"Nenhuma chave de API disponível para o provedor '{provider}'.")
    return key


def build_provider(provider: str, model: str | None, api_key: str) -> AIProvider:
    if provider == "groq":
        return GroqProvider(api_key=api_key, model=model or GROQ_DEFAULT_MODEL)
    if provider == "openai":
        return OpenAIProvider(api_key=api_key, model=model or OPENAI_DEFAULT_MODEL)
    raise UnknownProvider(f"Provedor de IA desconhecido: '{provider}'.")
