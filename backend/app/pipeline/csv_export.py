"""CSV export (Fase 7) -- respects the caller's active filters, closing a
real gap the legacy Streamlit app had: its one export button always dumped
the entire unfiltered dataset regardless of what the user had filtered to
on screen.
"""

from __future__ import annotations

import pandas as pd

EXPORT_COLUMNS = ["Data", "Descrição", "Categorias", "Valor"]


def build_csv(df: pd.DataFrame) -> str:
    if df.empty:
        return pd.DataFrame(columns=EXPORT_COLUMNS).to_csv(index=False)
    return df[EXPORT_COLUMNS].to_csv(index=False)
