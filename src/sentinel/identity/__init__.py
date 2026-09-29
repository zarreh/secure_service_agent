"""Credential verification and lockout. Reachable from the API layer only: the graph,
tools and guardrails never import this package (enforced by import-linter,
D-A4-9)."""

from sentinel.identity.gate import IdentityGate
from sentinel.identity.lockout import Lockout, LockoutPolicy

__all__ = ["IdentityGate", "Lockout", "LockoutPolicy"]
