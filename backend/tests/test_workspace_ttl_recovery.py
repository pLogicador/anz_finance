"""PARTE 5.6 state 5, proven at the API level (not just the store unit
tests in test_workspace_store.py): once the workspace TTL elapses, reads
report work_session_expired, and simply uploading again recovers -- no
re-auth, no fresh Syncron token needed, matching the plan's design ("re-
enviar os extratos" without leaving the product).
"""

from __future__ import annotations

from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.categorizer.groq_provider import GROQ_CHAT_COMPLETIONS_URL
from app.workspace.store import WorkspaceStore, get_workspace_store
from tests.fixtures.mock_syncron import mock_valid

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _mock_groq_sequence(n: int) -> None:
    respx.post(GROQ_CHAT_COMPLETIONS_URL).mock(side_effect=[httpx.Response(200, json={"choices": [{"message": {"content": "Mercado"}}]}) for _ in range(n)])


@respx.mock
def test_expired_workspace_recovers_via_a_plain_re_upload(client: TestClient, test_settings, workspace_store: WorkspaceStore) -> None:
    clock = FakeClock()
    short_ttl_store = WorkspaceStore(ttl_minutes=1, clock=clock)
    app.dependency_overrides[get_workspace_store] = lambda: short_ttl_store
    try:
        mock_valid(respx, email="tester@example.com")
        bridge = client.post("/auth/bridge", json={"token": "valid-token"})
        headers = {"Authorization": f"Bearer {bridge.json()['access_token']}"}

        _mock_groq_sequence(3)
        with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
            first_upload = client.post(
                "/workspace/upload", headers=headers, files={"files": ("valid_statement.ofx", fh, "application/octet-stream")}
            )
        assert first_upload.status_code == 200

        # Still within TTL: readable.
        assert client.get("/workspace/months", headers=headers).status_code == 200

        clock.advance(61)  # past the 1-minute TTL

        expired_read = client.get("/workspace/months", headers=headers)
        assert expired_read.status_code == 410
        assert expired_read.json()["detail"]["error_code"] == "work_session_expired"

        # The ANZ auth session (JWT) is untouched -- same headers still work,
        # no fresh Syncron token needed. Re-uploading recovers in place.
        _mock_groq_sequence(3)
        with open(FIXTURES / "valid_statement.ofx", "rb") as fh:
            second_upload = client.post(
                "/workspace/upload", headers=headers, files={"files": ("valid_statement.ofx", fh, "application/octet-stream")}
            )
        assert second_upload.status_code == 200

        recovered_read = client.get("/workspace/months", headers=headers)
        assert recovered_read.status_code == 200
        assert recovered_read.json()["months"] == ["2026-02", "2026-01"]
    finally:
        app.dependency_overrides.pop(get_workspace_store, None)
