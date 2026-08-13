"""Thin client for subscription_access_api's token-bridge endpoint.

Calls ``POST {SYNCRON_API_BASE}/validate-agendador-token`` -- the exact same
endpoint the legacy app already called
(``legacy_streamlit/run_dashboard.py:15-33``) and the same one AgenteOS's
``SyncronIdentityClient.validate_agendador_token`` calls
(``agenteos/backend/app/integrations/syncron_client.py:137-153``).

subscription_access_api itself already enforces the PARTE 5.3 plan rule
(``plan_end < now`` -> 403, regardless of free/paid -- see
``subscription_access_api/app.py:795-824``): a 200 response from this call
*is* proof the plan is active. This client's only job is to call it once,
never log the raw token, and translate its three real outcomes (valid /
token invalid / plan expired) plus network failure into the exceptions in
``states.py``.
"""

from __future__ import annotations

import logging

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.access.states import SyncronPlanExpired, SyncronServiceUnavailable, SyncronTokenInvalid
from app.core.config import Settings

logger = logging.getLogger("anz.access.syncron_client")


class SyncronValidatedUser:
    __slots__ = ("id", "email")

    def __init__(self, id_: str | int | None, email: str) -> None:
        self.id = id_
        self.email = email


class _TransientSyncronError(Exception):
    """Internal-only: network/timeout/5xx, worth a couple of retries."""


def _token_fingerprint(token: str) -> str:
    """A short, non-reversible-enough reference for log correlation.

    Never logs the raw token (PARTE 5.5 forbids it -- the legacy app broke
    this rule at ``legacy_streamlit/run_dashboard.py:65``,
    ``logger.info("Token recebido (raw): %s", token)``). Only length +
    first/last char are exposed, purely to correlate log lines for the same
    request without reconstructing the token.
    """
    if len(token) <= 4:
        return "***"
    return f"{token[0]}***{token[-1]}(len={len(token)})"


@retry(
    retry=retry_if_exception_type(_TransientSyncronError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.5),
    reraise=True,
)
async def _post_validate(client: httpx.AsyncClient, url: str, token: str, timeout: float) -> httpx.Response:
    try:
        return await client.post(url, json={"token": token}, timeout=timeout)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
        raise _TransientSyncronError(str(exc)) from exc


async def validate_agendador_token(token: str, settings: Settings) -> SyncronValidatedUser:
    """Validate a Syncron Hub token. Raises a ``SyncronAccessError`` subclass on any failure.

    Never returns a "valid" result without an actual successful call to
    subscription_access_api -- there is no code path here that authorizes
    without hitting the network.
    """
    if not token or not token.strip():
        raise SyncronTokenInvalid("Token ausente.")

    clean_token = token.strip()
    if clean_token.lower().startswith("bearer "):
        clean_token = clean_token.split(" ", 1)[1].strip()
    if not clean_token:
        raise SyncronTokenInvalid("Token ausente.")

    url = f"{settings.syncron_api_base.rstrip('/')}/validate-agendador-token"

    try:
        async with httpx.AsyncClient() as client:
            response = await _post_validate(client, url, clean_token, settings.syncron_validate_timeout_seconds)
    except _TransientSyncronError as exc:
        logger.warning(
            "subscription_access_api indisponivel (token=%s): %s",
            _token_fingerprint(clean_token),
            exc,
        )
        raise SyncronServiceUnavailable("Servico de autenticacao Syncron indisponivel.") from exc

    if response.status_code == 200:
        body = response.json()
        user = body.get("user") or {}
        email = user.get("email")
        if not email:
            # Successful-looking response with no usable identity -- treat
            # as a service contract failure, not a silent "authorized".
            logger.error("Resposta 200 de /validate-agendador-token sem 'user.email': %s", body)
            raise SyncronServiceUnavailable("Resposta invalida do servico de autenticacao Syncron.")
        return SyncronValidatedUser(id_=user.get("id"), email=email)

    if response.status_code == 403:
        raise SyncronPlanExpired("Plano expirado ou inativo.")

    if response.status_code in (401, 404):
        raise SyncronTokenInvalid("Token invalido ou expirado.")

    logger.warning(
        "subscription_access_api retornou status inesperado %s (token=%s)",
        response.status_code,
        _token_fingerprint(clean_token),
    )
    raise SyncronServiceUnavailable(f"Servico de autenticacao Syncron retornou status inesperado ({response.status_code}).")
