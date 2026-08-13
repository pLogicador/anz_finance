"""Contextual insights (PARTE 6.3), deterministic -- not an LLM call.

Deliberate engineering choice, not a scope-cut: every number these insights
quote (concentration %, delta %, savings rate %) is already computed by
``app/pipeline/metrics.py`` for the same request (KPIs/summary endpoint), so
turning them into a sentence is a pure, local, zero-latency, zero-cost,
zero-hallucination-risk operation -- there is nothing an LLM call would add
here except latency and a chance of getting its own arithmetic wrong. The
Q&A assistant (``app/routes/ai.py``'s ``/ai/ask``) is where a real LLM call
belongs, because open-ended questions genuinely need language understanding
that a rule can't provide; a "top category" insight does not.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from app.pipeline.metrics import PeriodSummary

Kind = Literal["positive", "negative", "neutral"]


@dataclass(frozen=True)
class Insight:
    kind: Kind
    text: str


def build_insights(
    *,
    summary: PeriodSummary,
    deltas: dict[str, float | None],
    category_breakdown: pd.DataFrame,
    month: str,
) -> list[Insight]:
    insights: list[Insight] = []

    # 1. Category concentration -- only meaningful once there's real expense volume.
    total_expense = abs(summary.expense)
    if summary.top_category and total_expense > 0:
        share = (summary.top_category_amount / total_expense) * 100
        if share >= 60:
            insights.append(
                Insight(
                    "negative",
                    f"“{summary.top_category}” concentra {share:.0f}% dos seus gastos em {month} -- vale revisar se dá para diluir esse peso.",
                )
            )
        elif share >= 30:
            insights.append(
                Insight(
                    "neutral",
                    f"“{summary.top_category}” foi a maior categoria de gasto em {month}, {share:.0f}% do total.",
                )
            )

    # 2. Expense trend vs. previous month.
    expense_delta = deltas.get("expense")
    if expense_delta is not None:
        if expense_delta >= 20:
            insights.append(Insight("negative", f"Suas despesas subiram {expense_delta:.0f}% em relação ao mês anterior."))
        elif expense_delta <= -20:
            insights.append(Insight("positive", f"Suas despesas caíram {abs(expense_delta):.0f}% em relação ao mês anterior."))

    # 3. Savings rate (net / income) -- only meaningful with real income.
    if summary.income > 0:
        savings_rate = (summary.net / summary.income) * 100
        if savings_rate >= 20:
            insights.append(Insight("positive", f"Você guardou {savings_rate:.0f}% da sua renda em {month} -- uma taxa de poupança saudável."))
        elif savings_rate < 0:
            insights.append(Insight("negative", f"Em {month} você gastou {abs(savings_rate):.0f}% a mais do que recebeu."))

    # 4. Fallback when there simply isn't enough signal for the rules above (e.g. first month, tiny dataset).
    if not insights:
        insights.append(Insight("neutral", f"Sem sinais relevantes para {month} ainda -- envie mais meses para comparações mais ricas."))

    return insights
