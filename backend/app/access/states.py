"""The PARTE 5.6 access states, expressed as exceptions + error codes.

Only the states a *backend* decision can produce live here:

- ``AUTHORIZED`` has no exception -- it's simply a successful response from
  the bridge endpoint (a minted session JWT).
- ``VALIDATING`` is a pure frontend transient state (request in flight) --
  nothing to represent backend-side.
- ``WORK_SESSION_EXPIRED`` (PARTE 4 workspace TTL, not the auth session)
  lives in ``app/workspace/store.py`` since it's about workspace data, not
  the Syncron token bridge.

The remaining three map 1:1 to a distinct HTTP status + machine-readable
``error_code`` the frontend switches on to choose which of the 6 screens to
render -- this is the fix for the legacy app's collapse of all three into
one generic "Sessão expirada" message (see
``legacy_streamlit/run_dashboard.py:75-82``).
"""

from enum import StrEnum


class AccessErrorCode(StrEnum):
    TOKEN_INVALID_OR_MISSING = "token_invalid_or_missing"
    PLAN_EXPIRED = "plan_expired"
    AUTH_SERVICE_UNAVAILABLE = "auth_service_unavailable"
    WORK_SESSION_EXPIRED = "work_session_expired"


class SyncronAccessError(Exception):
    """Base for every way the Syncron bridge can fail to authorize a user."""

    error_code: AccessErrorCode
    status_code: int

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SyncronTokenInvalid(SyncronAccessError):
    """No token, malformed token, or Syncron says it's unknown/expired."""

    error_code = AccessErrorCode.TOKEN_INVALID_OR_MISSING
    status_code = 401


class SyncronPlanExpired(SyncronAccessError):
    """Token is real, but the user's Syncron plan is expired/inactive."""

    error_code = AccessErrorCode.PLAN_EXPIRED
    status_code = 403


class SyncronServiceUnavailable(SyncronAccessError):
    """subscription_access_api timed out, errored, or is unreachable."""

    error_code = AccessErrorCode.AUTH_SERVICE_UNAVAILABLE
    status_code = 503
