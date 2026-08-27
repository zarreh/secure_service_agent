"""A specialist-facing projection of a prior interaction (docs/PLAN.md Phase 3).

Deliberately narrower than `sentinel.store.models.MemoryEvent`: graph state
and the LLM-facing schemas never import the store layer directly (the
layering contract in pyproject.toml has `graph` sit above `tools` and
`guardrails`, not beside `store`), so `context_loader` maps `MemoryEvent` ->
`HistoryEvent` at the boundary rather than the graph carrying a store row
type. `account_id` and `agent_used` are dropped here — a specialist reasons
about what happened and what was tried, not which internal queue handled it.
"""

from __future__ import annotations

from pydantic import BaseModel


class HistoryEvent(BaseModel):
    query: str
    intent: str
    resolution_type: str
    response_summary: str


def format_history(history: list[HistoryEvent]) -> str:
    """The one text rendering of history fed to every chain that needs it
    (`network_specialist`, `escalation_specialist`) — kept in one place so a
    future format change doesn't drift between them."""
    if not history:
        return "No prior contact on record."
    return "\n".join(
        f"- [{e.intent}/{e.resolution_type}] {e.query} — {e.response_summary}" for e in history
    )
