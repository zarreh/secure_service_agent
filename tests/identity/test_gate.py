"""The identity gate and lockout (docs/PLAN.md §5.2, §13 gates 3 and 4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from data.generate_synthetic import demo_pin
from secureagent.identity import IdentityGate, LockoutPolicy

from .conftest import ALICE, BOB, Clock, make_gate, wrong_pin


def test_the_correct_pin_yields_a_verified_principal(gate: IdentityGate) -> None:
    result = gate.verify(ALICE, demo_pin(ALICE), client="c1")
    assert result.reason == "verified"
    assert result.principal.verified and result.principal.account_id == ALICE


def test_a_wrong_pin_yields_an_unverified_principal_with_no_account(gate: IdentityGate) -> None:
    result = gate.verify(ALICE, wrong_pin(ALICE), client="c1")
    assert result.reason == "not_verified"
    assert not result.principal.verified and result.principal.account_id is None


def test_a_missing_account_is_indistinguishable_from_a_wrong_pin(gate: IdentityGate) -> None:
    missing = gate.verify("ACCT_9999", "1234", client="c1")
    wrong = gate.verify(ALICE, wrong_pin(ALICE), client="c2")
    assert (missing.reason, missing.principal) == (wrong.reason, wrong.principal)


@pytest.mark.parametrize("pin", ["", "12", "abcd", "١٢٣٤", "1234 ", "12345"])
def test_a_malformed_pin_is_simply_not_verified(gate: IdentityGate, pin: str) -> None:
    assert gate.verify(ALICE, pin, client="c1").reason == "not_verified"


def test_three_free_attempts_then_throttled(gate: IdentityGate, clock: Clock) -> None:
    for _ in range(3):
        assert gate.verify(ALICE, wrong_pin(ALICE), client="c1").reason == "not_verified"
    blocked = gate.verify(ALICE, wrong_pin(ALICE), client="c1")
    assert blocked.reason == "throttled" and blocked.retry_after_seconds > 0


def test_the_correct_pin_is_also_refused_while_throttled(gate: IdentityGate) -> None:
    """Otherwise lockout only stops honest guessers who happen to be wrong."""
    for _ in range(3):
        gate.verify(ALICE, wrong_pin(ALICE), client="c1")
    assert gate.verify(ALICE, demo_pin(ALICE), client="c1").reason == "throttled"


def test_backoff_lifts_after_the_delay(gate: IdentityGate, clock: Clock) -> None:
    for _ in range(3):
        gate.verify(ALICE, wrong_pin(ALICE), client="c1")
    assert gate.verify(ALICE, demo_pin(ALICE), client="c1").reason == "throttled"
    clock.now += 31
    assert gate.verify(ALICE, demo_pin(ALICE), client="c1").reason == "verified"


def test_backoff_grows_exponentially_to_a_ceiling() -> None:
    policy = LockoutPolicy()
    delays = [policy.delay_after(n) for n in range(0, 12)]
    assert delays[:3] == [0.0, 0.0, 0.0]
    assert delays[3] == 30.0 and delays[4] == 60.0 and delays[5] == 120.0
    assert max(delays) == policy.max_delay_seconds == 900.0
    assert delays == sorted(delays)


def test_lockout_survives_a_restart(db: Path, clock: Clock) -> None:
    """The source kept counters in memory: restarting reset an attacker's progress."""
    first = make_gate(db, clock)
    for _ in range(3):
        first.verify(ALICE, wrong_pin(ALICE), client="c1")
    restarted = make_gate(db, clock)  # a new process, same database
    assert restarted.verify(ALICE, demo_pin(ALICE), client="c1").reason == "throttled"


def test_a_missing_account_locks_out_like_a_real_one(gate: IdentityGate) -> None:
    """If only real accounts throttled, throttling itself would reveal which exist."""
    for _ in range(3):
        gate.verify("ACCT_9999", "1234", client="c1")
    assert gate.verify("ACCT_9999", "1234", client="c1").reason == "throttled"


def test_rotating_accounts_from_one_client_is_throttled_by_the_client_key(
    gate: IdentityGate,
) -> None:
    """The source keyed only on account, so an attacker could spread guesses."""
    for account in ("ACCT_1002", "ACCT_1003", "ACCT_1004"):
        gate.verify(account, wrong_pin(account), client="attacker")
    assert gate.verify("ACCT_1005", demo_pin("ACCT_1005"), client="attacker").reason == "throttled"
    # A different client is unaffected.
    assert (
        gate.verify("ACCT_1005", demo_pin("ACCT_1005"), client="someone-else").reason == "verified"
    )


def test_a_success_does_not_reset_the_clients_failure_count(gate: IdentityGate) -> None:
    """Otherwise an attacker with one valid account alternates it with guesses."""
    gate.verify(BOB, wrong_pin(BOB), client="attacker")
    gate.verify(BOB, wrong_pin(BOB), client="attacker")
    assert gate.verify(ALICE, demo_pin(ALICE), client="attacker").reason == "verified"
    gate.verify(BOB, wrong_pin(BOB), client="attacker")  # the client's third failure
    assert gate.verify(ALICE, demo_pin(ALICE), client="attacker").reason == "throttled"


def test_a_successful_login_clears_that_accounts_own_counter(gate: IdentityGate) -> None:
    gate.verify(ALICE, wrong_pin(ALICE), client="c1")
    gate.verify(ALICE, wrong_pin(ALICE), client="c1")
    assert gate.verify(ALICE, demo_pin(ALICE), client="c1").reason == "verified"
    # Two more failures would have been the fourth and fifth without the reset.
    gate.verify(ALICE, wrong_pin(ALICE), client="c2")
    gate.verify(ALICE, wrong_pin(ALICE), client="c2")
    assert gate.verify(ALICE, wrong_pin(ALICE), client="c2").reason == "not_verified"


def test_every_unverified_path_costs_one_key_derivation(
    gate: IdentityGate, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Timing tests are flaky; the cause is not. A missing account, a malformed PIN and
    a wrong PIN each perform exactly one derivation, so none is faster than the others
    and none reveals whether an account exists."""
    import secureagent.identity.pin as pin_module

    calls: list[int] = []
    real = pin_module._derive

    def counting(*args: Any, **kwargs: Any) -> bytes:
        calls.append(1)
        result: bytes = real(*args, **kwargs)
        return result

    monkeypatch.setattr(pin_module, "_derive", counting)

    def derivations(account: str, pin: str, client: str) -> int:
        calls.clear()
        gate.verify(account, pin, client=client)
        return len(calls)

    assert derivations("ACCT_9999", "1234", "a") == 1  # missing account
    assert derivations(ALICE, "abcd", "b") == 1  # malformed PIN
    assert derivations(ALICE, wrong_pin(ALICE), "c") == 1  # wrong PIN
    assert derivations(ALICE, demo_pin(ALICE), "d") == 1  # right PIN, for comparison


def test_the_gate_requires_a_pepper(db: Path, clock: Clock) -> None:
    from secureagent.identity import Lockout
    from secureagent.store import CredentialStore
    from secureagent.store.lockout_store import LockoutStore

    with pytest.raises(ValueError):
        IdentityGate(CredentialStore(db), Lockout(LockoutStore(db), clock=clock), "")
