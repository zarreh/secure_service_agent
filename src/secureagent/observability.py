"""Logging is provided by `zarreh_agentkit.observability`; re-exported here so
`secureagent.observability` is the one import path the app uses.

The redacting log processor (docs/PLAN.md §5.5) arrives in Phase 6 and needs
the library's `extra_processors` hook, which is in v0.2.1 and not yet published
(docs/HARVEST.md).
"""

from zarreh_agentkit.observability import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger"]
