import streamlit as st
import plotly.express as px
from modules.data.finance_data import filter_transactions

def run_dashboard(df):
    st.set_page_config(page_title="Finance Dashboard", layout="wide")
    st.title("💰 Personal Finance Dashboard")

    months = sorted(df["Mês"].unique(), reverse=True)
    selected_month = st.sidebar.selectbox("📅 Mês", months)

    all_categories = sorted(df["Categorias"].dropna().unique())
    selected_categories = st.sidebar.multiselect(
        "📂 Filtrar por categoria",
        options=all_categories,
        default=all_categories
    )

    filtered_df = filter_transactions(df, selected_month, selected_categories)

    col1, col2 = st.columns([0.6, 0.4])

    col1.subheader("📋 Tabela de Transações Filtradas")
    col1.dataframe(filtered_df, use_container_width=True)

    col2.subheader("📊 Distribuição por Categoria")

    if not filtered_df.empty:
        summary = (
            filtered_df
            .groupby("Categorias")["Valor"]
            .sum()
            .abs()
            .reset_index()
        )
        summary = summary[summary["Valor"] > 0]

        if len(summary) > 1:
            fig = px.pie(
                summary,
                values="Valor",
                names="Categorias",
                title="Distribuição de Gastos por Categoria",
                hole=0.3
            )
            col2.plotly_chart(fig, use_container_width=True)
        else:
            col2.info("🔍 É necessário mais de uma categoria com valores positivos para gerar o gráfico.")
    else:
        col2.warning("⚠️ Nenhuma transação encontrada com os filtros aplicados.")
