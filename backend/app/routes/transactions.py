"""Read endpoints over the current session's workspace data.

Two filtered views, matching the two real semantics from
app/pipeline/filters.py: `/transactions` (month+category+type, used by
KPIs/table) and `/trend` (category+type only, full history, used by
trend/heatmap charts) -- never conflated into one function, same as the
legacy app kept `period_df` and `trend_df` separate
(legacy_streamlit/modules/dashboard/streamlit_app.py:133-139).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.pipeline import metrics
from app.pipeline.filters import apply_type_filter, filter_transactions, filter_transactions_for_trend
from app.pipeline.serialization import df_to_records
from app.workspace.deps import get_workspace_payload
from app.workspace.models import WorkspacePayload

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/months")
def list_months(payload: WorkspacePayload = Depends(get_workspace_payload)) -> dict:
    df = payload.df
    if df.empty:
        return {"months": [], "years": []}
    months = sorted(df["Mês"].unique().tolist(), reverse=True)
    years = sorted({m.split("-")[0] for m in months}, reverse=True)
    return {"months": months, "years": years}


@router.get("/transactions")
def get_transactions(
    month: str = Query(...),
    categories: list[str] | None = Query(default=None),
    type: str = Query(default="Todas"),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    period_df = filter_transactions(payload.df, month, categories)
    period_df = apply_type_filter(period_df, type)
    return {"transactions": df_to_records(period_df), "count": int(len(period_df))}


@router.get("/trend")
def get_trend(
    categories: list[str] | None = Query(default=None),
    type: str = Query(default="Todas"),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    trend_df = filter_transactions_for_trend(payload.df, categories)
    trend_df = apply_type_filter(trend_df, type)
    return {"transactions": df_to_records(trend_df), "count": int(len(trend_df))}


@router.get("/category-counts")
def get_category_counts(month: str = Query(...), payload: WorkspacePayload = Depends(get_workspace_payload)) -> dict:
    """Live transaction counts per category for the given month -- backs
    the filter chips' "(N)" counts (Fase 6). Deliberately NOT filtered by
    the currently-selected categories -- a chip must always show how many
    transactions *would* match if it were toggled on, not shrink to 0 the
    moment its own category is the only one deselected."""
    period_df = filter_transactions(payload.df, month, None)
    if period_df.empty:
        return {"counts": {}}
    counts = period_df.groupby("Categorias").size().to_dict()
    return {"counts": {str(k): int(v) for k, v in counts.items()}}


@router.get("/search")
def search_transactions(
    q: str = Query(..., min_length=1),
    categories: list[str] | None = Query(default=None),
    type: str = Query(default="Todas"),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    """Global search (Fase 6): unlike `/transactions` (one month at a
    time), this searches the FULL uploaded history by description, so a
    user can find a transaction without first knowing which month it's in.
    Category/type filters still apply, matching the trend-view semantics
    (`filter_transactions_for_trend`) -- no month restriction at all."""
    df = apply_type_filter(filter_transactions_for_trend(payload.df, categories), type)
    if df.empty:
        return {"transactions": [], "count": 0}
    term = q.strip().lower()
    matches = df[df["Descrição"].str.lower().str.contains(term, na=False, regex=False)]
    matches = matches.sort_values("Data", ascending=False)
    return {"transactions": df_to_records(matches), "count": int(len(matches))}


@router.get("/summary")
def get_summary(
    month: str = Query(...),
    categories: list[str] | None = Query(default=None),
    type: str = Query(default="Todas"),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    period_df = apply_type_filter(filter_transactions(payload.df, month, categories), type)
    trend_df = apply_type_filter(filter_transactions_for_trend(payload.df, categories), type)

    period_summary = metrics.summarize(period_df)
    income_delta = metrics.month_over_month_delta(trend_df, month, "income")
    expense_delta = metrics.month_over_month_delta(trend_df, month, "expense")
    net_delta = metrics.month_over_month_delta(trend_df, month, "net")

    monthly = metrics.monthly_series(trend_df)
    breakdown = metrics.category_breakdown(period_df)

    return {
        "summary": {
            "income": period_summary.income,
            "expense": period_summary.expense,
            "net": period_summary.net,
            "transaction_count": period_summary.transaction_count,
            "top_category": period_summary.top_category,
            "top_category_amount": period_summary.top_category_amount,
        },
        "deltas": {"income": income_delta, "expense": expense_delta, "net": net_delta},
        "monthly_series": monthly.to_dict(orient="records"),
        "category_breakdown": breakdown.to_dict(orient="records"),
    }
