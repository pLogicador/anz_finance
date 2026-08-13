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

    Fase 13 revision: "never uploaded anything" and "uploaded, but the TTL
    lapsed" used to collapse into the same PARTE 5.6 state 5 response --
    that made sense before the frontend had anything else to offer a
    dataless session, but once a real first-run experience (a welcome
    screen with an "explore with example data" option) existed, a brand
    new user always seeing a "sua sessão de trabalho expirou" message
    (false -- nothing had expired, they'd simply never uploaded yet) was
    actively hiding that experience behind a misleading error state. The
    two cases are structurally distinguishable already: the workspace
    entry itself is missing/past its TTL (``WorkSessionExpired``/
    ``WorkSessionNotFound``, thrown by the store) vs. the entry exists and
    is live but its ``payload`` was never set (a brand-new entry from
    ``POST /auth/bridge``, see ``app/access/routes.py``). The auth session
    (JWT) may still be perfectly valid in either case -- that's the whole
    point of this being a distinct state from token-invalid/plan-expired.
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
            status_code=404,
            detail={"error_code": AccessErrorCode.NO_DATA_YET, "message": "Nenhum extrato enviado nesta sessão ainda."},
        )
    return payload
