"""Deterministic input scan — a regex/deny-list layer under the LLM
injection classifier (docs/PLAN.md Phase 2 risk note: the canonical eval set
must be deterministic-passable without depending on LLM scan variance).

Policy basis (`clause-escalation`): "Any case that follows a blocked or
suspicious input, such as a detected attempt to manipulate the assistant, is
treated as a possible security incident" — this is the layer that produces
that detection.
"""

from __future__ import annotations

from zarreh_agentkit.guardrails.injection import first_matching_rule

from sentinel.schemas.guardrail import GuardrailVerdict


def scan_input_deterministic(text: str) -> GuardrailVerdict:
    rule_id = first_matching_rule(text)
    if rule_id is not None:
        return GuardrailVerdict(
            blocked=True,
            layer="deterministic",
            rule_id=rule_id,
            reason=f"Matched injection pattern '{rule_id}'.",
        )
    return GuardrailVerdict(blocked=False, layer="deterministic")
