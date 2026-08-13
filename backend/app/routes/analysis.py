"""Fase 6: anomaly detection + arbitrary two-period comparison. Both read
the current session's workspace data (same 410-on-no-data semantics as
every other workspace-scoped route, via ``get_workspace_payload``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.pipeline.analysis import compare_periods, detect_anomalies
from app.pipeline.filters import apply_type_filter, filter_transactions_for_trend
from app.workspace.deps import get_workspace_payload
from app.workspace.models import WorkspacePayload

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/anomalies")
def get_anomalies(
    categories: list[str] | None = Query(default=None),
    type: str = Query(default="Todas"),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    df = apply_type_filter(filter_transactions_for_trend(payload.df, categories), type)
    anomalies = detect_anomalies(df)
    return {
        "anomalies": [
            {
                "date": a.date,
                "description": a.description,
                "category": a.category,
                "valor": a.valor,
                "category_average": a.category_average,
                "ratio": a.ratio,
            }
            for a in anomalies
        ]
    }


@router.get("/compare")
def get_compare(
    month_a: str = Query(...),
    month_b: str = Query(...),
    categories: list[str] | None = Query(default=None),
    type: str = Query(default="Todas"),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    available_months = set(payload.df["Mês"].unique()) if not payload.df.empty else set()
    if month_a not in available_months or month_b not in available_months:
        raise HTTPException(status_code=400, detail={"message": "Um dos meses selecionados não existe nos dados desta sessão."})

    df = apply_type_filter(filter_transactions_for_trend(payload.df, categories), type)
    result = compare_periods(df, month_a, month_b)

    def _summary(s):
        return {
            "income": s.income,
            "expense": s.expense,
            "net": s.net,
            "transaction_count": s.transaction_count,
            "top_category": s.top_category,
            "top_category_amount": s.top_category_amount,
        }

    return {
        "month_a": result.month_a,
        "month_b": result.month_b,
        "summary_a": _summary(result.summary_a),
        "summary_b": _summary(result.summary_b),
        "income_change_pct": result.income_change_pct,
        "expense_change_pct": result.expense_change_pct,
        "net_change_pct": result.net_change_pct,
        "category_deltas": [
            {"category": d.category, "valor_a": d.valor_a, "valor_b": d.valor_b, "delta": d.delta} for d in result.category_deltas
        ],
    }
