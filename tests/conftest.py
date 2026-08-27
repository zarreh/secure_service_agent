from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from data.generate_accounts import generate_accounts_db
from sentinel.store.account_store import AccountStore


@pytest.fixture(scope="session")
def accounts_fixture(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, str]]:
    path = tmp_path_factory.mktemp("fixture-stores") / "accounts.db"
    connection = sqlite3.connect(path)
    try:
        pins = generate_accounts_db(connection, seed=1)
    finally:
        connection.close()
    return path, pins


@pytest.fixture
def accounts_db_path(accounts_fixture: tuple[Path, dict[str, str]]) -> Path:
    return accounts_fixture[0]


@pytest.fixture
def known_pins(accounts_fixture: tuple[Path, dict[str, str]]) -> dict[str, str]:
    """`{account_id: plaintext_pin}` for the fixture population — exists only
    in test memory, never in the store (docs/PLAN.md Phase 1/2)."""
    return accounts_fixture[1]


@pytest.fixture
def account_store(accounts_db_path: Path) -> Iterator[AccountStore]:
    store = AccountStore(accounts_db_path)
    yield store
    store.close()
