"""Builds a TestClient over the *real* API surface wired to a stubbed, fully
offline sentinel graph and a freshly generated fixture account store
(docs/PLAN.md Phase 4).

Every LLM-backed piece is injected, so the whole create -> execute ->
get/stream path runs with no network and no key. Dependency overrides swap
the real graph, run store, and settings for the fixtures, so the background
task and the assertions read the same instances.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from fastapi.testclient import TestClient

from data.generate_accounts import generate_accounts_db
from sentinel.api import deps
from sentinel.api.main import app
from sentinel.graph.builder import SentinelGraph, build_sentinel_graph
from sentinel.graph.protocols import SpecialistChain, SupervisorReviewChain
from sentinel.settings import Settings
from sentinel.store.account_store import AccountStore
from sentinel.store.run_store import RunStore
from tests.fixtures.stub_chains import (
    AlwaysPassingReviewChain,
    FixedRouteChain,
    GroundedSpecialistChain,
    NoOpInjectionChain,
    NoOpLeakChain,
    StubEscalationChain,
)


@dataclass
class SentinelTestContext:
    client: TestClient
    run_store: RunStore
    account_store: AccountStore
    graph: SentinelGraph
    settings: Settings
    account_id: str
    pin: str


def build_sentinel_test_context(
    tmp_path: Path,
    *,
    route_specialist: str = "billing",
    specialist_chain: SpecialistChain | None = None,
    review_chain: SupervisorReviewChain | None = None,
) -> SentinelTestContext:
    accounts_db = tmp_path / "accounts.db"
    connection = sqlite3.connect(accounts_db)
    try:
        pins = generate_accounts_db(connection, seed=99)
    finally:
        connection.close()
    account_id, pin = next(iter(pins.items()))

    account_store = AccountStore(accounts_db)
    run_db = tmp_path / "runs.db"
    settings = Settings(run_store_path=str(run_db))

    chain = specialist_chain or GroundedSpecialistChain()
    graph = build_sentinel_graph(
        settings,
        account_store,
        injection_chain=NoOpInjectionChain(),
        leak_chain=NoOpLeakChain(),
        route_chain=FixedRouteChain(route_specialist),  # type: ignore[arg-type]
        network_chain=chain,
        billing_chain=chain,
        account_chain=chain,
        escalation_chain=StubEscalationChain(),
        review_chain=review_chain or AlwaysPassingReviewChain(),
    )
    run_store = RunStore(run_db)

    app.dependency_overrides[deps.get_sentinel_graph] = lambda: graph
    app.dependency_overrides[deps.get_run_store] = lambda: run_store
    app.dependency_overrides[deps.settings_dependency] = lambda: settings

    return SentinelTestContext(
        client=TestClient(app),
        run_store=run_store,
        account_store=account_store,
        graph=graph,
        settings=settings,
        account_id=account_id,
        pin=pin,
    )


def reset_sentinel_overrides() -> None:
    app.dependency_overrides.clear()
