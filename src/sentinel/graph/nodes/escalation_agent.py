"""Escalation node (docs/PLAN.md Phase 3). Builds the structured handoff
`clause-escalation` requires, then a short customer-facing draft confirming
the handoff — this node's draft is never itself the resolution, so
`supervisor_review`'s grounding check has less to verify, but still checks
scope (no account leak in the confirmation text)."""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.protocols import EscalationChain
from sentinel.graph.state import SentinelState
from sentinel.schemas.history import format_history


def build_escalation_agent_node(
    chain: EscalationChain,
) -> Callable[[SentinelState], dict[str, object]]:
    def escalation_agent(state: SentinelState) -> dict[str, object]:
        history_text = format_history(state.get("history", []))
        trigger = state.get("route_reason", "unresolved after standard steps")

        handoff = chain.invoke(
            {
                "question": state["question"],
                "trigger": trigger,
                "history": history_text,
            }
        )
        draft = (
            f"I've escalated this to a specialist (urgency: {handoff.urgency}). "
            f"They'll follow up on: {handoff.issue}"
        )
        context = f"Escalation trigger: {trigger}\n\nHistory:\n{history_text}"
        return {
            "draft": draft,
            "citations": ["clause-escalation"],
            "specialist_context": context,
            "escalation": handoff,
        }

    return escalation_agent
