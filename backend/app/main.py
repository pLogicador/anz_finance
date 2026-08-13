from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.access.routes import router as access_router
from app.core.config import get_settings
from app.routes.ai import router as ai_router
from app.routes.analysis import router as analysis_router
from app.routes.export import router as export_router
from app.routes.import_csv import router as import_csv_router
from app.routes.snapshots import router as snapshots_router
from app.routes.transactions import router as transactions_router
from app.routes.upload import router as upload_router

settings = get_settings()

app = FastAPI(title="ANZ Finance API", version="2.0.0-alpha")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,  # no cookies are ever used (see access/security.py) -- Bearer-header auth only
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def no_store_cache_control(request: Request, call_next):
    """Every response gets `Cache-Control: no-store`.

    Root-caused a real bug during Fase 4 testing: without this, a browser
    (not curl, not pytest's in-process TestClient -- both bypass the
    browser's HTTP cache entirely) applies its own heuristic caching to
    plain GET responses that carry no explicit cache directive. A GET to
    `/workspace/months` made once right after `/auth/bridge` (correctly
    returning `work_session_expired`, nothing uploaded yet) got silently
    replayed from the browser's cache for every *later* identical-URL GET
    -- even after a real upload had succeeded and the server had fresh
    data to return -- because the response never told the browser not to
    keep it. Confirmed by reproducing with plain `fetch()` calls (no
    frontend/React code involved) and observing the exact same stale
    response, then confirming `fetch(..., { cache: "no-store" })` fixed it
    client-side -- fixing it here, server-side, means no individual call
    site ever has to remember to opt out of caching for this class of bug.
    Every response in this API is dynamic/session-scoped; none of it
    should ever be cached by a browser or intermediary.
    """
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Fase 9 security pass: baseline defensive headers on every response.

    This is a pure JSON/file-download API with no server-rendered HTML and
    no cookies (Bearer-header auth only, see access/security.py) -- there
    is no first-party page here for clickjacking/MIME-sniffing to exploit
    directly, but these headers cost nothing and remove any doubt for a
    browser that ever renders a response from this origin (e.g. a
    downloaded PDF/CSV opened via a data URL, or a future regression that
    accidentally serves HTML).
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


app.include_router(access_router)
app.include_router(upload_router)
app.include_router(transactions_router)
app.include_router(ai_router)
app.include_router(analysis_router)
app.include_router(snapshots_router)
app.include_router(export_router)
app.include_router(import_csv_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
