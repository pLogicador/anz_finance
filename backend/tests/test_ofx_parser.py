from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.pipeline.ofx_parser import parse_uploaded_ofx_files

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"


def _upload_file(path: Path) -> UploadFile:
    return UploadFile(filename=path.name, file=open(path, "rb"), headers=Headers({"content-type": "application/octet-stream"}))


@pytest.mark.asyncio
async def test_valid_file_is_parsed_with_all_transactions_flattened() -> None:
    upload = _upload_file(FIXTURES / "valid_statement.ofx")

    df, results, balances = await parse_uploaded_ofx_files([upload])

    assert len(results) == 1
    assert results[0].status == "ok"
    assert results[0].rows_parsed == 3
    assert len(df) == 3
    # 2026-09-02: 3 novas colunas aditivas (§11) -- Beneficiário/NúmeroCheque
    # ficam vazias aqui (fixture não tem <NAME>/<CHECKNUM> em nenhuma
    # transação, só <MEMO>); BancoID vem de <BANKID>0001 no cabeçalho da conta.
    assert set(df.columns) == {
        "Data", "Valor", "Descrição", "ID", "Tipo", "Conta", "Beneficiário", "NúmeroCheque", "BancoID",
    }
    assert df["Valor"].tolist() == [-150.00, 3000.00, -89.90]
    assert df["ID"].tolist() == ["TX001", "TX002", "TX003"]
    assert df["Conta"].tolist() == ["123456", "123456", "123456"]
    assert df["BancoID"].tolist() == ["0001", "0001", "0001"]
    assert df["Beneficiário"].tolist() == ["", "", ""]
    assert df["NúmeroCheque"].tolist() == ["", "", ""]
    # This fixture's <LEDGERBAL> (2760.10) exactly equals SUM(transactions)
    # -- see test_balance.py for the dedicated validate_balance() coverage.
    assert len(balances) == 1
    assert balances[0].account == "123456"
    assert balances[0].reported_balance == 2760.10


@pytest.mark.asyncio
async def test_malformed_file_is_skipped_but_reported() -> None:
    upload = _upload_file(FIXTURES / "malformed_statement.ofx")

    df, results, balances = await parse_uploaded_ofx_files([upload])

    assert df.empty
    assert len(results) == 1
    assert results[0].status == "failed"
    assert results[0].error  # some parser error message, don't assert exact text
    assert results[0].rows_parsed == 0
    assert balances == []


@pytest.mark.asyncio
async def test_one_malformed_file_does_not_abort_the_rest_of_the_batch() -> None:
    """Multiple files: valid + malformed + valid again -- both valid ones
    must still be parsed. The two valid uploads are the SAME fixture (same
    FITIDs/account), so they're expected to dedupe down to 3 rows, not 6
    -- see test_duplicate_import_is_deduplicated_by_fitid below for the
    dedicated test of this behavior (prompt-mestre §13, item #13/20).
    Deliberate behavior change from the original port: the legacy/Fase-3
    contract was "no cross-file dedup" (this assertion used to read
    `len(df) == 6`), confirmed as a real gap during the 2026-09-02 audit,
    not a silent regression."""
    uploads = [
        _upload_file(FIXTURES / "valid_statement.ofx"),
        _upload_file(FIXTURES / "malformed_statement.ofx"),
        _upload_file(FIXTURES / "valid_statement.ofx"),
    ]

    df, results, balances = await parse_uploaded_ofx_files(uploads)

    assert len(results) == 3
    assert [r.status for r in results] == ["ok", "failed", "ok"]
    assert len(df) == 3  # 3 unique transactions, the 2nd valid file's rows are all duplicates of the 1st's
    assert sorted(df["ID"].tolist()) == ["TX001", "TX002", "TX003"]


@pytest.mark.asyncio
async def test_name_checknum_and_bankid_are_captured_when_present() -> None:
    """Prompt-mestre §11: NAME/CHECKNUM/BANKID são campos reais que
    `ofxparse` expõe (confirmado lendo o código-fonte da lib instalada,
    ver ofx_parser.py) mas que nunca eram capturados antes desta rodada."""
    upload = _upload_file(FIXTURES / "statement_with_name_checknum.ofx")

    df, results, _balances = await parse_uploaded_ofx_files([upload])

    assert results[0].status == "ok"
    assert len(df) == 1
    row = df.iloc[0]
    assert row["Beneficiário"] == "PAGAMENTO ALUGUEL"
    assert row["NúmeroCheque"] == "000123"
    assert row["BancoID"] == "9999"
    assert row["Descrição"] == "REF FEVEREIRO"  # MEMO continua vindo separado de NAME


@pytest.mark.asyncio
async def test_duplicate_import_is_deduplicated_by_fitid() -> None:
    """Prompt-mestre "Maestro + ANZ Finance" §13, test item #13/20: uploading
    the same statement twice must not duplicate transactions."""
    uploads = [_upload_file(FIXTURES / "valid_statement.ofx"), _upload_file(FIXTURES / "valid_statement.ofx")]

    df, _results, _balances = await parse_uploaded_ofx_files(uploads)

    assert len(df) == 3
    assert sorted(df["ID"].tolist()) == ["TX001", "TX002", "TX003"]
