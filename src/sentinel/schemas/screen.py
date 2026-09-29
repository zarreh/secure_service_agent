"""Result of the deterministic input screen (docs/PLAN.md, D-A4-8)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

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
