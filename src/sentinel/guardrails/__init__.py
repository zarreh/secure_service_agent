"""Input scanner, output scanner, identity/PIN gate, PII redaction — the
security envelope's guardrail primitives (docs/PLAN.md Phase 2).

A4 is the second app (after A3's policy gate) to build a guardrail of this
shape; this stays local rather than importing a shared abstraction, per the
"extract after two instances" rule (see docs/HARVEST.md #11).
"""
