"""Peppered, salted PIN hashing (D-A4-2, D-A4-10).

**What this does and does not protect against.** A 4-digit PIN has 10,000
possibilities, so *no* key-derivation function makes an offline attack on a
leaked hash expensive, whatever the iteration count. The salt keeps a PIN out of
dumps and logs; the controls that actually resist guessing are:

- a server-side **pepper** (an HMAC key held outside the database), so a stolen
  `accounts.db` alone cannot be brute-forced offline; and
- **online lockout** with backoff (`sentinel.identity`), so guessing through the
  API is slow.

`FIXTURE_PEPPER` is public and exists only so the synthetic population and the
tests are reproducible; `Settings` refuses it outside development. A real carrier
needs a real credential, not a PIN.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_ITERATIONS = 260_000
_SALT_BYTES = 16

FIXTURE_PEPPER = "sentinel-demo-pepper-not-a-secret"


def is_well_formed_pin(pin: str) -> bool:
    """Four ASCII digits. Rejected before any hashing so junk costs nothing."""
    return len(pin) == 4 and pin.isascii() and pin.isdigit()


def _derive(pin: str, pepper: str, salt: bytes) -> bytes:
    keyed = hmac.new(pepper.encode("utf-8"), pin.encode("utf-8"), hashlib.sha256).digest()
    return hashlib.pbkdf2_hmac("sha256", keyed, salt, _ITERATIONS)


def hash_pin(pin: str, *, pepper: str, salt: str | None = None) -> tuple[str, str]:
    """Returns `(hash_hex, salt_hex)`. Generates a fresh salt if none is given."""
    if not pepper:
        raise ValueError("a pepper is required to hash a PIN")
    salt_bytes = bytes.fromhex(salt) if salt is not None else secrets.token_bytes(_SALT_BYTES)
    return _derive(pin, pepper, salt_bytes).hex(), salt_bytes.hex()


def verify_pin(pin: str, pin_hash: str, pin_salt: str, *, pepper: str) -> bool:
    """Constant-time comparison; a malformed PIN or an empty pepper never verifies."""
    if not pepper or not is_well_formed_pin(pin):
        return False
    candidate, _ = hash_pin(pin, pepper=pepper, salt=pin_salt)
    return hmac.compare_digest(candidate, pin_hash)


def spend_equal_time(pepper: str) -> None:
    """Burn one derivation's worth of time, so "no such account" cannot be told
    from "wrong PIN" by timing."""
    _derive("0000", pepper or "-", b"\x00" * _SALT_BYTES)
