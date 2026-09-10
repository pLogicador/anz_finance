"""Deterministic balance validation (prompt-mestre "Maestro + ANZ Finance"
§17): ``SUM(transactions of an account)`` vs. the LEDGERBAL that account's
OFX statement reported. No LLM involved -- same rationale as
``metrics.py``/``insights.py``/``analysis.py``, all already audited
(``CLAUDE.md`` Fase 9) as the only deterministic layer in this pipeline.

**Real limitation, documented rather than hidden (the prompt-mestre's own
"não esconder o problema" applied to the check's own scope, not just to a
numeric mismatch)**: OFX's LEDGERBAL is a point-in-time balance as of the
statement's ``DTASOF``, not "the sum of the transactions in this file" --
reconciling it properly requires an *opening* balance too, which
``ofxparse`` does not expose (confirmed reading the installed library's
source: ``Statement`` only ever gets ``balance``/``available_balance`` set
dynamically, never an opening balance). This module computes
``SUM(every transaction uploaded so far for that account, across every
file in the current session)`` against the *most recently uploaded*
file's reported LEDGERBAL for that account -- which is only a true
reconciliation if the uploaded statements together cover that account's
entire history since it opened at a zero balance. When that assumption
doesn't hold (the far more common case -- someone uploads just this
month's statement), a real, legitimate divergence is expected and does
NOT by itself mean the data is wrong. `AccountBalanceCheck.assumption` is
returned specifically so any caller (API response, dashboard) surfaces
that caveat honestly instead of presenting a mismatch as proof of a
parsing bug or missing transactions.

Tolerance: the prompt-mestre specifies none, only "detectar; registrar;
informar; não esconder o problema" -- 1 cent (0.01) is used here to
absorb float rounding in the parsed amounts, not as a real business
tolerance. A real divergence beyond that is always surfaced, never
silently corrected or hidden.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.pipeline.ofx_parser import AccountBalance

TOLERANCE = 0.01

ASSUMPTION_NOTE = (
    "Este cálculo soma todas as transações desta conta enviadas nesta sessão e compara "
    "com o saldo informado no extrato mais recente. Só é uma validação exata se os "
    "extratos enviados cobrirem todo o histórico da conta desde a abertura (saldo "
    "inicial zero) -- se você enviou só um período parcial, uma diferença aqui é "
    "esperada e não significa necessariamente um problema nos dados."
)


@dataclass
class AccountBalanceCheck:
    account: str
    reported_balance: float
    computed_balance: float
    difference: float
    matches: bool
    source_filename: str
    assumption: str = ASSUMPTION_NOTE


def validate_balance(df: pd.DataFrame, account_balances: list[AccountBalance]) -> list[AccountBalanceCheck]:
    """One check per account that has a reported LEDGERBAL -- an account
    with no reported balance (not every OFX file includes one) simply
    doesn't appear here, it's not treated as a mismatch. When an account
    has more than one reported balance (multiple files uploaded for the
    same account), the most recently uploaded one is used -- it's the
    most likely to reflect the account's current state.
    """
    if not account_balances:
        return []

    sums_by_account: dict[str, float] = {}
    if not df.empty and "Conta" in df.columns:
        sums_by_account = df.groupby("Conta")["Valor"].sum().to_dict()

    latest_balance_by_account: dict[str, AccountBalance] = {}
    for balance in account_balances:
        latest_balance_by_account[balance.account] = balance  # last one wins -- upload order

    checks: list[AccountBalanceCheck] = []
    for balance in latest_balance_by_account.values():
        computed = float(sums_by_account.get(balance.account, 0.0))
        difference = computed - balance.reported_balance
        checks.append(
            AccountBalanceCheck(
                account=balance.account,
                reported_balance=balance.reported_balance,
                computed_balance=computed,
                difference=difference,
                matches=abs(difference) <= TOLERANCE,
                source_filename=balance.source_filename,
            )
        )
    return checks
