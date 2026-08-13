"""PARTE 4 workspace TTL mechanism -- proves state 5 ("sessão de trabalho
expirada") is real and triggerable, independent of the auth JWT's own
expiry (which is tested separately in test_no_bypass.py).
"""

from __future__ import annotations

import pytest

from app.workspace.store import WorkSessionExpired, WorkSessionNotFound, WorkspaceStore


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_freshly_created_workspace_is_readable() -> None:
    clock = FakeClock()
    store = WorkspaceStore(ttl_minutes=10, clock=clock)
    store.create("ws-1")

    store.set_payload("ws-1", {"rows": []})

    assert store.get_payload("ws-1") == {"rows": []}


def test_workspace_expires_after_its_ttl_elapses() -> None:
    clock = FakeClock()
    store = WorkspaceStore(ttl_minutes=10, clock=clock)
    store.create("ws-1")
    store.set_payload("ws-1", {"rows": [1, 2, 3]})

    clock.advance(10 * 60 + 1)  # just past the 10-minute TTL

    with pytest.raises(WorkSessionExpired):
        store.get_payload("ws-1")


def test_expired_workspace_is_evicted_not_just_flagged() -> None:
    """After expiry is observed once, the entry is gone -- a second read
    also raises (WorkSessionExpired the first time is not a fluke of timing,
    it's a real, permanent transition for that workspace id)."""
    clock = FakeClock()
    store = WorkspaceStore(ttl_minutes=1, clock=clock)
    store.create("ws-1")
    clock.advance(61)

    with pytest.raises(WorkSessionExpired):
        store.get_payload("ws-1")

    with pytest.raises(WorkSessionNotFound):
        store.get_payload("ws-1")


def test_touch_extends_the_ttl() -> None:
    clock = FakeClock()
    store = WorkspaceStore(ttl_minutes=10, clock=clock)
    store.create("ws-1")

    clock.advance(9 * 60)  # almost expired
    store.touch("ws-1")  # renews for another 10 minutes from now
    clock.advance(9 * 60)  # would have expired if not touched

    store.get_payload("ws-1")  # should not raise


def test_unknown_workspace_id_raises_not_found() -> None:
    store = WorkspaceStore(ttl_minutes=10)
    with pytest.raises(WorkSessionNotFound):
        store.get_payload("never-created")


def test_sweep_expired_evicts_only_expired_entries() -> None:
    clock = FakeClock()
    store = WorkspaceStore(ttl_minutes=1, clock=clock)
    store.create("old")
    clock.advance(61)
    store.create("fresh")

    removed = store.sweep_expired()

    assert removed == 1
    with pytest.raises(WorkSessionNotFound):
        store.get_payload("old")
    store.get_payload("fresh")  # still alive, does not raise
