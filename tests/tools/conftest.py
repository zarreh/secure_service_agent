from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from secureagent.retrieval.search import PolicyPassage
from secureagent.schemas.principal import UNVERIFIED, Principal
from secureagent.store import CustomerStore
from secureagent.store.ticket_store import TicketStore
from secureagent.tools import ScopedToolExecutor, ToolRegistry, build_registry

ALICE = "ACCT_1000"
BOB = "ACCT_1001"
RUN_ID = "run-under-test"


class FakePolicy:
    def search(self, query: str, *, limit: int) -> list[PolicyPassage]:
        return [
            PolicyPassage("refunds-and-credits", "Refunds and credits", "Reviewed in 5 days.", 1.0)
        ]


@pytest.fixture
def db(service_db: Path, tmp_path: Path) -> Path:
    """A private copy: tickets are written, and tests must not see each other's."""
    copy = tmp_path / "service.db"
    shutil.copy(service_db, copy)
    return copy


@pytest.fixture
def customers(db: Path) -> CustomerStore:
    return CustomerStore(db)


@pytest.fixture
def tickets(db: Path) -> TicketStore:
    return TicketStore(db, now=lambda: "2026-09-29T00:00:00+00:00")


@pytest.fixture
def registry(customers: CustomerStore, tickets: TicketStore) -> ToolRegistry:
    return build_registry(customers, tickets, FakePolicy())


@pytest.fixture
def executor(registry: ToolRegistry) -> ScopedToolExecutor:
    return ScopedToolExecutor(registry, now=lambda: "2026-09-29T00:00:00+00:00")


@pytest.fixture
def alice() -> Principal:
    return Principal(account_id=ALICE, verified=True, verified_at="2026-09-29T00:00:00+00:00")


@pytest.fixture
def unverified() -> Principal:
    return UNVERIFIED
