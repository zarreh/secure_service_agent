"""Phase 0 walking-skeleton chat endpoint — proves the SSE streaming path end
to end. Replaced by the real `/chat/stream` over `build_sentinel_graph`
starting Phase 4.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from sentinel.api.deps import get_compiled_graph
from sentinel.api.rate_limit import DEFAULT_RATE_LIMIT, limiter
from sentinel.api.streaming import stream_graph_events
from sentinel.graph.builder import SkeletonGraph
from sentinel.graph.state import SkeletonState
from sentinel.schemas.chat import ChatRequest

router = APIRouter(tags=["chat"])


@router.post("/chat/stream")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def chat_stream(
    request: Request,
    body: ChatRequest,
    graph: Annotated[SkeletonGraph, Depends(get_compiled_graph)],
) -> EventSourceResponse:
    initial: SkeletonState = {"question": body.question, "steps": []}
    return EventSourceResponse(stream_graph_events(graph, initial))
