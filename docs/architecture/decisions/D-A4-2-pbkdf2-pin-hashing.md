# D-A4-2 — PBKDF2-HMAC-SHA256 for PIN storage, never plaintext

**Status:** Accepted, implemented (`sentinel/store/pin_hash.py`, Phase 1).

## Context

The identity gate (Phase 2) verifies a customer-submitted PIN against the
account store. PINs are 4-digit, so their entropy is low (10,000 possible
values) — a fast general-purpose hash (SHA-256 alone, or none) would make an
offline brute force of a leaked `accounts.db` trivial.

## Decision

`hash_pin`/`verify_pin` use `hashlib.pbkdf2_hmac("sha256", ..., iterations=260_000)`
with a random 16-byte salt per account, stored alongside the hash
(`pin_hash`, `pin_salt` columns). No plaintext PIN is ever written to the
store, held in graph state, or logged — `AccountStore.verify_pin` returns
only a bool, never the stored hash or salt, and returns `False` (not an
exception) for an unknown account so a caller cannot distinguish "wrong PIN"
from "no such account."

No extra dependency (`bcrypt`, `argon2-cffi`) — `hashlib.pbkdf2_hmac` is
stdlib and the iteration count is tunable without a library upgrade.

## Consequences

- **Pros:** A leaked `accounts.db` does not hand over PINs. The
  account-enumeration side channel is closed at the store boundary, not left
  to the identity-gate node to remember.
- **Cons:** PBKDF2 is deliberately slow (~tens of ms per verification at this
  iteration count) — acceptable for an interactive support agent, but the
  identity gate (Phase 2) must not call `verify_pin` in a tight retry loop
  without its own lockout counter, or the cost compounds per attempt.
