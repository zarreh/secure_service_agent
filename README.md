# Secure Service Agent

**Portfolio app A4** — see [`PORTFOLIO_PLAN_V3.md`](../PORTFOLIO_PLAN_V3.md) §7
for the full spec and `docs/PLAN.md` for the as-built plan.

> **Telecom customer support that assumes the user might be hostile.**

---

## The problem

A support agent that only ever sees polite, well-formed requests is not
tested. The same interface that answers *"what's my data usage this month?"*
also receives a prompt-injection attempt buried in a pasted message, a request
for someone else's account details, and a jailbreak aimed at getting the model
to leak internal policy text.

Most demos put a system-prompt disclaimer in front of the model and call it
security. This one puts the guardrail in the graph — as nodes with their own
tests, not as a suggestion to the model.

## The pattern: a full security envelope

```mermaid
graph TD
  U[Customer message] --> G[Input guardrail<br/>regex + LLM injection/toxicity scan]
  G -->|blocked| OG2[Output guardrail]
  G --> ID[Identity gate<br/>PIN + lockout, unlocks account tools]
  ID --> CTX[Context loader<br/>per-customer long-term memory, redacted]
  CTX --> SUP[Supervisor<br/>routes to specialist]
  SUP --> N[Network agent] & B[Billing agent] & AC[Account agent] & E[Escalation agent]
  N & B & AC & E --> SR[Supervisor review<br/>grounding + scope check]
  SR --> OG[Output guardrail<br/>regex + LLM leak/PII scan]
  OG --> RESP[Response + audit log entry]
```

Every node sees a narrow, typed view of shared state rather than the whole
blob (least-privilege state access) — the same pattern independently arrived
at across the source coursework and now a hard convention across this
portfolio.

## Status

The full security envelope is built and tested end to end: guardrail nodes,
PIN identity gate, four specialists, supervisor review, background execution
with an audit-log-doubling event store, and a minimal Next.js frontend. See
`docs/PLAN.md` for the full build plan and phase-by-phase exit criteria.

| Phase | State |
|---|---|
| 0 · Scaffold + walking skeleton | done |
| 1 · Data foundation (policy KB, accounts) | done |
| 2 · Guardrail nodes (input/output scan, identity gate) | done |
| 3 · Specialist agents (network/billing/account/escalation) | done |
| 4 · API + observability | done |
| 5 · Frontend | done |
| 6 · Evaluation + docs | done |
| 7 · Deployment prep | Dockerfile/compose confirmed correct; VPS/DNS blocked on infra access |

## Security posture

The claim is not that the guardrails detect every attack. It is that **with every model
in the graph compromised, the customer's data still does not leave**, and that each
deterministic control is load-bearing for exactly what it is documented to contain.

- [Containment under a compromised model](docs/evidence/containment.md): 15 scenarios,
  then each control switched off in turn. `make eval` reproduces it.
- Input screen: 0/122 benign messages blocked; held-out set 104/112 blocked (95% Wilson
  86.5–96.3%). The misses are documented, not tuned away (D-A4-8).
- The PIN is verified before the graph starts and never enters graph state, so it cannot
  reach a trace (D-A4-9); lockout is durable exponential backoff (D-A4-10).
- What is **not** measured: any live-model behaviour. The LLM classifiers and routing need
  a configured model and are not populated.

## Run it

```bash
uv sync --extra dev
cp .env.example .env      # add SENTINEL_OPENAI_API_KEY
make data                 # generate the synthetic accounts + policy KB
make dev                  # http://localhost:8000/healthz
make check                # ruff, mypy --strict, import-linter, pytest
make eval                 # guardrail attack scenarios (no API key needed)
make frontend-dev         # http://localhost:3000 — use a demo account/PIN from `make data`'s output
```

Outside development the app refuses to start unless `SENTINEL_IDENTITY_PEPPER` is set to a
private value (`python -c "import secrets; print(secrets.token_urlsafe(32))"`) and
`SENTINEL_ENVIRONMENT` names the environment. The pepper is held outside the database so a
stolen `accounts.db` cannot be brute-forced; changing it invalidates every stored PIN hash,
so rebuild with `make data`.

## Layout

See `docs/PLAN.md` §"Repo scaffold" for the full nested `graph/` convention
shared with the other portfolio apps.

## Licence and provenance

See [`NOTICE.md`](NOTICE.md). Independent implementation; synthetic data only.
