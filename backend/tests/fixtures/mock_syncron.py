"""respx helpers that stand in for subscription_access_api's
``POST /validate-agendador-token`` in tests.

These mock the real contract confirmed by reading
``subscription_access_api/app.py:795-824`` directly (read-only, that repo is
never modified):
- 200 + ``{"ok": true, "user": {"id", "email"}, "expires_at": ...}`` on a
  valid token with an active plan.
- 403 + ``{"detail": "Plano expirado"}`` on a valid-but-expired-plan token.
- 401 + ``{"detail": "Token invalido ou expirado"}`` on an unknown/expired
  token.

Only used by tests -- never imported by ``app/*``.
"""

from __future__ import annotations

import respx
from httpx import Response

from tests.conftest import SYNCRON_API_BASE

VALIDATE_URL = f"{SYNCRON_API_BASE}/validate-agendador-token"


def mock_valid(router: respx.MockRouter, *, email: str = "usuario@example.com", user_id: int = 1) -> None:
    router.post(VALIDATE_URL).mock(
        return_value=Response(200, json={"ok": True, "user": {"id": user_id, "email": email}, "expires_at": 9999999999})
    )


def mock_plan_expired(router: respx.MockRouter) -> None:
    router.post(VALIDATE_URL).mock(return_value=Response(403, json={"detail": "Plano expirado"}))


def mock_token_invalid(router: respx.MockRouter) -> None:
    router.post(VALIDATE_URL).mock(return_value=Response(401, json={"detail": "Token invalido ou expirado"}))


def mock_service_down(router: respx.MockRouter) -> None:
    router.post(VALIDATE_URL).mock(return_value=Response(500, json={"detail": "internal error"}))


def mock_timeout(router: respx.MockRouter) -> None:
    import httpx

    router.post(VALIDATE_URL).mock(side_effect=httpx.TimeoutException("timed out"))
