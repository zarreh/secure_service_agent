"""Stub chains satisfying the `graph/protocols.py` Protocols — shared between
`tests/graph/test_sentinel_graph.py` and the API test context
(`tests/api/_sentinel_client.py`) so both run the graph with no network and
no API key."""

from __future__ import annotations

from sentinel.schemas.escalation import EscalationHandoff
from sentinel.schemas.guardrail import InjectionScanResult, LeakScanResult
from sentinel.schemas.review import ReviewResult
from sentinel.schemas.specialist import SpecialistResponse
from sentinel.schemas.supervisor import Specialist, SupervisorRoute


class NoOpInjectionChain:
    def invoke(self, input: dict[str, str]) -> InjectionScanResult:
        return InjectionScanResult(is_injection=False, confidence=0.0, reason="clean")


class NoOpLeakChain:
    def invoke(self, input: dict[str, object]) -> LeakScanResult:
        return LeakScanResult(leaks_sensitive_info=False, confidence=0.0, reason="clean")


class FixedRouteChain:
    def __init__(self, specialist: Specialist) -> None:
        self._specialist = specialist

    def invoke(self, input: dict[str, str]) -> SupervisorRoute:
        return SupervisorRoute(specialist=self._specialist, reason="stub route")


class GroundedSpecialistChain:
    def invoke(self, input: dict[str, object]) -> SpecialistResponse:
        return SpecialistResponse(draft="Here is your answer.", citations=["stub-clause"])


class AlwaysPassingReviewChain:
    def invoke(self, input: dict[str, object]) -> ReviewResult:
        return ReviewResult(grounded=True, in_scope=True, reason="fine")


class AlwaysFailingReviewChain:
    def invoke(self, input: dict[str, object]) -> ReviewResult:
        return ReviewResult(grounded=False, in_scope=True, reason="not grounded")


class StubEscalationChain:
    def invoke(self, input: dict[str, object]) -> EscalationHandoff:
        return EscalationHandoff(
            issue="stub issue",
            history_summary="none",
            attempted="none",
            reason="stub reason",
            urgency="low",
        )
