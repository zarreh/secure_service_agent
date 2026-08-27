# D-A4-6 — `POST /chat` never pre-validates `account_id`

**Status:** Accepted, implemented (`api/routes/chat.py::create_chat`, Phase 4).

## Context

It would be easy to make `POST /chat` friendlier by checking
`account_store.get_account(body.account_id)` up front and returning 404 for
an unknown id before even starting a run. D-A4-2 already closed this exact
side channel one layer down — `AccountStore.verify_pin` and
`check_identity` both return `False`/`unverified` for an unknown account
without ever revealing that the difference was "no such account" rather
than "wrong PIN."

## Decision

`create_chat` performs no existence check. Every request — real account,
wrong PIN; unknown account, any PIN — gets the same `202` and the same
downstream path: the run executes, `identity_gate` reports `unverified`
either way, and the response is the same generic verification-required
message. The HTTP layer adds no new oracle on top of the one already closed
inside the graph.

## Consequences

- **Pros:** Consistent with D-A4-2 end to end — a caller cannot distinguish
  "this account doesn't exist" from "this account exists but you don't know
  the PIN" at any layer, HTTP included.
- **Cons:** A legitimate typo in `account_id` produces the same unhelpful
  "please verify" message as a wrong PIN, rather than a clearer "check your
  account number" — a minor UX cost accepted deliberately for the security
  property.
