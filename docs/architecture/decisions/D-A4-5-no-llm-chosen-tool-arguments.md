# D-A4-5 — Specialists never let the model choose an account identifier

**Status:** Accepted, implemented (`graph/nodes/{network,billing,account}_agent.py`, Phase 3).

## Context

The source notebook's specialists are ReAct agents that call tools with
model-chosen arguments — the LLM decides which account id, plan, or record
to fetch. That is the most common shape for an agentic support bot, but it
means the one thing standing between "answer my own question" and "answer a
question about someone else's account" is the model's own judgement plus
whatever the tool's argument validation catches.

## Decision

None of `network_agent`, `billing_agent`, or `account_agent` expose a tool
the model calls with an account identifier. Instead, each node fetches its
own domain context — the caller's plan, account record, and the one relevant
policy clause — deterministically, keyed only by `state["account_id"]`,
which was set once by `identity_gate` from the verified PIN check and is
never revised downstream. The specialist LLM call receives that context as
plain text and drafts an answer from it; it has no argument to name a
*different* account even if it wanted to.

This is a deliberate deviation from the source's tool-calling design, not an
oversight — `docs/HARVEST.md` and `docs/PLAN.md`'s risk notes call out the
change and why.

## Consequences

- **Pros:** The strongest guarantee in the "adversarial security envelope"
  story is not the output scanner catching a leak after the fact — it's that
  a cross-account request has no code path to succeed in the first place.
  `supervisor_review`'s scope check and `output_scanner`'s cross-account
  regex become defense in depth for a mistake in the *drafted text*, not the
  only thing stopping a mistake in *which record was fetched*.
- **Cons:** No specialist can act on a second account even when that would
  be legitimate (e.g. a family plan lookup) — every request is scoped to
  exactly the identity-gate-verified account, with no path to expand that
  without a new, deliberately-reviewed capability. Multi-account support, if
  ever added, needs its own explicit re-verification step, not a wider tool
  argument.
