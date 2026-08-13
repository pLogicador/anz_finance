"""Fase 6: temporary filter-combination bookmarks, stored on the SAME
workspace TTL entry as the uploaded data (see workspace/models.py's
``Snapshot``) -- not a new storage mechanism, guardrail #1 stays intact.
"""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.access.deps import get_current_session
from app.access.security import SessionClaims
from app.workspace.deps import get_workspace_payload
from app.workspace.models import Snapshot, WorkspacePayload
from app.workspace.store import WorkspaceStore, get_workspace_store

router = APIRouter(prefix="/workspace/snapshots", tags=["workspace"])


class CreateSnapshotRequest(BaseModel):
    label: str
    month: str
    categories: list[str] = []
    type: str = "Todas"


def _serialize(s: Snapshot) -> dict:
    return {"id": s.id, "label": s.label, "month": s.month, "categories": s.categories, "type": s.type, "created_at": s.created_at}


@router.get("")
def list_snapshots(payload: WorkspacePayload = Depends(get_workspace_payload)) -> dict:
    return {"snapshots": [_serialize(s) for s in payload.snapshots]}


@router.post("")
def create_snapshot(
    body: CreateSnapshotRequest,
    session: SessionClaims = Depends(get_current_session),
    store: WorkspaceStore = Depends(get_workspace_store),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    snapshot = Snapshot(
        id=str(uuid.uuid4()),
        label=body.label.strip() or body.month,
        month=body.month,
        categories=body.categories,
        type=body.type,
        created_at=time.time(),
    )
    payload.snapshots.append(snapshot)
    store.touch(session.workspace_id)  # counts as activity, same as upload/read
    return {"snapshots": [_serialize(s) for s in payload.snapshots]}


@router.delete("/{snapshot_id}")
def delete_snapshot(
    snapshot_id: str,
    session: SessionClaims = Depends(get_current_session),
    store: WorkspaceStore = Depends(get_workspace_store),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    before = len(payload.snapshots)
    payload.snapshots[:] = [s for s in payload.snapshots if s.id != snapshot_id]
    if len(payload.snapshots) == before:
        raise HTTPException(status_code=404, detail={"message": "Snapshot não encontrado."})
    store.touch(session.workspace_id)
    return {"snapshots": [_serialize(s) for s in payload.snapshots]}
