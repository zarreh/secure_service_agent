# A4 Secure Service Agent — Build Plan

Source notebook: `reference/Telecom_Chatbot_v2.ipynb` + `reference/telecom_chatbot_app.py`
Merge source: `reference/MLS11_Developing_E_Commerce_Chatbot_with_Responsible_AI_12th_February.ipynb`
Session data: `reference/session_files_telecom/` (`policy_kb.pdf`, `plans.csv`, `accounts.csv`, `customer_memory.json`)

See `PORTFOLIO_PLAN_V3.md` §7 (A4) for the full portfolio-level spec, tiers
and advisory angle.

## Decisions already confirmed

1. **Package name `sentinel`**, env prefix `SENTINEL_`, target URL
   `secure-agent.zarreh.ai`.
2. **11-node graph**, confirmed against `reference/telecom_chatbot_app.py`
   (`add_node` calls): `guardrail -> identity_gate -> context_loader ->
   supervisor -> {network,billing,account,escalation}_agent ->
   supervisor_review -> output_guardrail -> response_node`.
3. **Base tier ships an input/output guardrail node using regex + an LLM
   classifier, not the full scanner stack.** `llm-guard` / `Detoxify` /
   spaCy PII / LlamaGuard are `pro`-tier only, wrapped as LCEL `Runnable`s
   per §9.1, and drive the guardrails-on/off attack console.
4. **Audit-log persistence: SQLite**, matching A7's `SqliteSaver` precedent
   — no new infra.
5. **No shared `guardrails` extraction into `zarreh_agentkit` yet.** A4 is
   the second app (after A3) to build a policy-gate-shaped guardrail from
   scratch; land it locally in `src/sentinel/guardrails/` and log the
   extraction candidacy in `docs/HARVEST.md`, per the "extract after two
   instances" rule (§8/X2 of the portfolio plan) — do not force it inside
   this build.
6. **State-projection convention carried forward**: each node receives a
   narrow typed view of state, not the whole blob (§9.3, now a hard
   convention across the portfolio).

## Phases

### Phase 0 — Scaffold (this commit)
- [x] Directory tree, `pyproject.toml`, `Makefile`, `Dockerfile`,
  `compose.yaml`, `mkdocs.yml`
- [x] `src/sentinel/` package skeleton: `api/`, `graph/` (nested
  `nodes/`/`agents`/`chains`), `guardrails/`, `tools/`, `schemas/`,
  `prompts/`, `store/`, `settings.py`
- [x] Walking-skeleton graph: `echo -> done`, proven end to end through the
  API and SSE streaming path
- [x] Smoke tests, CI workflow, `docs/PLAN.md`, `docs/HARVEST.md`
- [x] Source material copied to `reference/` (gitignored)

**Exit criteria:** `make test` passes; `make dev` healthz returns 200; CI
green.

### Phase 1 — Data foundation ✅
- [x] `data/build_policy_kb.py` — parses `policy_kb.pdf` into a typed,
  versioned clause list (mirrors A7's rulebook-as-code approach); output
  `data/policy_clauses.json` is committed, source PDF is not (D-A4-1).
- [x] `data/generate_accounts.py` — generates an **independent** synthetic
  account/plan/memory population rather than parsing the course CSVs
  (D-A4-1); output `data/accounts.db` is gitignored, rebuilt by `make data`.
- [x] PINs stored as PBKDF2-HMAC-SHA256 hash + salt, never plaintext
  (D-A4-2); `AccountStore.verify_pin` never returns the stored hash/salt and
  does not distinguish "wrong PIN" from "unknown account."
- [x] `sentinel/store/`: `AccountStore`, `policy_kb` loader, Pydantic models.

**Exit criteria:** `make data` regenerates deterministically; store schema
tests pass (17/17 green, ruff/mypy/import-linter clean).

### Phase 2 — Guardrail nodes ✅
- [x] Input guardrail: regex/deny-list layer (deterministic, always on) + an
  LLM injection classifier as an LCEL runnable (`chains/injection_scan.py`),
  combined via `combine_verdicts` (D-A4-3) so the canonical eval set is
  deterministic-passable and a deterministic block never spends a model call.
- [x] Identity gate: PIN verification against the account store
  (`guardrails/identity_gate.py`), lockout counter persisted in
  `pin_lockouts` (D-A4-4) after repeated failures.
- [x] Output guardrail: regex (PIN disclosure + cross-account reference) +
  LLM leak/PII classifier (`chains/leak_scan.py`) over the drafted response.

**Exit criteria:** unit tests cover block / allow / lockout paths for each
guardrail node in isolation (37/37 green; the short-circuit tests assert the
LLM stub is never called once the deterministic layer blocks). Real
specialist tool scoping — the *positive* enforcement of "only the verified
account's data" — lands in Phase 3; Phase 2 covers the guardrail layer only.

### Phase 3 — Specialist agents ✅
- [x] `context_loader`: per-customer history, mapped to the narrower
  `HistoryEvent` schema at the boundary rather than carrying a store row
  into graph state.
- [x] `supervisor`: routes to `network_agent` / `billing_agent` /
  `account_agent` / `escalation_agent` — **not** over LLM-called tools.
  Deliberate deviation from the source's ReAct-over-tools design: no
  specialist exposes a tool argument that could name an account; each node
  fetches its own context deterministically by the identity-gate-verified
  `account_id` (D-A4-5).
- [x] `supervisor_review`: grounding + scope check on the specialist's draft,
  retrying the same specialist once on failure, then a deterministic
  `give_up` — the retry loop is bounded and provably terminates
  (`graph/edges.py::route_after_review`).
- [x] Full graph wired in `build_sentinel_graph` (`graph/builder.py`):
  guardrail → identity gate → context loader → supervisor → specialist →
  review → output guardrail → publish, plus four deterministic terminal
  nodes (`blocked_input_response`, `verification_required`, `give_up`,
  `blocked_output_response`).

**Exit criteria:** Full-graph integration tests
(`tests/graph/test_sentinel_graph.py`) exercise the happy path, an
input-guardrail block, a failed-verification path, the review retry/give-up
loop, and an output-guardrail block, all with stubbed chains (no network, no
API key). The dedicated `make eval` canonical scenario harness against real
models is Phase 6's job, same as A7's phasing — Phase 3 proves the wiring is
correct, Phase 6 measures it against real model behavior.

### Phase 4 — API + observability ✅
- [x] `POST /chat` starts a run as a background task
  (`api/run_executor.py::execute_chat`, same shape as A2/A3's
  `execute_investigation`/`execute_conversation`); `GET /chat/{run_id}`
  returns the durable record + per-node cost; `GET /chat/{run_id}/events`
  replays then tails via SSE, filtered the way A3 does
  (`name == metadata["langgraph_node"]`).
- [x] `structlog` structured logging, correlation id per request
  (unchanged from Phase 0).
- [x] LangSmith/Langfuse tracing via `zarreh_agentkit.observability.build_tracing_callbacks`,
  attached as a graph-invocation callback in `execute_chat`.
- [x] Audit log: **no separate table** — `run_store.append_event` already
  persists every node's output (`input_verdict`, `identity`, `route`,
  `review`, `output_verdict`) in order, so the replay/events endpoint
  built for streaming *is* the audit trail (D-A4-7).
