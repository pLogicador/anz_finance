"""Combines a provider's raw classification with the label-normalization
step -- the legacy app did this as two separate steps only because
Streamlit's UI layer used to own the normalization
(legacy_streamlit/modules/dashboard/streamlit_app.py:86-96). Here it's one
call since there's no separate UI layer left to own it.

Classificador de regras primeiro (2026-09-02, achado real -- prompt-mestre
"Maestro + ANZ Finance" §14): antes desta mudança TODA descrição ia direto
pro LLM, mesmo padrões óbvios como "UBER"/"NETFLIX"/"ALUGUEL". Agora
`classify_by_rules` (rules.py) resolve o que conseguir determinar sozinho;
só o restante (o que não bateu com nenhuma regra) é mandado ao provedor de
IA configurado -- reduz chamadas reais ao LLM sem mudar a assinatura desta
função nem o contrato de `AIProvider`.
"""

from __future__ import annotations

from app.pipeline.categorizer.base import AIProvider
from app.pipeline.categorizer.labels import normalize_classification
from app.pipeline.categorizer.rules import classify_by_rules


async def classify_transactions(provider: AIProvider, descriptions: list[str]) -> list[str]:
    results: list[str | None] = [classify_by_rules(description) for description in descriptions]

    unresolved_indices = [i for i, result in enumerate(results) if result is None]
    if unresolved_indices:
        raw = await provider.classify([descriptions[i] for i in unresolved_indices])
        for position, index in enumerate(unresolved_indices):
            results[index] = normalize_classification(raw[position])

    # Por construção, todo item ou veio de uma regra (já uma categoria
    # válida) ou foi preenchido pelo loop acima -- nunca deveria sobrar
    # `None`. `assert` em vez de filtrar silenciosamente: um `None`
    # sobrevivente indicaria um bug de índice acima, e filtrar mudaria o
    # tamanho/ordem da lista devolvida, quebrando o contrato de
    # `AIProvider.classify` ("mesma ordem, mesmo tamanho") de um jeito
    # difícil de notar (a lista só ficaria mais curta, sem erro nenhum).
    assert all(result is not None for result in results)
    return results  # type: ignore[return-value]
