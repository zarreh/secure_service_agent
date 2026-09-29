"""Walking-skeleton node — replaced by the real `respond` node in Phase 5."""

from secureagent.graph.state import SkeletonState


def done(state: SkeletonState) -> dict[str, list[str]]:
    return {"steps": [*state["steps"], "done"]}
