"""Bridges a LangGraph run to Server-Sent Events, one event per node step.

Kept local rather than imported from `zarreh_agentkit.serialization` because the
published v0.2.0 emits every `on_chain_end`, including the graph-level event and
conditional-edge routing functions. The node filter is `name ==
metadata["langgraph_node"]`; the fix is in library v0.2.1 (docs/HARVEST.md).
"""

import json
from collections.abc import AsyncIterator

from secureagent.graph.builder import SkeletonGraph
from secureagent.graph.state import SkeletonState


async def stream_graph_events(
    graph: SkeletonGraph, initial_state: SkeletonState
) -> AsyncIterator[str]:
    async for event in graph.astream_events(initial_state, version="v2"):
        if event["event"] != "on_chain_end":
            continue
        node = (event.get("metadata") or {}).get("langgraph_node")
        if not node or event.get("name") != node:
            continue
        yield json.dumps({"node": node, "output": event.get("data", {}).get("output")}, default=str)
    yield json.dumps({"node": "__end__", "output": None})
