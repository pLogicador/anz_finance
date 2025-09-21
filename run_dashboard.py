import os
import logging
import requests
import streamlit as st
from modules.dashboard.streamlit_app import run_finance_dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard")

API_BASE = os.getenv("API_BASE")
API_HUB = os.getenv("API_HUB")

def validate_token_with_api(token: str):
    """Chama a API /validate-agendador-token e retorna o json se OK, else None."""
    if not token:
        return None
    try:
        resp = requests.post(
            f"{API_BASE}/validate-agendador-token",
            json={"token": token},
            timeout=5
        )
        # log útil para debug (não expor em produção)
        #logger.info("validate call status=%s body=%s", resp.status_code, resp.text[:400])
        if resp.status_code == 200:
            return resp.json()
        else:
            return None
    except requests.RequestException as e:
        logger.exception("Erro ao chamar API de validação")
        return None

def get_token_from_query():
    """Retorna token vindo da query string (lida por st.query_params)."""
    params = st.query_params or {}
    token_val = params.get("token")
    
    if token_val is None:
        return None
    if isinstance(token_val, list):
        token_val = token_val[0] if token_val else None
    # às vezes token pode vir com espaços ou prefixo; strip.
    if token_val:
        token_val = str(token_val).strip()
        # se veio com "Bearer ...", remove (por precaução)
        if token_val.lower().startswith("bearer "):
            token_val = token_val.split(" ", 1)[1]
    return token_val

def run_dashboard():
    st.set_page_config(page_title="ANZ Finance", layout="wide")

    token = get_token_from_query()
    logger.info("Token recebido (raw): %s", token)

    if not token:
        st.warning("Você precisa fazer login antes de acessar o dashboard.")
        st.markdown(f"[Ir para login]({API_HUB}/login.html)")
        st.stop()

    user_info = validate_token_with_api(token)
    if not user_info:
        st.error("⚠️ Token inválido ou expirado. Faça login novamente.")
        st.markdown(f"[Ir para login]({API_HUB}/login.html)")
        st.stop()

    user_email = user_info.get("user", {}).get("email", "Usuário")
    st.sidebar.success(f"Usuário: {user_email}")

    run_finance_dashboard()

if __name__ == "__main__":
    run_dashboard()
