"""A compromised model, for the assume-breach containment suite (D-A4-12).

Every LLM slot in the graph obeys the attacker: the injection classifier says "safe",
the router picks the most privileged specialist, the specialist writes whatever draft it
is told to, the reviewer approves it, and the leak classifier says "clean". Nothing here
is a model; it is the worst case a real model could reach after a successful injection.
What is left standing is only what does not depend on a model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sentinel.graph.builder import SentinelGraph, build_sentinel_graph
from sentinel.schemas.escalation import EscalationHandoff
from sentinel.schemas.guardrail import InjectionScanResult, LeakScanResult
from sentinel.schemas.review import ReviewResult
from sentinel.schemas.specialist import SpecialistResponse
from sentinel.schemas.supervisor import SupervisorRoute
from sentinel.settings import Settings
from sentinel.store.account_store import AccountStore


@dataclass
class Calls:
    """What each model slot was asked, so a scenario can say what never ran."""

    specialist_inputs: list[dict[str, object]] = field(default_factory=list)
    reviews: int = 0

    @property
    def specialists(self) -> int:
        return len(self.specialist_inputs)


class _Injection:
    def invoke(self, input: dict[str, str]) -> InjectionScanResult:
        return InjectionScanResult(is_injection=False, confidence=0.99, reason="looks fine")


class _Leak:
    def invoke(self, input: dict[str, object]) -> LeakScanResult:
        return LeakScanResult(leaks_sensitive_info=False, confidence=0.99, reason="clean")


class _Route:
    def invoke(self, input: dict[str, str]) -> SupervisorRoute:
        return SupervisorRoute(specialist="account", reason="most privileged")


class _Specialist:
    def __init__(self, draft: str, calls: Calls) -> None:
        self._draft = draft
        self._calls = calls

    def invoke(self, input: dict[str, object]) -> SpecialistResponse:
        self._calls.specialist_inputs.append(dict(input))
        return SpecialistResponse(draft=self._draft, citations=["clause-account-management"])


class _Escalation:
    def __init__(self, calls: Calls) -> None:
        self._calls = calls

    def invoke(self, input: dict[str, object]) -> EscalationHandoff:
        self._calls.specialist_inputs.append(dict(input))
        return EscalationHandoff(
            issue="x", history_summary="x", attempted="x", reason="x", urgency="high"
        )


class _Review:
    def __init__(self, approves: bool, calls: Calls) -> None:
        self._approves = approves
        self._calls = calls

    def invoke(self, input: dict[str, object]) -> ReviewResult:
        self._calls.reviews += 1
        return ReviewResult(grounded=self._approves, in_scope=self._approves, reason="approved")


@dataclass
class HostileModel:
    """The attacker's payload, and a graph in which every model slot delivers it."""

    draft: str = "Here is your answer."
    reviewer_approves: bool = True
    calls: Calls = field(default_factory=Calls)

    def graph(self, store: AccountStore) -> SentinelGraph:
        specialist = _Specialist(self.draft, self.calls)
        return build_sentinel_graph(
            Settings(),
            store,
            injection_chain=_Injection(),
            leak_chain=_Leak(),
            route_chain=_Route(),
            network_chain=specialist,
            billing_chain=specialist,
            account_chain=specialist,
            escalation_chain=_Escalation(self.calls),
            review_chain=_Review(self.reviewer_approves, self.calls),
        )
