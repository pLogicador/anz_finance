"""Filter semantics ported from the legacy app -- two real, distinct
functions, not one canonical + one hand-copied inline variant:

- ``filter_transactions``: ported verbatim from
  legacy_streamlit/modules/data/finance_data.py::filter_transactions.
  Month filter always applies; an empty/falsy ``categories`` list means "no
  category filter", not "show nothing". Used for KPIs and the transactions
  table.
- ``filter_transactions_for_trend``: formalizes what was only a hand-copied
  inline expression in the legacy app
  (legacy_streamlit/modules/dashboard/streamlit_app.py:138), used by
  trend/heatmap charts: category-only, across the FULL history (no month
  filter) -- same "empty categories = no filter" semantic, deliberately no
  month filter at all.
- ``apply_type_filter``: ported from the legacy app's UI-layer
  ``_apply_type_filter`` (streamlit_app.py:160-165) -- becomes real
  backend/business logic here since there's no more Streamlit
  UI-layer/business-layer split between reruns.
"""

from __future__ import annotations

import pandas as pd


def filter_transactions(df: pd.DataFrame, month: str, categories: list[str] | None) -> pd.DataFrame:
    filtered = df[df["Mês"] == month]
    if categories:
        filtered = filtered[filtered["Categorias"].isin(categories)]
    return filtered


def filter_transactions_for_trend(df: pd.DataFrame, categories: list[str] | None) -> pd.DataFrame:
    if categories:
        return df[df["Categorias"].isin(categories)]
    return df


def apply_type_filter(df: pd.DataFrame, selected_type: str) -> pd.DataFrame:
    if selected_type == "Receitas":
        return df[df["Valor"] >= 0]
    if selected_type == "Despesas":
        return df[df["Valor"] < 0]
    return df
