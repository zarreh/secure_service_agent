# D-A4-10 — Durable exponential-backoff lockout, keyed on account and client, with a pepper

**Status:** Accepted, implemented (`identity/lockout.py`, `identity/gate.py`,
`store/lockout_store.py`, `store/pin_hash.py`). Supersedes D-A4-4.

## Context

D-A4-4 locked an account permanently after three wrong PINs, with no reset path. Read
against an attacker rather than an honest user, that has four problems:

1. **Denial of service.** Anyone can lock any customer out forever with three requests.
2. **No client throttle.** Guesses spread across many accounts from one client are never
   slowed.
3. **A distinguishable response.** An unknown account never recorded a failure, so its
   `attempts_remaining` stayed at the maximum while a real account counted down.
4. **A 4-digit PIN cannot be protected by a key-derivation function.** With 10,000
   possibilities, no iteration count makes an offline attack on a leaked hash expensive.

## Decision

- **Free attempts, then exponential backoff to a ceiling** (3 free, then 30 s doubling
  to 900 s). Nobody is locked out for good.
- **Two keys, `acct:` and `client:`, both checked on every attempt.** A success clears
  only the account key, never the client's, so an attacker holding one valid account
  cannot alternate it with guesses at others.
- **Uniform behaviour.** Failures are recorded against the *supplied* id whether or not
  it exists, and a missing account or malformed PIN still spends one key derivation, so
  neither the response sequence nor the time distinguishes it. A test compares the full
  response sequence for a missing and a real account at every step.
- **Atomic.** Read-check-write on the counters runs under a lock; otherwise N parallel
  guesses all pass the throttle check before the first failure is recorded.
- **Durable, in its own database** (`identity.db`), so a restart does not reset an
  attacker's progress and rebuilding the synthetic accounts does not clear lockouts.
- **A server-side pepper** (an HMAC key held outside the database) before PBKDF2, so a
  stolen `accounts.db` alone cannot be brute-forced. `Settings` refuses the public
  fixture pepper outside development.

## Consequences

- The residual online risk is a distributed attacker: the client key is the remote
  address, so behind a shared proxy all callers share it (configure the proxy to pass a
  real client address), and the lockout table grows with the ids an attacker supplies,
  bounded only by the per-route rate limit.
- Changing the pepper invalidates existing hashes; `make data` regenerates the
  synthetic population.
