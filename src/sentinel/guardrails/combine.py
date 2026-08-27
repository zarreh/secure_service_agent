"""Merges a deterministic and an LLM guardrail verdict into one decision.

The deterministic layer wins on a block — its `rule_id` is a fixed pattern,
not a model judgement, so it is what the canonical eval set asserts against
(docs/PLAN.md Phase 2 risk note). The LLM layer only adds coverage the
deterministic layer cannot express (paraphrased injections, novel leak
phrasing); it never overrides a deterministic pass into a block being
*required* — it can still independently block.
"""

from __future__ import annotations

from sentinel.schemas.guardrail import GuardrailVerdict


def combine_verdicts(
    deterministic: GuardrailVerdict, llm_blocked: bool, llm_reason: str
) -> GuardrailVerdict:
    if deterministic.blocked:
        return deterministic
    if llm_blocked:
        return GuardrailVerdict(blocked=True, layer="llm", reason=llm_reason)
    return GuardrailVerdict(blocked=False, layer="llm")
