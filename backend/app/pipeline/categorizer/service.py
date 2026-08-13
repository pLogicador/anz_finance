"""Combines a provider's raw classification with the label-normalization
step -- the legacy app did this as two separate steps only because
Streamlit's UI layer used to own the normalization
(legacy_streamlit/modules/dashboard/streamlit_app.py:86-96). Here it's one
call since there's no separate UI layer left to own it.
"""

from __future__ import annotations

from app.pipeline.categorizer.base import AIProvider
from app.pipeline.categorizer.labels import normalize_classification


async def classify_transactions(provider: AIProvider, descriptions: list[str]) -> list[str]:
    raw = await provider.classify(descriptions)
    return [normalize_classification(label) for label in raw]
