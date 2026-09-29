"""The deterministic output check against a corpus written before it was extended
(D-A4-11). Measured behaviour must equal documented behaviour, including the leaks
the deterministic layer is designed to miss."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from data.generate_accounts import generate_accounts_db
from data.output_attacks import OutputCase, build_output_cases
from sentinel.guardrails.output_scanner import scan_output_deterministic
from sentinel.store.account_store import AccountStore


@pytest.fixture(scope="module")
def population(tmp_path_factory: pytest.TempPathFactory) -> tuple[AccountStore, dict[str, str]]:
    path = tmp_path_factory.mktemp("output-corpus") / "accounts.db"
    connection = sqlite3.connect(path)
    try:
        pins = generate_accounts_db(connection, seed=1)
    finally:
        connection.close()
    return AccountStore(Path(path)), pins


def _blocked(store: AccountStore, case: OutputCase) -> bool:
    return scan_output_deterministic(
        case.text,
        verified_account_id=case.verified_account_id,
        other_customer_names=store.other_customer_names(case.verified_account_id),
    ).blocked


def test_every_case_behaves_as_documented(
    population: tuple[AccountStore, dict[str, str]],
) -> None:
    store, pins = population
    wrong = [
        f"[{c.group}/{c.technique}] expected {c.expected}"
        for c in build_output_cases(store, pins)
        if _blocked(store, c) != (c.expected == "block")
    ]
    assert not wrong, wrong


def test_the_corpus_covers_every_group_and_documents_its_misses(
    population: tuple[AccountStore, dict[str, str]],
) -> None:
    cases = build_output_cases(*population)
    assert {c.group for c in cases} >= {"account_id", "name", "pin", "semantic", "benign"}
    assert sum(c.expected == "evade" for c in cases) >= 3
    assert sum(c.expected == "block" for c in cases) >= 15


def test_a_block_reason_never_quotes_the_leaked_value(
    population: tuple[AccountStore, dict[str, str]],
) -> None:
    """The verdict is streamed to the client; quoting the leak would be the leak."""
    store, pins = population
    for case in build_output_cases(store, pins):
        if case.expected != "block":
            continue
        verdict = scan_output_deterministic(
            case.text,
            verified_account_id=case.verified_account_id,
            other_customer_names=store.other_customer_names(case.verified_account_id),
        )
        ids = store.account_ids()
        names = [a.customer_name for i in ids if (a := store.get_account(i)) is not None]
        digits = [i.split("_")[1] for i in ids]
        reason = verdict.reason.casefold()
        for secret in [*ids, *digits, *names, *pins.values()]:
            assert secret.casefold() not in reason, (case.technique, secret)


def test_a_name_shared_with_another_customer_does_not_block_a_greeting(
    population: tuple[AccountStore, dict[str, str]],
) -> None:
    store, _ = population
    by_name: dict[str, list[str]] = {}
    for account_id in store.account_ids():
        account = store.get_account(account_id)
        assert account is not None
        by_name.setdefault(account.customer_name, []).append(account_id)
    shared = next((ids for ids in by_name.values() if len(ids) > 1), None)
    if shared is None:
        pytest.skip("fixture population has no shared name")
    caller = shared[0]
    name = store.get_account(caller).customer_name  # type: ignore[union-attr]

    verdict = scan_output_deterministic(
        f"Thanks, {name}. Your plan renews next month.",
        verified_account_id=caller,
        other_customer_names=store.other_customer_names(caller),
    )

    assert verdict.blocked is False


def test_policy_clause_text_is_not_blocked(
    population: tuple[AccountStore, dict[str, str]],
) -> None:
    """Specialists paraphrase the policy clauses, so the clause text is the best
    available proxy for a benign answer: a name or id check that fires on it would
    block ordinary replies."""
    from sentinel.store.policy_kb import get_policy_clauses

    store, _ = population
    caller = store.account_ids()[0]
    others = store.other_customer_names(caller)
    blocked = [
        clause.clause_id
        for clause in get_policy_clauses()
        if scan_output_deterministic(
            clause.body, verified_account_id=caller, other_customer_names=others
        ).blocked
    ]
    assert not blocked, blocked
