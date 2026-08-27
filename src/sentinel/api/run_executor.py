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

import json

import structlog
from pydantic import BaseModel
from zarreh_agentkit.cost import CostEntry
from zarreh_agentkit.observability import build_tracing_callbacks

from sentinel.graph.builder import SentinelGraph
from sentinel.graph.cost_tracking import CostTrackingHandler
from sentinel.graph.state import SentinelState
from sentinel.observability import get_logger
from sentinel.settings import Settings
from sentinel.store.run_store import RunStore

logger = get_logger(__name__)

# Only these are genuine node boundaries: astream_events also emits
# on_chain_end for internal LCEL sub-steps (prompt templates, parsers, the
# routing predicates themselves), whose event names can collide with a
# node's langgraph_node tag — filtering on name alone is not enough.
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


def _json_default(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return str(value)


async def execute_chat(
    run_id: str,
    question: str,
    account_id: str,
    pin: str,
    graph: SentinelGraph,
    run_store: RunStore,
    settings: Settings,
) -> None:
    """`pin` is used only to build the initial state passed to `graph.ainvoke`
    equivalent below — it is never written to `run_store` and no node output
    ever includes it (D-A4-2), so nothing here needs to scrub it after the
    fact."""
    structlog.contextvars.bind_contextvars(correlation_id=run_id)
    try:
        cost_handler = CostTrackingHandler()
        callbacks = [
            cost_handler,
            *build_tracing_callbacks(settings.langsmith_api_key, settings.langsmith_project),
        ]
        initial: SentinelState = {
            "question": question,
            "account_id": account_id,
            "pin": pin,
        }
        final_state: dict[str, object] = {}
        sequence = 0

        async for event in graph.astream_events(
            initial,
            version="v2",
            config={"callbacks": callbacks, "metadata": {"correlation_id": run_id}},
        ):
            if event["event"] != "on_chain_end":
                continue
            metadata = event.get("metadata") or {}
            node_name = metadata.get("langgraph_node")
            if node_name not in _GRAPH_NODE_NAMES or event.get("name") != node_name:
                continue

            output = event.get("data", {}).get("output")
            if isinstance(output, dict):
                final_state.update(output)
            run_store.append_event(
                run_id, sequence, node_name, json.dumps(output, default=_json_default)
            )
            sequence += 1

        run_store.record_costs(
            run_id,
            [
                CostEntry(e.node, e.model, e.prompt_tokens, e.completion_tokens, e.cost_usd)
                for e in cost_handler.entries
            ],
        )
        _finalize(run_store, run_id, final_state)
    except Exception as exc:  # noqa: BLE001 — any failure must mark the run failed
        logger.error("chat_failed", run_id=run_id, error=str(exc))
        run_store.fail_run(run_id, str(exc))
    finally:
        structlog.contextvars.unbind_contextvars("correlation_id")


def _finalize(run_store: RunStore, run_id: str, final_state: dict[str, object]) -> None:
    response = final_state.get("response")
    if isinstance(response, str):
        run_store.complete_run(run_id, response)
        return
    run_store.fail_run(run_id, "graph completed without producing a response")
