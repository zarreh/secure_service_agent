from sentinel.store.account_store import AccountStore


def test_account_ids_returns_every_generated_account(account_store: AccountStore) -> None:
    ids = account_store.account_ids()
    assert len(ids) == 20
    assert all(account_id.startswith("ACCT_") for account_id in ids)


def test_get_account_returns_none_for_an_unknown_id(account_store: AccountStore) -> None:
    assert account_store.get_account("ACCT_9999") is None


def test_get_plan_matches_the_account(account_store: AccountStore) -> None:
    account_id = account_store.account_ids()[0]
    plan = account_store.get_plan(account_id)
    assert plan is not None
    assert plan.account_id == account_id
    assert plan.plan_name in {"Basic", "Standard", "Plus", "Unlimited"}
