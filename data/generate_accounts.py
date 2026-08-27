"""Generate an independent synthetic account population.

Course reference material (`reference/session_files_telecom/accounts.csv`,
`plans.csv`, `customer_memory.json`) is a small, specific dataset of fictional
individuals — reproducing it, even reshaped, would contradict NOTICE.md's
"no course dataset redistributed" claim the way parsing `policy_kb.pdf`'s
generic policy prose does not. So account, plan and interaction-history data
here is generated independently, deterministically (a fixed seed), in the
same *shape* as the source schema but with none of its rows.

Output is `data/accounts.db` — gitignored, like every other app's
person-shaped store — rebuilt by `make data`, never committed.
"""

from __future__ import annotations

import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

from sentinel.store.pin_hash import hash_pin

OUTPUT = Path("data/accounts.db")

_SEED = 4242
_ACCOUNT_COUNT = 20

_FIRST_NAMES = [
    "Anwar",
    "Priya",
    "Marcus",
    "Elena",
    "Devon",
    "Fatima",
    "Lucas",
    "Naomi",
    "Kwame",
    "Sofia",
    "Ravi",
    "Colette",
    "Idris",
    "Maren",
    "Tobias",
    "Yuki",
    "Nadia",
    "Owen",
    "Selin",
    "Bram",
    "Aiyana",
    "Mateo",
    "Ingrid",
    "Zane",
]

_PLAN_TIERS = [
    # (name, monthly_cost_usd, data_allowance_gb, voice_minutes)
    ("Basic", 25.0, 5.0, "500"),
    ("Standard", 45.0, 15.0, "unlimited"),
    ("Plus", 60.0, 30.0, "unlimited"),
    ("Unlimited", 80.0, 999.0, "unlimited"),
]

_INTENTS = ["network", "billing", "account", "escalation"]
_QUERIES_BY_INTENT = {
    "network": "My connection keeps dropping — can you check for an outage?",
    "billing": "My last bill is higher than usual, can you explain the charge?",
    "account": "I'd like to know what upgrade options are on my plan.",
    "escalation": "I've called about this twice already and it's still not fixed.",
}

_SCHEMA = """
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    pin_salt TEXT NOT NULL,
    account_status TEXT NOT NULL,
    autopay_enabled INTEGER NOT NULL,
    date_joined TEXT NOT NULL
);

CREATE TABLE plans (
    account_id TEXT PRIMARY KEY REFERENCES accounts(account_id),
    plan_name TEXT NOT NULL,
    monthly_cost_usd REAL NOT NULL,
    data_allowance_gb REAL NOT NULL,
    data_used_gb REAL NOT NULL,
    voice_minutes TEXT NOT NULL,
    contract_end_date TEXT NOT NULL,
    roaming_enabled INTEGER NOT NULL
);

CREATE TABLE memory_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    timestamp TEXT NOT NULL,
    query TEXT NOT NULL,
    intent TEXT NOT NULL,
    agent_used TEXT NOT NULL,
    resolution_type TEXT NOT NULL,
    response_summary TEXT NOT NULL
);
"""


def _random_date(rng: random.Random, start: date, end: date) -> date:
    span_days = (end - start).days
    return start + timedelta(days=rng.randint(0, span_days))


def generate_accounts_db(connection: sqlite3.Connection, *, seed: int = _SEED) -> dict[str, str]:
    """Returns `{account_id: plaintext_pin}` — never written to the database,
    only handed back so tests can exercise `verify_pin` against a real PIN
    without the store ever holding one (docs/PLAN.md Phase 1/2)."""
    rng = random.Random(seed)
    connection.executescript(_SCHEMA)
    pins: dict[str, str] = {}

    for i in range(_ACCOUNT_COUNT):
        account_id = f"ACCT_{2000 + i}"
        name = rng.choice(_FIRST_NAMES)
        pin = f"{rng.randint(0, 9999):04d}"
        pins[account_id] = pin
        pin_hash, pin_salt = hash_pin(pin)
        status = "active" if rng.random() > 0.1 else "suspended"
        autopay = rng.random() > 0.4
        joined = _random_date(rng, date(2017, 1, 1), date(2025, 1, 1))

        connection.execute(
            "INSERT INTO accounts (account_id, customer_name, pin_hash, pin_salt, "
            "account_status, autopay_enabled, date_joined) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (account_id, name, pin_hash, pin_salt, status, int(autopay), joined.isoformat()),
        )

        plan_name, cost, allowance, voice = rng.choice(_PLAN_TIERS)
        # Occasionally over allowance, so billing scenarios have a real overage case.
        used = round(rng.uniform(0, allowance * 1.3), 1)
        contract_end = _random_date(rng, date(2025, 1, 1), date(2027, 1, 1))
        roaming = rng.random() > 0.6

        connection.execute(
            "INSERT INTO plans (account_id, plan_name, monthly_cost_usd, data_allowance_gb, "
            "data_used_gb, voice_minutes, contract_end_date, roaming_enabled) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                account_id,
                plan_name,
                cost,
                allowance,
                used,
                voice,
                contract_end.isoformat(),
                int(roaming),
            ),
        )

        for _ in range(rng.randint(0, 2)):
            intent = rng.choice(_INTENTS)
            when = _random_date(rng, date(2025, 6, 1), date(2026, 8, 1))
            connection.execute(
                "INSERT INTO memory_events (account_id, timestamp, query, intent, "
                "agent_used, resolution_type, response_summary) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    account_id,
                    when.isoformat() + "T00:00:00+00:00",
                    _QUERIES_BY_INTENT[intent],
                    intent,
                    f"{intent.capitalize()} Support Agent",
                    "resolved" if rng.random() > 0.3 else "escalated",
                    f"Handled a {intent} request; see transcript for detail.",
                ),
            )

    connection.commit()
    return pins


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.unlink(missing_ok=True)
    connection = sqlite3.connect(OUTPUT)
    try:
        generate_accounts_db(connection)
    finally:
        connection.close()
    print(f"Wrote {_ACCOUNT_COUNT} synthetic accounts to {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
