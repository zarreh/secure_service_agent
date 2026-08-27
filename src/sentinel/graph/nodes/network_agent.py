"""Network specialist node (docs/PLAN.md Phase 3, D-A4-5). Reads only
`question` and `history`; fetches the network-support clause itself rather
than trusting anything from state. Writes `draft`, `citations`,
`specialist_context` (the text `supervisor_review` checks groundedness
against)."""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.protocols import SpecialistChain
from sentinel.graph.state import SentinelState
from sentinel.schemas.history import format_history
from sentinel.store.policy_kb import get_clause

_CLAUSE_ID = "clause-network-support"


def build_network_agent_node(
    chain: SpecialistChain,
) -> Callable[[SentinelState], dict[str, object]]:
    def network_agent(state: SentinelState) -> dict[str, object]:
        clause = get_clause(_CLAUSE_ID)
        assert clause is not None, f"missing policy clause {_CLAUSE_ID}"
        history_text = format_history(state.get("history", []))

        result = chain.invoke(
            {
                "question": state["question"],
                "clause_id": clause.clause_id,
                "clause_body": clause.body,
                "history": history_text,
            }
        )
        context = f"Policy clause {clause.clause_id}: {clause.body}\n\nHistory:\n{history_text}"
        return {
            "draft": result.draft,
            "citations": result.citations,
            "specialist_context": context,
        }

    return network_agent
