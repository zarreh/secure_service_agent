"""Identity gate node — admits the identity decided before the graph started
(D-A4-9). Reads only `identity`; writes only `identity`.

The PIN is checked in the API layer by `sentinel.identity` and never enters graph
state, so no node, checkpoint or tracing backend can see it. This node exists so
the decision still appears in the trace and audit log at the point the graph
acts on it, and so a run started without one fails closed instead of defaulting
to verified.
"""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.state import SentinelState
from sentinel.schemas.identity import IdentityResult


def build_identity_gate_node() -> Callable[[SentinelState], dict[str, IdentityResult]]:
    def identity_gate(state: SentinelState) -> dict[str, IdentityResult]:
        return {"identity": state["identity"]}

    return identity_gate
