import streamlit as st

from modules.parsers.ofx_parser import parse_ofx_files_from_upload
from modules.data.finance_data import preprocess_df, filter_transactions
from modules.llm.categorizer import Categorizer
from modules.ui import theme, charts, metrics
from modules.ui.components import (
    card,
    empty_state,
    format_currency,
    kpi_card,
    kpi_row,
    section_header,
    sidebar_heading,
    theme_toggle,
    topbar,
    transactions_table,
)

TYPE_OPTIONS = ["Todas", "Receitas", "Despesas"]


def run_finance_dashboard(user_email: str | None = None) -> None:
    mode = st.session_state.get("anz_mode", "dark")
    mode = theme_toggle(mode)
    st.session_state["anz_mode"] = mode
    theme.apply(mode)

    topbar(user_email, mode)

    uploaded_files = st.file_uploader(
        "Faça upload dos extratos (.ofx)",
        type="ofx",
        accept_multiple_files=True,
        help="Você pode enviar um ou mais extratos bancários no formato OFX.",
    )

    if not uploaded_files:
        empty_state(
            "📂",
            "Nenhum extrato carregado",
            "Envie um ou mais arquivos .ofx acima para gerar seu painel financeiro.",
        )
        return

    df = _get_or_process(uploaded_files)
    if df is None:
        return
    if df.empty:
        st.error("❌ Nenhuma transação encontrada nos arquivos enviados.")
        return

    _render_dashboard(df, mode)


def _file_signature(files) -> tuple:
    return tuple((f.name, f.size) for f in files)


def _get_or_process(uploaded_files):
    """Runs the parse -> preprocess -> classify pipeline once per file set.

    Streamlit reruns the whole script on every widget interaction (filters,
    pagination, theme toggle); without this cache each click would silently
    re-parse the files and re-call the LLM classifier from scratch.
    """
    signature = _file_signature(uploaded_files)
    if st.session_state.get("anz_file_signature") == signature:
        return st.session_state.get("anz_processed_df")

    with st.status("Processando extratos...", expanded=True) as status:
        st.write("🔍 Lendo arquivos OFX...")
        df = parse_ofx_files_from_upload(uploaded_files)
        if df.empty:
            status.update(label="Nenhuma transação encontrada", state="error")
            st.session_state["anz_processed_df"] = df
            st.session_state["anz_file_signature"] = signature
            return df

        st.write("⚙️ Organizando dados...")
        df = preprocess_df(df)

        st.write("🧠 Classificando transações com IA...")
        categorizer = Categorizer()
        df["Categorias"] = categorizer.classify(df["Descrição"].values)
        # Display-only cleanup: a blank/NaN category (e.g. an LLM response
        # that came back empty) renders as a broken "undefined" label in the
        # Plotly legend/table instead of a real word. Never changes what the
        # classifier returns, just how an edge-case result is shown.
        df["Categorias"] = (
            df["Categorias"]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace({"": "Não classificado", "Error": "Erro na classificação"})
        )

        status.update(label="Extratos processados com sucesso", state="complete")

    st.session_state["anz_processed_df"] = df
    st.session_state["anz_file_signature"] = signature
    return df


def _render_dashboard(df, mode: str) -> None:
    months = sorted(df["Mês"].unique(), reverse=True)
    years = sorted({m.split("-")[0] for m in months}, reverse=True)

    st.sidebar.markdown('<div class="anz-divider"></div>', unsafe_allow_html=True)
    sidebar_heading("Filtros")

    selected_year = st.sidebar.selectbox("Ano", options=["Todos"] + years, index=0)
    months_for_year = [m for m in months if selected_year == "Todos" or m.startswith(selected_year)]
    if not months_for_year:
        months_for_year = months
    selected_month = st.sidebar.selectbox("Mês", options=months_for_year, index=0)

    all_categories = sorted(df["Categorias"].dropna().unique())
    selected_categories = st.sidebar.multiselect(
        "Categorias", options=all_categories, default=all_categories
    )
    selected_type = st.sidebar.radio("Tipo", options=TYPE_OPTIONS, horizontal=True)

    st.sidebar.markdown('<div class="anz-divider"></div>', unsafe_allow_html=True)
    st.sidebar.download_button(
        "💾 Baixar CSV completo",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="finances.csv",
        mime="text/csv",
        use_container_width=True,
    )

    period_df = filter_transactions(df, selected_month, selected_categories)
    period_df = _apply_type_filter(period_df, selected_type)

    # Mirrors filter_transactions' own semantics: an empty category selection
    # means "no category filter applied", not "show nothing".
    trend_df = df[df["Categorias"].isin(selected_categories)] if selected_categories else df
    trend_df = _apply_type_filter(trend_df, selected_type)

    _render_kpis(period_df, trend_df, selected_month)

    st.markdown('<div class="anz-divider"></div>', unsafe_allow_html=True)

    tab_overview, tab_trends, tab_heatmap, tab_table = st.tabs(
        ["📊 Visão Geral", "📈 Tendências", "🗓️ Mapa de Gastos", "📋 Transações"]
    )

    with tab_overview:
        _render_overview(period_df, mode)
    with tab_trends:
        _render_trends(trend_df, mode)
    with tab_heatmap:
        _render_heatmap(trend_df, mode)
    with tab_table, card():
        section_header("Transações do período", f"{selected_month} · {selected_type}")
        transactions_table(period_df, key_prefix="main")


