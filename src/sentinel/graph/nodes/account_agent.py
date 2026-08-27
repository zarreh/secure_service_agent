"""Account specialist node (docs/PLAN.md Phase 3, D-A4-5). Reads only
`question` and `account_id`; fetches the caller's own account/plan record
and the account-management clause itself. Writes `draft`, `citations`,
`specialist_context`."""

from __future__ import annotations

from collections.abc import Callable

from sentinel.graph.protocols import SpecialistChain
from sentinel.graph.state import SentinelState
from sentinel.store.account_store import AccountStore
from sentinel.store.policy_kb import get_clause

_CLAUSE_ID = "clause-account-management"


def build_account_agent_node(
    store: AccountStore, chain: SpecialistChain
) -> Callable[[SentinelState], dict[str, object]]:
    def account_agent(state: SentinelState) -> dict[str, object]:
        clause = get_clause(_CLAUSE_ID)
        assert clause is not None, f"missing policy clause {_CLAUSE_ID}"
        account = store.get_account(state["account_id"])
        plan = store.get_plan(state["account_id"])
        account_text = (
            account.model_dump_json(exclude={"pin_hash", "pin_salt"})
            if account
            else "No account on file."
        )
        plan_text = plan.model_dump_json() if plan else "No plan on file."

        result = chain.invoke(
            {
                "question": state["question"],
                "clause_id": clause.clause_id,
                "clause_body": clause.body,
                "account": account_text,
                "plan": plan_text,
            }
        )
        context = (
            f"Policy clause {clause.clause_id}: {clause.body}\n\n"
            f"Account: {account_text}\n\nPlan: {plan_text}"
        )
        return {
            "draft": result.draft,
            "citations": result.citations,
            "specialist_context": context,
        }

    return account_agent
