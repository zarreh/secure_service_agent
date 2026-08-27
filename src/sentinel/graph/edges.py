"""Routing predicates — one small function each (docs/PLAN.md §9.3).

`route_after_review` bounds the retry loop: on a failed review it routes
back to whichever specialist drafted the response (`state["route"]`) once,
then forces `give_up` — a specialist never retries itself more than once,
and `give_up` never calls a model, so the loop provably terminates.
"""

from __future__ import annotations

from typing import Literal

from sentinel.graph.state import SentinelState
from sentinel.schemas.supervisor import Specialist

_MAX_REVISIONS = 1


def route_after_guardrail(state: SentinelState) -> Literal["blocked", "allow"]:
    return "blocked" if state["input_verdict"].blocked else "allow"


def route_after_identity(state: SentinelState) -> Literal["verified", "unverified"]:
    return "verified" if state["identity"].verified else "unverified"


def route_supervisor_to_agent(state: SentinelState) -> Specialist:
    return state["route"]


def route_after_review(
    state: SentinelState,
) -> Literal["output_guardrail", "network", "billing", "account", "escalation", "give_up"]:
    review = state["review"]
    if review.grounded and review.in_scope:
        return "output_guardrail"
    if state.get("revision_count", 0) <= _MAX_REVISIONS:
        return state["route"]
    return "give_up"


def route_after_output_guardrail(state: SentinelState) -> Literal["respond", "blocked"]:
    return "blocked" if state["output_verdict"].blocked else "respond"
