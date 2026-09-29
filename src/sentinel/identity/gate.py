"""The identity gate: the only place a PIN is ever compared (D-A4-9, D-A4-10).

Runs in the API layer, before the graph. The PIN is checked here and then
dropped; only an `IdentityResult` travels into graph state, so the credential can
never reach a node, a checkpoint, or a tracing backend. Design properties:

- **No account enumeration.** A missing account, a wrong PIN and a throttled
  account are indistinguishable to the caller in response *and* time: a missing
  account still spends one key derivation, and failures are recorded against the
  *supplied* id whether or not it exists.
- **A success resets only the account counter, never the client's.** Otherwise an
  attacker holding one valid account could alternate it with guesses at others.
- **Lockout is durable** (SQLite), so a restart does not reset it, and it backs
  off exponentially to a ceiling rather than locking an account permanently, so
  a stranger cannot lock a customer out for good.
"""

from __future__ import annotations

import threading

from sentinel.identity.lockout import Lockout
from sentinel.schemas.identity import IdentityResult
from sentinel.store.account_store import AccountStore
from sentinel.store.pin_hash import is_well_formed_pin, spend_equal_time, verify_pin


class IdentityGate:
    def __init__(self, accounts: AccountStore, lockout: Lockout, pepper: str) -> None:
        if not pepper:
            raise ValueError("an identity gate requires a pepper")
        self._accounts = accounts
        self._lockout = lockout
        self._pepper = pepper
        # Read-check-write on the counters must be atomic, or N parallel guesses
        # all pass the throttle check before any failure is recorded.
        self._lock = threading.Lock()

    def verify(self, account_id: str, pin: str, *, client: str) -> IdentityResult:
        with self._lock:
            return self._verify(account_id, pin, client)

    def _verify(self, account_id: str, pin: str, client: str) -> IdentityResult:
        account_key = f"acct:{account_id}"
        client_key = f"client:{client}"
        free = self._lockout.policy.free_attempts

        wait = self._lockout.retry_after(account_key, client_key)
        if wait > 0:
            # A throttled attempt is neither verified nor counted as a fresh guess.
            return IdentityResult(
                verified=False, locked=True, attempts_remaining=0, retry_after_seconds=wait
            )

        account = self._accounts.get_account(account_id)
        if account is None or not is_well_formed_pin(pin):
            spend_equal_time(self._pepper)
            matched = False
        else:
            matched = verify_pin(pin, account.pin_hash, account.pin_salt, pepper=self._pepper)

        if matched:
            self._lockout.record_success(account_key)  # never the client key
            return IdentityResult(verified=True, locked=False, attempts_remaining=free)

        self._lockout.record_failure(account_key, client_key)
        wait = self._lockout.retry_after(account_key, client_key)
        remaining = max(0, free - self._lockout.failures(account_key))
        return IdentityResult(
            verified=False,
            locked=wait > 0,
            attempts_remaining=remaining,
            retry_after_seconds=wait,
        )
