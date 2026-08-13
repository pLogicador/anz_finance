"""Ported from legacy_streamlit/modules/parsers/ofx_parser.py, verbatim on
the parsing semantics (multiple accounts per file flattened, multiple files
concatenated with no cross-file dedup, a malformed file is skipped without
aborting the batch).

The one real behavior change (authorized by the plan, Fase 3): the legacy
version only ``print()``-ed a parse failure server-side -- the caller had no
way to know which file failed short of reading server logs. Here,
``parse_uploaded_ofx_files`` returns a ``FileParseResult`` per file so the
frontend can show it.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import ofxparse
import pandas as pd
from fastapi import UploadFile

from app.pipeline.limits import MAX_UPLOAD_FILE_BYTES


@dataclass
class FileParseResult:
    filename: str
    status: str  # "ok" | "failed"
    rows_parsed: int
    error: str | None = None


def _extract_transactions(ofx) -> list[dict]:
    """Flatten every account/transaction in a parsed OFX object into row dicts."""
    rows = []
    for account in ofx.accounts:
        for transaction in account.statement.transactions:
            rows.append(
                {
                    "Data": transaction.date,
                    "Valor": float(transaction.amount),
                    "Descrição": transaction.memo,
                    "ID": transaction.id,
                }
            )
    return rows


def _finalize(df_temp: pd.DataFrame) -> pd.DataFrame:
    df_temp["Data"] = df_temp["Data"].apply(lambda x: x.date())
    return df_temp


async def parse_uploaded_ofx_files(files: list[UploadFile]) -> tuple[pd.DataFrame, list[FileParseResult]]:
    """Async counterpart of the legacy ``parse_ofx_files_from_upload`` --
    reads each ``UploadFile`` into memory (same as the legacy code parsing
    Streamlit's already-in-memory ``UploadedFile``), same concatenation and
    skip-on-error behavior, plus a per-file result.
    """
    df = pd.DataFrame()
    results: list[FileParseResult] = []

    for upload in files:
        raw = await upload.read()
        if len(raw) > MAX_UPLOAD_FILE_BYTES:
            # Same per-file failure contract as a parse error (see module
            # docstring) -- one oversized file must not abort the batch.
            results.append(
                FileParseResult(
                    filename=upload.filename or "arquivo.ofx",
                    status="failed",
                    rows_parsed=0,
                    error=f"Arquivo maior que o limite de {MAX_UPLOAD_FILE_BYTES // (1024 * 1024)}MB.",
                )
            )
            continue
        try:
            ofx = ofxparse.OfxParser.parse(BytesIO(raw))
            df_temp = pd.DataFrame(_extract_transactions(ofx))
            rows_parsed = len(df_temp)
            if not df_temp.empty:
                df = pd.concat([df, _finalize(df_temp)], ignore_index=True)
            results.append(FileParseResult(filename=upload.filename or "arquivo.ofx", status="ok", rows_parsed=rows_parsed))
        except Exception as exc:  # noqa: BLE001 -- a single bad file must not abort the batch
            results.append(
                FileParseResult(filename=upload.filename or "arquivo.ofx", status="failed", rows_parsed=0, error=str(exc))
            )

    return df, results
