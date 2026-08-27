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


class SkeletonState(TypedDict):
    """Walking-skeleton state — replaced by `SentinelState` starting Phase 2."""

    question: str
    steps: list[str]
