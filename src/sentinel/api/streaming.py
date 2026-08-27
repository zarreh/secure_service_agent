"""Bridges a LangGraph run to Server-Sent Events, one event per node step.

The node filter is `name == metadata["langgraph_node"]` rather than a
presence check on `langgraph_node`: conditional-edge routing functions also
emit `on_chain_end` with the *source* node in their metadata, under their own
function name (same filter as A3's `api/streaming.py`).
"""

import asyncio
import json
from collections.abc import AsyncIterator

from sentinel.graph.builder import SkeletonGraph
from sentinel.graph.state import SkeletonState
from sentinel.store.run_store import RunStore

_POLL_INTERVAL_SECONDS = 0.25


async def stream_graph_events(
    graph: SkeletonGraph, initial_state: SkeletonState
) -> AsyncIterator[str]:
    async for event in graph.astream_events(initial_state, version="v2"):
        if event["event"] != "on_chain_end":
            continue
        node = event.get("metadata", {}).get("langgraph_node")
        if not node or event.get("name") != node:
            continue
        yield json.dumps({"node": node, "output": event.get("data", {}).get("output")}, default=str)
    yield json.dumps({"node": "__end__", "output": None})


async def stream_run_events(run_store: RunStore, run_id: str) -> AsyncIterator[str]:
    """Replays every event already persisted for a run, then — while it is
    still executing — tails newly-appended events until it reaches a
    terminal status. Works identically whether the client connects the
    instant a run starts or reconnects long after it finished."""
    last_sequence = -1
    while True:
        events = run_store.get_events(run_id, after_sequence=last_sequence)
        for event in events:
            yield json.dumps({"node": event.node, "output": json.loads(event.payload_json)})
            last_sequence = event.sequence

        run = run_store.get_run(run_id)
        if run is None or run.status != "running":
            break
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)

    status = run.status if run is not None else "not_found"
    response = run.response if run is not None else None
    yield json.dumps({"node": "__end__", "output": {"status": status, "response": response}})
