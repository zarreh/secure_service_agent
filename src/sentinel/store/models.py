"""Typed records returned by the stores.

Every account record carries a PIN **hash and salt**, never a PIN — the
identity gate (Phase 2) verifies a submitted PIN against these via
`sentinel.store.pin_hash.verify_pin` and never holds a plaintext PIN in
state or in a log line.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class PolicyClause(BaseModel):
    """One clause of the support-policy knowledge base, split on its
    ``POLICY: <title>`` heading (docs/PLAN.md Phase 1)."""

    clause_id: str
    title: str
    body: str
    page: int


class Account(BaseModel):
    account_id: str
    customer_name: str
    pin_hash: str
    pin_salt: str
    account_status: str
    autopay_enabled: bool
    date_joined: date


class Plan(BaseModel):
    account_id: str
    plan_name: str
    monthly_cost_usd: float
    data_allowance_gb: float
    data_used_gb: float
    voice_minutes: str
    contract_end_date: date
    roaming_enabled: bool


class MemoryEvent(BaseModel):
    """One prior support interaction, surfaced to `context_loader` (Phase 3)
    so a specialist can see history without a fresh account-wide query."""

    account_id: str
    timestamp: datetime
    query: str
    intent: str
    agent_used: str
    resolution_type: str
    response_summary: str
