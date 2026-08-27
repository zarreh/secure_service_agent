"""Salted PIN hashing.

The identity gate (Phase 2) is the whole reason this app exists, so the PIN
never sits in the store — or in a log line, or in graph state — as plaintext.
`hash_pin` is used once, at build time (`data/generate_accounts.py`);
`verify_pin` is used on every identity-gate check.

PBKDF2-HMAC-SHA256 rather than a fast general-purpose hash: PINs are
low-entropy (4 digits here), so the hash must be deliberately slow to make
offline brute-force of a leaked `accounts.db` expensive. `hashlib.pbkdf2_hmac`
needs no extra dependency.
"""

from __future__ import annotations

import hashlib
import secrets

_ITERATIONS = 260_000


def hash_pin(pin: str, salt: str | None = None) -> tuple[str, str]:
    """Returns `(hash_hex, salt_hex)`. Generates a fresh salt if none is given."""
    salt_bytes = bytes.fromhex(salt) if salt is not None else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt_bytes, _ITERATIONS)
    return digest.hex(), salt_bytes.hex()


def verify_pin(pin: str, pin_hash: str, pin_salt: str) -> bool:
    """Constant-time comparison against a stored hash."""
    candidate, _ = hash_pin(pin, salt=pin_salt)
    return secrets.compare_digest(candidate, pin_hash)
