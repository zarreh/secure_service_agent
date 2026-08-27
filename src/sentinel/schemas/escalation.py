"""Structured escalation handoff (docs/PLAN.md Phase 3), matching
`clause-escalation`'s requirement literally: "the agent builds a structured
handoff that records the customer, the issue, the history, what was
attempted, and the reason for escalation, and assigns an urgency level."
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Urgency = Literal["low", "medium", "high"]


class EscalationHandoff(BaseModel):
    issue: str
    history_summary: str
    attempted: str
    reason: str
    urgency: Urgency
