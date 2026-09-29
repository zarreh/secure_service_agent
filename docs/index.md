# Secure Service Agent

!!! warning "Read this first"
    You are reading about an AI system. This is an architectural demonstration on
    **fully synthetic** data: no real customer, carrier or payment data, and no
    real account or SIM operation is ever performed.

**A telecom customer-service agent built on the assumption that the user is
hostile.**

> **Guardrails detect. The architecture enforces.**

A detection layer — a pattern, a classifier, a second model asked to judge the
first — is a probabilistic filter, and a determined attacker eventually beats
one. So this project makes two separate, separately measured claims:

1. **Containment.** Assume the model is fully compromised and obeys every
   injected instruction. Does the system still refuse to disclose another
   customer's data, act for an unverified caller, or reveal its own prompt?
2. **Detection.** How often, and at which layer, is an attack caught before it
   reaches a tool?

Both are reported next to a control condition, because a security claim without
one is an assertion.

!!! info "Status"
    Phase 0 — the repository skeleton streams a run through the API end to end.
    None of the security controls are built yet, and this site does not describe
    any as if they were. The plan of record lives in the repository at
    `docs/PLAN.md`.
