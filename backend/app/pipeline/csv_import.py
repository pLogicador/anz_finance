"""CSV import with preview + column mapping (Fase 7, PARTE 6.7) -- unlike
OFX (a fixed, known format), a user's own CSV export can name its columns
anything, so the flow is: upload once to preview headers/sample rows, let
the user map "which column is the date/value/description", then commit
with that mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import pandas as pd


class CsvImportError(ValueError):
    pass


@dataclass(frozen=True)
class CsvPreview:
    columns: list[str]
    sample_rows: list[dict]
    row_count: int


def _read_csv(raw: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(BytesIO(raw))
    except Exception as exc:  # noqa: BLE001 -- surfaced as a clear 400, not a 500
        raise CsvImportError(f"Não foi possível ler o arquivo CSV: {exc}") from exc
    if df.empty:
        raise CsvImportError("O arquivo CSV está vazio.")
    return df


def preview_csv(raw: bytes, *, sample_size: int = 5) -> CsvPreview:
    df = _read_csv(raw)
    sample = df.head(sample_size)
    sample = sample.astype(object).where(pd.notna(sample), None)
    return CsvPreview(columns=[str(c) for c in df.columns], sample_rows=sample.to_dict(orient="records"), row_count=int(len(df)))


def apply_column_mapping(raw: bytes, *, date_column: str, valor_column: str, description_column: str) -> pd.DataFrame:
    """Returns a df with exactly ``Data``/``Valor``/``Descrição`` (the same
    shape `app/pipeline/preprocess.py` expects from a freshly-parsed OFX
    file), so the rest of the pipeline (preprocess -> classify -> store) is
    identical regardless of where the row came from."""
    df = _read_csv(raw)

    for label, column in (("data", date_column), ("valor", valor_column), ("descrição", description_column)):
        if column not in df.columns:
            raise CsvImportError(f"Coluna de {label} ('{column}') não existe no arquivo.")

    result = pd.DataFrame(
        {
            # No `dayfirst=True` here -- a first draft used it unconditionally
            # and it silently corrupted unambiguous ISO dates ("2026-03-05"
            # parsed as May 3rd instead of March 5th, confirmed by hand: pandas
            # only respects `dayfirst` as a *tiebreaker* for genuinely
            # ambiguous D/M vs M/D numeric dates, but still applies it to
            # dates that were never ambiguous in the first place). Plain
            # `pd.to_datetime` correctly handles ISO (`YYYY-MM-DD`) and most
            # unambiguous formats; slash-separated dd/mm/yyyy vs mm/dd/yyyy
            # is inherently ambiguous without knowing the source locale and
            # is a known limitation here, not silently guessed at.
            "Data": pd.to_datetime(df[date_column], errors="coerce"),
            "Valor": pd.to_numeric(df[valor_column], errors="coerce"),
            "Descrição": df[description_column].astype(str),
        }
    )
    result = result.dropna(subset=["Data", "Valor"])
    if result.empty:
        raise CsvImportError("Nenhuma linha válida após aplicar o mapeamento -- confira o formato de data e valor no arquivo.")

    result["Data"] = result["Data"].dt.date
    return result.reset_index(drop=True)
