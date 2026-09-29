"""Scoping records: what a run may reach, what it did, and what was refused."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SecurityEventKind = Literal[
    "identity_argument_supplied",
    "unexpected_argument",
    "blocked_unknown_tool",
    "out_of_scope_tool",
    "invalid_arguments",
]


class ToolScope(BaseModel):
    """The tools a run may reach and how many rows each may return.

    Derived from the principal by the registry. A tool outside the scope is
    unreachable, not merely discouraged.
    """

    model_config = ConfigDict(frozen=True)

    allowed_tool_names: frozenset[str]
    row_cap: int = Field(gt=0)


class EvidenceRecord(BaseModel):
    """One executed tool call, addressable by `tool_call_id`."""

    model_config = ConfigDict(frozen=True)

    tool_call_id: str
    tool_name: str
    args: dict[str, object]
    result: dict[str, object]
    retrieved_at: str


class SecurityEvent(BaseModel):
    """A control that fired, persisted and surfaced in the trace.

    `requested` is what the model asked for; `enforced` is what happened. An
    attempt to name another customer's account is the most interesting event this
    system records.
    """

    model_config = ConfigDict(frozen=True)

    kind: SecurityEventKind
    tool_name: str
    requested: str
    enforced: str
    run_id: str
    at: str
