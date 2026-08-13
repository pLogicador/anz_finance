from __future__ import annotations

from fastapi import Depends, HTTPException

from app.access.deps import get_current_session
from app.access.security import SessionClaims
from app.access.states import AccessErrorCode
from app.workspace.models import WorkspacePayload
from app.workspace.store import WorkSessionExpired, WorkSessionNotFound, WorkspaceStore, get_workspace_store


def get_workspace_payload(
    session: SessionClaims = Depends(get_current_session),
    store: WorkspaceStore = Depends(get_workspace_store),
) -> WorkspacePayload:
    """Resolves the current session's uploaded/classified data.

    Both "never uploaded anything" and "uploaded, but the TTL lapsed" map
    to the same PARTE 5.6 state 5 response -- from the frontend's
    perspective, both mean "prompt the user to (re-)upload", not two
    different screens. The auth session (JWT) may still be perfectly
    valid here -- that's the whole point of this being a distinct state
    from token-invalid/plan-expired.
    """
    try:
        payload = store.get_payload(session.workspace_id)
    except (WorkSessionExpired, WorkSessionNotFound) as exc:
        raise HTTPException(
            status_code=410,
            detail={"error_code": AccessErrorCode.WORK_SESSION_EXPIRED, "message": "Sessão de trabalho expirada. Envie os extratos novamente."},
        ) from exc

    if payload is None:
        raise HTTPException(
            status_code=410,
            detail={"error_code": AccessErrorCode.WORK_SESSION_EXPIRED, "message": "Nenhum extrato enviado nesta sessão ainda."},
        )
    return payload
