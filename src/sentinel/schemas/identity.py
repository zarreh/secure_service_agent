"""Identity-gate result (D-A4-9). Never carries the submitted PIN or the stored
hash/salt — only the outcome."""

from __future__ import annotations

from pydantic import BaseModel


class IdentityResult(BaseModel):
    verified: bool
    locked: bool
    attempts_remaining: int
    retry_after_seconds: float = 0.0
