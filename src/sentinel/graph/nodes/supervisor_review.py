"""Supervisor review node (docs/PLAN.md Phase 3) — the centrepiece. Reads
only `draft`, `citations`, `specialist_context`; writes `review` and
increments `revision_count` on a failure so the retry loop is bounded."""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.protocols import SupervisorReviewChain
from sentinel.graph.state import SentinelState


def build_supervisor_review_node(
    review_chain: SupervisorReviewChain,
) -> Callable[[SentinelState], dict[str, object]]:
    def supervisor_review(state: SentinelState) -> dict[str, object]:
        result = review_chain.invoke(
            {
                "draft": state["draft"],
                "citations": ", ".join(state.get("citations", [])) or "none",
                "context": state.get("specialist_context", ""),
            }
        )
        passed = result.grounded and result.in_scope
        revision_count = state.get("revision_count", 0)
        return {
            "review": result,
            "revision_count": revision_count if passed else revision_count + 1,
        }

    return supervisor_review
