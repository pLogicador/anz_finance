"""POST /workspace/upload -- parse, preprocess, classify, store.

Requires an authenticated ANZ session (PARTE 5's job is already done by the
time this runs). This is also where PARTE 5.6 state 5 gets a real trigger:
if the caller's workspace TTL entry lapsed since their session started,
uploading again simply re-creates it -- the auth session (JWT) is what's
actually gated by Syncron; the workspace TTL is just "uploaded data doesn't
live forever", not a security boundary (guardrail #2).

Fase 5: ``provider``/``model``/``api_key`` are optional multipart form
fields alongside the files -- ``api_key``, when present, is the user's own
key (PARTE 6.2). It is used only to build a provider instance for this one
request and is never logged, never stored on ``WorkspacePayload`` or the
workspace TTL store, and never echoed back in the response (guardrail #1:
no persistence of user-supplied secrets, session-only means "this request
only", not even "this session").
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.access.deps import get_current_session
from app.access.security import SessionClaims
from app.core.config import Settings, get_settings
from app.pipeline.categorizer.registry import DEFAULT_PROVIDER, UnknownProvider, build_provider, resolve_api_key
from app.pipeline.categorizer.service import classify_transactions
from app.pipeline.ofx_parser import FileParseResult, parse_uploaded_ofx_files
from app.pipeline.preprocess import preprocess_df
from app.workspace.models import WorkspacePayload
from app.workspace.store import WorkSessionExpired, WorkSessionNotFound, WorkspaceStore, get_workspace_store

router = APIRouter(prefix="/workspace", tags=["workspace"])


class UploadResponse:
    def __init__(self, files: list[FileParseResult], total_transactions: int, months: list[str]) -> None:
        self.files = files
        self.total_transactions = total_transactions
        self.months = months

    def model_dump(self) -> dict:
        return {
            "files": [{"filename": f.filename, "status": f.status, "rows_parsed": f.rows_parsed, "error": f.error} for f in self.files],
            "total_transactions": self.total_transactions,
            "months": self.months,
        }


@router.post("/upload")
async def upload_statements(
    files: list[UploadFile] = File(...),
    provider_id: str = Form(default=DEFAULT_PROVIDER, alias="provider"),
    model: str | None = Form(default=None),
    api_key: str | None = Form(default=None),
    session: SessionClaims = Depends(get_current_session),
    settings: Settings = Depends(get_settings),
    store: WorkspaceStore = Depends(get_workspace_store),
) -> dict:
    df, file_results = await parse_uploaded_ofx_files(files)

    months: list[str] = []
    if not df.empty:
        df = preprocess_df(df)
        try:
            # Soft resolution on purpose -- see registry.resolve_api_key's
            # docstring: an unconfigured key must not block the whole
            # upload, only degrade each transaction to "Erro na
            # classificação" (Fase 4's validated graceful-degradation
            # behavior).
            resolved_key = resolve_api_key(provider_id, settings, api_key)
            provider = build_provider(provider_id, model, resolved_key)
        except UnknownProvider as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        df["Categorias"] = await classify_transactions(provider, list(df["Descrição"].values))
        months = sorted(df["Mês"].unique().tolist(), reverse=True)

    try:
        existing_payload = store.get_payload(session.workspace_id)
    except (WorkSessionExpired, WorkSessionNotFound):
        existing_payload = None
    # "Novo envio" replaces the transaction data, but a user's saved
    # snapshots (Fase 6, filter-combination bookmarks) are a separate
    # concern -- they shouldn't silently vanish just because the underlying
    # data got refreshed.
    carried_over_snapshots = existing_payload.snapshots if existing_payload is not None else []

    try:
        store.touch(session.workspace_id)
    except (WorkSessionExpired, WorkSessionNotFound):
        store.create(session.workspace_id)

    store.set_payload(session.workspace_id, WorkspacePayload(df=df, file_results=file_results, snapshots=carried_over_snapshots))

    return UploadResponse(files=file_results, total_transactions=int(len(df)), months=months).model_dump()
