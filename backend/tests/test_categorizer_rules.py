"""Achado real (2026-09-02, prompt-mestre "Maestro + ANZ Finance" §14):
`classify_transactions` mandava toda descrição pro LLM, mesmo padrões
óbvios. Este arquivo cobre o classificador de regras novo (rules.py) e o
merge em service.py (regra primeiro, LLM só pro que sobrar)."""

from __future__ import annotations

import pytest

from app.pipeline.categorizer.labels import VALID_CATEGORIES
from app.pipeline.categorizer.rules import classify_by_rules
from app.pipeline.categorizer.service import classify_transactions


class _RecordingProvider:
    """Fake AIProvider que grava exatamente quais descrições recebeu --
    prova que o merge só manda ao "LLM" o que as regras não resolveram."""

    def __init__(self, label: str = "Compras") -> None:
        self.label = label
        self.received: list[str] | None = None

    async def classify(self, descriptions: list[str]) -> list[str]:
        self.received = list(descriptions)
        return [self.label] * len(descriptions)

    async def test_connection(self) -> bool:
        return True

    async def complete(self, *, system: str, user: str) -> str:
        raise NotImplementedError


@pytest.mark.parametrize(
    "description,expected_category",
    [
        ("UBER   *TRIP HELP.UBER.COM", "Transporte"),
        ("PIX RECEBIDO - JOAO DA SILVA", "Receitas"),
        ("PIX ENVIADO - MARIA SOUZA", "Transferência para terceiros"),
        ("IFOOD *IFOOD.COM.BR", "Alimentação"),
        ("SUPERMERCADO EXTRA LTDA", "Mercado"),
        ("CONDOMINIO EDIFICIO CENTRAL", "Moradia"),
        ("VIVO S.A. RECARGA", "Telefone"),
        ("DROGARIA SAO PAULO FILIAL 12", "Saúde"),
        ("MENSALIDADE ESCOLAR COLEGIO SANTA FE", "Educação"),
        ("MERCADO LIVRE COMPRA 998877", "Compras"),
        ("APLICACAO AUTOMATICA CDB", "Investimento"),
        # Acentuação/caixa não deveriam importar.
        ("condomínio edifício jardins", "Moradia"),
    ],
)
def test_classify_by_rules_recognizes_unambiguous_patterns(description, expected_category):
    assert classify_by_rules(description) == expected_category
    assert expected_category in VALID_CATEGORIES


@pytest.mark.parametrize(
    "description",
    [
        "",
        "   ",
        "TRANSFERENCIA 998877",  # genérico demais -- não bate com nenhuma palavra-chave
        "PAGAMENTO DIVERSOS LTDA",
        "COMPRA CARTAO 04/09",
    ],
)
def test_classify_by_rules_returns_none_for_ambiguous_descriptions(description):
    assert classify_by_rules(description) is None


@pytest.mark.asyncio
async def test_classify_transactions_only_sends_unresolved_descriptions_to_the_provider():
    provider = _RecordingProvider(label="Compras")
    descriptions = ["UBER *TRIP", "PAGAMENTO DIVERSOS LTDA", "IFOOD *IFOOD.COM.BR", "XYZ LOJA DESCONHECIDA"]

    results = await classify_transactions(provider, descriptions)

    assert results == ["Transporte", "Compras", "Alimentação", "Compras"]
    # Só as 2 descrições que as regras não resolveram deveriam ter ido ao provedor.
    assert provider.received == ["PAGAMENTO DIVERSOS LTDA", "XYZ LOJA DESCONHECIDA"]


@pytest.mark.asyncio
async def test_classify_transactions_never_calls_the_provider_when_every_description_is_resolved_by_rules():
    """Teste de custo (prompt-mestre §80): quando toda descrição bate com
    uma regra determinística, zero chamadas ao provedor de IA."""
    provider = _RecordingProvider()
    descriptions = ["UBER *TRIP", "SUPERMERCADO EXTRA", "CONDOMINIO EDIFICIO X"]

    results = await classify_transactions(provider, descriptions)

    assert results == ["Transporte", "Mercado", "Moradia"]
    assert provider.received is None  # `classify` nunca foi chamado


@pytest.mark.asyncio
async def test_classify_transactions_preserves_order_and_length_with_mixed_input():
    provider = _RecordingProvider(label="Erro na classificação")
    descriptions = ["a" * 0 or "??? desconhecido 1", "UBER *TRIP", "??? desconhecido 2", "IFOOD *X"]

    results = await classify_transactions(provider, descriptions)

    assert len(results) == len(descriptions)
    assert results[1] == "Transporte"
    assert results[3] == "Alimentação"
