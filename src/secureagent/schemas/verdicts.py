"""Verdicts produced by the input and output envelopes (docs/PLAN.md §5.1, §5.4)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Verdict = Literal["allow", "flag", "block"]
Severity = Literal["block", "flag"]


class ScreenMatch(BaseModel):
    """One rule that matched, and which normalised view of the message it matched in.

    `view` is what makes a block attributable to an evasion technique: a match in
    `spaced` or `decoded1` means the raw text would have passed a plain regex.
    """

    model_config = ConfigDict(frozen=True)

    category: str
    severity: Severity
    view: str
    span: str


class ScreenResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    verdict: Verdict
    matches: list[ScreenMatch] = []

    @property
    def categories(self) -> list[str]:
        return sorted({m.category for m in self.matches})


class InjectionAssessment(BaseModel):
    """The layer-2 classifier's structured output (docs/PLAN.md §5.1).

    `span` is a verbatim quote from the message, so the judgement is falsifiable
    against the actual text rather than a free-text rationale. `confidence` is
    recorded, never trusted: the architecture holds if this is wrong.
    """

    model_config = ConfigDict(frozen=True)

    verdict: Literal["safe", "unsafe"]
    category: str = ""
    span: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
