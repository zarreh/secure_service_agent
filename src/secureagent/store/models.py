"""Typed read models for the service database.

Frozen dataclasses: internal read models, not API or tool boundaries (those are
Pydantic and live in `schemas/`). `Account` deliberately has no credential field.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    account_id: str
    name: str
    phone: str
    address: str
    region: str
    status: str
    autopay: bool
    date_joined: str


@dataclass(frozen=True)
class Subscription:
    account_id: str
    plan_name: str
    monthly_cost_usd: float
    data_allowance_gb: float
    data_used_gb: float
    voice_minutes: str
    contract_end_date: str
    roaming_enabled: bool

    @property
    def over_allowance(self) -> bool:
        return self.data_used_gb > self.data_allowance_gb


@dataclass(frozen=True)
class Bill:
    bill_id: str
    account_id: str
    period: str
    plan_charge: float
    overage_charge: float
    roaming_charge: float
    taxes_fees: float
    credits: float
    total: float
    status: str


@dataclass(frozen=True)
class Outage:
    outage_id: str
    region: str
    service: str
    started_at: str
    expected_resolution: str
    status: str
    description: str


@dataclass(frozen=True)
class MemoryEntry:
    memory_id: str
    account_id: str
    created_at: str
    intent: str
    summary: str
