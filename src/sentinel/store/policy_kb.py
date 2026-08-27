"""Structured clause lookup over the policy knowledge base — a typed,
versioned JSON artifact, not vector search (same technique as A7's rulebook,
docs/HARVEST.md #12). `data/build_policy_kb.py` produces `data/policy_clauses.json`
from `reference/session_files_telecom/policy_kb.pdf`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import TypeAdapter

from sentinel.store.models import PolicyClause

_CLAUSES_ADAPTER = TypeAdapter(list[PolicyClause])


def load_policy_clauses(path: str | Path = "data/policy_clauses.json") -> list[PolicyClause]:
    with open(path, encoding="utf-8") as handle:
        return _CLAUSES_ADAPTER.validate_python(json.load(handle))


@lru_cache(maxsize=1)
def get_policy_clauses(path: str | Path = "data/policy_clauses.json") -> tuple[PolicyClause, ...]:
    return tuple(load_policy_clauses(path))


def get_clause(
    clause_id: str, path: str | Path = "data/policy_clauses.json"
) -> PolicyClause | None:
    for clause in get_policy_clauses(path):
        if clause.clause_id == clause_id:
            return clause
    return None
