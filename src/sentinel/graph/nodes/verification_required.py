"""Deterministic terminal node when identity verification fails
(docs/PLAN.md Phase 3). Reads only `identity`; never runs a specialist. Per
`clause-identity-verification`, a caller who cannot verify gets general help
only — Phase 3 implements the safe default (decline, no specialist), not yet
the fuller "answer general questions anyway" allowance; see docs/PLAN.md
open questions."""

from __future__ import annotations

from sentinel.graph.state import SentinelState


def verification_required(state: SentinelState) -> dict[str, str]:
    identity = state["identity"]
    if identity.locked:
        return {
            "response": "This account is locked after too many incorrect PIN "
            "attempts. Please contact support through another verified channel."
        }
    return {
        "response": "I can't share account-specific details until you verify with your account PIN."
    }
