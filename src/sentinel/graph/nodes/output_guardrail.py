"""Output guardrail node — the graph's last node before `response_node` once
wired in Phase 3 (docs/PLAN.md). Reads only `draft` and `account_id` (as the
verified account to compare cross-account references against); writes only
`output_verdict`."""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.protocols import LeakScanChain
from sentinel.graph.state import SentinelState
from sentinel.guardrails.combine import combine_verdicts
from sentinel.guardrails.output_scanner import scan_output_deterministic
from sentinel.schemas.guardrail import GuardrailVerdict


def build_output_guardrail_node(
    leak_chain: LeakScanChain,
) -> Callable[[SentinelState], dict[str, GuardrailVerdict]]:
    def output_guardrail(state: SentinelState) -> dict[str, GuardrailVerdict]:
        draft = state["draft"]
        verified_account_id = state.get("account_id")
        deterministic = scan_output_deterministic(draft, verified_account_id=verified_account_id)
        if deterministic.blocked:
            return {"output_verdict": deterministic}

        result = leak_chain.invoke({"draft": draft, "verified_account_id": verified_account_id})
        verdict = combine_verdicts(deterministic, result.leaks_sensitive_info, result.reason)
        return {"output_verdict": verdict}

    return output_guardrail
