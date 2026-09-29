"""Identity gate behaviour: what a caller can and cannot learn, and what an
attacker can and cannot do (D-A4-9, D-A4-10)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pytest

import sentinel.store.pin_hash as pin_module
from sentinel.identity import IdentityGate, Lockout, LockoutPolicy
from sentinel.store.account_store import AccountStore

from .conftest import Clock, make_gate, wrong_pin


@pytest.fixture
def alice_bob(known_pins: dict[str, str]) -> tuple[tuple[str, str], tuple[str, str]]:
    items = list(known_pins.items())
    return items[0], items[1]


def test_the_correct_pin_verifies(gate: IdentityGate, known_pins: dict[str, str]) -> None:
    account_id, pin = next(iter(known_pins.items()))
    result = gate.verify(account_id, pin, client="c1")
    assert result.verified and not result.locked


def test_a_wrong_pin_does_not_verify(gate: IdentityGate, known_pins: dict[str, str]) -> None:
    account_id, pin = next(iter(known_pins.items()))
    result = gate.verify(account_id, wrong_pin(pin), client="c1")
    assert not result.verified and not result.locked
    assert result.attempts_remaining == 2


def test_a_missing_account_is_indistinguishable_from_a_wrong_pin_at_every_step(
    gate: IdentityGate, known_pins: dict[str, str]
) -> None:
    """The whole response sequence matches, not only the first reply: attempts
    remaining, locked and retry-after all count down identically."""
    account_id, pin = next(iter(known_pins.items()))
    for attempt in range(6):
        missing = gate.verify("ACCT_9999", "1234", client=f"m{attempt % 2}")
        real = gate.verify(account_id, wrong_pin(pin), client=f"r{attempt % 2}")
        assert missing.model_dump() == real.model_dump(), attempt


@pytest.mark.parametrize("pin", ["", "12", "abcd", "١٢٣٤", "1234 ", "12345"])
def test_a_malformed_pin_is_simply_not_verified(
    gate: IdentityGate, known_pins: dict[str, str], pin: str
) -> None:
    assert not gate.verify(next(iter(known_pins)), pin, client="c1").verified


def test_three_free_attempts_then_throttled(gate: IdentityGate, known_pins: dict[str, str]) -> None:
    account_id, pin = next(iter(known_pins.items()))
    for remaining in (2, 1):
        result = gate.verify(account_id, wrong_pin(pin), client="c1")
        assert (result.locked, result.attempts_remaining) == (False, remaining)
    third = gate.verify(account_id, wrong_pin(pin), client="c1")
    assert third.locked and third.attempts_remaining == 0
    assert third.retry_after_seconds > 0


def test_the_correct_pin_is_also_refused_while_throttled(
    gate: IdentityGate, known_pins: dict[str, str]
) -> None:
    """Otherwise lockout only stops honest guessers who happen to be wrong."""
    account_id, pin = next(iter(known_pins.items()))
    for _ in range(3):
        gate.verify(account_id, wrong_pin(pin), client="c1")
    result = gate.verify(account_id, pin, client="c1")
    assert not result.verified and result.locked


def test_backoff_lifts_after_the_delay(
    gate: IdentityGate, known_pins: dict[str, str], clock: Clock
) -> None:
    account_id, pin = next(iter(known_pins.items()))
    for _ in range(3):
        gate.verify(account_id, wrong_pin(pin), client="c1")
    assert gate.verify(account_id, pin, client="c1").locked
    clock.now += 31
    assert gate.verify(account_id, pin, client="c1").verified


def test_a_stranger_cannot_lock_a_customer_out_for_good(
    gate: IdentityGate, known_pins: dict[str, str], clock: Clock
) -> None:
    """The old counter locked an account permanently after three wrong PINs, with no
    reset path: anyone could deny a customer service forever."""
    account_id, pin = next(iter(known_pins.items()))
    for _ in range(10):
        gate.verify(account_id, wrong_pin(pin), client="stranger")
    clock.now += 900
    assert gate.verify(account_id, pin, client="customer").verified


def test_backoff_grows_exponentially_to_a_ceiling() -> None:
    policy = LockoutPolicy()
    delays = [policy.delay_after(n) for n in range(0, 12)]
    assert delays[:3] == [0.0, 0.0, 0.0]
    assert delays[3] == 30.0 and delays[4] == 60.0 and delays[5] == 120.0
    assert max(delays) == policy.max_delay_seconds == 900.0
    assert delays == sorted(delays)


def test_lockout_survives_a_restart(
    account_store: AccountStore, lockout_db: Path, known_pins: dict[str, str], clock: Clock
) -> None:
    account_id, pin = next(iter(known_pins.items()))
    first = make_gate(account_store, lockout_db, clock)
    for _ in range(3):
        first.verify(account_id, wrong_pin(pin), client="c1")
    restarted = make_gate(account_store, lockout_db, clock)  # new process, same database
    assert restarted.verify(account_id, pin, client="c1").locked


def test_rotating_accounts_from_one_client_is_throttled_by_the_client_key(
    gate: IdentityGate, known_pins: dict[str, str]
) -> None:
    """Keying only on account would let an attacker spread guesses across accounts."""
    accounts = list(known_pins.items())
    for account_id, pin in accounts[2:5]:
        gate.verify(account_id, wrong_pin(pin), client="attacker")
    target, target_pin = accounts[5]
    assert gate.verify(target, target_pin, client="attacker").locked
    assert gate.verify(target, target_pin, client="someone-else").verified


def test_a_success_does_not_reset_the_clients_failure_count(
    gate: IdentityGate, alice_bob: tuple[tuple[str, str], tuple[str, str]]
) -> None:
    """Otherwise an attacker holding one valid account alternates it with guesses."""
    (alice, alice_pin), (bob, bob_pin) = alice_bob
    gate.verify(bob, wrong_pin(bob_pin), client="attacker")
    gate.verify(bob, wrong_pin(bob_pin), client="attacker")
    assert gate.verify(alice, alice_pin, client="attacker").verified
    gate.verify(bob, wrong_pin(bob_pin), client="attacker")  # the client's third failure
    assert gate.verify(alice, alice_pin, client="attacker").locked


def test_a_successful_login_clears_that_accounts_own_counter(
    gate: IdentityGate, known_pins: dict[str, str]
) -> None:
    account_id, pin = next(iter(known_pins.items()))
    gate.verify(account_id, wrong_pin(pin), client="c1")
    gate.verify(account_id, wrong_pin(pin), client="c1")
    assert gate.verify(account_id, pin, client="c1").verified
    gate.verify(account_id, wrong_pin(pin), client="c2")
    gate.verify(account_id, wrong_pin(pin), client="c2")
    assert not gate.verify(account_id, wrong_pin(pin), client="c2").verified


def test_every_unverified_path_costs_one_key_derivation(
    gate: IdentityGate, known_pins: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Timing tests are flaky; the cause is not. A missing account, a malformed PIN
    and a wrong PIN each perform exactly one derivation, so none is faster than the
    others and none reveals whether an account exists."""
    account_id, pin = next(iter(known_pins.items()))
    calls: list[int] = []
    real = pin_module._derive

    def counting(*args: Any, **kwargs: Any) -> bytes:
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(pin_module, "_derive", counting)

    def derivations(account: str, attempt: str, client: str) -> int:
        calls.clear()
        gate.verify(account, attempt, client=client)
        return len(calls)

    assert derivations("ACCT_9999", "1234", "a") == 1
    assert derivations(account_id, "abcd", "b") == 1
    assert derivations(account_id, wrong_pin(pin), "c") == 1
    assert derivations(account_id, pin, "d") == 1


def test_parallel_guesses_cannot_outrun_the_throttle(
    gate: IdentityGate, known_pins: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Read-check-write on the counters must be atomic: N parallel requests must not
    all pass the throttle check before the first failure is recorded."""
    account_id, pin = next(iter(known_pins.items()))
    derivations: list[int] = []
    real = pin_module._derive

    def counting(*args: Any, **kwargs: Any) -> bytes:
        derivations.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(pin_module, "_derive", counting)

    threads = [
        threading.Thread(
            target=gate.verify, args=(account_id, wrong_pin(pin)), kwargs={"client": "x"}
        )
        for _ in range(10)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(derivations) == 3  # the free attempts; the other seven were throttled


def test_the_gate_requires_a_pepper(account_store: AccountStore, lockout_db: Path) -> None:
    from sentinel.store.lockout_store import LockoutStore

    with pytest.raises(ValueError):
        IdentityGate(account_store, Lockout(LockoutStore(lockout_db)), "")
