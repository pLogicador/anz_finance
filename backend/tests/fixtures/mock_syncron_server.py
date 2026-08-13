"""Standalone local-dev stand-in for subscription_access_api.

Not part of the production backend and never imported by ``app/*`` -- this
exists purely so a developer can iterate on the frontend/backend locally
without a real/staging subscription_access_api instance running (see the
plan's "Dev local" section). Point ``SYNCRON_API_BASE`` at this server's URL.

Run:
    cd backend
    uvicorn tests.fixtures.mock_syncron_server:app --port 9100 --reload

Behavior is controlled by the token value sent to ``/validate-agendador-token``:
    token starting with "valid"         -> 200 (authorized)
    token starting with "expired-plan"  -> 403 (PARTE 5.3 plan-expired case)
    token == "down"                     -> 500 (simulates service failure)
    anything else (including empty)     -> 401 (invalid/unknown token)
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="mock subscription_access_api (dev only)")


@app.post("/validate-agendador-token")
async def validate_agendador_token(request: Request) -> JSONResponse:
    body = await request.json()
    token = str(body.get("token", ""))

    if token == "down":
        return JSONResponse(status_code=500, content={"detail": "internal error"})
    if token.startswith("expired-plan"):
        return JSONResponse(status_code=403, content={"detail": "Plano expirado"})
    if token.startswith("valid"):
        return JSONResponse(
            status_code=200,
            content={"ok": True, "user": {"id": 1, "email": "dev@example.com"}, "expires_at": 9999999999},
        )
    return JSONResponse(status_code=401, content={"detail": "Token invalido ou expirado"})
