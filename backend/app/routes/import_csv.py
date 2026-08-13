"""POST /workspace/import/csv/preview + /commit (Fase 7).

Unlike `/workspace/upload` (OFX, always REPLACES the session's data -- it's
"here are my bank statements", a complete data-loading action), CSV import
always APPENDS to whatever's already in the workspace (creating a fresh
workspace if there's nothing yet) -- it's framed as *supplementing* existing
data (e.g. adding a second bank/account's export), not replacing it.
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.access.deps import get_current_session
from app.access.security import SessionClaims
from app.core.config import Settings, get_settings
from app.pipeline.categorizer.registry import DEFAULT_PROVIDER, UnknownProvider, build_provider, resolve_api_key
from app.pipeline.categorizer.service import classify_transactions
from app.pipeline.csv_import import CsvImportError, apply_column_mapping, preview_csv
from app.pipeline.limits import MAX_UPLOAD_FILE_BYTES
from app.pipeline.ofx_parser import FileParseResult
from app.pipeline.preprocess import preprocess_df
from app.workspace.models import WorkspacePayload
from app.workspace.store import WorkSessionExpired, WorkSessionNotFound, WorkspaceStore, get_workspace_store

router = APIRouter(prefix="/workspace/import/csv", tags=["workspace"])


def _reject_if_too_large(raw: bytes) -> None:
    if len(raw) > MAX_UPLOAD_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail={"message": f"Arquivo maior que o limite de {MAX_UPLOAD_FILE_BYTES // (1024 * 1024)}MB."},
        )


@router.post("/preview")
async def preview(file: UploadFile = File(...), _: SessionClaims = Depends(get_current_session)) -> dict:
    raw = await file.read()
    _reject_if_too_large(raw)
    try:
        result = preview_csv(raw)
    except CsvImportError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    return {"columns": result.columns, "sample_rows": result.sample_rows, "row_count": result.row_count}


@router.post("/commit")
async def commit(
    file: UploadFile = File(...),
    date_column: str = Form(...),
    valor_column: str = Form(...),
    description_column: str = Form(...),
    provider_id: str = Form(default=DEFAULT_PROVIDER, alias="provider"),
    model: str | None = Form(default=None),
    api_key: str | None = Form(default=None),
    session: SessionClaims = Depends(get_current_session),
    settings: Settings = Depends(get_settings),
    store: WorkspaceStore = Depends(get_workspace_store),
) -> dict:
    raw = await file.read()
    _reject_if_too_large(raw)
    try:
        new_df = apply_column_mapping(raw, date_column=date_column, valor_column=valor_column, description_column=description_column)
    except CsvImportError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    new_df = preprocess_df(new_df)

    try:
        # Soft resolution, same reasoning as routes/upload.py: an
        # unconfigured key must degrade to "Erro na classificação" per row,
        # not block the import outright.
        resolved_key = resolve_api_key(provider_id, settings, api_key)
        provider = build_provider(provider_id, model, resolved_key)
    except UnknownProvider as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    new_df["Categorias"] = await classify_transactions(provider, list(new_df["Descrição"].values))

    try:
        existing_payload = store.get_payload(session.workspace_id)
    except (WorkSessionExpired, WorkSessionNotFound):
        existing_payload = None

    base_df = existing_payload.df if existing_payload is not None else pd.DataFrame()
    file_results = list(existing_payload.file_results) if existing_payload is not None else []
    file_results.append(FileParseResult(filename=file.filename or "import.csv", status="ok", rows_parsed=int(len(new_df))))
    carried_over_snapshots = existing_payload.snapshots if existing_payload is not None else []

    combined_df = pd.concat([base_df, new_df], ignore_index=True) if not base_df.empty else new_df

    try:
        store.touch(session.workspace_id)
    except (WorkSessionExpired, WorkSessionNotFound):
        store.create(session.workspace_id)
    store.set_payload(session.workspace_id, WorkspacePayload(df=combined_df, file_results=file_results, snapshots=carried_over_snapshots))

    months = sorted(combined_df["Mês"].unique().tolist(), reverse=True) if not combined_df.empty else []
    return {"total_transactions": int(len(combined_df)), "imported_rows": int(len(new_df)), "months": months}
