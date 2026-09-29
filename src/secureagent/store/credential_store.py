"""Credential lookup, for `secureagent.identity` only (docs/PLAN.md §5.2).

Kept apart from `CustomerStore` so nothing customer-facing can read a hash. Phase
2 adds the persisted lockout counters here.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class CredentialStore:
    def __init__(self, db_path: Path) -> None:
        self._connection = sqlite3.connect(
            f"file:{db_path}?mode=ro", uri=True, check_same_thread=False
        )

    def close(self) -> None:
        self._connection.close()

    def pin_hash(self, account_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT pin_hash FROM accounts WHERE account_id = ?", (account_id,)
        ).fetchone()
        return str(row[0]) if row else None
