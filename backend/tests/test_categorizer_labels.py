from __future__ import annotations

import pytest

from app.pipeline.categorizer.labels import (
    CLASSIFICATION_ERROR,
    NOT_CLASSIFIED,
    VALID_CATEGORIES,
    normalize_classification,
)


def test_the_11_category_labels_are_exact() -> None:
    """Verbatim contract -- must not drift, anything downstream keys off these exact strings."""
    assert VALID_CATEGORIES == (
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


@pytest.mark.parametrize("raw", VALID_CATEGORIES)
def test_a_valid_label_passes_through_unchanged(raw: str) -> None:
    assert normalize_classification(raw) == raw


@pytest.mark.parametrize("raw", [None, "", "   ", "\t\n"])
def test_blank_or_missing_becomes_not_classified(raw: str | None) -> None:
    assert normalize_classification(raw) == NOT_CLASSIFIED


def test_the_error_sentinel_becomes_classification_error() -> None:
    assert normalize_classification("Error") == CLASSIFICATION_ERROR


@pytest.mark.parametrize(
    "raw",
    [
        "moradia",  # wrong case
        "Alimentacao",  # missing accent
        "Something the LLM made up",
        "Moradia extra text",
    ],
)
def test_unrecognized_label_is_treated_as_classification_error(raw: str) -> None:
    """NEW validation authorized by the plan: the legacy app trusted the
    LLM's raw output verbatim with zero enforcement it was one of the 11
    labels. Anything outside the approved set now maps to the same
    "Erro na classificação" fallback as an outright API failure, rather
    than polluting charts/filters with an unrecognized label."""
    assert normalize_classification(raw) == CLASSIFICATION_ERROR
