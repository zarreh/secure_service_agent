"""Typed argument and result models for the tools (docs/PLAN.md §5.3).

Argument models are what the *model* sees. None of them has an identity field:
who the caller is comes from the principal, injected by the executor, so a model
has no argument through which to choose it. Results are typed, not JSON strings
the model has to re-parse.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SensitiveAction = Literal[
    "suspend_account",
    "cancel_account",
    "transfer_ownership",
    "reset_pin",
    "sim_change",
    "refund",
]

Urgency = Literal["low", "normal", "high"]

# --- arguments (model-facing; no identity field) ---------------------------


class NoArgs(BaseModel):
    pass


class BillArgs(BaseModel):
    limit: int | None = Field(
        default=None, gt=0, description="How many recent bills to return; capped by the scope."
    )


class OutageArgs(BaseModel):
    region: str = Field(min_length=1, max_length=64, description="The region to check.")


class NetworkTicketArgs(BaseModel):
    issue: str = Field(min_length=1, max_length=500, description="What the customer is seeing.")


class PolicyArgs(BaseModel):
    query: str = Field(min_length=1, max_length=300, description="What to look up in policy.")


class EscalateArgs(BaseModel):
    reason: str = Field(min_length=1, max_length=500, description="Why a human is needed.")
    urgency: Urgency = "normal"


class SensitiveActionArgs(BaseModel):
    action: SensitiveAction = Field(description="The sensitive action being requested.")
    detail: str = Field(max_length=500, default="", description="What the customer asked for.")


# --- results -----------------------------------------------------------------


class _Result(BaseModel):
    model_config = ConfigDict(frozen=True)


class PlanResult(_Result):
    plan_name: str
    monthly_cost_usd: float
    data_allowance_gb: float
    voice_minutes: str
    contract_end_date: str
    roaming_enabled: bool
    account_status: str


class UsageResult(_Result):
    data_used_gb: float
    data_allowance_gb: float
    over_allowance: bool
    gb_over: float


class BillLine(_Result):
    period: str
    plan_charge: float
    overage_charge: float
    roaming_charge: float
    taxes_fees: float
    credits: float
    total: float
    status: str


class BillsResult(_Result):
    bills: list[BillLine]
    count: int


class OutageItem(_Result):
    service: str
    region: str
    started_at: str
    expected_resolution: str
    status: str
    description: str


class OutagesResult(_Result):
    outages: list[OutageItem]
    count: int


class PolicyPassageItem(_Result):
    doc_id: str
    title: str
    text: str


class PolicyResult(_Result):
    """Retrieved policy is *data*. Phase 4 wraps and scans it before a model sees it."""

    passages: list[PolicyPassageItem]
    count: int


class TicketResult(_Result):
    ticket_id: str
    kind: str
    status: str
    performed: bool = Field(
        description="Always False for a sensitive action: the assistant records a request, "
        "it never carries one out."
    )
    note: str
