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

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from zarreh_agentkit.cost import CostEntry

from sentinel.store.models import RunEvent, RunRecord

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
CREATE TABLE IF NOT EXISTS run_events (
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    node TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, sequence)
);
CREATE TABLE IF NOT EXISTS run_costs (
    run_id TEXT NOT NULL,
    node TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


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


class RunStore:
    """Persists chat runs, their node-by-node events, and per-node LLM
    cost — the single source of truth `GET /chat/{run_id}` and its events
    endpoint read from."""

    def __init__(self, db_path: Path) -> None:
        # check_same_thread=False: FastAPI's request handling and the
        # background run executor run from different tasks against one connection.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def create_run(self, run_id: str, question: str, account_id: str) -> None:
        now = _now()
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
            (_now(), response, run_id),
        )
        self._conn.commit()

    def fail_run(self, run_id: str, error: str) -> None:
        self._conn.execute(
            "UPDATE runs SET status = 'failed', updated_at = ?, error = ? WHERE id = ?",
            (_now(), error, run_id),
        )
        self._conn.commit()

    def append_event(self, run_id: str, sequence: int, node: str, payload_json: str) -> None:
        self._conn.execute(
            "INSERT INTO run_events (run_id, sequence, node, payload_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (run_id, sequence, node, payload_json, _now()),
        )
        self._conn.commit()

    def get_events(self, run_id: str, after_sequence: int = -1) -> list[RunEvent]:
        """Every event with `sequence > after_sequence`, in order — the same
        call replays a whole run from the start (default) or tails new events
        since the last one a client already saw."""
        rows = self._conn.execute(
            "SELECT run_id, sequence, node, payload_json, created_at FROM run_events "
            "WHERE run_id = ? AND sequence > ? ORDER BY sequence",
            (run_id, after_sequence),
        ).fetchall()
        return [
            RunEvent(
                run_id=str(row[0]),
                sequence=int(row[1]),
                node=str(row[2]),
                payload_json=str(row[3]),
                created_at=str(row[4]),
            )
            for row in rows
        ]

    def record_costs(self, run_id: str, entries: list[CostEntry]) -> None:
        self._conn.executemany(
            "INSERT INTO run_costs "
            "(run_id, node, model, prompt_tokens, completion_tokens, cost_usd) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (run_id, e.node, e.model, e.prompt_tokens, e.completion_tokens, e.cost_usd)
                for e in entries
            ],
        )
        self._conn.commit()

    def get_costs(self, run_id: str) -> list[CostEntry]:
        rows = self._conn.execute(
            "SELECT node, model, prompt_tokens, completion_tokens, cost_usd "
            "FROM run_costs WHERE run_id = ?",
            (run_id,),
        ).fetchall()
        return [
            CostEntry(
                node=str(row[0]),
                model=str(row[1]),
                prompt_tokens=int(row[2]),
                completion_tokens=int(row[3]),
                cost_usd=float(row[4]),
            )
            for row in rows
        ]
