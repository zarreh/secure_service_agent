"""Policy search contract (docs/PLAN.md §5.3). The Qdrant-backed implementation
arrives in Phase 4; tools depend only on this protocol, so they are testable with
a fake and the vector store stays an implementation detail."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PolicyPassage:
    doc_id: str
    title: str
    text: str
    score: float


class PolicySearcher(Protocol):
    def search(self, query: str, *, limit: int) -> list[PolicyPassage]: ...
