"""Deterministic terminal node when the input guardrail blocks
(docs/PLAN.md Phase 3). Never runs a specialist, never touches the account
store. Deliberately does not echo `input_verdict.reason` back to the caller
— confirming *which* pattern tripped would help an attacker iterate."""

from __future__ import annotations

from sentinel.graph.state import SentinelState


def blocked_input_response(state: SentinelState) -> dict[str, str]:
    return {
        "response": "I can't help with that request. If you have a genuine "
        "support question, please rephrase it."
    }
