# D-A4-7 — The audit log is the persisted node-event stream, not a separate table

**Status:** Accepted, implemented (`store/run_store.py`, `api/run_executor.py`, Phase 4).

## Context

docs/PLAN.md's Phase 4 requires "an audit log records every guardrail
decision." A dedicated `audit_log` table (verdict, rule id, timestamp) was
one option; another is to notice that the guardrail verdicts, the identity
result, and the routing decision are already node outputs in
`SentinelState`, and every node output is already captured by
`run_executor.execute_chat`'s `astream_events` loop.

## Decision

There is no separate audit table. `run_store.append_event` persists every
node's output as it happens (the same mechanism A2/A3/A7 use for
replayable run history), and that log already contains `input_verdict`,
`identity`, `route`, `review`, and `output_verdict` in full, in order, per
run. `GET /chat/{run_id}/events` — built for replay/streaming — **is** the
audit trail; there was nothing extra to build.

## Consequences

- **Pros:** One mechanism serves two purposes (replay and audit) instead of
  two mechanisms that could drift apart. A reviewer asking "what did the
  guardrails decide on this run" gets the answer from the same endpoint a
  customer's own client uses to watch their answer stream in.
- **Cons:** There is no dedicated, queryable "show me every blocked
  request across all runs" view — that would require scanning
  `run_events` for `input_verdict`/`output_verdict` payloads with
  `blocked: true`, which is fine at demo scale but would want a real
  index or a projection table before the `pro`-tier attack console's OWASP
  coverage matrix reports on it at volume.
