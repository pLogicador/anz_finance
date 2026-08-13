"""app/pipeline/insights.py is deterministic -- no mocking needed, just
feed it the same shaped data metrics.py would produce and assert the
sentence-level output, including the numbers it quotes."""

from __future__ import annotations

import pandas as pd

from app.pipeline.insights import build_insights
from app.pipeline.metrics import PeriodSummary


def _breakdown(rows: list[tuple[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Categorias", "Valor"])


def test_high_concentration_produces_a_negative_insight_with_correct_percentage() -> None:
    summary = PeriodSummary(income=0, expense=-1000, net=-1000, transaction_count=5, top_category="Moradia", top_category_amount=700)
    insights = build_insights(summary=summary, deltas={"income": None, "expense": None, "net": None}, category_breakdown=_breakdown([]), month="2026-01")
    assert any(i.kind == "negative" and "Moradia" in i.text and "70%" in i.text for i in insights)


def test_moderate_concentration_produces_a_neutral_insight() -> None:
    summary = PeriodSummary(income=0, expense=-1000, net=-1000, transaction_count=5, top_category="Mercado", top_category_amount=350)
    insights = build_insights(summary=summary, deltas={"income": None, "expense": None, "net": None}, category_breakdown=_breakdown([]), month="2026-01")
    assert any(i.kind == "neutral" and "Mercado" in i.text and "35%" in i.text for i in insights)


def test_low_concentration_produces_no_concentration_insight() -> None:
    summary = PeriodSummary(income=0, expense=-1000, net=-1000, transaction_count=5, top_category="Lazer", top_category_amount=100)
    insights = build_insights(summary=summary, deltas={"income": None, "expense": None, "net": None}, category_breakdown=_breakdown([]), month="2026-01")
    assert not any("Lazer" in i.text for i in insights)


def test_expense_spike_is_flagged_negative() -> None:
    summary = PeriodSummary(income=0, expense=0, net=0, transaction_count=0, top_category=None, top_category_amount=0)
    insights = build_insights(summary=summary, deltas={"income": None, "expense": 35.0, "net": None}, category_breakdown=_breakdown([]), month="2026-01")
    assert any(i.kind == "negative" and "subiram 35%" in i.text for i in insights)


def test_expense_drop_is_flagged_positive() -> None:
    summary = PeriodSummary(income=0, expense=0, net=0, transaction_count=0, top_category=None, top_category_amount=0)
    insights = build_insights(summary=summary, deltas={"income": None, "expense": -25.0, "net": None}, category_breakdown=_breakdown([]), month="2026-01")
    assert any(i.kind == "positive" and "caíram 25%" in i.text for i in insights)


def test_healthy_savings_rate_is_flagged_positive() -> None:
    summary = PeriodSummary(income=1000, expense=-700, net=300, transaction_count=3, top_category=None, top_category_amount=0)
    insights = build_insights(summary=summary, deltas={"income": None, "expense": None, "net": None}, category_breakdown=_breakdown([]), month="2026-01")
    assert any(i.kind == "positive" and "30%" in i.text for i in insights)


def test_negative_net_is_flagged_negative() -> None:
    summary = PeriodSummary(income=1000, expense=-1200, net=-200, transaction_count=3, top_category=None, top_category_amount=0)
    insights = build_insights(summary=summary, deltas={"income": None, "expense": None, "net": None}, category_breakdown=_breakdown([]), month="2026-01")
    assert any(i.kind == "negative" and "gastou 20%" in i.text for i in insights)


def test_falls_back_to_a_neutral_message_when_no_rule_triggers() -> None:
    summary = PeriodSummary(income=0, expense=0, net=0, transaction_count=0, top_category=None, top_category_amount=0)
    insights = build_insights(summary=summary, deltas={"income": None, "expense": None, "net": None}, category_breakdown=_breakdown([]), month="2026-01")
    assert len(insights) == 1
    assert insights[0].kind == "neutral"
