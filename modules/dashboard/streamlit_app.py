import streamlit as st
import plotly.express as px
from io import BytesIO

from modules.parsers.ofx_parser import parse_ofx_files_from_upload
from modules.data.finance_data import preprocess_df, filter_transactions
from modules.llm.categorizer import Categorizer


def run_finance_dashboard():
    #st.set_page_config(page_title="Finance Dashboard", layout="wide")
    #st.title("💰 Personal Finance Dashboard")
    #st.title("💰 Finlytics - Painel de Controle Financeiro")
    st.markdown("""
    <h1>💰 Finlytics</h1>
    <h4 style="color: #9CA3AF;">Painel de Controle Financeiro</h4>
    """, unsafe_allow_html=True)


    uploaded_files = st.file_uploader(
        "📂 Faça upload dos extratos (.ofx)",
        type="ofx",
        accept_multiple_files=True
    )

    if uploaded_files:
        with st.spinner("⏳ Processando arquivos..."):
            # Parser dos arquivos enviados
            df = parse_ofx_files_from_upload(uploaded_files)
            if df.empty:
                st.error("❌ Nenhuma transação encontrada nos arquivos enviados.")
                return

            # Pré-processamento
            df = preprocess_df(df)

            # Classificação LLM
            categorizer = Categorizer()
            df["Categorias"] = categorizer.classify(df["Descrição"].values)

        # Botão para baixar CSV
        st.download_button(
            "💾 Baixar CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="finances.csv",
            mime="text/csv",
        )

        # Exibir o dashboard
        show_dashboard(df)

    else:
        st.info("⬆️ Envie um ou mais arquivos OFX para começar.")


def show_dashboard(df):
    """Renderiza a interface de dashboard (filtros, tabela e gráficos)."""

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

    # Tabela de transações
    col1.subheader("📋 Tabela de Transações Filtradas")
    col1.dataframe(filtered_df, use_container_width=True)

    # Gráfico de pizza por categoria
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
