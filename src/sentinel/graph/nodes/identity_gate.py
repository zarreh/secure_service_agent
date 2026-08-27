"""Identity gate node — the graph's second node once wired in Phase 3
(docs/PLAN.md). Reads only `account_id`/`pin`; writes only `identity`. Never
reads or writes `question`, `draft`, or anything specialist-scoped — a
verified identity is the only thing downstream nodes are allowed to trust
this node for."""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.state import SentinelState
from sentinel.guardrails.identity_gate import check_identity
from sentinel.schemas.identity import IdentityResult
from sentinel.settings import Settings
from sentinel.store.account_store import AccountStore


def build_identity_gate_node(
    store: AccountStore, settings: Settings
) -> Callable[[SentinelState], dict[str, IdentityResult]]:
    def identity_gate(state: SentinelState) -> dict[str, IdentityResult]:
        result = check_identity(
            store,
            state["account_id"],
            state["pin"],
            max_attempts=settings.pin_max_attempts,
        )
        return {"identity": result}

    return identity_gate
