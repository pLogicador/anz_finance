"""Reusable presentation components for the ANZ Finance dashboard.

Every function here only renders markup/widgets; none of them read from
or write to the classification pipeline, the auth flow, or any external
API. They operate on data already produced by the existing business logic.
"""

import base64
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import streamlit as st

LOGO_PATH = Path("assets/images/logo.png")


@contextmanager
def card():
    """A bordered, elevated panel matching the design system's card style.

    Wraps st.container(border=True) and drops a zero-size marker so the CSS
    in theme.py can target this specific container (Streamlit gives no other
    hook to distinguish one bordered container from another).
    """
    container = st.container(border=True)
    with container:
        st.markdown('<div class="anz-card-marker"></div>', unsafe_allow_html=True)
        yield container


def sidebar_heading(text: str) -> None:
    st.sidebar.markdown(f'<div class="anz-sidebar-heading">{text}</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _logo_b64() -> str:
    return base64.b64encode(LOGO_PATH.read_bytes()).decode()


def topbar(user_email: str | None = None, mode: str = "dark") -> None:
    """Renders the app header as a single-line HTML string.

    Deliberately built with no embedded newlines: Streamlit's markdown
    parser treats a raw HTML block as ending at the first blank line, and a
    template line consisting only of `{some_var}` becomes blank whenever
    that variable is an empty string (e.g. no user_email) — silently
    breaking the rest of the block into a misrendered "indented code"
    block. Keeping everything on one line makes that failure mode impossible.
    """
    logo = _logo_b64()
    initials = (user_email or "?")[:1].upper()
    user_chip = (
        f'<div class="anz-user-chip"><div class="anz-user-avatar">{initials}</div>'
        f"<span>{user_email}</span></div>"
        if user_email
        else ""
    )
    brand = (
        f'<img src="data:image/png;base64,{logo}" width="34" style="border-radius:8px;" />'
        '<div><div class="anz-topbar-title">ANZ Finance</div>'
        '<div class="anz-topbar-subtitle">Painel de Controle Financeiro</div></div>'
    )
    st.markdown(
        f'<div class="anz-topbar"><div class="anz-topbar-brand">{brand}</div>{user_chip}</div>',
        unsafe_allow_html=True,
    )


def theme_toggle(current_mode: str) -> str:
    """Renders a small light/dark switch in the sidebar; returns the active mode."""
    sidebar_heading("Aparência")
    is_light = st.sidebar.toggle("Modo claro", value=(current_mode == "light"), key="anz_theme_toggle")
    return "light" if is_light else "dark"


def section_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f'<div class="anz-section-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="anz-section-title">{title}</div>{subtitle_html}',
        unsafe_allow_html=True,
    )


def badge(text: str, tone: str = "neutral") -> str:
    return f'<span class="anz-badge {tone}">{text}</span>'


def kpi_card(
    label: str,
    value: str,
    icon: str = "",
    delta: float | None = None,
    invert: bool = False,
    delta_suffix: str = " vs mês anterior",
    footnote: str | None = None,
) -> str:
    """`delta` is the % change in the intuitive direction (positive = more of
    the metric happened). `invert=True` marks metrics where "more" is bad
    (e.g. expenses), so the color reflects favorability, not raw sign.
    `footnote` is optional muted text under the value (e.g. an amount next
    to a value that's itself a label, like the top-spending category)."""
    delta_html = ""
    if delta is not None:
        arrow = "▲" if delta > 0 else "▼" if delta < 0 else "•"
        favorable = (delta < 0) if invert else (delta > 0)
        tone = "flat" if delta == 0 else ("up" if favorable else "down")
        delta_html = (
            f'<div class="anz-kpi-delta {tone}">'
            f'<span class="pill">{arrow} {abs(delta):.1f}%</span>{delta_suffix}</div>'
        )
    footnote_html = f'<div class="anz-kpi-footnote">{footnote}</div>' if footnote else ""
    icon_html = f'<div class="anz-kpi-icon">{icon}</div>' if icon else ""
    # Single-line HTML (see topbar() docstring): any of icon_html/footnote_html/
    # delta_html can be "", and a template line with only `{var}` would go
    # blank and break markdown's HTML-block parsing mid-card.
    head = f'<div class="anz-kpi-head"><div class="anz-kpi-label">{label}</div>{icon_html}</div>'
    value_html = f'<div class="anz-kpi-value">{value}</div>'
    return f'<div class="anz-kpi-card">{head}{value_html}{footnote_html}{delta_html}</div>'


