# A4 — Secure Service Agent

Telecom customer support behind a full security envelope.

## What it does

A customer support interface — plan/usage, billing disputes, network faults,
escalation — where every message passes through:

1. **Input guardrail** — regex + LLM injection/toxicity scan, before anything
   else runs.
2. **Identity gate** — PIN verification with lockout, before any account tool
   unlocks.
3. **Specialist routing** — a supervisor routes to a network, billing,
   account or escalation specialist.
4. **Supervisor review** — a grounding and scope check on the drafted
   response.
5. **Output guardrail** — regex + LLM leak/PII scan, before the customer sees
   anything.

Every step is logged to an audit trail.

## Key design decisions

See [Architecture decisions](architecture/decisions/index.md).
