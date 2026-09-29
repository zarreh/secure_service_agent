"""Credential verification, lockout and the frozen `Principal` (docs/PLAN.md §5.2).

Deliberately unreachable from the graph, tools and guardrails: the credential is
verified in the API layer and only a `Principal` travels (D-A4-2, enforced by an
import-linter contract).
"""

from secureagent.identity.gate import IdentityGate, Verification
from secureagent.identity.lockout import Lockout, LockoutPolicy
from secureagent.identity.pin import hash_pin, is_well_formed_pin, verify_pin

__all__ = [
    "IdentityGate",
    "Lockout",
    "LockoutPolicy",
    "Verification",
    "hash_pin",
    "is_well_formed_pin",
    "verify_pin",
]
