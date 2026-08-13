"""Fase 7: CSV/PDF export, both respecting the caller's currently-active
filters (month/categories/type) -- the real gap the legacy app had (its one
export button always dumped the whole unfiltered dataset).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.pipeline import metrics
from app.pipeline.csv_export import build_csv
from app.pipeline.filters import apply_type_filter, filter_transactions
from app.pipeline.pdf_report import build_pdf_report
from app.workspace.deps import get_workspace_payload
from app.workspace.models import WorkspacePayload

router = APIRouter(prefix="/workspace/export", tags=["workspace"])


@router.get("/csv")
def export_csv(
    month: str = Query(...),
    categories: list[str] | None = Query(default=None),
    type: str = Query(default="Todas"),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> Response:
    df = apply_type_filter(filter_transactions(payload.df, month, categories), type)
    csv_text = build_csv(df)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="anz-finance-{month}.csv"'},
    )


@router.get("/pdf")
def export_pdf(
    month: str = Query(...),
    categories: list[str] | None = Query(default=None),
    type: str = Query(default="Todas"),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> Response:
    df = apply_type_filter(filter_transactions(payload.df, month, categories), type)
    summary = metrics.summarize(df)
    breakdown = metrics.category_breakdown(df)
    pdf_bytes = build_pdf_report(month=month, categories=categories or [], type_filter=type, summary=summary, category_breakdown=breakdown)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="anz-finance-{month}.pdf"'},
    )
