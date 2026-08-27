# Architecture overview

Phase 0: a walking-skeleton graph (`echo -> done`) proves the API and SSE
streaming path end to end. The real 11-node graph — input guardrail, identity
gate, context loader, supervisor, four specialists, supervisor review, output
guardrail, response — is built incrementally starting at Phase 2 (see
`docs/PLAN.md`).

```mermaid
graph TD
  U[Customer message] --> G[Input guardrail]
  G -->|blocked| OG2[Output guardrail]
  G --> ID[Identity gate]
  ID --> CTX[Context loader]
  CTX --> SUP[Supervisor]
  SUP --> N[Network] & B[Billing] & AC[Account] & E[Escalation]
  N & B & AC & E --> SR[Supervisor review]
  SR --> OG[Output guardrail]
  OG --> RESP[Response]
```

This page is filled in as each phase lands.
