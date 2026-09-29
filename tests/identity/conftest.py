"""The identity gate and lockout (D-A4-9, D-A4-10)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.identity import IdentityGate, Lockout, LockoutPolicy
from sentinel.store.account_store import AccountStore
from sentinel.store.lockout_store import LockoutStore
from sentinel.store.pin_hash import FIXTURE_PEPPER


class Clock:
    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def lockout_db(tmp_path: Path) -> Path:
    return tmp_path / "identity.db"


def make_gate(accounts: AccountStore, lockout_db: Path, clock: Clock) -> IdentityGate:
    lockout = Lockout(LockoutStore(lockout_db), LockoutPolicy(), clock=clock)
    return IdentityGate(accounts, lockout, FIXTURE_PEPPER)


@pytest.fixture
def gate(account_store: AccountStore, lockout_db: Path, clock: Clock) -> IdentityGate:
    return make_gate(account_store, lockout_db, clock)


def wrong_pin(pin: str) -> str:
    return f"{(int(pin) + 1) % 10_000:04d}"
