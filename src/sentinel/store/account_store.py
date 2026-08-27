"""Repository over `accounts.db` — accounts, plans, prior support
interactions, and identity-gate lockout state (docs/PLAN.md Phase 1/2).

`verify_pin` is the only place a submitted PIN is ever compared; it never
returns the stored hash or salt to a caller, only a bool. Lockout state is
the one thing this store writes — everything else is read-only, built once
by `data/generate_accounts.py`.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from sentinel.store.models import Account, MemoryEvent, Plan
from sentinel.store.pin_hash import verify_pin


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

    def verify_pin(self, account_id: str, pin: str) -> bool:
        """Verifies a submitted PIN against the stored hash. Returns False for
        an unknown account rather than raising, so a caller cannot distinguish
        "wrong PIN" from "no such account" — that distinction is exactly what
        an attacker enumerating account ids would want."""
        account = self.get_account(account_id)
        if account is None:
            return False
        return verify_pin(pin, account.pin_hash, account.pin_salt)

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

    def is_locked(self, account_id: str) -> bool:
        row = self._connection.execute(
            "SELECT locked FROM pin_lockouts WHERE account_id = ?", (account_id,)
        ).fetchone()
        return bool(row[0]) if row else False

    def failed_attempts(self, account_id: str) -> int:
        row = self._connection.execute(
            "SELECT failed_attempts FROM pin_lockouts WHERE account_id = ?", (account_id,)
        ).fetchone()
        return int(row[0]) if row else 0

    def record_failed_pin_attempt(self, account_id: str, *, max_attempts: int) -> int:
        """Increments the failed-attempt counter, locking the account once it
        reaches `max_attempts`. Returns the new count."""
        attempts = self.failed_attempts(account_id) + 1
        locked = attempts >= max_attempts
        self._connection.execute(
            "INSERT INTO pin_lockouts (account_id, failed_attempts, locked) VALUES (?, ?, ?) "
            "ON CONFLICT(account_id) DO UPDATE SET failed_attempts = ?, locked = ?",
            (account_id, attempts, int(locked), attempts, int(locked)),
        )
        self._connection.commit()
        return attempts

    def reset_pin_attempts(self, account_id: str) -> None:
        """Clears the lockout counter — called after a successful verification."""
        self._connection.execute(
            "INSERT INTO pin_lockouts (account_id, failed_attempts, locked) VALUES (?, 0, 0) "
            "ON CONFLICT(account_id) DO UPDATE SET failed_attempts = 0, locked = 0",
            (account_id,),
        )
        self._connection.commit()
