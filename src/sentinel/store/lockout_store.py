"""Persisted lockout counters (D-A4-10). Policy lives in `sentinel.identity`; this is
only durable storage, so a restart does not reset an attacker's progress.

It has its own database file, separate from `accounts.db`, so rebuilding the
synthetic account population does not silently clear lockouts.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS lockouts (
    key TEXT PRIMARY KEY,
    failures INTEGER NOT NULL,
    next_allowed REAL NOT NULL
)
"""


class LockoutStore:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._connection.execute(_SCHEMA)
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def get(self, key: str) -> tuple[int, float]:
        """`(failures, next_allowed_epoch_seconds)`; `(0, 0.0)` for an unseen key."""
        row = self._connection.execute(
            "SELECT failures, next_allowed FROM lockouts WHERE key = ?", (key,)
        ).fetchone()
        return (int(row[0]), float(row[1])) if row else (0, 0.0)

    def set(self, key: str, failures: int, next_allowed: float) -> None:
        self._connection.execute(
            "INSERT INTO lockouts (key, failures, next_allowed) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET failures = excluded.failures, "
            "next_allowed = excluded.next_allowed",
            (key, failures, next_allowed),
        )
        self._connection.commit()

    def clear(self, key: str) -> None:
        self._connection.execute("DELETE FROM lockouts WHERE key = ?", (key,))
        self._connection.commit()
