"""FastAPI dependencies for reading the current ANZ session.

Used by ``/auth/me`` here in Fase 1, and will be reused by every protected
route group added in later phases (upload, transactions, ai, export, ...) --
this is the one place "who is the current user, and is their ANZ session
still valid" gets decided.

Note what this does *not* do: it never re-contacts subscription_access_api.
Once a session JWT has been minted, checking it is purely local (decode +
expiry check) -- see ``app/access/security.py`` module docstring for why
that's the correct tradeoff given ANZ has no database to keep in sync.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.access.security import InvalidSessionToken, SessionClaims, decode_session_token
from app.access.states import AccessErrorCode
from app.core.config import Settings, get_settings

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> SessionClaims:
    """Resolve the caller's ANZ session from the ``Authorization: Bearer`` header.

    Missing header, malformed JWT, or an expired JWT all map to the same
    PARTE 5.6 state as "token ausente/inválido" (state 4) -- from ANZ's own
    perspective there is no login of its own to fall back to (guardrail #2:
    ANZ never grows an independent auth path), so an expired ANZ session
    sends the user back to the institutional block screen, not to a
    self-serve "renew" flow.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": AccessErrorCode.TOKEN_INVALID_OR_MISSING, "message": "Sessao ausente."},
        )
    try:
        return decode_session_token(credentials.credentials, settings)
    except InvalidSessionToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": AccessErrorCode.TOKEN_INVALID_OR_MISSING, "message": str(exc)},
        ) from exc
