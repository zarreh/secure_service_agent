"""Persisted lockout counters (docs/PLAN.md §5.2). Policy lives in `identity`; this
is only durable storage, so a restart does not reset an attacker's progress."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class LockoutStore:
    def __init__(self, db_path: Path) -> None:
        self._connection = sqlite3.connect(db_path, check_same_thread=False)

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
