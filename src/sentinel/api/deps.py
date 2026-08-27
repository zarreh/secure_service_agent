"""FastAPI dependencies: process-shared singletons.

Phase 0 only needs the skeleton graph. Phase 1–4 add the policy/accounts/audit
stores, the tool registry, and the real compiled `sentinel` graph (with a
SQLite checkpointer), following the same `lru_cache`-per-singleton shape as
A3's `api/deps.py`.
"""

from functools import lru_cache

from sentinel.graph.builder import SkeletonGraph, build_skeleton_graph
from sentinel.settings import Settings, get_settings


def settings_dependency() -> Settings:
    return get_settings()


@lru_cache
def get_compiled_graph() -> SkeletonGraph:
    """The Phase 0 skeleton graph, kept as the streaming proof (docs/PLAN.md)."""
    return build_skeleton_graph()
