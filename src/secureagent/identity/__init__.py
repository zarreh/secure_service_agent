"""Credential verification, lockout and the frozen `Principal` (docs/PLAN.md §5.2).

Deliberately unreachable from the graph, tools and guardrails: the credential is
verified in the API layer and only a `Principal` travels (D-A4-2, enforced by an
import-linter contract). Populated in Phase 2.
"""
