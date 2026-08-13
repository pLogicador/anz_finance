"""Themed Plotly chart builders used by the dashboard.

Every function takes already-classified/filtered data (from
modules/data/finance_data.py + modules/ui/metrics.py) and returns a
go.Figure. No financial computation happens here beyond simple
presentation aggregation already done in metrics.py.
"""

import pandas as pd
import plotly.graph_objects as go

from modules.ui.theme import category_color, plotly_template


def _apply_layout(fig: go.Figure, mode: str, **overrides) -> go.Figure:
    layout = plotly_template(mode)
    for key, value in overrides.items():
        # One-level-deep merge for dict values (legend, margin, ...) so a
        # partial override (e.g. just `orientation`) doesn't silently drop
        # the base theme's font/bgcolor for that key.
        if isinstance(value, dict) and isinstance(layout.get(key), dict):
            layout[key] = {**layout[key], **value}
        else:
            layout[key] = value
    fig.update_layout(**layout)
    return fig


def category_donut(breakdown: pd.DataFrame, mode: str) -> go.Figure:
    colors = [category_color(c, i) for i, c in enumerate(breakdown["Categorias"])]
    fig = go.Figure(
        go.Pie(
            labels=breakdown["Categorias"],
            values=breakdown["Valor"],
            hole=0.62,
            marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0)", width=0)),
            textinfo="percent",
            textfont=dict(size=12),
            hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
        )
    )
    return _apply_layout(
        fig,
        mode,
        showlegend=True,
        height=380,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12, yanchor="top"),
        margin=dict(l=10, r=10, t=20, b=10),
    )


def monthly_income_vs_expense(monthly: pd.DataFrame, mode: str) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(
        name="Receitas",
        x=monthly["Mês"],
        y=monthly["Receitas"],
        marker_color="#10B981",
        hovertemplate="%{x}<br>Receitas: R$ %{y:,.2f}<extra></extra>",
    )
    fig.add_bar(
        name="Despesas",
        x=monthly["Mês"],
        y=monthly["Despesas"].abs(),
        marker_color="#EF4444",
        hovertemplate="%{x}<br>Despesas: R$ %{y:,.2f}<extra></extra>",
    )
    fig = _apply_layout(
        fig, mode, barmode="group", bargap=0.3, showlegend=True, xaxis=dict(type="category")
    )
    return fig


def cumulative_balance(monthly: pd.DataFrame, mode: str) -> go.Figure:
    running = monthly.copy()
    running["Acumulado"] = running["Saldo"].cumsum()
    fig = go.Figure(
        go.Scatter(
            x=running["Mês"],
            y=running["Acumulado"],
            mode="lines+markers",
            line=dict(color="#2F6FED", width=3, shape="spline"),
            marker=dict(size=6, color="#2F6FED"),
            fill="tozeroy",
            fillcolor="rgba(47, 111, 237, 0.12)",
            hovertemplate="%{x}<br>Saldo acumulado: R$ %{y:,.2f}<extra></extra>",
        )
    )
    return _apply_layout(fig, mode, showlegend=False, xaxis=dict(type="category"))


def top_categories_bar(breakdown: pd.DataFrame, mode: str, limit: int = 8) -> go.Figure:
    top = breakdown.head(limit).sort_values("Valor")
    colors = [category_color(c, i) for i, c in enumerate(top["Categorias"])]
    fig = go.Figure(
        go.Bar(
            x=top["Valor"],
            y=top["Categorias"],
            orientation="h",
            marker_color=colors,
            text=top["Valor"].map(lambda v: f"{v:,.0f}"),
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
        )
    )
    return _apply_layout(
        fig,
        mode,
        showlegend=False,
        margin=dict(l=10, r=40, t=20, b=10),
        xaxis=dict(automargin=True),
    )


def category_month_heatmap(df: pd.DataFrame, mode: str) -> go.Figure:
    expenses = df[df["Valor"] < 0]
    if expenses.empty:
        return go.Figure()
    pivot = (
        expenses.groupby(["Categorias", "Mês"])["Valor"]
        .sum()
        .abs()
        .unstack(fill_value=0)
    )
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale=[
                [0, "rgba(47,111,237,0.05)"],
                [0.35, "rgba(47,111,237,0.35)"],
                [0.7, "#2F6FED"],
                [1, "#153E8A"],
            ],
            hovertemplate="%{y} · %{x}<br>R$ %{z:,.2f}<extra></extra>",
            colorbar=dict(thickness=12, outlinewidth=0),
        )
    )
    return _apply_layout(fig, mode, showlegend=False, xaxis=dict(type="category"))
