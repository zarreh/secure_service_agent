from sentinel.store.policy_kb import get_clause, get_policy_clauses


def test_all_six_policy_sections_are_present() -> None:
    clauses = get_policy_clauses()
    ids = {c.clause_id for c in clauses}
    assert ids == {
        "clause-identity-verification",
        "clause-data-privacy",
        "clause-network-support",
        "clause-billing-and-refunds",
        "clause-account-management",
        "clause-escalation",
    }


def test_every_clause_has_a_non_empty_body() -> None:
    for clause in get_policy_clauses():
        assert clause.body.strip(), clause.clause_id


def test_get_clause_returns_none_for_an_unknown_id() -> None:
    assert get_clause("clause-does-not-exist") is None


def test_get_clause_returns_the_matching_clause() -> None:
    clause = get_clause("clause-identity-verification")
    assert clause is not None
    assert "verified" in clause.body.lower()