- [x] `POST /chat` never pre-checks whether `account_id` exists (D-A4-6) —
  consistent with D-A4-2's "no enumeration oracle" all the way to the HTTP
  layer.
- [x] The PIN is never persisted: not on the `RunRecord`, not in any node
  output, not in a log line — verified directly by
  `test_create_response_never_echoes_the_pin` and
  `test_events_never_persist_the_pin`.

**Exit criteria:** Full API integration tests
(`tests/api/test_chat.py`, `tests/store/test_run_store.py`) cover create →
get → events for a happy path, a wrong-PIN path, and unknown-run 404s, with
the graph fully stubbed (no network, no API key) — 56/56 tests green.
Real LangSmith trace visibility depends on a configured API key and is a
manual verification step at deploy time, not a CI assertion.

### Phase 5 — Frontend
- Minimal Next.js chat UI + an audit-trail view (no attack console yet —
  that is `pro` tier, Phase 8).

### Phase 6 — Evaluation + documentation
- Layer 1 canonical scenario set: legitimate requests across all four
  specialists, plus a labelled attack set (injection, cross-account
  request, PII exfiltration attempt) with expected block layer.
- MkDocs site: architecture pages, ADRs (state-projection convention,
  guardrail layering, PIN lockout policy, audit-log persistence — `D-A4-1`
  onward, `Context`/`Decision`/`Consequences` format matching A7's ADRs).

**Exit criteria:** `make eval` gates PRs; `mkdocs build --strict` passes.

### Phase 7 — Deployment prep (deferred until DNS/VPS ready)
- Caddy + Docker Compose on VPS; `secure-agent.zarreh.ai`.

### Phase 8 — `pro` tier (separately time-boxed, after `base` ships)
- Live attack console: injection, indirect injection via policy document,
  cross-account data request, PII exfiltration, jailbreak-then-tool-call —
  each with a guardrails-on/off toggle reproducing the Applied GenAI
  failure-first demo.
- Full scanner stack (`llm-guard`, `Detoxify`, spaCy PII, LlamaGuard
  reference) wrapped as LCEL `Runnable`s.
- OWASP LLM Top 10 coverage matrix linked to tests.
- Guardrail cost accounting (latency/tokens per layer).

Do not let Phase 8 bleed into the Phase 0–7 timeline — this is the same risk
the portfolio plan names explicitly after A2's L-cost build.

## Risks

- `policy_kb.pdf` parsing may be messy (headers/footers, multi-column).
  Mitigation: deterministic extraction script + schema validation, same
  posture as A7's rulebook parse.
- LLM-based injection/leak scanners are probabilistic. Mitigation: a
  regex/deny-list layer underneath the LLM scan so the canonical eval set's
  exit criteria never depend on LLM scan variance alone.
- Scope creep from the attack console's appeal. Mitigation: strictly
  `pro`-tier (Phase 8), after `base` ships and is wired into observability.

## Open questions

- DNS/VPS setup for `secure-agent.zarreh.ai`: same Caddy pattern as the
  other deployed apps.
- Whether `identity_gate` lockout state should be per-session or persisted
  across sessions for the same account — leaning persisted, to be decided
  in Phase 2's ADR.
