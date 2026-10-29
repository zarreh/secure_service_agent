"""Read-write repository over `runs.db` — the operational record of every
chat run, its node-by-node events, and per-node LLM cost (docs/PLAN.md
Phase 4). This *is* the audit log: every guardrail verdict, the identity
result, and the routing decision are node outputs, so persisting every event
persists every guardrail decision without a separate audit table.

Unlike `AccountStore`, this store creates its own schema on first use: it
holds operational state, not build-time data.

Redaction is deliberately not applied to events here (same reasoning as
A3's `run_executor.py`): a run's events are its own record of what happened
to answer its own question, and the PIN never appears in them in the first
place (D-A4-2) — no node output ever includes it.
"""

from __future__ import annotations

from pathlib import Path

from zarreh_agentkit.runs import RunEventLog, utc_now

from sentinel.store.models import RunRecord

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    account_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    response TEXT,
    error TEXT
);
"""


def _run_from_row(row: tuple[object, ...]) -> RunRecord:
    return RunRecord(
        id=str(row[0]),
        question=str(row[1]),
        account_id=str(row[2]),
        status=str(row[3]),
        created_at=str(row[4]),
        updated_at=str(row[5]),
        response=None if row[6] is None else str(row[6]),
        error=None if row[7] is None else str(row[7]),
    )


class RunStore(RunEventLog):
    """Persists chat runs, their node-by-node events, and per-node LLM
    cost — the single source of truth `GET /chat/{run_id}` and its events
    endpoint read from."""

    def __init__(self, db_path: Path) -> None:
        super().__init__(db_path)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def create_run(self, run_id: str, question: str, account_id: str) -> None:
        now = utc_now()
        self._conn.execute(
            "INSERT INTO runs (id, question, account_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'running', ?, ?)",
            (run_id, question, account_id, now, now),
        )
        self._conn.commit()

    def get_run(self, run_id: str) -> RunRecord | None:
        row = self._conn.execute(
            "SELECT id, question, account_id, status, created_at, updated_at, "
            "response, error FROM runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        return _run_from_row(row) if row else None

    def complete_run(self, run_id: str, response: str) -> None:
        self._conn.execute(
            "UPDATE runs SET status = 'completed', updated_at = ?, response = ? WHERE id = ?",
            (utc_now(), response, run_id),
        )
        self._conn.commit()

    def fail_run(self, run_id: str, error: str) -> None:
        self._conn.execute(
            "UPDATE runs SET status = 'failed', updated_at = ?, error = ? WHERE id = ?",
            (utc_now(), error, run_id),
        )
        self._conn.commit()
