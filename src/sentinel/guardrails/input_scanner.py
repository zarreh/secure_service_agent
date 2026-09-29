"""Deterministic input scan — the first layer, under the LLM injection classifier.

A thin adapter: detection lives in `input_screen` (normalised views, measured
limits); this module keeps the `GuardrailVerdict` contract the graph and the
canonical eval set already depend on, and the rule ids they assert against.

Policy basis (`clause-escalation`): "Any case that follows a blocked or
suspicious input, such as a detected attempt to manipulate the assistant, is
treated as a possible security incident" — this is the layer that produces
that detection.
"""

from __future__ import annotations

from sentinel.guardrails.input_screen import screen
from sentinel.schemas.guardrail import GuardrailVerdict

# Stable public rule ids (asserted by evals/scenarios.py) for the categories that
# existed before the normaliser; new categories use their own name, hyphenated.
_RULE_IDS = {
    "instruction_override": "ignore-instructions",
    "role_hijack": "role-override",
    "jailbreak_terms": "developer-mode",
    "prompt_extraction": "reveal-system-prompt",
}


def scan_input_deterministic(text: str) -> GuardrailVerdict:
    result = screen(text)
    if result.verdict != "block":
        return GuardrailVerdict(blocked=False, layer="deterministic")

    hit = next(m for m in result.matches if m.severity == "block")
    rule_id = _RULE_IDS.get(hit.category, hit.category.replace("_", "-"))
    return GuardrailVerdict(
        blocked=True,
        layer="deterministic",
        rule_id=rule_id,
        reason=f"Matched injection pattern '{rule_id}' (view: {hit.view}).",
    )
