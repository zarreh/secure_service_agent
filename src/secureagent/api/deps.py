"""FastAPI dependencies: process-shared singletons, built once and injected."""

from __future__ import annotations

from functools import lru_cache

from secureagent.graph.builder import SkeletonGraph, build_skeleton_graph
from secureagent.settings import Settings, get_settings


def settings_dependency() -> Settings:
    return get_settings()


@lru_cache
def get_compiled_graph() -> SkeletonGraph:
    """The Phase 0 skeleton graph, kept as the streaming proof (docs/PLAN.md §9)."""
    return build_skeleton_graph()
