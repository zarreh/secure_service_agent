"""Graph state.

`SkeletonState` is the Phase 0 walking skeleton, kept so the streaming path stays
proven end to end. The real state and its per-node views arrive in Phase 4
(docs/PLAN.md §4.3).
"""

from __future__ import annotations

from typing import TypedDict


class SkeletonState(TypedDict):
    question: str
    steps: list[str]
