"""Input guardrail node — the graph's first node once wired in Phase 3
(docs/PLAN.md). Reads only `question`; writes only `input_verdict`."""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.protocols import InjectionScanChain
from sentinel.graph.state import SentinelState
from sentinel.guardrails.combine import combine_verdicts
from sentinel.guardrails.input_scanner import scan_input_deterministic
from sentinel.schemas.guardrail import GuardrailVerdict


def build_guardrail_node(
    injection_chain: InjectionScanChain,
) -> Callable[[SentinelState], dict[str, GuardrailVerdict]]:
    def guardrail(state: SentinelState) -> dict[str, GuardrailVerdict]:
        question = state["question"]
        deterministic = scan_input_deterministic(question)
        if deterministic.blocked:
            return {"input_verdict": deterministic}

        result = injection_chain.invoke({"message": question})
        verdict = combine_verdicts(deterministic, result.is_injection, result.reason)
        return {"input_verdict": verdict}

    return guardrail
