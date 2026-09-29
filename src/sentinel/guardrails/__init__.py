"""Input scanner, output scanner, PII redaction — the security envelope's
guardrail primitives (docs/PLAN.md Phase 2). Credential checking is not here: it
lives in `sentinel.identity` and is unreachable from the graph (D-A4-9).

A4 is the second app (after A3's policy gate) to build a guardrail of this
shape; this stays local rather than importing a shared abstraction, per the
"extract after two instances" rule (see docs/HARVEST.md #11).
"""

from sentinel.guardrails.combine import combine_verdicts
from sentinel.guardrails.input_scanner import scan_input_deterministic
from sentinel.guardrails.output_scanner import scan_output_deterministic

__all__ = [
    "combine_verdicts",
    "scan_input_deterministic",
    "scan_output_deterministic",
]
