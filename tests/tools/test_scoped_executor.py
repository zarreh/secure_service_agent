"""The scoped executor: the enforcement points that do not depend on a model
behaving (docs/PLAN.md §4.2, §13 gates 1, 2 and 6)."""

from __future__ import annotations

import pytest
from langchain_core.messages.tool import ToolCall

from secureagent.schemas.principal import Principal
from secureagent.store import CustomerStore
from secureagent.store.ticket_store import TicketStore
from secureagent.tools import ScopedToolExecutor, ToolRegistry
from secureagent.tools.scoping import IDENTITY_ARGUMENT_NAMES, _normalise_key

RUN_ID = "run-under-test"
ALICE, BOB = "ACCT_1000", "ACCT_1001"


def _call(name: str, call_id: str, **args: object) -> ToolCall:
    return ToolCall(name=name, args=dict(args), id=call_id, type="tool_call")


# --- capability by verification ------------------------------------------------


def test_an_unverified_scope_contains_no_account_tool(
    registry: ToolRegistry, unverified: Principal
) -> None:
    scope = registry.scope_for(unverified)
    assert scope.allowed_tool_names == {"list_outages", "search_policy", "escalate_to_human"}
    for name in ("get_plan", "get_usage", "get_bills", "raise_network_ticket"):
        assert name not in scope.allowed_tool_names


def test_a_verified_scope_adds_the_account_tools(registry: ToolRegistry, alice: Principal) -> None:
    scope = registry.scope_for(alice)
    assert {"get_plan", "get_usage", "get_bills", "request_sensitive_action"} <= (
        scope.allowed_tool_names
    )


def test_an_unverified_caller_cannot_reach_an_account_tool(
    executor: ScopedToolExecutor, registry: ToolRegistry, unverified: Principal
) -> None:
    result = executor.execute(
        [_call("get_plan", "c1")],
        principal=unverified,
        scope=registry.scope_for(unverified),
        run_id=RUN_ID,
    )
    assert not result.evidence
    assert [e.kind for e in result.security_events] == ["out_of_scope_tool"]
    assert result.messages[0].status == "error"


def test_a_model_is_only_shown_the_tools_in_scope(
    registry: ToolRegistry, unverified: Principal
) -> None:
    shown = {tool.name for tool in registry.langchain_tools(registry.scope_for(unverified))}
    assert "get_plan" not in shown and "list_outages" in shown


# --- the principal is injected, never chosen ------------------------------------


def test_a_tool_reads_the_principals_account_not_one_the_model_names(
    executor: ScopedToolExecutor,
    registry: ToolRegistry,
    customers: CustomerStore,
    alice: Principal,
) -> None:
    result = executor.execute(
        [_call("get_plan", "c1", account_id=BOB)],
        principal=alice,
        scope=registry.scope_for(alice),
        run_id=RUN_ID,
    )
    expected = customers.subscription(ALICE)
    other = customers.subscription(BOB)
    assert expected is not None and other is not None
    assert result.evidence[0].result["plan_name"] == expected.plan_name
    assert result.evidence[0].result["contract_end_date"] == expected.contract_end_date
    # Guard against a vacuous pass: the two accounts genuinely differ.
    assert expected.contract_end_date != other.contract_end_date


def test_a_supplied_identity_argument_is_recorded_with_what_was_requested(
    executor: ScopedToolExecutor, registry: ToolRegistry, alice: Principal
) -> None:
    result = executor.execute(
        [_call("get_plan", "c1", account_id=BOB)],
        principal=alice,
        scope=registry.scope_for(alice),
        run_id=RUN_ID,
    )
    (event,) = result.security_events
    assert event.kind == "identity_argument_supplied"
    assert BOB in event.requested
    assert event.run_id == RUN_ID
    assert ALICE not in event.requested  # never blur what the model asked for with what ran


@pytest.mark.parametrize(
    "key", ["account_id", "accountId", "ACCOUNT-ID", "customer_account_id", "phone", "msisdn"]
)
def test_identity_argument_names_are_matched_however_they_are_spelled(
    key: str, executor: ScopedToolExecutor, registry: ToolRegistry, alice: Principal
) -> None:
    result = executor.execute(
        [_call("get_bills", "c1", **{key: BOB})],
        principal=alice,
        scope=registry.scope_for(alice),
        run_id=RUN_ID,
    )
    assert [e.kind for e in result.security_events] == ["identity_argument_supplied"]


def test_an_unexpected_key_carrying_a_customer_is_still_attributed_and_harmless(
    executor: ScopedToolExecutor,
    registry: ToolRegistry,
    customers: CustomerStore,
    alice: Principal,
) -> None:
    """A model that names the victim under a key nobody listed gets no data, and the
    attempt still leaves a trail rather than vanishing into validation."""
    result = executor.execute(
        [_call("get_plan", "c1", target=BOB, for_customer=BOB)],
        principal=alice,
        scope=registry.scope_for(alice),
        run_id=RUN_ID,
    )
    kinds = [e.kind for e in result.security_events]
    assert kinds.count("unexpected_argument") == 2
    assert {"target", "for_customer"} == {e.requested.split("=")[0] for e in result.security_events}
    own = customers.subscription(ALICE)
    assert own is not None
    assert result.evidence[0].result["plan_name"] == own.plan_name


