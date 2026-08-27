"""Input scanner, output scanner, identity/PIN gate, PII redaction — the
security envelope's guardrail primitives (docs/PLAN.md Phase 2).

A4 is the second app (after A3's policy gate) to build a guardrail of this
shape; this stays local rather than importing a shared abstraction, per the
"extract after two instances" rule (see docs/HARVEST.md #11).
"""

from sentinel.guardrails.combine import combine_verdicts
from sentinel.guardrails.identity_gate import check_identity
from sentinel.guardrails.input_scanner import scan_input_deterministic
from sentinel.guardrails.output_scanner import scan_output_deterministic

__all__ = [
    "check_identity",
    "combine_verdicts",
    "scan_input_deterministic",
    "scan_output_deterministic",
]
