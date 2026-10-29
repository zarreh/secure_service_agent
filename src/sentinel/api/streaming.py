"""Bridges a LangGraph run to Server-Sent Events, one event per node step.

The node filter is `name == metadata["langgraph_node"]` rather than a
presence check on `langgraph_node`: conditional-edge routing functions also
emit `on_chain_end` with the *source* node in their metadata, under their own
function name (same filter as A3's `api/streaming.py`). Both the filter and the
replay loop now live in `zarreh_agentkit`.
"""

from collections.abc import AsyncIterator
from functools import partial
from typing import Any

from zarreh_agentkit.runs import replay_and_tail
from zarreh_agentkit.serialization import stream_graph_events

from sentinel.store.run_store import RunStore

__all__ = ["stream_graph_events", "stream_run_events"]


def stream_run_events(run_store: RunStore, run_id: str) -> AsyncIterator[str]:
    """Replays every event already persisted for a run, then — while it is
    still executing — tails newly-appended events until it reaches a
    terminal status. Works identically whether the client connects the
    instant a run starts or reconnects long after it finished."""

    def poll_end() -> dict[str, Any] | None:
        run = run_store.get_run(run_id)
        if run is not None and run.status == "running":
            return None
        status = run.status if run is not None else "not_found"
        response = run.response if run is not None else None
        return {"status": status, "response": response}

    return replay_and_tail(partial(run_store.get_events, run_id), poll_end)