def test_no_tool_argument_schema_has_an_identity_field(registry: ToolRegistry) -> None:
    """Structural guard: a future tool that grows an identity argument fails here."""
    for spec in registry.specs.values():
        for field in spec.args_model.model_fields:
            assert _normalise_key(field) not in IDENTITY_ARGUMENT_NAMES, (spec.name, field)


def test_every_verified_tool_is_absent_from_an_unverified_scope(
    registry: ToolRegistry, unverified: Principal
) -> None:
    scope = registry.scope_for(unverified)
    for name, spec in registry.specs.items():
        assert (name in scope.allowed_tool_names) == (not spec.requires_verified)


# --- sensitive actions are recorded, never performed ----------------------------


@pytest.mark.parametrize(
    "action",
    [
        "suspend_account",
        "cancel_account",
        "transfer_ownership",
        "reset_pin",
        "sim_change",
        "refund",
    ],
)
def test_a_sensitive_action_creates_a_ticket_and_performs_nothing(
    action: str,
    executor: ScopedToolExecutor,
    registry: ToolRegistry,
    customers: CustomerStore,
    tickets: TicketStore,
    alice: Principal,
) -> None:
    before_account = customers.account(ALICE)
    before_plan = customers.subscription(ALICE)
    result = executor.execute(
        [_call("request_sensitive_action", "c1", action=action, detail="please")],
        principal=alice,
        scope=registry.scope_for(alice),
        run_id=RUN_ID,
    )
    assert result.evidence[0].result["performed"] is False
    assert "NOT been carried out" in str(result.evidence[0].result["note"])
    kinds = [kind for _, kind, _ in tickets.for_account(ALICE)]
    assert f"sensitive_action:{action}" in kinds
    assert "account_change_notice" in kinds  # 47 CFR 64.2010(f), modelled
    # Nothing changed.
    assert customers.account(ALICE) == before_account
    assert customers.subscription(ALICE) == before_plan


def test_there_is_no_tool_that_performs_a_sensitive_action(registry: ToolRegistry) -> None:
    banned = ("suspend", "cancel", "transfer", "reset", "refund", "sim", "delete", "update", "set_")
    for name in registry.specs:
        if name == "request_sensitive_action":
            continue  # records a request; asserted above to perform nothing
        assert not any(word in name for word in banned), name


def test_an_unknown_sensitive_action_is_rejected(
    executor: ScopedToolExecutor, registry: ToolRegistry, alice: Principal
) -> None:
    result = executor.execute(
        [_call("request_sensitive_action", "c1", action="wipe_database")],
        principal=alice,
        scope=registry.scope_for(alice),
        run_id=RUN_ID,
    )
    assert not result.evidence
    assert [e.kind for e in result.security_events] == ["invalid_arguments"]


# --- allowlist, validation, caps ------------------------------------------------


def test_an_unknown_tool_is_blocked_and_recorded(
    executor: ScopedToolExecutor, registry: ToolRegistry, alice: Principal
) -> None:
    result = executor.execute(
        [_call("drop_all_tables", "c1")],
        principal=alice,
        scope=registry.scope_for(alice),
        run_id=RUN_ID,
    )
    assert not result.evidence
    assert [e.kind for e in result.security_events] == ["blocked_unknown_tool"]


def test_an_unverified_caller_can_still_escalate_to_a_human(
    executor: ScopedToolExecutor,
    registry: ToolRegistry,
    tickets: TicketStore,
    unverified: Principal,
) -> None:
    result = executor.execute(
        [_call("escalate_to_human", "c1", reason="I am locked out", urgency="high")],
        principal=unverified,
        scope=registry.scope_for(unverified),
        run_id=RUN_ID,
    )
    assert result.evidence[0].result["kind"] == "escalation"
    assert "escalation" in tickets.kinds()


def test_row_cap_clamps_a_requested_limit(
    executor: ScopedToolExecutor, registry: ToolRegistry, alice: Principal
) -> None:
    scope = registry.scope_for(alice, row_cap=2)
    result = executor.execute(
        [_call("get_bills", "c1", limit=1000)], principal=alice, scope=scope, run_id=RUN_ID
    )
    assert result.evidence[0].result["count"] == 2


def test_every_result_is_addressable_by_its_tool_call_id(
    executor: ScopedToolExecutor, registry: ToolRegistry, alice: Principal
) -> None:
    result = executor.execute(
        [_call("get_plan", "a"), _call("get_usage", "b"), _call("get_bills", "c")],
        principal=alice,
        scope=registry.scope_for(alice),
        run_id=RUN_ID,
    )
    assert {e.tool_call_id for e in result.evidence} == {"a", "b", "c"}
    assert {m.tool_call_id for m in result.messages} == {"a", "b", "c"}


def test_public_tools_work_for_an_unverified_caller(
    executor: ScopedToolExecutor, registry: ToolRegistry, unverified: Principal
) -> None:
    result = executor.execute(
        [
            _call("list_outages", "c1", region="North Ridge"),
            _call("search_policy", "c2", query="x"),
        ],
        principal=unverified,
        scope=registry.scope_for(unverified),
        run_id=RUN_ID,
    )
    assert len(result.evidence) == 2 and not result.security_events
