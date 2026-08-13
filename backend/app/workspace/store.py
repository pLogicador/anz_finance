"""PARTE 4 workspace: in-memory, TTL-expiring session data. No persistence.

This is the shell only (Fase 1) -- ``payload`` stays ``None`` until Fase 3
wires in real uploaded/classified transaction data. What this phase proves
is the *expiry mechanism itself*: a workspace entry created now and queried
after its TTL has elapsed must raise ``WorkSessionExpired`` -- the concrete,
triggerable version of PARTE 5.6 state 5 ("sessão de trabalho expirada, mas
o token/plano Syncron continua válido").

Guardrail #1: this is a plain in-process dict, nothing is written to disk,
a database, or Redis. Entries vanish on process restart by design -- that's
the intended behavior for "no persistent database", not a gap to fix later.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable


class WorkSessionExpired(Exception):
    """The PARTE-4 workspace TTL elapsed. Auth (JWT) may still be valid."""


class WorkSessionNotFound(Exception):
    """No workspace was ever created for this id (e.g. server restarted)."""


@dataclass
class _Entry:
    created_at: float
    expires_at: float
    payload: Any = None


class WorkspaceStore:
    """Process-local TTL store. One instance is shared app-wide (see main.py)."""

    def __init__(self, *, ttl_minutes: int, clock: Callable[[], float] = time.monotonic) -> None:
        self._ttl_seconds = ttl_minutes * 60
        self._clock = clock
        self._entries: dict[str, _Entry] = {}
        self._lock = Lock()

    def create(self, workspace_id: str) -> None:
        now = self._clock()
        with self._lock:
            self._entries[workspace_id] = _Entry(created_at=now, expires_at=now + self._ttl_seconds)

    def touch(self, workspace_id: str) -> None:
        """Extend a workspace's TTL (e.g. on active use). Raises if already expired/missing."""
        entry = self._get_live_entry(workspace_id)
        now = self._clock()
        with self._lock:
            entry.expires_at = now + self._ttl_seconds

    def get_payload(self, workspace_id: str) -> Any:
        return self._get_live_entry(workspace_id).payload

    def set_payload(self, workspace_id: str, payload: Any) -> None:
        entry = self._get_live_entry(workspace_id)
        with self._lock:
            entry.payload = payload

    def _get_live_entry(self, workspace_id: str) -> _Entry:
        with self._lock:
            entry = self._entries.get(workspace_id)
            if entry is None:
                raise WorkSessionNotFound(workspace_id)
            if self._clock() >= entry.expires_at:
                del self._entries[workspace_id]
                raise WorkSessionExpired(workspace_id)
            return entry

    def sweep_expired(self) -> int:
        """Evict every expired entry. Returns how many were removed.

        Safe to call periodically (e.g. a background task) purely to bound
        memory -- correctness never depends on this running, since
        ``_get_live_entry`` already lazily expires on access.
        """
        now = self._clock()
        with self._lock:
            expired = [wid for wid, e in self._entries.items() if now >= e.expires_at]
            for wid in expired:
                del self._entries[wid]
        return len(expired)


_singleton: WorkspaceStore | None = None


def get_workspace_store() -> WorkspaceStore:
    """FastAPI dependency: one shared, process-local store for the app's lifetime.

    A single instance (not one per request) is the point -- workspace
    entries created by ``POST /auth/bridge`` must still be there when a
    later request reads them.
    """
    global _singleton
    if _singleton is None:
        # Local import to avoid a circular import (config -> ... -> store).
        from app.core.config import get_settings

        _singleton = WorkspaceStore(ttl_minutes=get_settings().workspace_ttl_minutes)
    return _singleton
