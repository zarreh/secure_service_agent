"""Structural (Protocol) types for the LLM-backed pieces nodes depend on.

Node factories accept these instead of concrete `Runnable[...]` types so a
plain test double (with just a matching `.invoke()`) can stand in without
subclassing LangChain's `Runnable` — real chains satisfy them structurally
too. This is what lets the guardrail nodes be tested with no LLM and no
network (docs/PLAN.md Phase 2).
"""

from __future__ import annotations

from typing import Protocol

from sentinel.schemas.escalation import EscalationHandoff
from sentinel.schemas.guardrail import InjectionScanResult, LeakScanResult
from sentinel.schemas.review import ReviewResult
from sentinel.schemas.specialist import SpecialistResponse
from sentinel.schemas.supervisor import SupervisorRoute


class InjectionScanChain(Protocol):
    def invoke(self, input: dict[str, str]) -> InjectionScanResult: ...


class LeakScanChain(Protocol):
    def invoke(self, input: dict[str, object]) -> LeakScanResult: ...


class SupervisorRouteChain(Protocol):
    def invoke(self, input: dict[str, str]) -> SupervisorRoute: ...


class SpecialistChain(Protocol):
    """Shared shape for the network/billing/account specialists — each takes
    the question plus whatever domain context its node fetched, and returns a
    cited draft."""

    def invoke(self, input: dict[str, object]) -> SpecialistResponse: ...


class EscalationChain(Protocol):
    def invoke(self, input: dict[str, object]) -> EscalationHandoff: ...


class SupervisorReviewChain(Protocol):
    def invoke(self, input: dict[str, object]) -> ReviewResult: ...
