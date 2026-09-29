"""Account-scoped read tools. Each requires a verified principal and reads only the
principal's own account: the account id comes from the context, never an argument."""

from __future__ import annotations

from pydantic import BaseModel

from secureagent.schemas.tools import (
    BillArgs,
    BillLine,
    BillsResult,
    NoArgs,
    PlanResult,
    UsageResult,
)
from secureagent.store import CustomerStore
from secureagent.tools.base import ToolContext, ToolSpec


def build_account_tools(store: CustomerStore) -> list[ToolSpec]:
    def get_plan(ctx: ToolContext, _: BaseModel) -> BaseModel:
        subscription = store.subscription(ctx.account_id)
        account = store.account(ctx.account_id)
        if subscription is None or account is None:
            raise LookupError("no subscription on record")
        return PlanResult(
            plan_name=subscription.plan_name,
            monthly_cost_usd=subscription.monthly_cost_usd,
            data_allowance_gb=subscription.data_allowance_gb,
            voice_minutes=subscription.voice_minutes,
            contract_end_date=subscription.contract_end_date,
            roaming_enabled=subscription.roaming_enabled,
            account_status=account.status,
        )

    def get_usage(ctx: ToolContext, _: BaseModel) -> BaseModel:
        subscription = store.subscription(ctx.account_id)
        if subscription is None:
            raise LookupError("no subscription on record")
        over = max(0.0, round(subscription.data_used_gb - subscription.data_allowance_gb, 1))
        return UsageResult(
            data_used_gb=subscription.data_used_gb,
            data_allowance_gb=subscription.data_allowance_gb,
            over_allowance=subscription.over_allowance,
            gb_over=over,
        )

    def get_bills(ctx: ToolContext, args: BaseModel) -> BaseModel:
        assert isinstance(args, BillArgs)  # noqa: S101 - validated by the executor
        rows = store.bills(ctx.account_id, limit=min(args.limit or ctx.row_cap, ctx.row_cap))
        lines = [
            BillLine(
                period=b.period,
                plan_charge=b.plan_charge,
                overage_charge=b.overage_charge,
                roaming_charge=b.roaming_charge,
                taxes_fees=b.taxes_fees,
                credits=b.credits,
                total=b.total,
                status=b.status,
            )
            for b in rows
        ]
        return BillsResult(bills=lines, count=len(lines))

    return [
        ToolSpec(
            "get_plan",
            "Read the caller's own plan, allowance, contract end date and account status.",
            NoArgs,
            get_plan,
            requires_verified=True,
        ),
        ToolSpec(
            "get_usage",
            "Read the caller's own data usage against their allowance.",
            NoArgs,
            get_usage,
            requires_verified=True,
        ),
        ToolSpec(
            "get_bills",
            "Read the caller's own recent bills with each charge line.",
            BillArgs,
            get_bills,
            requires_verified=True,
        ),
    ]
