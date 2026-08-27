"""Deterministic finalize (docs/PLAN.md Phase 3) — a reviewed, guardrail-passed
draft becomes the response verbatim. No model call; nothing left to decide."""

from __future__ import annotations

from sentinel.graph.state import SentinelState


def publish(state: SentinelState) -> dict[str, str]:
    return {"response": state["draft"]}
