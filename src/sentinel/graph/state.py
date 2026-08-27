"""Graph state.

`SkeletonState` is the Phase 0 walking skeleton, kept so the streaming path
stays proven end to end once the real graph exists (docs/PLAN.md §7). The real
`SentinelState` — carrying the guardrail verdicts, identity status, per-customer
context, specialist draft and review outcome — is added in Phase 2 onward
(docs/PLAN.md).

The narrow per-node projections (state-projection convention, §9.3) are
enforced by what each node reads, not by separate TypedDicts: e.g. the
`network_agent` should never read billing fields, and `context_loader` should
never see PII outside its own scope — a deliberate, testable privacy property.
"""

from __future__ import annotations

from typing import TypedDict

from sentinel.schemas.escalation import EscalationHandoff
from sentinel.schemas.guardrail import GuardrailVerdict
from sentinel.schemas.history import HistoryEvent
from sentinel.schemas.identity import IdentityResult
from sentinel.schemas.review import ReviewResult
from sentinel.schemas.supervisor import Specialist


class SkeletonState(TypedDict):
    """Walking-skeleton state — replaced by `SentinelState` starting Phase 2."""

    question: str
    steps: list[str]


class SentinelState(TypedDict, total=False):
    """The real graph state (docs/PLAN.md), built incrementally: Phase 2 adds
    the guardrail and identity fields below; Phase 3 adds the specialist
    routing, draft and review fields.

    `total=False` because the state accumulates — a field is present only
    after the node that owns it has run. Each node reads a narrow projection
    of this (§9.3): `guardrail` reads only `question`; `identity_gate` reads
    only `account_id`/`pin`; `output_guardrail` reads only `draft` and
    `account_id` — none of them see the whole blob.
    """

    # input guardrail
    question: str
    input_verdict: GuardrailVerdict

    # identity gate
    account_id: str
    pin: str
    identity: IdentityResult

    # context loader (Phase 3)
    history: list[HistoryEvent]

    # supervisor routing (Phase 3)
    route: Specialist
    route_reason: str

    # specialist draft (Phase 3)
    draft: str
    citations: list[str]
    specialist_context: str
    escalation: EscalationHandoff

    # supervisor review (Phase 3) — grounding + scope check before the output guardrail
    review: ReviewResult
    revision_count: int

    # output guardrail
    output_verdict: GuardrailVerdict

    # final customer-facing text, set by whichever terminal node runs
    response: str
