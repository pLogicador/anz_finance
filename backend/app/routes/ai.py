"""Fase 5: model selection, "test connection", contextual insights, and the
grounded Q&A assistant. Every route here that touches an API key follows the
same rule as ``routes/upload.py``: a user-supplied key is used for exactly
one request and never logged, stored, or echoed back.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.access.deps import get_current_session
from app.access.security import SessionClaims
from app.core.config import Settings, get_settings
from app.pipeline import metrics
from app.pipeline.categorizer.registry import AVAILABLE_MODELS, MissingApiKey, UnknownProvider, build_provider, require_api_key
from app.pipeline.categorizer.schemas import AiAskRequest, AiTestConnectionRequest
from app.pipeline.filters import apply_type_filter, filter_transactions, filter_transactions_for_trend
from app.pipeline.insights import build_insights
from app.workspace.deps import get_workspace_payload
from app.workspace.models import WorkspacePayload

router = APIRouter(prefix="/ai", tags=["ai"])


def _build_provider_or_400(provider_id: str, model: str | None, api_key: str | None, settings: Settings):
    try:
        resolved_key = require_api_key(provider_id, settings, api_key)
        return build_provider(provider_id, model, resolved_key)
    except (UnknownProvider, MissingApiKey) as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


@router.get("/models")
def list_models(_: SessionClaims = Depends(get_current_session)) -> dict:
    """Requires only a valid ANZ session (not workspace data) -- the model
    picker is shown on the upload screen, before any data exists."""
    return {"models": [{"provider": m.provider, "model": m.model, "label": m.label} for m in AVAILABLE_MODELS]}


@router.post("/settings/test-connection")
async def test_connection(
    body: AiTestConnectionRequest,
    _: SessionClaims = Depends(get_current_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    provider = _build_provider_or_400(body.provider, body.model, body.api_key, settings)
    ok = await provider.test_connection()
    return {"ok": ok}


@router.get("/insights")
def get_insights(
    month: str = Query(...),
    categories: list[str] | None = Query(default=None),
    type: str = Query(default="Todas"),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    """Deterministic, no LLM call -- see app/pipeline/insights.py for why."""
    period_df = apply_type_filter(filter_transactions(payload.df, month, categories), type)
    trend_df = apply_type_filter(filter_transactions_for_trend(payload.df, categories), type)

    summary = metrics.summarize(period_df)
    deltas = {
        "income": metrics.month_over_month_delta(trend_df, month, "income"),
        "expense": metrics.month_over_month_delta(trend_df, month, "expense"),
        "net": metrics.month_over_month_delta(trend_df, month, "net"),
    }
    breakdown = metrics.category_breakdown(period_df)

    insights = build_insights(summary=summary, deltas=deltas, category_breakdown=breakdown, month=month)
    return {"insights": [{"kind": i.kind, "text": i.text} for i in insights]}


def _build_grounding_context(*, summary: metrics.PeriodSummary, deltas: dict[str, float | None], breakdown, monthly, month: str) -> str:
    top_categories = ", ".join(f"{row['Categorias']}: R$ {row['Valor']:.2f}" for _, row in breakdown.head(5).iterrows()) or "nenhuma"
    monthly_lines = "\n".join(
        f"- {row['Mês']}: receitas R$ {row['Receitas']:.2f}, despesas R$ {abs(row['Despesas']):.2f}, saldo R$ {row['Saldo']:.2f}"
        for _, row in monthly.iterrows()
    ) or "nenhum"
    return (
        f"Mês selecionado: {month}\n"
        f"Receitas do período: R$ {summary.income:.2f}\n"
        f"Despesas do período: R$ {abs(summary.expense):.2f}\n"
        f"Saldo do período: R$ {summary.net:.2f}\n"
        f"Número de transações no período: {summary.transaction_count}\n"
        f"Maior categoria de gasto: {summary.top_category or 'nenhuma'} (R$ {summary.top_category_amount:.2f})\n"
        f"Variação vs. mês anterior -- receitas: {deltas['income']}, despesas: {deltas['expense']}, saldo: {deltas['net']}\n"
        f"Maiores categorias no período (até 5): {top_categories}\n"
        f"Série mensal disponível:\n{monthly_lines}"
    )


GROUNDING_SYSTEM_PROMPT = (
    "Você é o assistente financeiro do ANZ Finance. Responda em português do Brasil, de forma curta e direta. "
    "Use SOMENTE os dados fornecidos abaixo, que vêm da sessão atual do usuário -- nunca invente números, "
    "nunca use conhecimento externo sobre bancos, mercado financeiro ou o usuário. "
    "Se a pergunta não puder ser respondida com os dados fornecidos, diga claramente que não possui essa "
    "informação na sessão atual, em vez de tentar adivinhar ou responder com dados genéricos."
)


@router.post("/ask")
async def ask(
    body: AiAskRequest,
    settings: Settings = Depends(get_settings),
    payload: WorkspacePayload = Depends(get_workspace_payload),
) -> dict:
    period_df = apply_type_filter(filter_transactions(payload.df, body.month, body.categories), body.type)
    trend_df = apply_type_filter(filter_transactions_for_trend(payload.df, body.categories), body.type)

    summary = metrics.summarize(period_df)
    deltas = {
        "income": metrics.month_over_month_delta(trend_df, body.month, "income"),
        "expense": metrics.month_over_month_delta(trend_df, body.month, "expense"),
        "net": metrics.month_over_month_delta(trend_df, body.month, "net"),
    }
    breakdown = metrics.category_breakdown(period_df)
    monthly = metrics.monthly_series(trend_df)

    context = _build_grounding_context(summary=summary, deltas=deltas, breakdown=breakdown, monthly=monthly, month=body.month)
    provider = _build_provider_or_400(body.provider, body.model, body.api_key, settings)

    user_prompt = f"Dados da sessão atual:\n{context}\n\nPergunta do usuário: {body.question}"
    try:
        answer = await provider.complete(system=GROUNDING_SYSTEM_PROMPT, user=user_prompt)
    except Exception as exc:  # noqa: BLE001 -- provider-specific exceptions, never surfaced raw
        raise HTTPException(status_code=502, detail={"message": "O provedor de IA não respondeu. Tente novamente em instantes."}) from exc

    return {"answer": answer}
