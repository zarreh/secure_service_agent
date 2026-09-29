"""The service database schema (docs/PLAN.md §4.4).

One SQLite file, several narrow stores over it. `accounts.pin_hash` is readable
only through `CredentialStore`, which only `secureagent.identity` uses; the
customer-facing store never selects it.
"""

from __future__ import annotations

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    account_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    phone        TEXT NOT NULL,
    address      TEXT NOT NULL,
    region       TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('active', 'suspended')),
    autopay      INTEGER NOT NULL,
    date_joined  TEXT NOT NULL,
    pin_hash     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    account_id         TEXT PRIMARY KEY REFERENCES accounts(account_id),
    plan_name          TEXT NOT NULL,
    monthly_cost_usd   REAL NOT NULL,
    data_allowance_gb  REAL NOT NULL,
    data_used_gb       REAL NOT NULL,
    voice_minutes      TEXT NOT NULL,
    contract_end_date  TEXT NOT NULL,
    roaming_enabled    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS bills (
    bill_id         TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL REFERENCES accounts(account_id),
    period          TEXT NOT NULL,
    plan_charge     REAL NOT NULL,
    overage_charge  REAL NOT NULL,
    roaming_charge  REAL NOT NULL,
    taxes_fees      REAL NOT NULL,
    credits         REAL NOT NULL,
    total           REAL NOT NULL,
    status          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outages (
    outage_id            TEXT PRIMARY KEY,
    region               TEXT NOT NULL,
    service              TEXT NOT NULL,
    started_at           TEXT NOT NULL,
    expected_resolution  TEXT NOT NULL,
    status               TEXT NOT NULL,
    description          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id   TEXT PRIMARY KEY,
    account_id  TEXT,
    kind        TEXT NOT NULL,
    summary     TEXT NOT NULL,
    urgency     TEXT NOT NULL,
    status      TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory (
    memory_id   TEXT PRIMARY KEY,
    account_id  TEXT NOT NULL REFERENCES accounts(account_id),
    created_at  TEXT NOT NULL,
    intent      TEXT NOT NULL,
    summary     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lockouts (
    key            TEXT PRIMARY KEY,
    failures       INTEGER NOT NULL,
    next_allowed   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS audit (
    audit_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    node         TEXT NOT NULL,
    principal_id TEXT,
    verdict      TEXT NOT NULL,
    layer        TEXT,
    span         TEXT,
    resolution   TEXT
);

CREATE TABLE IF NOT EXISTS scenario_fixtures (
    fixture_id  TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    table_name  TEXT NOT NULL,
    row_id      TEXT NOT NULL,
    detail      TEXT NOT NULL
);
"""

# Tables the generator fills and the committed fixture carries. The others
# (tickets, lockouts, audit) are written at runtime and start empty.
SEEDED_TABLES = (
    "accounts",
    "subscriptions",
    "bills",
    "outages",
    "memory",
    "scenario_fixtures",
)
