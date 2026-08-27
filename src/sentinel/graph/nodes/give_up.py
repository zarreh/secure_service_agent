"""Deterministic terminal node when a specialist's draft fails
`supervisor_review` twice in a row (docs/PLAN.md Phase 3). Guarantees the
retry loop terminates: no further LLM call, no further review."""

from __future__ import annotations

from sentinel.graph.state import SentinelState


def give_up(state: SentinelState) -> dict[str, str]:
    return {
        "response": "I'm not confident I can answer that correctly and "
        "safely, so I'm connecting you to a specialist instead."
    }
