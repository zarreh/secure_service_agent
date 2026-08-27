"""Chat API (docs/PLAN.md Phase 4).

`POST /chat/stream` is the Phase 0 walking-skeleton stream, kept as the
streaming proof. `POST /chat` starts a real run as a background task and
returns immediately with its id; the work persists every node event (the
audit log) to the run store as it happens. `GET /chat/{run_id}` returns the
durable record and per-node cost; `GET /chat/{run_id}/events` streams the
run — replaying what already happened, then tailing to completion.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from sentinel.api.deps import (
    get_compiled_graph,
    get_run_store,
    get_sentinel_graph,
    settings_dependency,
)
from sentinel.api.rate_limit import DEFAULT_RATE_LIMIT, limiter
from sentinel.api.run_executor import execute_chat
from sentinel.api.schemas import (
    ChatRunResponse,
    CostSummaryEntry,
    CreateChatRequest,
    CreateChatResponse,
)
from sentinel.api.streaming import stream_graph_events, stream_run_events
from sentinel.graph.builder import SentinelGraph, SkeletonGraph
from sentinel.graph.state import SkeletonState
from sentinel.schemas.chat import ChatRequest
from sentinel.settings import Settings
from sentinel.store.run_store import RunStore

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


@router.post("/chat", status_code=202)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def create_chat(
    request: Request,
    body: CreateChatRequest,
    background_tasks: BackgroundTasks,
    graph: Annotated[SentinelGraph, Depends(get_sentinel_graph)],
    run_store: Annotated[RunStore, Depends(get_run_store)],
    settings: Annotated[Settings, Depends(settings_dependency)],
) -> CreateChatResponse:
    """Deliberately does not pre-check whether `account_id` exists: a 404
    here vs. a 202 for a real account would be exactly the enumeration
    oracle D-A4-2 closes at the store layer. An unknown account reaches
    `identity_gate` like any other and comes back `unverified`, same as a
    real account with a wrong PIN."""
    run_id = uuid.uuid4().hex
    run_store.create_run(run_id, body.question, body.account_id)
    background_tasks.add_task(
        execute_chat, run_id, body.question, body.account_id, body.pin, graph, run_store, settings
    )
    return CreateChatResponse(id=run_id, status="running")


@router.get("/chat/{run_id}")
async def get_chat(
    run_id: str, run_store: Annotated[RunStore, Depends(get_run_store)]
) -> ChatRunResponse:
    run = run_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="chat run not found")
    costs = run_store.get_costs(run_id)
    return ChatRunResponse(
        id=run.id,
        question=run.question,
        account_id=run.account_id,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        response=run.response,
        error=run.error,
        total_cost_usd=sum(c.cost_usd for c in costs),
        costs=[
            CostSummaryEntry(
                node=c.node,
                model=c.model,
                prompt_tokens=c.prompt_tokens,
                completion_tokens=c.completion_tokens,
                cost_usd=c.cost_usd,
            )
            for c in costs
        ],
    )


@router.get("/chat/{run_id}/events")
async def stream_chat(
    run_id: str, run_store: Annotated[RunStore, Depends(get_run_store)]
) -> EventSourceResponse:
    if run_store.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="chat run not found")
    return EventSourceResponse(stream_run_events(run_store, run_id))
