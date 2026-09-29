from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from data.generate_synthetic import FIXTURE_PEPPER, demo_pin
from secureagent.identity import IdentityGate, Lockout, LockoutPolicy
from secureagent.store import CredentialStore
from secureagent.store.lockout_store import LockoutStore

ALICE, BOB = "ACCT_1000", "ACCT_1001"


class Clock:
    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def db(service_db: Path, tmp_path: Path) -> Path:
    copy = tmp_path / "service.db"
    shutil.copy(service_db, copy)
    return copy


@pytest.fixture
def clock() -> Clock:
    return Clock()


def make_gate(db: Path, clock: Clock) -> IdentityGate:
    lockout = Lockout(LockoutStore(db), LockoutPolicy(), clock=clock)
    return IdentityGate(
        CredentialStore(db), lockout, FIXTURE_PEPPER, now=lambda: "2026-09-29T00:00:00+00:00"
    )


@pytest.fixture
def gate(db: Path, clock: Clock) -> IdentityGate:
    return make_gate(db, clock)


def wrong_pin(account_id: str) -> str:
    pin = demo_pin(account_id)
    return f"{(int(pin) + 1) % 10_000:04d}"
