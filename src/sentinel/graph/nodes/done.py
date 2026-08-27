"""Walking-skeleton node — replaced by the real `response_node` in Phase 3."""

from sentinel.graph.state import SkeletonState


def done(state: SkeletonState) -> dict[str, list[str]]:
    return {"steps": [*state["steps"], "done"]}
