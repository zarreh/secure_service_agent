"""PIN verification with lockout (docs/PLAN.md Phase 2, D-A4-2).

Policy basis (`data/policy_clauses.json`, `clause-identity-verification`):
before any account-specific information is shared, the customer must
verify with a matching PIN; general information may be shared without
verification. This module implements only the verification decision — what
a node does with `IdentityResult` (unlock tools, or fall back to general
help) is the identity_gate node's job, not this one's.
"""

from __future__ import annotations

from sentinel.schemas.identity import IdentityResult
from sentinel.store.account_store import AccountStore


def check_identity(
    store: AccountStore, account_id: str, pin: str, *, max_attempts: int
) -> IdentityResult:
    """Never records an attempt against an unknown account id — that would
    let a caller probe which ids exist by watching the lockout counter, the
    same enumeration channel `AccountStore.verify_pin` already closes."""
    if store.get_account(account_id) is None:
        return IdentityResult(verified=False, locked=False, attempts_remaining=max_attempts)

    if store.is_locked(account_id):
        return IdentityResult(verified=False, locked=True, attempts_remaining=0)

    if store.verify_pin(account_id, pin):
        store.reset_pin_attempts(account_id)
        return IdentityResult(verified=True, locked=False, attempts_remaining=max_attempts)

    attempts = store.record_failed_pin_attempt(account_id, max_attempts=max_attempts)
    locked = attempts >= max_attempts
    return IdentityResult(
        verified=False, locked=locked, attempts_remaining=max(0, max_attempts - attempts)
    )
