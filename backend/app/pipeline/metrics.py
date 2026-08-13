"""Ported near-verbatim from legacy_streamlit/modules/ui/metrics.py -- these
were already pure, dependency-free aggregation functions, no Streamlit
coupling to remove.

Note on ``month_over_month_delta``'s ``invert`` pattern: this module
doesn't apply any inversion itself -- it just returns the raw % delta.
"Positive delta on expense should read as unfavorable" is a presentation
concern, applied by whatever renders it (Fase 4's KPI cards), same as the
legacy app's ``invert=True`` passed to ``kpi_card`` at the call site
(legacy_streamlit/modules/dashboard/streamlit_app.py:174).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PeriodSummary:
    income: float
    expense: float
    net: float
    transaction_count: int
    top_category: str | None
    top_category_amount: float


def summarize(df: pd.DataFrame) -> PeriodSummary:
    if df.empty:
        return PeriodSummary(0.0, 0.0, 0.0, 0, None, 0.0)

    income = df.loc[df["Valor"] > 0, "Valor"].sum()
    expense = df.loc[df["Valor"] < 0, "Valor"].sum()
    net = df["Valor"].sum()

    top_category = None
    top_category_amount = 0.0
    expenses = df[df["Valor"] < 0]
    if not expenses.empty:
        by_category = expenses.groupby("Categorias")["Valor"].sum().abs().sort_values(ascending=False)
        if not by_category.empty:
            top_category = by_category.index[0]
            top_category_amount = float(by_category.iloc[0])

    return PeriodSummary(
        income=float(income),
        expense=float(expense),
        net=float(net),
        transaction_count=int(len(df)),
        top_category=top_category,
        top_category_amount=top_category_amount,
    )


def month_over_month_delta(df: pd.DataFrame, current_month: str, metric: str = "net") -> float | None:
    """% change of `metric` (net/income/expense) vs. the previous available month."""
    months = sorted(df["Mês"].unique())
    if current_month not in months:
        return None
    idx = months.index(current_month)
    if idx == 0:
        return None
    previous_month = months[idx - 1]

    current = summarize(df[df["Mês"] == current_month])
    previous = summarize(df[df["Mês"] == previous_month])

    current_val = getattr(current, metric)
    previous_val = getattr(previous, metric)
    if previous_val == 0:
        return None
    return ((current_val - previous_val) / abs(previous_val)) * 100


def monthly_series(df: pd.DataFrame) -> pd.DataFrame:
    """One row per month with income/expense/net totals, sorted chronologically."""
    if df.empty:
        return pd.DataFrame(columns=["Mês", "Receitas", "Despesas", "Saldo"])

    grouped = (
        df.groupby("Mês")["Valor"]
        .agg(
            Receitas=lambda s: s[s > 0].sum(),
            Despesas=lambda s: s[s < 0].sum(),
            Saldo="sum",
        )
        .reset_index()
    )
    return grouped.sort_values("Mês")


def category_breakdown(df: pd.DataFrame, only_expenses: bool = True) -> pd.DataFrame:
    subset = df[df["Valor"] < 0] if only_expenses else df
    if subset.empty:
        return pd.DataFrame(columns=["Categorias", "Valor"])
    summary = subset.groupby("Categorias")["Valor"].sum().abs().reset_index()
    return summary[summary["Valor"] > 0].sort_values("Valor", ascending=False)
