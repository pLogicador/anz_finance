import streamlit as st
import pandas as pd
import plotly.express as px

# ========== Page Setup ==========
st.set_page_config(page_title="Finance Dashboard", layout="wide")

# ========== Load Data ==========
df = pd.read_csv("finances.csv")

# Remove 'ID' column if present
if "ID" in df.columns:
    df.drop(columns=["ID"], inplace=True)

# Convert and format date
df["Data"] = pd.to_datetime(df["Data"])
df["Mês"] = df["Data"].dt.to_period("M").astype(str)  # Format: YYYY-MM
df["Data"] = df["Data"].dt.date

# ========== Sidebar Filters ==========
st.title("💰 Personal Finance Dashboard")

months = sorted(df["Mês"].unique(), reverse=True)
selected_month = st.sidebar.selectbox("📅 Mês", months)

all_categories = sorted(df["Categorias"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "📂 Filtrar por categoria",
    options=all_categories,
    default=all_categories
)

# ========== Filter Function ==========
def filter_transactions(data, month, categories):
    filtered = data[data["Mês"] == month]
    if categories:
        filtered = filtered[filtered["Categorias"].isin(categories)]
    return filtered

filtered_df = filter_transactions(df, selected_month, selected_categories)

# ========== Layout ==========
col1, col2 = st.columns([0.6, 0.4])

# Table of transactions
col1.subheader("📋 Tabela de Transações Filtradas")
col1.dataframe(filtered_df, use_container_width=True)

# Pie chart of category distribution
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
