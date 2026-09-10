"""Ported from legacy_streamlit/modules/parsers/ofx_parser.py, verbatim on
the parsing semantics (multiple accounts per file flattened, a malformed
file is skipped without aborting the batch).

Real behavior changes since the legacy port (both authorized by the plan):
Fase 3 added a ``FileParseResult`` per file (the legacy version only
``print()``-ed a parse failure server-side). This module (2026-09-02,
prompt-mestre "Maestro + ANZ Finance" §13/§17) adds FITID-based
deduplication -- the legacy/Fase-3 behavior was "no cross-file dedup",
confirmed as a real gap: uploading the same statement twice produced
fully duplicated transactions -- and extraction of the reported
LEDGERBAL/AVAILBAL per account, for balance validation
(``app.pipeline.balance``).
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


@dataclass
class AccountBalance:
    account: str
    reported_balance: float
    source_filename: str


def _extract_transactions(ofx) -> list[dict]:
    """Flatten every account/transaction in a parsed OFX object into row dicts.

    ``ID`` (FITID), ``Tipo`` (TRNTYPE) and ``Conta`` (ACCTID) are the 3
    extra fields the composite dedup key (§13) needs beyond
    date/amount/description -- confirmed present on ``ofxparse``'s
    ``Transaction``/``Account`` objects by reading the installed library's
    source directly, not assumed.

    ``Beneficiário`` (NAME/``transaction.payee``), ``NúmeroCheque``
    (CHECKNUM/``transaction.checknum``) and ``BancoID``
    (BANKID/``account.routing_number``) (2026-09-02, prompt-mestre §11)
    are captured the same way -- confirmed present on the installed
    library by reading ``ofxparse.py`` directly (``ofxparse.py:209-210``
    for ``routing_number``, ``:317-321`` for ``payee``/``checknum``).
    Additive columns only: nothing downstream (``metrics.py``/
    ``filters.py``/``csv_export.py``) breaks by a DataFrame gaining new
    columns it doesn't reference -- ``preprocess.py`` already selects an
    explicit whitelist (``EXPORT_COLUMNS``) before CSV export, so these
    don't leak there unless deliberately added.

    ``REFNUM`` (also listed in §11) is NOT captured: confirmed by reading
    the installed ``ofxparse`` source in full that it never parses that
    tag at all (no ``find('refnum')`` anywhere in the library, unlike
    ``checknum``/``bankid`` which it does parse) -- there's no attribute
    to read it from without forking the parsing library or bypassing it
    to re-walk the raw SGML/XML tree ourselves, which would be a much
    larger and riskier change for a field Brazilian bank OFX exports
    essentially never populate. Documented here per §20 ("se um teste não
    puder ser executado, informe por que e qual dependência falta").
    """
    rows = []
    for account in ofx.accounts:
        bank_id = getattr(account, "routing_number", "") or ""
        for transaction in account.statement.transactions:
            rows.append(
                {
                    "Data": transaction.date,
                    "Valor": float(transaction.amount),
                    "Descrição": transaction.memo,
                    "ID": transaction.id,
                    "Tipo": transaction.type,
                    "Conta": account.account_id,
                    "Beneficiário": getattr(transaction, "payee", "") or "",
                    "NúmeroCheque": getattr(transaction, "checknum", "") or "",
                    "BancoID": bank_id,
                }
            )
    return rows


def _extract_account_balances(ofx, filename: str) -> list[AccountBalance]:
    """Reported LEDGERBAL per account, when the OFX file includes it (not
    every file does -- ``ofxparse`` sets ``statement.balance`` dynamically
    only when a ``<LEDGERBAL>`` tag was present, confirmed by reading the
    library's ``parseBalance``). Used by ``app.pipeline.balance`` to check
    ``SUM(transactions)`` against what the bank itself reported, never to
    silently correct or hide a mismatch (§17)."""
    balances = []
    for account in ofx.accounts:
        reported = getattr(account.statement, "balance", None)
        if reported is not None:
            balances.append(AccountBalance(account=account.account_id, reported_balance=float(reported), source_filename=filename))
    return balances


def _finalize(df_temp: pd.DataFrame) -> pd.DataFrame:
    df_temp["Data"] = df_temp["Data"].apply(lambda x: x.date())
    return df_temp


def dedupe_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """De-duplicate by FITID when present and non-empty; otherwise a
    composite key of (date, amount, description, type, account) -- exactly
    the fallback the prompt-mestre §13 asks for. Applied wherever
    transactions from potentially-overlapping sources get concatenated:
    within a single multi-file OFX upload, and when CSV import appends
    onto an existing workspace (the two real duplication paths found
    during the audit -- OFX upload itself always *replaces* the workspace,
    so it can only self-duplicate within one batch).

    Keeps the FIRST occurrence of each key -- arbitrary but deterministic,
    and no OFX field distinguishes "this one is the real one" when two
    rows are genuinely identical.
    """
    if df.empty or "ID" not in df.columns:
        return df
    fitid = df["ID"].astype(str).str.strip()
    has_fitid = df["ID"].notna() & fitid.ne("")

    key = pd.Series(index=df.index, dtype=object)
    key[has_fitid] = "fitid:" + df.loc[has_fitid, "Conta"].astype(str) + ":" + fitid[has_fitid]

    composite_idx = ~has_fitid
    if composite_idx.any():
        key[composite_idx] = (
            "composite:"
            + df.loc[composite_idx, "Data"].astype(str)
            + ":"
            + df.loc[composite_idx, "Valor"].astype(str)
            + ":"
            + df.loc[composite_idx, "Descrição"].astype(str)
            + ":"
            + df.loc[composite_idx, "Tipo"].astype(str)
            + ":"
            + df.loc[composite_idx, "Conta"].astype(str)
        )

    return df.loc[~key.duplicated(keep="first")].reset_index(drop=True)


async def parse_uploaded_ofx_files(
    files: list[UploadFile],
) -> tuple[pd.DataFrame, list[FileParseResult], list[AccountBalance]]:
    """Async counterpart of the legacy ``parse_ofx_files_from_upload`` --
    reads each ``UploadFile`` into memory (same as the legacy code parsing
    Streamlit's already-in-memory ``UploadedFile``), same concatenation and
    skip-on-error behavior, plus a per-file result. The concatenated frame
    is deduplicated (see ``dedupe_transactions``) before being returned --
    a deliberate behavior change from the legacy/Fase-3 "no cross-file
    dedup" contract, not a silent regression (the test that used to assert
    the old behavior was updated to match, see test_ofx_parser.py).
    """
    df = pd.DataFrame()
    results: list[FileParseResult] = []
    balances: list[AccountBalance] = []

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
            balances.extend(_extract_account_balances(ofx, upload.filename or "arquivo.ofx"))
            results.append(FileParseResult(filename=upload.filename or "arquivo.ofx", status="ok", rows_parsed=rows_parsed))
        except Exception as exc:  # noqa: BLE001 -- a single bad file must not abort the batch
            results.append(
                FileParseResult(filename=upload.filename or "arquivo.ofx", status="failed", rows_parsed=0, error=str(exc))
            )

    df = dedupe_transactions(df)
    return df, results, balances
