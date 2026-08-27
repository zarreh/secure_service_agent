# Architecture Decision Records (A4)

- [D-A4-1 Independently generated account data, not the course CSVs](D-A4-1-independent-synthetic-accounts.md)
- [D-A4-2 PBKDF2-HMAC-SHA256 for PIN storage, never plaintext](D-A4-2-pbkdf2-pin-hashing.md)
- [D-A4-3 The deterministic guardrail layer wins, and short-circuits the LLM call](D-A4-3-deterministic-layer-wins.md)
- [D-A4-4 The PIN lockout counter lives in the account store, not in graph state](D-A4-4-persistent-lockout-counter.md)
- [D-A4-5 Specialists never let the model choose an account identifier](D-A4-5-no-llm-chosen-tool-arguments.md)
- [D-A4-6 `POST /chat` never pre-validates `account_id`](D-A4-6-no-enumeration-via-http-status.md)
- [D-A4-7 The audit log is the persisted node-event stream, not a separate table](D-A4-7-audit-log-is-the-event-store.md)
