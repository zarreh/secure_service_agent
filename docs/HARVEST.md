# Harvest log — patterns copied from A2/A3/A7/A12

`PORTFOLIO_PLAN_V3.md` §8: shared code lives in `zarreh_agentkit` once a
pattern has appeared in two independent implementations; conventions that are
essential (the apps genuinely need to differ) stay local even after a second
occurrence. This log tracks both.

| # | Pattern | Source | Status in A4 | Difference |
|---|---|---|---|---|
| 1 | `Settings` + `get_settings` via `pydantic-settings` | `zarreh_agentkit.settings.AgentSettings` | Harvested from the start — `sentinel.settings.Settings` subclasses it, `SENTINEL_` prefix | Incidental |
| 2 | `get_logger` | `zarreh_agentkit.observability` | Harvested from the start | Incidental |
| 3 | `MaxBodySizeMiddleware` | `zarreh_agentkit.api.middleware` | Harvested from the start | Incidental |
| 4 | Per-route `Limiter` | `zarreh_agentkit.api.rate_limit` | Harvested from the start | Incidental |
| 5 | Multi-stage Dockerfile, non-root, `HEALTHCHECK` | `Dockerfile` (A7) | Copied, package name only | Incidental |
| 6 | CI split (lint/type/test job + docs-build job) | `.github/workflows/` (A7) | Copied, package name only | Incidental |
| 7 | MkDocs + Material config and plugin set | `mkdocs.yml` (A7) | Copied, different nav | Incidental — this is X5 `zarreh-docs-theme` |
| 8 | ✅ SSE bridge over `astream_events`, filtered on `name == metadata["langgraph_node"]` | `api/streaming.py` (A3) | Copied Phase 4 as `stream_run_events`; the skeleton's `stream_graph_events` kept unchanged | Incidental |
| 9 | ✅ `builder.py` as the only wiring file; node filename == registered node name == trace span name | `graph/builder.py` (A3/A7/A12) | Adopted from Phase 0, full graph wired Phase 3 | **Essential convention**, not shared code |
| 10 | ✅ Narrow state projections per node | `graph/state.py` (A2/A3/A7/A12, and independently UT wk11/wk13) | Adopted from Phase 0, extended Phase 3 (`schemas/history.py`'s `HistoryEvent` deliberately narrower than the store's `MemoryEvent`) | **Essential convention** — now evidenced in six independent places |
| 11 | ✅ Policy-gate-shaped guardrail (pre-flight + post-flight, deterministic layer under an LLM layer) | A3's `screen_rules`/`post_flight` | Implemented Phase 2: `guardrails/input_scanner.py` + `guardrails/output_scanner.py` + `guardrails/combine.py` (D-A4-3) | **Candidate for `zarreh_agentkit.guardrails` extraction** — flag for a follow-up ADR once A4's `base` ships |
| 12 | ✅ Structured clause lookup over a versioned rulebook, not vector search | A7's `data/build_rulebook.py` | Adopted for `data/build_policy_kb.py` (Phase 1) | Incidental — same technique, different source document |
| 15 | Salted PBKDF2 PIN hashing (D-A4-2) | New in A4 — no prior app stores a credential this shape | `sentinel/store/pin_hash.py` | New pattern; log here as a `zarreh_agentkit` candidate if a second app ever stores a low-entropy credential |
| 13 | SQLite-backed durable persistence (`SqliteSaver` / plain audit table) | A7's `D-A7-2` | Adopted for the audit log (Phase 4) | Incidental |
| 14 | Two-layer canonical + attack eval set | A7/A3's Layer 1 canonical harness | To be built in Phase 6, extended with an attack-scenario layer specific to A4 | **Essential** — A4's eval set needs a labelled expected-block-layer field the others don't have |
| 15 | ✅ Background-task run executor + `RunStore` (runs/events/costs tables), `GET /{id}` + `GET /{id}/events` replay-then-tail | A2's `execute_investigation`/`RunStore` (closest match — no HITL) | Copied near-verbatim as `execute_chat`/`RunStore` (Phase 4); A4 has no interrupt path so `resume_*` was not needed | Incidental — A4 also gets a free audit log from this (D-A4-7) because its node outputs happen to be the guardrail verdicts |

## Frontend components

Filled in during Phase 5. Each logged here as an X3 `@zarreh/agent-ui`
extraction candidate, per the F-numbering convention started in A3's
`HARVEST.md`.
