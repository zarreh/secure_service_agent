"""Typed tools and the principal-bound scoped executor."""

from secureagent.tools.base import ToolContext, ToolSpec
from secureagent.tools.registry import ToolRegistry, build_registry
from secureagent.tools.scoping import ScopedToolExecutor, ToolExecution

__all__ = [
    "ScopedToolExecutor",
    "ToolContext",
    "ToolExecution",
    "ToolRegistry",
    "ToolSpec",
    "build_registry",
]
