"""The synthetic data generator: deterministic, fictional, and free of plaintext PINs."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from data.generate_synthetic import (
    FIXTURE_PEPPER,
    POISONED_MEMORY_ID,
    demo_pin,
    generate,
)
from secureagent.identity.pin import verify_pin
from tests.conftest import ACCOUNTS


def _dump(path: Path) -> list[str]:
    connection = sqlite3.connect(path)
    try:
        return list(connection.iterdump())
    finally:
        connection.close()


def test_generation_is_deterministic(service_db: Path, tmp_path: Path) -> None:
    again = tmp_path / "again.db"
    generate(again, accounts=ACCOUNTS)
    assert _dump(again) == _dump(service_db)


def test_counts(service_db: Path) -> None:
    connection = sqlite3.connect(service_db)
    assert connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == ACCOUNTS
    assert connection.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0] == ACCOUNTS
    assert connection.execute("SELECT COUNT(*) FROM bills").fetchone()[0] == ACCOUNTS * 3


def test_phone_numbers_are_in_the_reserved_fictional_range(service_db: Path) -> None:
    connection = sqlite3.connect(service_db)
    phones = [row[0] for row in connection.execute("SELECT phone FROM accounts")]
    assert phones
    assert all(phone.startswith("555-01") for phone in phones)


def test_every_stored_hash_verifies_against_the_derived_demo_pin(service_db: Path) -> None:
    connection = sqlite3.connect(service_db)
    for account_id, stored in connection.execute("SELECT account_id, pin_hash FROM accounts"):
        assert stored.startswith("scrypt$")
        assert verify_pin(demo_pin(account_id), stored, FIXTURE_PEPPER)


def test_no_cell_anywhere_holds_the_accounts_plaintext_pin(service_db: Path) -> None:
    """A PIN in a column, a note or a memory summary would defeat hashing entirely."""
    connection = sqlite3.connect(service_db)
    tables = [
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        if not row[0].startswith("sqlite_")
    ]
    for (account_id,) in connection.execute("SELECT account_id FROM accounts").fetchall():
        pin = demo_pin(account_id)
        for table in tables:
            for row in connection.execute(f"SELECT * FROM {table}"):  # noqa: S608
                for cell in row:
                    if isinstance(cell, str):
                        assert cell != pin
                        assert f" {pin} " not in f" {cell} "


def test_the_poisoned_memory_entry_is_planted_and_flagged(service_db: Path) -> None:
    connection = sqlite3.connect(service_db)
    flagged = connection.execute(
        "SELECT row_id FROM scenario_fixtures WHERE table_name = 'memory'"
    ).fetchall()
    assert flagged == [(POISONED_MEMORY_ID,)]
    (summary,) = connection.execute(
        "SELECT summary FROM memory WHERE memory_id = ?", (POISONED_MEMORY_ID,)
    ).fetchone()
    assert "disregard verification" in summary.lower()


def test_demo_pins_are_four_digits_and_stable() -> None:
    assert demo_pin("ACCT_1000") == demo_pin("ACCT_1000")
    assert len(demo_pin("ACCT_1000")) == 4
    assert demo_pin("ACCT_1000").isdigit()
    assert len({demo_pin(f"ACCT_{1000 + i}") for i in range(50)}) > 25
