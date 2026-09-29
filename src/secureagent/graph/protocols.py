"""Structural (Protocol) types for the model-backed pieces nodes depend on.

Node factories accept these rather than concrete `Runnable` types, so a plain test
double with a matching `.invoke()` stands in without subclassing LangChain -- and
real chains satisfy them structurally too. This is what lets the whole envelope be
tested with no LLM and no network.
"""

from __future__ import annotations

from typing import Protocol

from secureagent.schemas.verdicts import InjectionAssessment


class InjectionClassifierChain(Protocol):
    def invoke(self, input: dict[str, str]) -> InjectionAssessment: ...