def _apply_type_filter(df, selected_type: str):
    if selected_type == "Receitas":
        return df[df["Valor"] >= 0]
    if selected_type == "Despesas":
        return df[df["Valor"] < 0]
    return df


def _render_kpis(period_df, trend_df, selected_month: str) -> None:
    summary = metrics.summarize(period_df)
    net_delta = metrics.month_over_month_delta(trend_df, selected_month, "net")
    income_delta = metrics.month_over_month_delta(trend_df, selected_month, "income")
    expense_delta_raw = metrics.month_over_month_delta(trend_df, selected_month, "expense")
    # "expense" totals are negative sums; flip so positive delta = spent more.
    expense_delta = None if expense_delta_raw is None else -expense_delta_raw

    top_category_value = summary.top_category or "—"
    top_category_footnote = (
        format_currency(summary.top_category_amount) if summary.top_category else "Sem gastos no período"
    )

    kpi_row([
        kpi_card("Receitas do período", format_currency(summary.income), icon="💰", delta=income_delta),
        kpi_card("Despesas do período", format_currency(abs(summary.expense)), icon="💸", delta=expense_delta, invert=True),
        kpi_card("Saldo do período", format_currency(summary.net), icon="📈", delta=net_delta),
        kpi_card("Maior categoria", top_category_value, icon="🏷️", footnote=top_category_footnote),
    ])


def _render_overview(period_df, mode: str) -> None:
    summary = metrics.summarize(period_df)
    if summary.transaction_count == 0:
        empty_state("🔍", "Nenhuma transação neste período", "Ajuste os filtros na barra lateral.")
        return

    breakdown = metrics.category_breakdown(period_df)
    col_a, col_b = st.columns([1, 1])
    with col_a, card():
        section_header("Distribuição por categoria")
        if len(breakdown) > 1:
            st.plotly_chart(charts.category_donut(breakdown, mode), use_container_width=True)
        else:
            st.info("É necessário mais de uma categoria com valores para gerar o gráfico.")
    with col_b, card():
        section_header("Maiores categorias de gasto")
        if not breakdown.empty:
            st.plotly_chart(charts.top_categories_bar(breakdown, mode), use_container_width=True)
        else:
            st.info("Nenhuma despesa classificada neste período.")


def _render_trends(trend_df, mode: str) -> None:
    monthly = metrics.monthly_series(trend_df)
    if len(monthly) < 2:
        empty_state(
            "📈",
            "Dados insuficientes para tendências",
            "Envie extratos de mais de um mês para ver a evolução ao longo do tempo.",
        )
        return

    with card():
        section_header("Receitas vs. Despesas por mês")
        st.plotly_chart(charts.monthly_income_vs_expense(monthly, mode), use_container_width=True)

    with card():
        section_header("Saldo acumulado")
        st.plotly_chart(charts.cumulative_balance(monthly, mode), use_container_width=True)


def _render_heatmap(trend_df, mode: str) -> None:
    if trend_df["Mês"].nunique() < 2:
        empty_state(
            "🗓️",
            "Dados insuficientes para o mapa de gastos",
            "Envie extratos de mais de um mês para comparar categorias ao longo do tempo.",
        )
        return
    with card():
        section_header("Gastos por categoria e mês")
        st.plotly_chart(charts.category_month_heatmap(trend_df, mode), use_container_width=True)
