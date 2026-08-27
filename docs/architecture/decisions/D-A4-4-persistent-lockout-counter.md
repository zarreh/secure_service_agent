# D-A4-4 — The PIN lockout counter lives in the account store, not in graph state

**Status:** Accepted, implemented (`pin_lockouts` table, `AccountStore`, Phase 2).

## Context

A lockout counter that reset every conversation would not stop brute force —
an attacker would simply start a fresh run for each guess. The counter has
to persist across separate graph invocations for the same account.

## Decision

`accounts.db` carries a `pin_lockouts` table (`account_id`, `failed_attempts`,
`locked`), separate from the `accounts` table itself. `AccountStore.record_failed_pin_attempt`
and `reset_pin_attempts` are the only writes this otherwise read-only store
performs. Looking up an **unknown** account id never creates a lockout row
(`check_identity` checks `get_account` first) — otherwise an attacker could
enumerate real account ids by watching which ids ever appear in the lockout
table.

The counter is not time-boxed or auto-expiring: once `pin_max_attempts` wrong
PINs are recorded, the account stays locked until an operator resets it (no
such reset path exists yet — noted as an open question in docs/PLAN.md).

## Consequences

- **Pros:** Lockout state survives process restarts and separate
  conversations, which is the entire point of a lockout — and it is testable
  in isolation (`tests/guardrails/test_identity_gate.py`) without spinning up
  the graph.
- **Cons:** `make data`'s full rebuild of `accounts.db` also clears every
  lockout — acceptable for a demo, but a real deployment would need lockout
  state to survive a data refresh, i.e. a separate table/database from the
  regenerated account population. No auto-unlock path exists yet; a
  permanently locked demo account has no self-service recovery, only a
  fresh `make data`.
