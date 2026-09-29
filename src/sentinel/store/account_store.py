"""Read-only repository over `accounts.db` — accounts, plans and prior support
interactions (docs/PLAN.md Phase 1).

Credential checking and lockout state live in `sentinel.identity`, not here: this
store is reachable from the graph, and the graph must never be able to verify a
PIN or touch lockout state (D-A4-10).
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from sentinel.store.models import Account, MemoryEvent, Plan


class AccountStore:
    """Read access to `accounts.db`."""

    def __init__(self, db_path: Path) -> None:
        self._connection = sqlite3.connect(db_path, check_same_thread=False)

    def close(self) -> None:
        self._connection.close()

    def get_account(self, account_id: str) -> Account | None:
        row = self._connection.execute(
            "SELECT account_id, customer_name, pin_hash, pin_salt, account_status, "
            "autopay_enabled, date_joined FROM accounts WHERE account_id = ?",
            (account_id,),
        ).fetchone()
        if row is None:
            return None
        return Account(
            account_id=row[0],
            customer_name=row[1],
            pin_hash=row[2],
            pin_salt=row[3],
            account_status=row[4],
            autopay_enabled=bool(row[5]),
            date_joined=date.fromisoformat(row[6]),
        )

    def get_plan(self, account_id: str) -> Plan | None:
        row = self._connection.execute(
            "SELECT account_id, plan_name, monthly_cost_usd, data_allowance_gb, "
            "data_used_gb, voice_minutes, contract_end_date, roaming_enabled "
            "FROM plans WHERE account_id = ?",
            (account_id,),
        ).fetchone()
        if row is None:
            return None
        return Plan(
            account_id=row[0],
            plan_name=row[1],
            monthly_cost_usd=row[2],
            data_allowance_gb=row[3],
            data_used_gb=row[4],
            voice_minutes=row[5],
            contract_end_date=date.fromisoformat(row[6]),
            roaming_enabled=bool(row[7]),
        )

    def get_memory_events(self, account_id: str) -> list[MemoryEvent]:
        rows = self._connection.execute(
            "SELECT account_id, timestamp, query, intent, agent_used, "
            "resolution_type, response_summary FROM memory_events "
            "WHERE account_id = ? ORDER BY timestamp DESC",
            (account_id,),
        ).fetchall()
        return [
            MemoryEvent(
                account_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                query=row[2],
                intent=row[3],
                agent_used=row[4],
                resolution_type=row[5],
                response_summary=row[6],
            )
            for row in rows
        ]

    def account_ids(self) -> list[str]:
        rows = self._connection.execute("SELECT account_id FROM accounts").fetchall()
        return [row[0] for row in rows]

    def other_customer_names(self, account_id: str) -> list[str]:
        """Names of every other customer, for the output check. A name the caller
        shares with another customer is left out, or greeting them by name would be
        blocked."""
        rows = self._connection.execute(
            "SELECT DISTINCT customer_name FROM accounts WHERE account_id != ?", (account_id,)
        ).fetchall()
        own = self.get_account(account_id)
        own_name = own.customer_name.casefold() if own else None
        return sorted(row[0] for row in rows if row[0].casefold() != own_name)
