from __future__ import annotations

from pydantic import BaseModel, Field

from app.pipeline.categorizer.registry import DEFAULT_PROVIDER


class AiTestConnectionRequest(BaseModel):
    provider: str = DEFAULT_PROVIDER
    model: str | None = None
    api_key: str | None = Field(default=None, description="User's own key, used once for this request only -- never persisted.")


class AiAskRequest(BaseModel):
    question: str
    month: str
    categories: list[str] | None = None
    type: str = "Todas"
    provider: str = DEFAULT_PROVIDER
    model: str | None = None
    api_key: str | None = Field(default=None, description="User's own key, used once for this request only -- never persisted.")
