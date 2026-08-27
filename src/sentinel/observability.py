"""Logging is provided by `zarreh_agentkit.observability` (extracted substrate);
this module re-exports it so `sentinel.observability` imports keep working, and
carries `build_tracing_callbacks`, needed to make LangSmith tracing actually
run — inheriting `AgentSettings` only supplies the config fields, not the
callback wiring.

A PII-redaction hook (docs/PLAN.md Phase 2/4 — the A4 pattern of redacting at
the trace boundary, not just the response) will make `configure_logging` grow
a local wrapper the way A3's did, once `sentinel.guardrails` exists. Until
then this stays a straight re-export.
"""

from zarreh_agentkit.observability import build_tracing_callbacks, configure_logging, get_logger

__all__ = ["build_tracing_callbacks", "configure_logging", "get_logger"]
