"""Supervisor review — the grounding + scope check on a specialist's draft
before it reaches the output guardrail (docs/PLAN.md Phase 3)."""

from __future__ import annotations

from pydantic import BaseModel


class ReviewResult(BaseModel):
    grounded: bool
    in_scope: bool
    reason: str
