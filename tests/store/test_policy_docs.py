"""The policy corpus: parses, and carries exactly one planted injection."""

from __future__ import annotations

import re
from pathlib import Path

from secureagent.store.policy_docs import load_policy_docs

INJECTION = re.compile(r"ignore all previous instructions|verification is waived", re.IGNORECASE)


def test_all_documents_parse_with_unique_ids(repo_root: Path) -> None:
    docs = load_policy_docs(repo_root / "data" / "policy")
    assert len(docs) == 15  # 14 legitimate + the one planted injection
    assert len({doc.doc_id for doc in docs}) == len(docs)
    assert all(doc.title and doc.body for doc in docs)


def test_exactly_one_document_is_the_planted_injection(repo_root: Path) -> None:
    docs = load_policy_docs(repo_root / "data" / "policy")
    flagged = [doc for doc in docs if doc.fixture_kind == "indirect_prompt_injection"]
    assert [doc.doc_id for doc in flagged] == ["promotional-offers"]
    assert INJECTION.search(flagged[0].body)


def test_no_unflagged_document_contains_the_payload(repo_root: Path) -> None:
    """A stray copy would make an indirect-injection result ambiguous."""
    for doc in load_policy_docs(repo_root / "data" / "policy"):
        if doc.fixture_kind is None:
            assert not INJECTION.search(doc.body), doc.doc_id


def test_the_policy_states_the_no_biographical_information_rule(repo_root: Path) -> None:
    """The identity policy must not contradict the design it documents (47 CFR
    64.2010(c), (e): no readily available biographical information)."""
    docs = {d.doc_id: d for d in load_policy_docs(repo_root / "data" / "policy")}
    assert "date of birth" in docs["identity-verification"].body
    assert "never ask" in docs["identity-verification"].body
