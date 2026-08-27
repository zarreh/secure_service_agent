"""A specialist's drafted response (docs/PLAN.md Phase 3).

`citations` names the policy clause ids the draft relied on — the same
citation discipline every other portfolio app uses, so `supervisor_review`
can check groundedness by clause id rather than re-deriving it from prose.
"""

from __future__ import annotations

from pydantic import BaseModel


class SpecialistResponse(BaseModel):
    draft: str
    citations: list[str]
