"""API-contract request/response models — separate from `schemas/`, which
holds the domain models the graph itself produces (docs/PLAN.md Phase 4).

`CreateChatRequest.pin` is `Field(exclude=True)` nowhere near enough on its
own — the real guarantee is architectural (D-A4-2: no node output ever
includes it) — but excluding it here too means even a naive
`request.model_dump()` in a future log statement can't leak it.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    account_id: str = Field(min_length=1, max_length=64)
    pin: str = Field(min_length=1, max_length=16, exclude=True)


class CreateChatResponse(BaseModel):
    id: str
    status: str


class CostSummaryEntry(BaseModel):
    node: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


class ChatRunResponse(BaseModel):
    id: str
    question: str
    account_id: str
    status: str
    created_at: str
    updated_at: str
    response: str | None
    error: str | None
    total_cost_usd: float
    costs: list[CostSummaryEntry]
