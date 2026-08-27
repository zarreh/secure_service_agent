"""Supervisor routing decision (docs/PLAN.md Phase 3)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Specialist = Literal["network", "billing", "account", "escalation"]


class SupervisorRoute(BaseModel):
    specialist: Specialist
    reason: str
