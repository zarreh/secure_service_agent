"""The identity gate: the only producer of a verified `Principal` (D-A4-2).

Runs in the API layer, before the graph. The credential is checked here and then
dropped; only a frozen `Principal` travels. Design properties:

- **No account enumeration.** A missing account, a wrong PIN and a locked account
  are indistinguishable to the caller in both *response* and *time*: a missing
  account still spends one key derivation, and failures are recorded against the
  *supplied* id whether or not it exists.
- **A success resets only the account counter, never the client's.** Otherwise an
  attacker holding one valid account could alternate it with guesses at others.
- **Lockout is durable** (SQLite), so a restart does not reset it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from secureagent.identity.lockout import Lockout
from secureagent.identity.pin import is_well_formed_pin, spend_equal_time, verify_pin
from secureagent.schemas.principal import UNVERIFIED, Principal
from secureagent.store import CredentialStore

Reason = Literal["verified", "not_verified", "throttled"]


@dataclass(frozen=True)
class Verification:
    principal: Principal
    reason: Reason
    retry_after_seconds: float = 0.0


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class IdentityGate:
    def __init__(
        self,
        credentials: CredentialStore,
        lockout: Lockout,
        pepper: str,
        *,
        now: Callable[[], str] = _utc_now,
    ) -> None:
        if not pepper:
            raise ValueError("an identity gate requires a pepper")
        self._credentials = credentials
        self._lockout = lockout
        self._pepper = pepper
        self._now = now

    def verify(self, account_id: str, pin: str, *, client: str) -> Verification:
        account_key = f"acct:{account_id}"
        client_key = f"client:{client}"

        wait = self._lockout.retry_after(account_key, client_key)
        if wait > 0:
            # Throttled attempts are neither verified nor counted as fresh guesses.
            return Verification(UNVERIFIED, "throttled", retry_after_seconds=wait)

        stored = self._credentials.pin_hash(account_id)
        if stored is None or not is_well_formed_pin(pin):
            spend_equal_time(self._pepper)
            matched = False
        else:
            matched = verify_pin(pin, stored, self._pepper)

        if matched:
            self._lockout.record_success(account_key)  # never the client key
            principal = Principal(account_id=account_id, verified=True, verified_at=self._now())
            return Verification(principal, "verified")

        self._lockout.record_failure(account_key, client_key)
        return Verification(UNVERIFIED, "not_verified")
