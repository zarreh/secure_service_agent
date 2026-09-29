"""The only writable customer-facing store: tickets (docs/PLAN.md §4.2, §5.3).

Tickets are how the assistant "acts" without acting. A network ticket asks the
field team to investigate; a sensitive action (refund, suspension, SIM change...)
is a *request* a human completes later. Nothing here changes an account, a plan,
a PIN or a SIM.
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class TicketStore:
    def __init__(self, db_path: Path, *, now: Callable[[], str] = _utc_now) -> None:
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._now = now

    def close(self) -> None:
        self._connection.close()

    def create(self, *, account_id: str | None, kind: str, summary: str, urgency: str) -> str:
        ticket_id = f"TKT-{uuid.uuid4().hex[:10].upper()}"
        self._connection.execute(
            "INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, account_id, kind, summary, urgency, "open", self._now()),
        )
        self._connection.commit()
        return ticket_id

    def for_account(self, account_id: str) -> list[tuple[str, str, str]]:
        rows = self._connection.execute(
            "SELECT ticket_id, kind, status FROM tickets WHERE account_id = ? ORDER BY created_at",
            (account_id,),
        ).fetchall()
        return [(str(r[0]), str(r[1]), str(r[2])) for r in rows]

    def kinds(self) -> list[str]:
        rows = self._connection.execute("SELECT kind FROM tickets ORDER BY created_at").fetchall()
        return [str(r[0]) for r in rows]
