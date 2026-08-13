"""DataFrame -> JSON-safe records. No pipeline module returns raw pandas
objects across an API boundary -- this is the one place that conversion
happens.
"""

from __future__ import annotations

import math

import pandas as pd


def df_to_records(df: pd.DataFrame) -> list[dict]:
    records = []
    for row in df.to_dict(orient="records"):
        record = dict(row)
        data_value = record.get("Data")
        if hasattr(data_value, "isoformat"):
            record["Data"] = data_value.isoformat()
        valor = record.get("Valor")
        if isinstance(valor, float) and math.isnan(valor):
            record["Valor"] = None
        records.append(record)
    return records
