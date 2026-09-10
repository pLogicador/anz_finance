"""Ported from legacy_streamlit/modules/data/finance_data.py::preprocess_df.

One real behavior change (2026-09-02, prompt-mestre "Maestro + ANZ
Finance" §13): the legacy version dropped the ``ID`` (FITID) column
immediately -- it's kept now, since ``app.pipeline.ofx_parser.
dedupe_transactions`` needs it (and needs ``Tipo``/``Conta``, also new)
to de-duplicate transactions. ``csv_export.py`` already whitelists its
output columns (``EXPORT_COLUMNS``), so these extra columns don't leak
into user-facing exports.
"""

from __future__ import annotations

import pandas as pd


def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    df["Data"] = pd.to_datetime(df["Data"])
    df["Mês"] = df["Data"].dt.to_period("M").astype(str)
    df["Data"] = df["Data"].dt.date
    return df
