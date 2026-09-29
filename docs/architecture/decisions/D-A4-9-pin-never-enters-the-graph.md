# D-A4-9 — The PIN never enters the graph

**Status:** Accepted, implemented (`sentinel/identity/`, `api/run_executor.py`).
Corrects a claim in D-A4-2.

## Context

D-A4-2 states that no plaintext PIN is "held in graph state". It was: the PIN was a
field of the initial graph state. That state is the root run's input, so any tracing
callback (`build_tracing_callbacks` installs LangSmith's) receives it, and the state
was also passed through node outputs. `tests/api/test_pin_never_traced.py` first
failed against that design with the PIN visible in the recorded root inputs and in
later state snapshots. The earlier guarantee ("no node output includes it") covered
the run store and the SSE stream, not the tracer.

## Decision

The PIN is checked in the API layer, before the graph starts, by `IdentityGate`
(`sentinel.identity`), and then dropped. Only an `IdentityResult` (verified, locked,
attempts remaining, retry-after) enters graph state. The `identity_gate` node remains
in the graph so the decision still appears in the trace and audit log at the point the
graph acts on it, and so a run without an identity fails closed (`KeyError`) instead of
defaulting to verified.

Two import contracts make the separation structural: the graph, tools and guardrails
never import `sentinel.identity`, and `identity` depends only on `store` and `schemas`.
Both were confirmed to break when violated.

`AccountStore` no longer verifies PINs or holds lockout state: it is a read-only
repository, so a compromised graph cannot check a credential or touch a counter.

## Consequences

- A blocked input now also spends an identity attempt (the PIN is checked first).
  That is deliberate: it removes a free, un-throttled path that never verified
  anything.
- The recording-callback test drives the real `POST /chat` path, so it fails if the
  PIN is ever put back into state (confirmed by sabotage).
- Verification runs in a worker thread (PBKDF2 is ~100 ms) behind a lock; see D-A4-10.
