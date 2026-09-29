"""PIN hashing (docs/PLAN.md §3, §5.2).

**What this does and does not protect against.** A 4-digit PIN has 10,000
possibilities, so *no* key-derivation function makes an offline attack on a
leaked hash expensive. Salted scrypt keeps a PIN out of logs, dumps and casual
disclosure; the two controls that actually resist guessing are:

- a server-side **pepper** (an HMAC key held outside the database), so a stolen
  database alone cannot be brute-forced offline; and
- **online lockout** with backoff (Phase 2), so guessing through the API is slow.

A real carrier needs a real credential, not a PIN (docs/PLAN.md §7.3).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_N, _R, _P = 2**14, 8, 1
_SALT_BYTES = 16
_DKLEN = 32
_MAXMEM = 64 * 1024 * 1024
_PREFIX = "scrypt"


def is_well_formed_pin(pin: str) -> bool:
    """Four ASCII digits. Rejected before any hashing so junk costs nothing."""
    return len(pin) == 4 and pin.isascii() and pin.isdigit()


def _derive(pin: str, pepper: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    keyed = hmac.new(pepper.encode(), pin.encode(), hashlib.sha256).digest()
    return hashlib.scrypt(keyed, salt=salt, n=n, r=r, p=p, maxmem=_MAXMEM, dklen=_DKLEN)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def hash_pin(pin: str, pepper: str, *, salt: bytes | None = None) -> str:
    """`scrypt$N$r$p$salt$digest`. The parameters travel with the hash, so they
    can be raised later without invalidating existing credentials."""
    if not pepper:
        raise ValueError("a pepper is required to hash a PIN")
    if not is_well_formed_pin(pin):
        raise ValueError("a PIN is exactly four digits")
    salt = salt if salt is not None else secrets.token_bytes(_SALT_BYTES)
    digest = _derive(pin, pepper, salt, _N, _R, _P)
    return f"{_PREFIX}${_N}${_R}${_P}${_b64(salt)}${_b64(digest)}"


def verify_pin(pin: str, stored: str, pepper: str) -> bool:
    """Constant-time comparison; a malformed stored value or PIN never verifies."""
    if not pepper or not is_well_formed_pin(pin):
        return False
    try:
        prefix, n, r, p, salt_b64, digest_b64 = stored.split("$")
        if prefix != _PREFIX:
            return False
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(digest_b64, validate=True)
        candidate = _derive(pin, pepper, salt, int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


def spend_equal_time(pepper: str) -> None:
    """Burn one derivation's worth of time.

    Called when an account does not exist, so a caller cannot tell "no such
    account" from "wrong PIN" by timing (account enumeration).
    """
    _derive("0000", pepper or "-", b"\x00" * _SALT_BYTES, _N, _R, _P)
