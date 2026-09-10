"""Classificador determinístico (regras), rodando ANTES do LLM.

Achado real (auditoria 2026-09-02, prompt-mestre "Maestro + ANZ Finance"
§14): `classify_transactions` (service.py) sempre mandava TODAS as
descrições ao provedor de IA configurado -- nenhum caminho determinístico
existia, mesmo para padrões óbvios e inambíguos ("UBER", "NETFLIX",
"ALUGUEL", "IFOOD"). Isso contraria o princípio central do prompt: "Quando
uma classificação simples puder ser realizada por regras, faça por
regras. IA somente quando houver necessidade real de classificação
semântica."

Este módulo NÃO substitui o LLM -- reduz o volume que chega até ele.
`classify_by_rules` devolve `None` (não uma categoria genérica) sempre que
o padrão não é claramente inambíguo; `service.classify_transactions` trata
`None` como "manda pro provedor de IA". Uma regra errada é pior que
nenhuma regra (classificaria errado com confiança total), então as regras
abaixo são deliberadamente conservadoras -- termos de marca/palavra-chave
específicos o bastante para não colidir entre categorias, não uma
tentativa de cobrir 100% dos casos.

As 11 categorias e seus significados vêm exatamente de
`labels.PROMPT_TEMPLATE` (a mesma definição que o LLM já usa) -- nenhuma
taxonomia nova foi inventada aqui.
"""

from __future__ import annotations

import re
import unicodedata

from app.pipeline.categorizer.labels import VALID_CATEGORIES

# Ordem importa: a primeira categoria cujo conjunto de palavras-chave bate
# vence. Categorias mais específicas (ex.: "Investimento") vêm antes de
# categorias mais genéricas que poderiam colidir por acaso (ex.: um nome de
# banco também aparecer num padrão de "Transferência").
_RULES: tuple[tuple[str, tuple[str, ...]], tuple[str, tuple[str, ...]], ...] = (
    (
        "Investimento",
        (
            "tesouro direto", "tesouro nacional", "aplicacao rdb", "aplicacao cdb",
            "resgate cdb", "corretora", "clear corretora", "xp investimentos",
            "rico investimentos", "btg pactual", "nuinvest", "aplic financeira",
            "aplicacao automatica", "fundo de investimento", "tesouro selic",
        ),
    ),
    (
        "Transferência para terceiros",
        (
            "pix enviado", "ted enviado", "doc enviado", "transferencia enviada",
            "envio pix", "pix qr code enviado",
        ),
    ),
    (
        "Receitas",
        (
            "pix recebido", "ted recebido", "doc recebido", "transferencia recebida",
            "deposito em dinheiro", "salario", "folha de pagamento",
            "rendimento poupanca", "estorno",
        ),
    ),
    (
        "Moradia",
        (
            "condominio", "aluguel", "iptu", "cia de agua", "sabesp", "companhia de saneamento",
            "energia eletrica", "cemig", "enel", "light sa", "conta de luz", "conta de agua",
            "conta de gas", "comgas",
        ),
    ),
    (
        "Telefone",
        (
            "vivo s.a", "vivo sa", "claro sa", "claro s.a", "tim sa", "tim s.a",
            "oi telefonia", "recarga de celular", "net servicos", "internet fibra",
            "plano de internet",
        ),
    ),
    (
        "Transporte",
        (
            "uber do brasil", "uber trip", "99app", "99 tecnologia", "posto de gasolina",
            "posto shell", "posto ipiranga", "posto br", "petrobras distribuidora",
            "pedagio", "sem parar", "estacionamento", "bilhete unico", "metro sp",
            "combustivel",
        ),
    ),
    (
        "Alimentação",
        (
            "ifood", "rappi", "restaurante", "lanchonete", "padaria", "cafeteria",
            "starbucks", "mcdonalds", "burger king", "habib's", "habibs", "delivery de comida",
        ),
    ),
    (
        "Mercado",
        (
            "supermercado", "hipermercado", "atacadao", "carrefour", "extra hiper",
            "pao de acucar", "assai atacadista", "hortifruti", "acougue",
        ),
    ),
    (
        "Compras",
        (
            "mercado livre", "magazine luiza", "americanas.com", "shopee", "aliexpress",
            "amazon.com.br", "loja de roupas", "renner", "c&a", "riachuelo",
        ),
    ),
    (
        "Educação",
        (
            "mensalidade escolar", "mensalidade faculdade", "universidade", "colegio",
            "curso online", "udemy", "alura cursos", "material escolar", "livraria",
        ),
    ),
    (
        "Saúde",
        (
            "farmacia", "drogaria", "drogasil", "raia farmacias", "plano de saude",
            "unimed", "hospital", "laboratorio de exames", "consulta medica", "clinica medica",
        ),
    ),
)


def _normalize(text: str) -> str:
    """minúsculas + sem acento, pra `"Condomínio"`/`"CONDOMINIO"`/
    `"condominio"` casarem com o mesmo padrão -- mesma técnica já usada em
    `preprocess.py` pra normalizar texto de transação.

    Achado real durante a validação: descrições de transação de cartão vêm
    quase sempre com códigos de processadora entre as palavras
    (`"UBER   *TRIP HELP.UBER.COM"`, `"IFOOD *IFOOD.COM.BR"`) -- um padrão
    de 2 palavras como `"uber trip"` nunca batia contra
    `"uber   *trip..."` porque o `*`/espaços múltiplos quebravam a
    substring exata. Qualquer sequência de caracteres não-alfanuméricos
    vira um único espaço antes da comparação, então pontuação/símbolos
    nunca mais separam duas palavras que deveriam casar.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    lowered = without_accents.lower()
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


# Palavras-chave pré-normalizadas uma única vez no carregamento do módulo
# (não a cada chamada de `classify_by_rules`) -- a própria palavra-chave
# precisa passar pela mesma normalização que a descrição (ex.: "c&a" ->
# "c a", "habib's" -> "habib s", "amazon.com.br" -> "amazon com br"),
# senão pontuação dentro da palavra-chave em si nunca bateria contra a
# descrição já normalizada.
_NORMALIZED_RULES: tuple[tuple[str, tuple[str, ...]], ...] = tuple(
    (category, tuple(_normalize(keyword) for keyword in keywords)) for category, keywords in _RULES
)


def classify_by_rules(description: str) -> str | None:
    """Devolve uma das 11 categorias válidas se a descrição bater
    claramente com um padrão conhecido, senão `None` (o chamador deve
    então mandar essa descrição ao provedor de IA). Nunca devolve
    "Não classificado"/"Erro na classificação" -- esses são estados de
    `labels.normalize_classification`, não desta camada."""
    if not description or not description.strip():
        return None
    normalized = _normalize(description)
    for category, keywords in _NORMALIZED_RULES:
        for keyword in keywords:
            if keyword in normalized:
                return category
    return None


# Confirma em import-time que nenhuma regra aponta pra uma categoria fora
# do contrato oficial (labels.VALID_CATEGORIES) -- pega um erro de
# digitação na tabela acima na hora de carregar o módulo, não em produção.
assert all(category in VALID_CATEGORIES for category, _ in _RULES), (
    "classify_by_rules referencia uma categoria fora de VALID_CATEGORIES"
)
