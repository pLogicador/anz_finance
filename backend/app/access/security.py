"""ANZ's own session token.

Mirrors the pattern in AgenteOS (``agenteos/backend/app/core/security.py``):
a self-issued JWT, signed with a ``SECRET_KEY`` entirely independent from
subscription_access_api's own secret, returned to the frontend in the
response body (never a cookie), carrying only the minimal claims needed.

Deliberately simpler than AgenteOS's version: AgenteOS re-derives plan
state from its own DB-mirrored Subscription model on every request (it has
a database). ANZ has none -- guardrail #1 forbids introducing one -- so the
plan check happens exactly once, at bridge time, via
``subscription_access_api``'s response; a 200 there already proves the plan
was active *then*. Keeping ``access_token_expire_minutes`` short (default
30) is the only defense against that fact going stale, matching the
guardrail that this JWT must never outlive the trust placed in that one
validation call, and must never grow a renewal path that doesn't go back
through Syncron.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import Settings


class InvalidSessionToken(Exception):
    pass


class SessionClaims(BaseModel):
    sub: str  # Syncron user email -- identity reference only, never a second source of truth
    workspace_id: str  # correlates to app/workspace/store.py's PARTE-4 TTL entry
    iat: datetime
    exp: datetime


def create_session_token(*, subject_email: str, settings: Settings, workspace_id: str | None = None) -> tuple[str, SessionClaims]:
    now = datetime.now(UTC)
    claims = SessionClaims(
        sub=subject_email,
        workspace_id=workspace_id or str(uuid.uuid4()),
        iat=now,
        exp=now + timedelta(minutes=settings.access_token_expire_minutes),
    )
    token = jwt.encode(
        {
            "sub": claims.sub,
            "workspace_id": claims.workspace_id,
            "iat": int(claims.iat.timestamp()),
            "exp": int(claims.exp.timestamp()),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return token, claims


def decode_session_token(token: str, settings: Settings) -> SessionClaims:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise InvalidSessionToken(str(exc)) from exc

    sub = payload.get("sub")
    workspace_id = payload.get("workspace_id")
    if not sub or not workspace_id:
        raise InvalidSessionToken("Claims obrigatorias ausentes no token de sessao.")

    return SessionClaims(
        sub=sub,
        workspace_id=workspace_id,
        iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
        exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
    )
