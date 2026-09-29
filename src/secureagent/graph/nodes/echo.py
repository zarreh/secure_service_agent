"""Walking-skeleton node — replaced by the real `input_screen` node in Phase 3."""

from secureagent.graph.state import SkeletonState


def echo(state: SkeletonState) -> dict[str, list[str]]:
    return {"steps": [*state["steps"], f"echo:{state['question']}"]}
