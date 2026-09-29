"""Read-only customer data, and nothing else (docs/PLAN.md §4.4).

Every account-scoped read takes an `account_id`; the scoped executor supplies the
principal's, never the model's. There is no method that returns a credential and
no method that lists accounts: enumeration is not a capability a tool can have.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from secureagent.store.models import Account, Bill, MemoryEntry, Outage, Subscription

DEFAULT_ROW_CAP = 12


class CustomerStore:
    def __init__(self, db_path: Path, row_cap: int = DEFAULT_ROW_CAP) -> None:
        self._connection = sqlite3.connect(
            f"file:{db_path}?mode=ro", uri=True, check_same_thread=False
        )
        self._connection.row_factory = sqlite3.Row
        self._row_cap = row_cap

    def close(self) -> None:
        self._connection.close()

    def _limit(self, limit: int | None) -> int:
        if limit is None:
            return self._row_cap
        return max(1, min(limit, self._row_cap))

    def account(self, account_id: str) -> Account | None:
        row = self._connection.execute(
            "SELECT account_id, name, phone, address, region, status, autopay, date_joined "
            "FROM accounts WHERE account_id = ?",
            (account_id,),
        ).fetchone()
        if row is None:
            return None
        return Account(
            row["account_id"],
            row["name"],
            row["phone"],
            row["address"],
            row["region"],
            row["status"],
            bool(row["autopay"]),
            row["date_joined"],
        )

    def subscription(self, account_id: str) -> Subscription | None:
        row = self._connection.execute(
            "SELECT * FROM subscriptions WHERE account_id = ?", (account_id,)
        ).fetchone()
        if row is None:
            return None
        return Subscription(
            row["account_id"],
            row["plan_name"],
            row["monthly_cost_usd"],
            row["data_allowance_gb"],
            row["data_used_gb"],
            row["voice_minutes"],
            row["contract_end_date"],
            bool(row["roaming_enabled"]),
        )

    def bills(self, account_id: str, *, limit: int | None = None) -> list[Bill]:
        rows = self._connection.execute(
            "SELECT * FROM bills WHERE account_id = ? ORDER BY period DESC LIMIT ?",
            (account_id, self._limit(limit)),
        ).fetchall()
        return [
            Bill(
                r["bill_id"],
                r["account_id"],
                r["period"],
                r["plan_charge"],
                r["overage_charge"],
                r["roaming_charge"],
                r["taxes_fees"],
                r["credits"],
                r["total"],
                r["status"],
            )
            for r in rows
        ]

    def outages(self, region: str, *, limit: int | None = None) -> list[Outage]:
        """Public information: outages are not account data."""
        rows = self._connection.execute(
            "SELECT * FROM outages WHERE region = ? ORDER BY started_at DESC LIMIT ?",
            (region, self._limit(limit)),
        ).fetchall()
        return [
            Outage(
                r["outage_id"],
                r["region"],
                r["service"],
                r["started_at"],
                r["expected_resolution"],
                r["status"],
                r["description"],
            )
            for r in rows
        ]

    def memory(self, account_id: str, *, limit: int | None = None) -> list[MemoryEntry]:
        rows = self._connection.execute(
            "SELECT * FROM memory WHERE account_id = ? ORDER BY created_at DESC LIMIT ?",
            (account_id, self._limit(limit)),
        ).fetchall()
        return [
            MemoryEntry(r["memory_id"], r["account_id"], r["created_at"], r["intent"], r["summary"])
            for r in rows
        ]

    def protected_values(self) -> list[Account]:
        """Every account, for building the redactor and the output leak check.

        Not reachable from a tool: this is for the guardrails' own use, where the
        whole point is to know what must never appear in a reply.
        """
        rows = self._connection.execute(
            "SELECT account_id, name, phone, address, region, status, autopay, date_joined "
            "FROM accounts ORDER BY account_id"
        ).fetchall()
        return [
            Account(
                r["account_id"],
                r["name"],
                r["phone"],
                r["address"],
                r["region"],
                r["status"],
                bool(r["autopay"]),
                r["date_joined"],
            )
            for r in rows
        ]
