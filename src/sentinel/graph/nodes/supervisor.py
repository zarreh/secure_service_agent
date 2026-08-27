"""Supervisor routing node (docs/PLAN.md Phase 3). Reads only `question`;
writes only `route`/`route_reason`. The specialist a question routes to is
decided here, once — a specialist node never redirects itself."""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.protocols import SupervisorRouteChain
from sentinel.graph.state import SentinelState


def build_supervisor_node(
    route_chain: SupervisorRouteChain,
) -> Callable[[SentinelState], dict[str, object]]:
    def supervisor(state: SentinelState) -> dict[str, object]:
        result = route_chain.invoke({"question": state["question"]})
        return {"route": result.specialist, "route_reason": result.reason}

    return supervisor
