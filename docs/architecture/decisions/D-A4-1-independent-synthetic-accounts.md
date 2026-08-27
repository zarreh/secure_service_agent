# D-A4-1 — Independently generated account data, not the course CSVs

**Status:** Accepted, implemented (`data/generate_accounts.py`, Phase 1).

## Context

The source coursework ships `accounts.csv`, `plans.csv` and
`customer_memory.json` — 12 fictional Union Mobile customers with names, PINs
and usage history. `NOTICE.md` commits this repository to an independent,
clean-room implementation that redistributes no course dataset. Parsing those
files directly, even reshaped into a database, would still be redistributing
that specific dataset — the same objection that does *not* apply to
`policy_kb.pdf`, which is generic support-policy prose rather than a table of
individuals.

## Decision

`data/generate_accounts.py` generates an independent synthetic population —
20 accounts, plans and prior-interaction records — deterministically (a fixed
seed) in the *same schema shape* as the source CSVs but containing none of
their rows: different name pool, randomly generated PINs, procedurally
assigned plans and usage. Output is `data/accounts.db`, gitignored like every
other app's person-shaped store (see A3's `data/records.db`), rebuilt by
`make data`.

The source PDF (`policy_kb.pdf`) is treated differently: `data/build_policy_kb.py`
parses it directly and the derived `data/policy_clauses.json` **is** committed,
matching A7's precedent for `data/rulebook.json` — generic policy text, not a
dataset of individuals.

## Consequences

- **Pros:** `NOTICE.md`'s "no dataset redistributed" claim holds for every
  file in the repo, not just the code. A fresh clone with no `reference/`
  material can still run `make data` and get a working, self-consistent
  population.
- **Cons:** The generated accounts don't reproduce the source notebook's
  specific edge cases (e.g. its exact overage or suspended-account rows) —
  Phase 6's scenario design has to construct those deliberately rather than
  relying on the source data already containing them.
