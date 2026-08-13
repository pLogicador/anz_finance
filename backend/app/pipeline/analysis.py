"""Fase 6: anomaly detection and multi-period comparison. Both deterministic
(same rationale as insights.py -- no LLM call needed for arithmetic over
already-available data).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.pipeline import metrics

ANOMALY_RATIO_THRESHOLD = 2.5
ANOMALY_MIN_CATEGORY_SIZE = 3


@dataclass(frozen=True)
class Anomaly:
    date: str
    description: str
    category: str
    valor: float
    category_average: float
    ratio: float


def detect_anomalies(
    df: pd.DataFrame,
    *,
    min_category_size: int = ANOMALY_MIN_CATEGORY_SIZE,
    ratio_threshold: float = ANOMALY_RATIO_THRESHOLD,
) -> list[Anomaly]:
    """Flags expense transactions whose absolute value is at least
    ``ratio_threshold``x their category's own average -- a simple,
    small-N-safe outlier rule (a straight z-score needs more samples per
    category than a few months of personal transactions usually have).
    Categories with fewer than ``min_category_size`` transactions are
    skipped entirely: there's no meaningful "average" to compare against
    with 1-2 data points.
    """
    if df.empty:
        return []
    expenses = df[df["Valor"] < 0].copy()
    if expenses.empty:
        return []
    expenses["_abs"] = expenses["Valor"].abs()

    anomalies: list[Anomaly] = []
    for category, group in expenses.groupby("Categorias"):
        if len(group) < min_category_size:
            continue
        average = float(group["_abs"].mean())
        if average <= 0:
            continue
        for _, row in group.iterrows():
            ratio = float(row["_abs"]) / average
            if ratio < ratio_threshold:
                continue
            date_value = row["Data"]
            date_str = date_value.isoformat() if hasattr(date_value, "isoformat") else str(date_value)
            anomalies.append(
                Anomaly(
                    date=date_str,
                    description=str(row["Descrição"]),
                    category=str(category),
                    valor=float(row["Valor"]),
                    category_average=average,
                    ratio=ratio,
                )
            )

    anomalies.sort(key=lambda a: a.ratio, reverse=True)
    return anomalies


@dataclass(frozen=True)
class CategoryDelta:
    category: str
    valor_a: float
    valor_b: float
    delta: float


@dataclass(frozen=True)
class PeriodComparison:
    month_a: str
    month_b: str
    summary_a: metrics.PeriodSummary
    summary_b: metrics.PeriodSummary
    income_change_pct: float | None
    expense_change_pct: float | None
    net_change_pct: float | None
    category_deltas: list[CategoryDelta]


def _pct_change(before: float, after: float) -> float | None:
    if before == 0:
        return None
    return ((after - before) / abs(before)) * 100


def compare_periods(df: pd.DataFrame, month_a: str, month_b: str) -> PeriodComparison:
    """Unlike ``metrics.month_over_month_delta`` (always "vs. the
    immediately preceding available month"), this compares any two
    explicitly chosen months -- e.g. the same month a year apart, or two
    non-adjacent months -- which is the real gap the plan calls out
    ("comparações além do delta de 1 mês atual")."""
    df_a = df[df["Mês"] == month_a]
    df_b = df[df["Mês"] == month_b]

    summary_a = metrics.summarize(df_a)
    summary_b = metrics.summarize(df_b)

    breakdown_a = metrics.category_breakdown(df_a, only_expenses=True).set_index("Categorias")["Valor"].to_dict()
    breakdown_b = metrics.category_breakdown(df_b, only_expenses=True).set_index("Categorias")["Valor"].to_dict()
    categories = sorted(set(breakdown_a) | set(breakdown_b))
    category_deltas = [
        CategoryDelta(
            category=c,
            valor_a=float(breakdown_a.get(c, 0.0)),
            valor_b=float(breakdown_b.get(c, 0.0)),
            delta=float(breakdown_b.get(c, 0.0)) - float(breakdown_a.get(c, 0.0)),
        )
        for c in categories
    ]

    return PeriodComparison(
        month_a=month_a,
        month_b=month_b,
        summary_a=summary_a,
        summary_b=summary_b,
        income_change_pct=_pct_change(summary_a.income, summary_b.income),
        expense_change_pct=_pct_change(summary_a.expense, summary_b.expense),
        net_change_pct=_pct_change(summary_a.net, summary_b.net),
        category_deltas=category_deltas,
    )
