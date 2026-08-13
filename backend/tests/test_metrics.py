from __future__ import annotations

import pandas as pd

from app.pipeline import metrics


def _df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_summarize_computes_income_expense_net_and_top_category() -> None:
    df = _df(
        [
            {"Valor": -150.0, "Categorias": "Mercado"},
            {"Valor": 3000.0, "Categorias": "Receitas"},
            {"Valor": -89.9, "Categorias": "Moradia"},
            {"Valor": -70.1, "Categorias": "Moradia"},
        ]
    )

    summary = metrics.summarize(df)

    assert summary.income == 3000.0
    assert round(summary.expense, 2) == -310.0
    assert round(summary.net, 2) == 2690.0
    assert summary.transaction_count == 4
    assert summary.top_category == "Moradia"  # 89.9 + 70.1 = 160.0 > Mercado's 150.0
    assert round(summary.top_category_amount, 2) == 160.0


def test_summarize_on_empty_df_returns_zeroed_summary() -> None:
    summary = metrics.summarize(pd.DataFrame(columns=["Valor", "Categorias"]))
    assert summary == metrics.PeriodSummary(0.0, 0.0, 0.0, 0, None, 0.0)


def test_month_over_month_delta_computes_percentage_change() -> None:
    df = _df(
        [
            {"Mês": "2026-01", "Valor": 100.0, "Categorias": "Receitas"},
            {"Mês": "2026-02", "Valor": 150.0, "Categorias": "Receitas"},
        ]
    )

    delta = metrics.month_over_month_delta(df, "2026-02", "net")

    assert delta == 50.0  # (150-100)/100 * 100


def test_month_over_month_delta_none_when_no_previous_month() -> None:
    df = _df([{"Mês": "2026-01", "Valor": 100.0, "Categorias": "Receitas"}])
    assert metrics.month_over_month_delta(df, "2026-01", "net") is None


def test_month_over_month_delta_none_when_previous_value_is_zero() -> None:
    df = _df(
        [
            {"Mês": "2026-01", "Valor": 0.0, "Categorias": "Receitas"},
            {"Mês": "2026-02", "Valor": 100.0, "Categorias": "Receitas"},
        ]
    )
    assert metrics.month_over_month_delta(df, "2026-02", "net") is None


def test_month_over_month_delta_on_expense_returns_raw_negative_sum_delta() -> None:
    """Confirms the raw (unfavorability-uninverted) contract: an expense
    that got MORE negative (spent more) still yields a raw delta whose sign
    depends on the negative sums themselves -- inverting it for "spent more
    = unfavorable" display is a presentation-layer concern (Fase 4's KPI
    cards), not this function's job."""
    df = _df(
        [
            {"Mês": "2026-01", "Valor": -100.0, "Categorias": "Mercado"},
            {"Mês": "2026-02", "Valor": -200.0, "Categorias": "Mercado"},
        ]
    )
    delta = metrics.month_over_month_delta(df, "2026-02", "expense")
    # expense went from -100 to -200: (-200 - -100) / abs(-100) * 100 = -100.0
    assert delta == -100.0


def test_monthly_series_aggregates_income_expense_and_net_per_month() -> None:
    df = _df(
        [
            {"Mês": "2026-01", "Valor": 100.0},
            {"Mês": "2026-01", "Valor": -40.0},
            {"Mês": "2026-02", "Valor": -10.0},
        ]
    )

    series = metrics.monthly_series(df)

    row_jan = series[series["Mês"] == "2026-01"].iloc[0]
    assert row_jan["Receitas"] == 100.0
    assert row_jan["Despesas"] == -40.0
    assert row_jan["Saldo"] == 60.0


def test_category_breakdown_only_includes_expenses_by_default() -> None:
    df = _df(
        [
            {"Valor": -100.0, "Categorias": "Mercado"},
            {"Valor": 500.0, "Categorias": "Receitas"},
            {"Valor": -50.0, "Categorias": "Mercado"},
        ]
    )

    breakdown = metrics.category_breakdown(df)

    assert breakdown["Categorias"].tolist() == ["Mercado"]
    assert breakdown["Valor"].tolist() == [150.0]
