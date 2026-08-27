"""Deterministic input scan — a regex/deny-list layer under the LLM
injection classifier (docs/PLAN.md Phase 2 risk note: the canonical eval set
must be deterministic-passable without depending on LLM scan variance).

Policy basis (`clause-escalation`): "Any case that follows a blocked or
suspicious input, such as a detected attempt to manipulate the assistant, is
treated as a possible security incident" — this is the layer that produces
that detection.
"""

from __future__ import annotations

import re

from sentinel.schemas.guardrail import GuardrailVerdict

_INJECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "ignore-instructions": re.compile(
        r"\bignore\s+(all\s+|the\s+)?(previous|prior|above)\s+instructions\b", re.IGNORECASE
    ),
    "disregard-rules": re.compile(
        r"\bdisregard\s+(your\s+)?(rules|instructions|guidelines|policy)\b", re.IGNORECASE
    ),
    "reveal-system-prompt": re.compile(
        r"\b(reveal|show|print|repeat)\s+(your\s+)?(system\s+prompt|instructions)\b",
        re.IGNORECASE,
    ),
    "role-override": re.compile(
        r"\byou\s+are\s+now\b|\bact\s+as\s+(a|an)\b|\bpretend\s+(you\s+are|to\s+be)\b",
        re.IGNORECASE,
    ),
    "developer-mode": re.compile(r"\bdeveloper\s+mode\b|\bjailbreak\b", re.IGNORECASE),
}


def scan_input_deterministic(text: str) -> GuardrailVerdict:
    for rule_id, pattern in _INJECTION_PATTERNS.items():
        if pattern.search(text):
            return GuardrailVerdict(
                blocked=True,
                layer="deterministic",
                rule_id=rule_id,
                reason=f"Matched injection pattern '{rule_id}'.",
            )
    return GuardrailVerdict(blocked=False, layer="deterministic")
