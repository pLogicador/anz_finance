"""Ported verbatim from legacy_streamlit/modules/data/finance_data.py::preprocess_df."""

from __future__ import annotations

import pandas as pd


def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    if "ID" in df.columns:
        df = df.drop(columns=["ID"])
    df["Data"] = pd.to_datetime(df["Data"])
    df["Mês"] = df["Data"].dt.to_period("M").astype(str)
    df["Data"] = df["Data"].dt.date
    return df
