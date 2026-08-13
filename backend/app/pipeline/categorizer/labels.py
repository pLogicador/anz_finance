"""The exact category contract from legacy_streamlit/modules/llm/categorizer.py.

Must-follow-exactly per the plan: the 11 labels are verbatim, character for
character (including accents) -- CATEGORY_COLORS-equivalent mapping in
Fase 4's design system, and anything else downstream, keys off these exact
strings.
"""

from __future__ import annotations

VALID_CATEGORIES: tuple[str, ...] = (
    "Moradia",
    "Alimentação",
    "Mercado",
    "Transporte",
    "Telefone",
    "Receitas",
    "Transferência para terceiros",
    "Compras",
    "Educação",
    "Saúde",
    "Investimento",
)

NOT_CLASSIFIED = "Não classificado"
CLASSIFICATION_ERROR = "Erro na classificação"

# Verbatim from legacy_streamlit/modules/llm/categorizer.py:6-33. The only
# template variable is {text}. Do not edit the category list here without
# updating VALID_CATEGORIES above to match.
PROMPT_TEMPLATE = """
Você é um assistente especializado em análise de finanças pessoais.
Seu papel é **classificar transações financeiras** com base em sua descrição, valor e data.

Cada transação representa um gasto ou receita real feito por uma pessoa física, como você ou eu.

Escolha a **categoria mais adequada** para cada transação analisando o contexto do texto (descrição),
o valor e, se necessário, o padrão comum de comportamento financeiro.

Considere os seguintes grupos de categorias disponíveis:

🏠 Moradia → Aluguel, condomínio, contas de luz/água/gás, manutenção da casa
🍞 Alimentação → Restaurantes, cafés, delivery, padaria, lanches
🛒 Mercado → Supermercado, açougue, hortifruti, compras mensais
🚗 Transporte → Gasolina, Uber, ônibus, manutenção de carro ou moto
💡 Telefone → Plano de celular, internet, recarga
💰 Receitas → Salários, depósitos, transferências recebidas
💸 Transferência para terceiros → Envio de dinheiro para amigos, familiares, Pix
🧾 Compras → Eletrodomésticos, eletrônicos, roupas, itens de uso pessoal
📚 Educação → Mensalidades, cursos online, livros, materiais escolares
🏥 Saúde → Farmácia, exames, planos de saúde, médicos
📈 Investimento → Aporte em corretoras, fundos, Tesouro Direto, ações

Responda apenas com uma das categorias acima (exatamente como está escrita), sem explicações.

Agora, classifique a seguinte transação:
{text}
"""


def build_prompt(description: str) -> str:
    return PROMPT_TEMPLATE.format(text=description)


def normalize_classification(raw: str | None) -> str:
    """Display-layer normalization, moved here from the legacy app's UI
    layer (legacy_streamlit/modules/dashboard/streamlit_app.py:86-96) since
    there's no separate UI layer anymore -- the backend is the only place
    left to do it.

    - blank/NaN/None -> "Não classificado"
    - the classifier's own "Error" sentinel (a failed API call) -> "Erro na classificação"
    - NEW validation (authorized by the plan, not in the legacy app): any
      string that isn't one of the 11 approved labels also becomes "Erro na
      classificação" instead of being trusted verbatim -- the legacy app had
      zero enforcement that the LLM's raw output was actually a valid label.
    """
    cleaned = (raw or "").strip()
    if not cleaned:
        return NOT_CLASSIFIED
    if cleaned == "Error":
        return CLASSIFICATION_ERROR
    if cleaned not in VALID_CATEGORIES:
        return CLASSIFICATION_ERROR
    return cleaned
