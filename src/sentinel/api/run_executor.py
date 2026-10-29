"""Runs one chat request to completion, persisting every node event and the
final response to the RunStore as it happens — so a run is replayable from
the store whether a client is watching live or reconnects later (docs/PLAN.md
Phase 4). Runs as an in-process background task: a single-instance demo
deployment doesn't need a separate task queue.

This is the audit log the security-envelope story depends on: every
guardrail verdict, the identity result, and the routing decision are node
outputs, so persisting every event persists every guardrail decision.
"""

from __future__ import annotations

from typing import Any

from zarreh_agentkit.observability import build_tracing_callbacks
from zarreh_agentkit.runs import execute_run

from sentinel.graph.builder import SentinelGraph
from sentinel.graph.state import SentinelState
from sentinel.settings import Settings
from sentinel.store.run_store import RunStore

# Only these are genuine node boundaries (execute_run also requires
# name == langgraph_node, which drops routing predicates and LCEL sub-steps).
_GRAPH_NODE_NAMES = frozenset(
    {
        "guardrail",
        "identity_gate",
        "context_loader",
        "supervisor",
        "network_agent",
        "billing_agent",
        "account_agent",
        "escalation_agent",
        "supervisor_review",
        "output_guardrail",
        "publish",
        "blocked_input_response",
        "verification_required",
        "give_up",
        "blocked_output_response",
    }
)


async def execute_chat(
    run_id: str,
    question: str,
    account_id: str,
    pin: str,
    graph: SentinelGraph,
    run_store: RunStore,
    settings: Settings,
) -> None:
    """`pin` is used only to build the initial graph input — it is never
    written to `run_store` (execute_run persists node *outputs* only) and no
    node output ever includes it (D-A4-2), so nothing here needs to scrub it
    after the fact."""
    initial: SentinelState = {
        "question": question,
        "account_id": account_id,
        "pin": pin,
    }
    await execute_run(
        run_id=run_id,
        graph=graph,
        graph_input=initial,
        store=run_store,
        finalize=lambda final_state: _finalize(run_store, run_id, final_state),
        callbacks=build_tracing_callbacks(settings.langsmith_api_key, settings.langsmith_project),
        node_names=_GRAPH_NODE_NAMES,
    )


def _finalize(run_store: RunStore, run_id: str, final_state: dict[str, Any]) -> None:
    response = final_state.get("response")
    if isinstance(response, str):
        run_store.complete_run(run_id, response)
        return
    run_store.fail_run(run_id, "graph completed without producing a response")
