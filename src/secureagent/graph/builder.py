"""The only file that wires nodes and edges (docs/PLAN.md §9.3).

`build_skeleton_graph` is the Phase 0 walking skeleton: it proves a run streams
node by node through the API before any real node exists.

Node filename == registered node name == trace span name (§9.3 rule 3).
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from secureagent.graph.nodes.done import done
from secureagent.graph.nodes.echo import echo
from secureagent.graph.state import SkeletonState

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
