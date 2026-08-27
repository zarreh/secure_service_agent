"""Walking-skeleton node — replaced by the real `guardrail` (input) node in
Phase 2."""

from sentinel.graph.state import SkeletonState


def echo(state: SkeletonState) -> dict[str, list[str]]:
    return {"steps": [*state["steps"], f"echo:{state['question']}"]}
