"""Deterministic output scan — a regex layer under the LLM leak/PII
classifier (docs/PLAN.md Phase 2), enforcing two clauses from
`data/policy_clauses.json` literally:

- `clause-identity-verification`: "Agents must never reveal, confirm, or
  hint at a customer's PIN, and must never read a PIN back to a caller."
- `clause-data-privacy`: "An agent must never reference or compare against
  another customer's account[.]"

The account-reference check is why this scan needs the caller's own verified
account id — it is the one output check that is relative to who is asking,
not a property of the text alone.
"""

from __future__ import annotations

import re

from sentinel.schemas.guardrail import GuardrailVerdict

_PIN_MENTION = re.compile(
    r"\b(pin|passcode)\b[^.\n]{0,20}\b(is|was|:)\b[^.\n]{0,10}\d{4}\b"
    r"|\b\d{4}\b[^.\n]{0,20}\b(is|as)\s+(your|the)\s+(pin|passcode)\b",
    re.IGNORECASE,
)
_ACCOUNT_ID = re.compile(r"\bACCT_\d+\b")


def scan_output_deterministic(text: str, *, verified_account_id: str | None) -> GuardrailVerdict:
    if _PIN_MENTION.search(text):
        return GuardrailVerdict(
            blocked=True,
            layer="deterministic",
            rule_id="pin-disclosure",
            reason="Response appears to state or confirm a PIN.",
        )

    for match in _ACCOUNT_ID.finditer(text):
        if match.group(0) != verified_account_id:
            return GuardrailVerdict(
                blocked=True,
                layer="deterministic",
                rule_id="cross-account-reference",
                reason=f"Response references {match.group(0)}, not the verified account.",
            )

    return GuardrailVerdict(blocked=False, layer="deterministic")
