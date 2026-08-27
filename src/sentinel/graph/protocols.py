"""Structural (Protocol) types for the LLM-backed pieces nodes depend on.

Node factories accept these instead of concrete `Runnable[...]` types so a
plain test double (with just a matching `.invoke()`) can stand in without
subclassing LangChain's `Runnable` — real chains satisfy them structurally
too. This is what lets the guardrail nodes be tested with no LLM and no
network (docs/PLAN.md Phase 2).
"""

from __future__ import annotations

from typing import Protocol

from sentinel.schemas.guardrail import InjectionScanResult, LeakScanResult


class InjectionScanChain(Protocol):
    def invoke(self, input: dict[str, str]) -> InjectionScanResult: ...


class LeakScanChain(Protocol):
    def invoke(self, input: dict[str, object]) -> LeakScanResult: ...
