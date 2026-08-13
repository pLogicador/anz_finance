from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from app.pipeline.ofx_parser import FileParseResult


@dataclass
class Snapshot:
    """A named bookmark of a filter combination (Fase 6, PARTE 6.6) -- not
    a copy of the data itself, just the month/categories/type that
    produced a view the user wants to return to quickly. Lives and dies
    with the same workspace TTL entry as everything else here (guardrail
    #1: no persistence beyond the in-memory session)."""

    id: str
    label: str
    month: str
    categories: list[str]
    type: str
    created_at: float


@dataclass
class WorkspacePayload:
    df: pd.DataFrame
    file_results: list[FileParseResult]
    snapshots: list[Snapshot] = field(default_factory=list)
