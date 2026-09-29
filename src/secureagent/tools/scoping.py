"""The scoped tool executor: where a hostile model's requests meet the enforcement
(docs/PLAN.md §4.2). Second occurrence of A3's `ScopedToolExecutor` (docs/HARVEST.md).

What it guarantees, none of it dependent on a model behaving:

- **The principal is injected, never chosen.** Tool argument schemas contain no
  identity field. If a model supplies one anyway (`account_id`, `customer_id`...),
  the value is discarded and a `SecurityEvent` records what was requested.
- **Scope is a function of the principal.** A tool outside it is refused here, and
  an unverified caller's scope holds no account tool at all.
- **Arguments are validated** against the tool's own model before it runs.
- **Rows are capped** by the scope.
- Every call yields an addressable `EvidenceRecord`; every refusal a `SecurityEvent`.

Runs with no LLM and no network.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from langchain_core.messages import ToolMessage
from langchain_core.messages.tool import ToolCall
from pydantic import BaseModel, ValidationError

from secureagent.schemas.principal import Principal
from secureagent.schemas.scoping import EvidenceRecord, SecurityEvent, ToolScope
from secureagent.tools.base import ToolContext
from secureagent.tools.registry import ToolRegistry

# Argument names a model might use to try to name another customer. Matching is on
# the normalised key; the *value* is recorded, never used.
IDENTITY_ARGUMENT_NAMES = frozenset(
    {
        "accountid",
        "account",
        "acct",
        "acctid",
        "customerid",
        "customeraccountid",
        "customer",
        "userid",
        "user",
        "phone",
        "phonenumber",
        "msisdn",
        "number",
    }
)


def _normalise_key(key: str) -> str:
    return "".join(ch for ch in key.lower() if ch.isalnum())


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class ToolExecution:
    messages: list[ToolMessage] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    security_events: list[SecurityEvent] = field(default_factory=list)


class ScopedToolExecutor:
    def __init__(self, registry: ToolRegistry, *, now: Callable[[], str] = _utc_now) -> None:
        self._registry = registry
        self._now = now

    def execute(
        self,
        tool_calls: Sequence[ToolCall],
        *,
        principal: Principal,
        scope: ToolScope,
        run_id: str,
    ) -> ToolExecution:
        out = ToolExecution()
        ctx = ToolContext(principal=principal, run_id=run_id, row_cap=scope.row_cap)
        for call in tool_calls:
            self._execute_one(call, ctx=ctx, scope=scope, out=out)
        return out

    def _event(
        self, kind: str, tool: str, requested: str, enforced: str, ctx: ToolContext
    ) -> SecurityEvent:
        return SecurityEvent(
            kind=kind,  # type: ignore[arg-type]
            tool_name=tool,
            requested=requested,
            enforced=enforced,
            run_id=ctx.run_id,
            at=self._now(),
        )

    def _execute_one(
        self, call: ToolCall, *, ctx: ToolContext, scope: ToolScope, out: ToolExecution
    ) -> None:
        name = call["name"]
        call_id = call.get("id") or ""
        raw: dict[str, object] = dict(call.get("args") or {})

        spec = self._registry.specs.get(name)
        if spec is None:
            out.security_events.append(
                self._event("blocked_unknown_tool", name, name, "blocked", ctx)
            )
            out.messages.append(_error(name, call_id, f"Blocked unknown tool: {name}"))
            return

        if name not in scope.allowed_tool_names:
            out.security_events.append(self._event("out_of_scope_tool", name, name, "blocked", ctx))
            out.messages.append(
                _error(name, call_id, f"Tool {name} is not available for this caller")
            )
            return

        # The principal is injected, never chosen: any identity argument is recorded and dropped.
        for key in list(raw):
            if _normalise_key(key) in IDENTITY_ARGUMENT_NAMES:
                out.security_events.append(
                    self._event(
                        "identity_argument_supplied",
                        name,
                        f"{key}={raw.pop(key)!s}",
                        "discarded; the verified principal was used",
                        ctx,
                    )
                )

        # Any other argument the tool does not declare is ignored by validation, but a
        # model naming a customer under an unexpected key is still worth attributing.
        for key in sorted(set(raw) - set(spec.args_model.model_fields)):
            out.security_events.append(
                self._event(
                    "unexpected_argument", name, f"{key}={raw.pop(key)!s}", "discarded", ctx
                )
            )

        try:
            args = spec.args_model.model_validate(raw)
        except ValidationError as exc:
            out.security_events.append(
                self._event("invalid_arguments", name, str(sorted(raw)), "rejected", ctx)
            )
            out.messages.append(
                _error(name, call_id, f"Invalid arguments: {exc.error_count()} error(s)")
            )
            return

        result = spec.fn(ctx, args)
        out.evidence.append(
            EvidenceRecord(
                tool_call_id=call_id,
                tool_name=name,
                args=args.model_dump(mode="json"),
                result=_dump(result),
                retrieved_at=self._now(),
            )
        )
        out.messages.append(
            ToolMessage(content=result.model_dump_json(), name=name, tool_call_id=call_id)
        )


def _dump(model: BaseModel) -> dict[str, object]:
    return model.model_dump(mode="json")


def _error(name: str, call_id: str, message: str) -> ToolMessage:
    return ToolMessage(content=message, name=name, tool_call_id=call_id, status="error")
