"""The only file that wires nodes and edges (docs/PLAN.md §9.3).

`build_skeleton_graph` is the Phase 0 walking skeleton, kept so the streaming
path stays proven end to end. `build_sentinel_graph` wires the real graph
(docs/PLAN.md): input guardrail -> identity gate -> context loader ->
supervisor -> one of four specialists -> supervisor review (retrying the same
specialist once, then giving up) -> output guardrail -> publish.

Node filename == registered node name == trace span name (§9.3 rule 3).
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Checkpointer

from sentinel.graph.chains.account_specialist import build_account_specialist_chain
from sentinel.graph.chains.billing_specialist import build_billing_specialist_chain
from sentinel.graph.chains.escalation_specialist import build_escalation_specialist_chain
from sentinel.graph.chains.injection_scan import build_injection_scan_chain
from sentinel.graph.chains.leak_scan import build_leak_scan_chain
from sentinel.graph.chains.network_specialist import build_network_specialist_chain
from sentinel.graph.chains.supervisor_review import build_supervisor_review_chain
from sentinel.graph.chains.supervisor_route import build_supervisor_route_chain
from sentinel.graph.edges import (
    route_after_guardrail,
    route_after_identity,
    route_after_output_guardrail,
    route_after_review,
    route_supervisor_to_agent,
)
from sentinel.graph.nodes.account_agent import build_account_agent_node
from sentinel.graph.nodes.billing_agent import build_billing_agent_node
from sentinel.graph.nodes.blocked_input_response import blocked_input_response
from sentinel.graph.nodes.blocked_output_response import blocked_output_response
from sentinel.graph.nodes.context_loader import build_context_loader_node
from sentinel.graph.nodes.done import done
from sentinel.graph.nodes.echo import echo
from sentinel.graph.nodes.escalation_agent import build_escalation_agent_node
from sentinel.graph.nodes.give_up import give_up
from sentinel.graph.nodes.guardrail import build_guardrail_node
from sentinel.graph.nodes.identity_gate import build_identity_gate_node
from sentinel.graph.nodes.network_agent import build_network_agent_node
from sentinel.graph.nodes.output_guardrail import build_output_guardrail_node
from sentinel.graph.nodes.publish import publish
from sentinel.graph.nodes.supervisor import build_supervisor_node
from sentinel.graph.nodes.supervisor_review import build_supervisor_review_node
from sentinel.graph.nodes.verification_required import verification_required
from sentinel.graph.policies import build_fast_model, build_reasoning_model
from sentinel.graph.protocols import (
    EscalationChain,
    InjectionScanChain,
    LeakScanChain,
    SpecialistChain,
    SupervisorReviewChain,
    SupervisorRouteChain,
)
from sentinel.graph.state import SentinelState, SkeletonState
from sentinel.settings import Settings
from sentinel.store.account_store import AccountStore

SkeletonGraph = CompiledStateGraph[SkeletonState, None, SkeletonState, SkeletonState]
SentinelGraph = CompiledStateGraph[SentinelState, None, SentinelState, SentinelState]


def build_skeleton_graph() -> SkeletonGraph:
    """Phase 0 walking skeleton: echo -> done."""
    workflow = StateGraph(SkeletonState)
    workflow.add_node("echo", echo)
    workflow.add_node("done", done)
    workflow.set_entry_point("echo")
    workflow.add_edge("echo", "done")
    workflow.add_edge("done", END)
    return workflow.compile()


def build_sentinel_graph(
    settings: Settings,
    store: AccountStore,
    *,
    injection_chain: InjectionScanChain | None = None,
    leak_chain: LeakScanChain | None = None,
    route_chain: SupervisorRouteChain | None = None,
    network_chain: SpecialistChain | None = None,
    billing_chain: SpecialistChain | None = None,
    account_chain: SpecialistChain | None = None,
    escalation_chain: EscalationChain | None = None,
    review_chain: SupervisorReviewChain | None = None,
    checkpointer: Checkpointer = None,
) -> SentinelGraph:
    """The only function that wires the real graph's nodes and edges.

    Every LLM-backed chain is injectable so the graph can be assembled and
    tested offline with stubs (docs/PLAN.md Phase 2/3); in production they
    are built from the configured models.
    """
    if (
        injection_chain is None
        or leak_chain is None
        or route_chain is None
        or escalation_chain is None
    ):
        fast_model = build_fast_model(settings)
        if injection_chain is None:
            injection_chain = build_injection_scan_chain(fast_model)
        if leak_chain is None:
            leak_chain = build_leak_scan_chain(fast_model)
        if route_chain is None:
            route_chain = build_supervisor_route_chain(fast_model)
        if escalation_chain is None:
            escalation_chain = build_escalation_specialist_chain(fast_model)

    if (
        network_chain is None
        or billing_chain is None
        or account_chain is None
        or review_chain is None
    ):
        reasoning_model = build_reasoning_model(settings)
        if network_chain is None:
            network_chain = build_network_specialist_chain(reasoning_model)
        if billing_chain is None:
            billing_chain = build_billing_specialist_chain(reasoning_model)
        if account_chain is None:
            account_chain = build_account_specialist_chain(reasoning_model)
        if review_chain is None:
            review_chain = build_supervisor_review_chain(reasoning_model)

    # mypy cannot resolve add_node's overloads against a factory-returned
    # Callable (vs. a plain top-level function) — confirmed upstream
    # limitation, not a real type error; each node is unit-tested directly
    # in tests/graph/ (same precedent as A3's builder.py).
    guardrail_node = build_guardrail_node(injection_chain)
    identity_gate_node = build_identity_gate_node(store, settings)
    context_loader_node = build_context_loader_node(store)
    supervisor_node = build_supervisor_node(route_chain)
    network_agent_node = build_network_agent_node(network_chain)
    billing_agent_node = build_billing_agent_node(store, billing_chain)
    account_agent_node = build_account_agent_node(store, account_chain)
    escalation_agent_node = build_escalation_agent_node(escalation_chain)
    supervisor_review_node = build_supervisor_review_node(review_chain)
    output_guardrail_node = build_output_guardrail_node(leak_chain)

    workflow = StateGraph(SentinelState)
    workflow.add_node("guardrail", guardrail_node)  # type: ignore[arg-type]
    workflow.add_node("identity_gate", identity_gate_node)  # type: ignore[arg-type]
    workflow.add_node("context_loader", context_loader_node)  # type: ignore[arg-type]
    workflow.add_node("supervisor", supervisor_node)  # type: ignore[arg-type]
    workflow.add_node("network_agent", network_agent_node)  # type: ignore[arg-type]
    workflow.add_node("billing_agent", billing_agent_node)  # type: ignore[arg-type]
    workflow.add_node("account_agent", account_agent_node)  # type: ignore[arg-type]
    workflow.add_node("escalation_agent", escalation_agent_node)  # type: ignore[arg-type]
    workflow.add_node("supervisor_review", supervisor_review_node)  # type: ignore[arg-type]
    workflow.add_node("output_guardrail", output_guardrail_node)  # type: ignore[arg-type]
    workflow.add_node("publish", publish)
    workflow.add_node("blocked_input_response", blocked_input_response)
    workflow.add_node("verification_required", verification_required)
    workflow.add_node("give_up", give_up)
    workflow.add_node("blocked_output_response", blocked_output_response)

    workflow.set_entry_point("guardrail")
    workflow.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {"blocked": "blocked_input_response", "allow": "identity_gate"},
    )
    workflow.add_conditional_edges(
        "identity_gate",
        route_after_identity,
        {"verified": "context_loader", "unverified": "verification_required"},
    )
    workflow.add_edge("context_loader", "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor_to_agent,
        {
            "network": "network_agent",
            "billing": "billing_agent",
            "account": "account_agent",
            "escalation": "escalation_agent",
        },
    )
    for agent in ("network_agent", "billing_agent", "account_agent", "escalation_agent"):
        workflow.add_edge(agent, "supervisor_review")
    workflow.add_conditional_edges(
        "supervisor_review",
        route_after_review,
        {
            "output_guardrail": "output_guardrail",
            "network": "network_agent",
            "billing": "billing_agent",
            "account": "account_agent",
            "escalation": "escalation_agent",
            "give_up": "give_up",
        },
    )
    workflow.add_conditional_edges(
        "output_guardrail",
        route_after_output_guardrail,
        {"respond": "publish", "blocked": "blocked_output_response"},
    )
    workflow.add_edge("publish", END)
    workflow.add_edge("blocked_input_response", END)
    workflow.add_edge("verification_required", END)
    workflow.add_edge("give_up", END)
    workflow.add_edge("blocked_output_response", END)
    return workflow.compile(checkpointer=checkpointer)
