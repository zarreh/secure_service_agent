"""Store isolation: what a customer-facing read can and cannot return."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from secureagent.store import DEFAULT_ROW_CAP, CredentialStore, CustomerStore


@pytest.fixture
def store(service_db: Path) -> CustomerStore:
    return CustomerStore(service_db)


def test_an_account_read_carries_no_credential(store: CustomerStore) -> None:
    account = store.account("ACCT_1000")
    assert account is not None
    assert not any("pin" in name for name in vars(account))
    assert "scrypt" not in repr(account)


def test_reads_are_scoped_to_the_requested_account(store: CustomerStore) -> None:
    for bill in store.bills("ACCT_1002"):
        assert bill.account_id == "ACCT_1002"
    subscription = store.subscription("ACCT_1002")
    assert subscription is not None and subscription.account_id == "ACCT_1002"


def test_an_unknown_account_reads_nothing(store: CustomerStore) -> None:
    assert store.account("ACCT_9999") is None
    assert store.subscription("ACCT_9999") is None
    assert store.bills("ACCT_9999") == []
    assert store.memory("ACCT_9999") == []


def test_reads_are_capped_even_when_a_caller_asks_for_more(store: CustomerStore) -> None:
    assert len(store.bills("ACCT_1000", limit=10_000)) <= DEFAULT_ROW_CAP
    assert len(store.bills("ACCT_1000", limit=1)) == 1


def test_outages_are_public_and_keyed_by_region(store: CustomerStore) -> None:
    outages = store.outages("North Ridge")
    assert outages and all(outage.region == "North Ridge" for outage in outages)


def test_the_customer_store_is_read_only(service_db: Path) -> None:
    """A tool that reached the connection still could not change a record."""
    connection = CustomerStore(service_db)._connection  # noqa: SLF001
    with pytest.raises(sqlite3.OperationalError):
        connection.execute("UPDATE accounts SET status = 'active'")


def test_there_is_no_way_to_read_a_credential_through_the_customer_store(
    store: CustomerStore,
) -> None:
    public = [name for name in dir(store) if not name.startswith("_")]
    assert not any("pin" in name or "credential" in name or "hash" in name for name in public)


def test_only_the_credential_store_returns_a_hash(service_db: Path) -> None:
    credentials = CredentialStore(service_db)
    stored = credentials.pin_hash("ACCT_1000")
    assert stored is not None and stored.startswith("scrypt$")
    assert credentials.pin_hash("ACCT_9999") is None
