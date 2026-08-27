# D-A4-3 — The deterministic guardrail layer wins, and short-circuits the LLM call

**Status:** Accepted, implemented (`sentinel/guardrails/combine.py`, Phase 2).

## Context

Each guardrail direction (input, output) has two layers: a regex/deny-list
scan that is fixed and instant, and an LLM classifier that catches
paraphrases the deny-list cannot express. docs/PLAN.md's Phase 2 risk note
requires that the canonical eval set (Phase 6) be deterministic-passable —
its exit criteria cannot depend on LLM scan variance, or a flaky model call
could flip a CI gate.

## Decision

`combine_verdicts` checks the deterministic verdict first. If it blocks, that
verdict is returned immediately and **the LLM chain is never invoked** — both
`build_guardrail_node` and `build_output_guardrail_node` short-circuit before
calling `.invoke()` on the injection/leak chain (see
`tests/graph/test_guardrail_nodes.py`'s `test_..._short_circuits_on_deterministic_block`,
which asserts the stub chain's `.called` flag stays `False`). The LLM layer
only ever adds an *additional* way to block; it cannot override a
deterministic block into a pass.

## Consequences

- **Pros:** Every case the deny-list catches is free (no token cost, no
  network call, no latency) and its outcome is exactly reproducible — the
  eval set's assertions about deny-list-covered attacks never flake.
  Attempting an already-known-bad injection literally costs nothing extra to
  block.
- **Cons:** The deny-list must be kept honest — a rule that's too broad
  blocks legitimate traffic before the LLM layer ever gets a chance to
  disagree. `tests/guardrails/test_input_scanner.py` and
  `test_output_scanner.py` assert both directions (blocks the attack,
  passes the legitimate phrasing) for exactly this reason.
