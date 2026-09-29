"""Deterministic output scan — a layer under the LLM leak/PII classifier
(docs/PLAN.md Phase 2, D-A4-11), enforcing two policy clauses literally:

- `clause-identity-verification`: "Agents must never reveal, confirm, or hint at
  a customer's PIN, and must never read a PIN back to a caller."
- `clause-data-privacy`: "An agent must never reference or compare against
  another customer's account[.]"

The account checks are relative to who is asking, so the scan needs the caller's
verified account id and the names of every *other* customer, read from the store.
That is what makes it a check against stored values rather than against a pattern
the model can rephrase.

Every check runs over the same normalised views as the input screen, so a leak
that is spaced out, leet-encoded or base64-wrapped is caught like a plain one.

A block's `reason` never contains the value that was blocked: the verdict is
streamed to the client, and quoting the leak would itself be the leak.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from sentinel.guardrails.normalise import views
from sentinel.schemas.guardrail import GuardrailVerdict

_PIN_MENTION = re.compile(
    r"\b(?:pin|passcode)\b[^.\n]{0,20}\b(?:is|was|:)\b[^.\n]{0,10}\d{4}\b"
    r"|\b\d{4}\b[^.\n]{0,20}\b(?:is|as)\s+(?:your|the)\s+(?:pin|passcode)\b"
)
# With letter spacing, word boundaries are unrecoverable; only the collapsed view uses this.
_PIN_MENTION_COLLAPSED = re.compile(r"(?:pin|passcode)\D{0,12}\d{4}")

_ACCOUNT_REF = re.compile(r"(?<![a-z0-9])acct[\s_\-]*(\d+)(?!\d)")
_ACCOUNT_REF_COLLAPSED = re.compile(r"acct[\s_\-]*(\d+)")

_MIN_NAME_LENGTH = 3


def _blocked(rule_id: str, reason: str) -> GuardrailVerdict:
    return GuardrailVerdict(blocked=True, layer="deterministic", rule_id=rule_id, reason=reason)


def _digits(account_id: str | None) -> str | None:
    if account_id is None:
        return None
    found = re.search(r"\d+", account_id)
    return found.group(0) if found else None


def _name_pattern(name: str, *, collapsed: bool) -> re.Pattern[str]:
    core = re.sub(r"[\s.\-_*]", "", name) if collapsed else re.escape(name)
    if collapsed:
        return re.compile(re.escape(core))
    return re.compile(rf"(?<![a-z0-9]){core}(?![a-z0-9])")


def scan_output_deterministic(
    text: str,
    *,
    verified_account_id: str | None,
    other_customer_names: Sequence[str] = (),
) -> GuardrailVerdict:
    own_digits = _digits(verified_account_id)
    names = [n.casefold() for n in other_customer_names if len(n.strip()) >= _MIN_NAME_LENGTH]

    for view_name, view in views(text).items():
        collapsed = view_name == "collapsed"

        pin = _PIN_MENTION_COLLAPSED if collapsed else _PIN_MENTION
        if pin.search(view):
            return _blocked("pin-disclosure", "Response appears to state or confirm a PIN.")

        account = _ACCOUNT_REF_COLLAPSED if collapsed else _ACCOUNT_REF
        # The leet view rewrites digits to letters, so it would turn the caller's own
        # id into a mismatch; the other views already cover a digit-bearing id.
        for match in () if view_name == "leet" else account.finditer(view):
            if match.group(1) != own_digits:
                return _blocked(
                    "cross-account-reference",
                    "Response references an account other than the verified one.",
                )

        for name in names:
            if _name_pattern(name, collapsed=collapsed).search(view):
                return _blocked(
                    "other-customer-name",
                    "Response names a customer other than the verified one.",
                )

    return GuardrailVerdict(blocked=False, layer="deterministic")
