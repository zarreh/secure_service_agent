"""Context loader — per-customer redacted long-term memory (docs/PLAN.md
Phase 3). Reads only `account_id`; writes only `history`. Maps the store's
`MemoryEvent` rows to the narrower `HistoryEvent` schema at this boundary —
account id and which internal agent handled a past case never cross into
graph state (schemas/history.py)."""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.state import SentinelState
from sentinel.schemas.history import HistoryEvent
from sentinel.store.account_store import AccountStore


def build_context_loader_node(
    store: AccountStore,
) -> Callable[[SentinelState], dict[str, list[HistoryEvent]]]:
    def context_loader(state: SentinelState) -> dict[str, list[HistoryEvent]]:
        events = store.get_memory_events(state["account_id"])
        history = [
            HistoryEvent(
                query=e.query,
                intent=e.intent,
                resolution_type=e.resolution_type,
                response_summary=e.response_summary,
            )
            for e in events
        ]
        return {"history": history}

    return context_loader