def kpi_row(cards: list[str]) -> None:
    cols = st.columns(len(cards))
    for col, card_html in zip(cols, cards):
        with col:
            st.markdown(card_html, unsafe_allow_html=True)


def empty_state(icon: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="anz-empty-state">
            <div class="icon">{icon}</div>
            <div class="title">{title}</div>
            <div>{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_currency(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}R$ {abs(value):,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")


def transactions_table(df: pd.DataFrame, key_prefix: str = "tbl") -> None:
    """Search + sort (native) + paginated, formatted view of a transactions df."""
    if df.empty:
        empty_state("🔍", "Nenhuma transação para exibir", "Ajuste os filtros para ver resultados.")
        return

    top_l, top_r = st.columns([3, 1])
    with top_l:
        query = st.text_input(
            "Pesquisar por descrição ou categoria",
            key=f"{key_prefix}_search",
            placeholder="🔎 Pesquisar transações...",
            label_visibility="collapsed",
        )
    with top_r:
        page_size = st.selectbox(
            "Linhas por página",
            options=[10, 25, 50, 100],
            index=1,
            key=f"{key_prefix}_page_size",
            label_visibility="collapsed",
        )

    view = df.copy()
    if query:
        mask = (
            view["Descrição"].astype(str).str.contains(query, case=False, na=False)
            | view["Categorias"].astype(str).str.contains(query, case=False, na=False)
        )
        view = view[mask]

    view = view.sort_values("Data", ascending=False)
    total_rows = len(view)
    total_pages = max(1, -(-total_rows // page_size))

    page_key = f"{key_prefix}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    st.session_state[page_key] = min(st.session_state[page_key], total_pages)

    display_cols = ["Data", "Descrição", "Categorias", "Valor"]
    page = st.session_state[page_key]
    start, end = (page - 1) * page_size, page * page_size
    page_df = view.iloc[start:end][display_cols].copy()
    page_df["Data"] = pd.to_datetime(page_df["Data"])
    page_df["Tipo"] = page_df["Valor"].apply(lambda v: "Receita" if v >= 0 else "Despesa")
    # NumberColumn's format string can't produce Brazilian "1.234,56" —
    # only Python/printf "1234.56" — which read as inconsistent right next
    # to the KPI cards above (which do use format_currency). Pre-format as
    # text instead so the whole app agrees on one currency style.
    page_df["Valor"] = page_df["Valor"].apply(format_currency)

    st.dataframe(
        page_df,
        use_container_width=True,
        hide_index=True,
        height=min(46 * (len(page_df) + 1), 46 * page_size + 40),
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "Descrição": st.column_config.TextColumn("Descrição", width="large"),
            "Categorias": st.column_config.TextColumn("Categoria"),
            "Valor": st.column_config.TextColumn("Valor"),
            "Tipo": st.column_config.TextColumn("Tipo", width="small"),
        },
    )

    nav_l, nav_c, nav_r = st.columns([1, 2, 1])
    with nav_l:
        if st.button("← Anterior", key=f"{key_prefix}_prev", disabled=(page <= 1)):
            st.session_state[page_key] = page - 1
            st.rerun()
    with nav_c:
        st.markdown(
            f'<div class="anz-table-nav-label">Página {page} de {total_pages} · {total_rows} transações</div>',
            unsafe_allow_html=True,
        )
    with nav_r:
        if st.button("Próxima →", key=f"{key_prefix}_next", disabled=(page >= total_pages)):
            st.session_state[page_key] = page + 1
            st.rerun()
