"""Structural (Protocol) types for the LLM-backed pieces nodes depend on.

Node factories accept these instead of concrete `Runnable[...]` types so a
plain test double (with just a matching `.invoke()`) can stand in without
subclassing LangChain's `Runnable` — real chains satisfy them structurally
too. Empty until Phase 2 adds the injection/leak scanner and review-judge
chains.
"""

from __future__ import annotations
