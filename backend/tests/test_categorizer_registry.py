from __future__ import annotations

import pytest

from app.core.config import Settings
from app.pipeline.categorizer.groq_provider import GroqProvider
from app.pipeline.categorizer.openai_provider import OpenAIProvider
from app.pipeline.categorizer.registry import (
    AVAILABLE_MODELS,
    MissingApiKey,
    UnknownProvider,
    build_provider,
    require_api_key,
    resolve_api_key,
)


def _settings(**overrides) -> Settings:
    return Settings(groq_api_key="default-groq-key", openai_api_key="default-openai-key", **overrides)


def test_available_models_cover_both_providers_with_unique_pairs() -> None:
    providers = {m.provider for m in AVAILABLE_MODELS}
    assert providers == {"groq", "openai"}
    pairs = [(m.provider, m.model) for m in AVAILABLE_MODELS]
    assert len(pairs) == len(set(pairs))


def test_resolve_api_key_prefers_users_own_key_over_default() -> None:
    assert resolve_api_key("groq", _settings(), "user-supplied-key") == "user-supplied-key"


def test_resolve_api_key_falls_back_to_operator_default() -> None:
    assert resolve_api_key("groq", _settings(), None) == "default-groq-key"
    assert resolve_api_key("openai", _settings(), None) == "default-openai-key"


def test_resolve_api_key_returns_empty_string_when_neither_is_available() -> None:
    """Soft resolution -- used by the upload/classify path, which must
    degrade each transaction to "Erro na classificação" rather than block
    the whole upload (Fase 4's validated graceful-degradation behavior)."""
    assert resolve_api_key("groq", Settings(groq_api_key="", openai_api_key=""), None) == ""


def test_require_api_key_raises_when_neither_is_available() -> None:
    """Strict resolution -- used by the explicit AI actions
    (test-connection/ask), where an immediate 400 is more honest than a
    confusing downstream provider failure."""
    with pytest.raises(MissingApiKey):
        require_api_key("groq", Settings(groq_api_key="", openai_api_key=""), None)


def test_require_api_key_still_prefers_the_users_own_key() -> None:
    assert require_api_key("groq", Settings(groq_api_key="", openai_api_key=""), "user-key") == "user-key"


def test_build_provider_groq_uses_default_model_when_none_given() -> None:
    provider = build_provider("groq", None, "k")
    assert isinstance(provider, GroqProvider)
    assert provider.model  # non-empty default


def test_build_provider_openai_honors_explicit_model() -> None:
    provider = build_provider("openai", "gpt-4o", "k")
    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "gpt-4o"


def test_build_provider_rejects_unknown_provider() -> None:
    with pytest.raises(UnknownProvider):
        build_provider("anthropic", None, "k")
