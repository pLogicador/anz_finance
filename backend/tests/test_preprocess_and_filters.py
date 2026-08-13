from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from app.pipeline.filters import apply_type_filter, filter_transactions, filter_transactions_for_trend
from app.pipeline.preprocess import preprocess_df


def _raw_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Data": dt.datetime(2026, 1, 5), "Valor": -150.0, "Descrição": "Mercado", "ID": "1"},
            {"Data": dt.datetime(2026, 1, 10), "Valor": 3000.0, "Descrição": "Salário", "ID": "2"},
            {"Data": dt.datetime(2026, 2, 12), "Valor": -89.9, "Descrição": "Luz", "ID": "3"},
        ]
    )


def test_preprocess_drops_id_and_derives_month() -> None:
    df = preprocess_df(_raw_df())

    assert "ID" not in df.columns
    assert df["Mês"].tolist() == ["2026-01", "2026-01", "2026-02"]
    assert all(isinstance(d, dt.date) and not isinstance(d, dt.datetime) for d in df["Data"])


def test_preprocess_is_a_noop_on_id_when_already_absent() -> None:
    df = _raw_df().drop(columns=["ID"])
    result = preprocess_df(df)
    assert "ID" not in result.columns


def _classified_df() -> pd.DataFrame:
    df = preprocess_df(_raw_df())
    df["Categorias"] = ["Mercado", "Receitas", "Moradia"]
    return df


def test_filter_transactions_applies_month_and_category() -> None:
    df = _classified_df()

    result = filter_transactions(df, "2026-01", ["Mercado"])

    assert result["Descrição"].tolist() == ["Mercado"]


def test_filter_transactions_empty_categories_means_no_category_filter() -> None:
    """The core semantic: an empty (or falsy) categories list means "all categories", not "none"."""
    df = _classified_df()

    result = filter_transactions(df, "2026-01", [])

    assert sorted(result["Descrição"].tolist()) == ["Mercado", "Salário"]


def test_filter_transactions_none_categories_also_means_no_filter() -> None:
    df = _classified_df()
    result = filter_transactions(df, "2026-01", None)
    assert len(result) == 2


def test_filter_transactions_always_applies_the_month_filter() -> None:
    df = _classified_df()
    result = filter_transactions(df, "2026-02", None)
    assert result["Descrição"].tolist() == ["Luz"]


def test_filter_transactions_for_trend_ignores_month_entirely() -> None:
    """The distinct trend variant: category-only, full history -- this is
    what powers trend/heatmap charts, which must not be scoped to one month."""
    df = _classified_df()

    result = filter_transactions_for_trend(df, ["Mercado"])

    assert result["Descrição"].tolist() == ["Mercado"]  # spans both months, only 1 row matches the category though


def test_filter_transactions_for_trend_empty_categories_returns_full_history() -> None:
    df = _classified_df()
    result = filter_transactions_for_trend(df, [])
    assert len(result) == 3  # all 3 rows, both months


@pytest.mark.parametrize(
    ("selected_type", "expected_descriptions"),
    [
        ("Receitas", ["Salário"]),
        ("Despesas", ["Mercado", "Luz"]),
        ("Todas", ["Mercado", "Salário", "Luz"]),
    ],
)
def test_apply_type_filter(selected_type: str, expected_descriptions: list[str]) -> None:
    df = _classified_df()
    result = apply_type_filter(df, selected_type)
    assert result["Descrição"].tolist() == expected_descriptions
