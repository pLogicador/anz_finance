from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BridgeRequest(BaseModel):
    token: str


class BridgeUser(BaseModel):
    email: str


class BridgeResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    workspace_id: str
    user: BridgeUser


class MeResponse(BaseModel):
    email: str
    workspace_id: str
    expires_at: datetime
