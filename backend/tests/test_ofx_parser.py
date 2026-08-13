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

    df, results = await parse_uploaded_ofx_files([upload])

    assert len(results) == 1
    assert results[0].status == "ok"
    assert results[0].rows_parsed == 3
    assert len(df) == 3
    assert set(df.columns) == {"Data", "Valor", "Descrição", "ID"}
    assert df["Valor"].tolist() == [-150.00, 3000.00, -89.90]


@pytest.mark.asyncio
async def test_malformed_file_is_skipped_but_reported() -> None:
    upload = _upload_file(FIXTURES / "malformed_statement.ofx")

    df, results = await parse_uploaded_ofx_files([upload])

    assert df.empty
    assert len(results) == 1
    assert results[0].status == "failed"
    assert results[0].error  # some parser error message, don't assert exact text
    assert results[0].rows_parsed == 0


@pytest.mark.asyncio
async def test_one_malformed_file_does_not_abort_the_rest_of_the_batch() -> None:
    """Multiple files: valid + malformed + valid again -- both valid ones
    must still be parsed and concatenated, matching the legacy app's
    per-file try/except (legacy_streamlit/modules/parsers/ofx_parser.py)."""
    uploads = [
        _upload_file(FIXTURES / "valid_statement.ofx"),
        _upload_file(FIXTURES / "malformed_statement.ofx"),
        _upload_file(FIXTURES / "valid_statement.ofx"),
    ]

    df, results = await parse_uploaded_ofx_files(uploads)

    assert len(results) == 3
    assert [r.status for r in results] == ["ok", "failed", "ok"]
    assert len(df) == 6  # 3 + 3 from the two valid files, no cross-file dedup
