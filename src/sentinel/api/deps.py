"""FastAPI dependencies: process-shared singletons for the stores and the
compiled graphs (docs/PLAN.md Phase 4).

Everything here is `lru_cache`d so a connection or a compiled graph is opened
once and injected, never rebuilt per request. `sentinel`'s graph has no
interrupt/HITL surface, so unlike A3 it needs no checkpointer and no
app-lifespan wiring — a plain `lru_cache`d singleton is enough.
"""

from functools import lru_cache
from pathlib import Path

from sentinel.graph.builder import (
    SentinelGraph,
    SkeletonGraph,
    build_sentinel_graph,
    build_skeleton_graph,
)
from sentinel.settings import Settings, get_settings
from sentinel.store.account_store import AccountStore
from sentinel.store.run_store import RunStore


def settings_dependency() -> Settings:
    return get_settings()


@lru_cache
def get_compiled_graph() -> SkeletonGraph:
    """The Phase 0 skeleton graph, kept as the streaming proof (docs/PLAN.md)."""
    return build_skeleton_graph()


@lru_cache
def get_account_store() -> AccountStore:
    """One read-write account-store connection, shared across requests."""
    return AccountStore(Path(get_settings().accounts_db_path))


@lru_cache
def get_run_store() -> RunStore:
    """Durable chat-run store (runs, events, per-node costs) — the audit log."""
    return RunStore(Path(get_settings().run_store_path))


@lru_cache
def get_sentinel_graph() -> SentinelGraph:
    """The real graph, built once against the shared account store."""
    return build_sentinel_graph(get_settings(), get_account_store())
