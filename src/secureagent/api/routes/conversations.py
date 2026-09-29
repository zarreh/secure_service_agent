"""Conversation API. Phase 0 exposes only the walking-skeleton stream; the real
run/persistence endpoints arrive in Phase 6 (docs/PLAN.md §9)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from secureagent.api.deps import get_compiled_graph
from secureagent.api.rate_limit import DEFAULT_RATE_LIMIT, limiter
from secureagent.api.streaming import stream_graph_events
from secureagent.graph.builder import SkeletonGraph

router = APIRouter(prefix="/conversations", tags=["conversations"])


class StreamRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)


@router.post("/stream")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def stream_skeleton(
    request: Request,
    body: StreamRequest,
    graph: Annotated[SkeletonGraph, Depends(get_compiled_graph)],
) -> EventSourceResponse:
    return EventSourceResponse(stream_graph_events(graph, {"question": body.question, "steps": []}))
