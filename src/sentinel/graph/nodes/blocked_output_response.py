"""Deterministic terminal node when the output guardrail blocks a drafted
response (docs/PLAN.md Phase 3). The draft is discarded entirely — it is
never partially shown."""

from __future__ import annotations

from sentinel.graph.state import SentinelState


def blocked_output_response(state: SentinelState) -> dict[str, str]:
    return {
        "response": "I'm not able to share that. If this is about your own "
        "account, please contact support directly."
    }
