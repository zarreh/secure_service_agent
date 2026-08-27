"""The only file that wires nodes and edges (docs/PLAN.md §9.3).

`build_skeleton_graph` is the Phase 0 walking skeleton, kept so the streaming
path stays proven end to end once `build_sentinel_graph` exists. The real
graph is wired incrementally starting Phase 2 (docs/PLAN.md): input guardrail
-> identity gate -> context loader -> supervisor -> one of four specialists ->
supervisor review -> output guardrail -> response.

Node filename == registered node name == trace span name (§9.3 rule 3).
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from sentinel.graph.nodes.done import done
from sentinel.graph.nodes.echo import echo
from sentinel.graph.state import SkeletonState

SkeletonGraph = CompiledStateGraph[SkeletonState, None, SkeletonState, SkeletonState]


def build_skeleton_graph() -> SkeletonGraph:
    """Phase 0 walking skeleton: echo -> done."""
    workflow = StateGraph(SkeletonState)
    workflow.add_node("echo", echo)
    workflow.add_node("done", done)
    workflow.set_entry_point("echo")
    workflow.add_edge("echo", "done")
    workflow.add_edge("done", END)
    return workflow.compile()
