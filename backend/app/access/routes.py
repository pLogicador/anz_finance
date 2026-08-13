"""PARTE 5 — the token bridge and session-check endpoints.

``POST /auth/bridge`` is the only door in: the frontend sends the raw
``?token=`` value here, once, as a JSON body (never left in a URL the
backend logs, never sent as a header that ends up in access logs the same
way a query string would). See ``app/access/syncron_client.py`` for what
happens to it, and ``states.py`` for how failures map to the PARTE 5.6
states.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.access.deps import get_current_session
from app.access.schemas import BridgeRequest, BridgeResponse, BridgeUser, MeResponse
from app.access.security import SessionClaims, create_session_token
from app.access.states import SyncronAccessError
from app.access.syncron_client import validate_agendador_token
from app.core.config import Settings, get_settings
from app.workspace.store import WorkspaceStore, get_workspace_store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/bridge", response_model=BridgeResponse)
async def bridge_from_syncron_token(
    payload: BridgeRequest,
    settings: Settings = Depends(get_settings),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
) -> BridgeResponse:
    try:
        validated_user = await validate_agendador_token(payload.token, settings)
    except SyncronAccessError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error_code": exc.error_code, "message": exc.message},
        ) from exc

    access_token, claims = create_session_token(subject_email=validated_user.email, settings=settings)
    workspace_store.create(claims.workspace_id)

    return BridgeResponse(
        access_token=access_token,
        expires_at=claims.exp,
        workspace_id=claims.workspace_id,
        user=BridgeUser(email=validated_user.email),
    )


@router.get("/me", response_model=MeResponse)
def read_current_session(session: SessionClaims = Depends(get_current_session)) -> MeResponse:
    """Cheap, local check the frontend uses on load/reload -- never re-hits Syncron.

    This is what closes the gap the legacy app had (see
    ``legacy_streamlit/run_dashboard.py``): that app re-validated against
    subscription_access_api on *every* Streamlit rerun. Here, validation
    happens exactly once (at ``/auth/bridge``); everything after that just
    checks the locally-issued JWT.
    """
    return MeResponse(email=session.sub, workspace_id=session.workspace_id, expires_at=session.exp)
