"""Tools that record a request. None of them performs anything (docs/PLAN.md §4.2 #3).

Excessive agency is removed by construction rather than policed: there is no tool
that refunds, suspends, cancels, transfers, resets a PIN or changes a SIM. Those
requests become tickets a human completes, and (mirroring 47 CFR 64.2010(f)) an
account-change notice is queued for the contact details already on file.
"""

from __future__ import annotations

from pydantic import BaseModel

from secureagent.schemas.tools import (
    EscalateArgs,
    NetworkTicketArgs,
    SensitiveActionArgs,
    TicketResult,
)
from secureagent.store.ticket_store import TicketStore
from secureagent.tools.base import ToolContext, ToolSpec

_SENSITIVE_NOTE = (
    "Request recorded for a human agent. It has NOT been carried out, and it will not be "
    "until an additional verification step is completed."
)


def build_action_tools(tickets: TicketStore) -> list[ToolSpec]:
    def raise_network_ticket(ctx: ToolContext, args: BaseModel) -> BaseModel:
        assert isinstance(args, NetworkTicketArgs)  # noqa: S101 - validated by the executor
        ticket_id = tickets.create(
            account_id=ctx.account_id, kind="network", summary=args.issue, urgency="normal"
        )
        return TicketResult(
            ticket_id=ticket_id,
            kind="network",
            status="open",
            performed=False,
            note="A network ticket was opened for the field team.",
        )

    def escalate_to_human(ctx: ToolContext, args: BaseModel) -> BaseModel:
        assert isinstance(args, EscalateArgs)  # noqa: S101 - validated by the executor
        # Available to unverified callers too: a locked-out customer still needs a person.
        ticket_id = tickets.create(
            account_id=ctx.principal.account_id,
            kind="escalation",
            summary=args.reason,
            urgency=args.urgency,
        )
        return TicketResult(
            ticket_id=ticket_id,
            kind="escalation",
            status="open",
            performed=False,
            note="A human agent will follow up.",
        )

    def request_sensitive_action(ctx: ToolContext, args: BaseModel) -> BaseModel:
        assert isinstance(args, SensitiveActionArgs)  # noqa: S101 - validated by the executor
        ticket_id = tickets.create(
            account_id=ctx.account_id,
            kind=f"sensitive_action:{args.action}",
            summary=args.detail or args.action,
            urgency="high",
        )
        tickets.create(
            account_id=ctx.account_id,
            kind="account_change_notice",
            summary=f"Notify the holder of a requested {args.action}; do not repeat the details.",
            urgency="high",
        )
        return TicketResult(
            ticket_id=ticket_id,
            kind=f"sensitive_action:{args.action}",
            status="open",
            performed=False,
            note=_SENSITIVE_NOTE,
        )

    return [
        ToolSpec(
            "raise_network_ticket",
            "Open a network ticket for the field team about the caller's own service problem.",
            NetworkTicketArgs,
            raise_network_ticket,
            requires_verified=True,
        ),
        ToolSpec(
            "escalate_to_human",
            "Hand the customer to a human agent, with a one-sentence reason.",
            EscalateArgs,
            escalate_to_human,
            requires_verified=False,
        ),
        ToolSpec(
            "request_sensitive_action",
            "Record a request for a sensitive action (refund, suspension, cancellation, "
            "ownership transfer, PIN reset, SIM change). It is never carried out by the "
            "assistant; a human completes it.",
            SensitiveActionArgs,
            request_sensitive_action,
            requires_verified=True,
        ),
    ]
