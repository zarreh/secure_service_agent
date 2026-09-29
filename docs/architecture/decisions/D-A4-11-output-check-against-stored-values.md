# D-A4-11 — The output check compares against stored values, and nothing blocked is echoed

**Status:** Accepted, implemented (`guardrails/output_scanner.py`, `api/client_view.py`,
`AccountStore.other_customer_names`).

## Context

The output guardrail's deterministic layer had two regexes: a PIN-disclosure pattern
and `ACCT_\d+` compared with the verified account id. Two problems, found by writing
an attack corpus first and by driving the real API:

1. **It checked a pattern, not the data.** A model that names another customer, writes
   an id in lowercase, hyphenates it, spaces it out or base64-wraps it walks past it.
2. **A block leaked what it blocked.** The verdict's `reason` quoted the other
   customer's account id, and the verdict is streamed to the client. Separately, the
   stored event stream doubles as the client replay (D-A4-7), so the specialist node's
   `draft` (the very text the guardrail blocked) was readable through
   `GET /chat/{id}/events` even though the UI says it was "discarded, not shown".

## Decision

- The scan runs over the same normalised views as the input screen (spaced, leet,
  base64/hex-decoded, letter-collapsed), so an obfuscated leak is caught like a plain one.
- **Stored values, not only shapes.** The node reads every other customer's name from
  the store and blocks a response containing one (`other-customer-name`). A name the
  caller shares with another customer is left out, or greeting them would be blocked.
  Account ids are compared by their digits across `ACCT_`, `acct-`, `ACCT 2001` and
  spaced forms; the leet view is skipped for ids because it rewrites digits and would
  block the caller's own id.
- **A block never quotes its value.** Reasons are fixed strings; a test asserts no
  account id, id digits, customer name or PIN appears in any block reason.
- **The client replay is an allow-list** (`project_for_client`): only the fields the UI
  renders (`input_verdict`, `identity`, `route`, `review`, `citations`, `output_verdict`,
  `response`) leave the server. The audit log keeps everything, including a blocked
  draft, because an operator needs it; that is itself sensitive and is documented as such.

## Measured (development corpus, `data/output_attacks.py`, n=26)

Written before the extension existed; built from a generated population so a "leaked
name" is a real one. **These are development figures: the corpus was iterated against
and there is no held-out output set.**

| | Before (raw first run) | After |
|---|---|---|
| Leaks expected to block (n=15) | 4 blocked (27%) | 15 blocked |
| Account-id forms (plain, lowercase, hyphen, space, spaced, base64) | 1 of 6 | 6 of 6 |
| Other customers' names (plain, lowercase, spaced, base64) | 0 of 4 | 4 of 4 |
| PINs (plain, other account, confirm, spaced, base64) | 3 of 5 | 5 of 5 |
| Ordinary answers wrongly blocked (n=7) | 0 | 0 |
| Policy clause text wrongly blocked (n=6, proxy for a paraphrased answer) | not measured | 0 |

Two real defects were found while extending it: a spaced-out account id needed a
separator-tolerant pattern, and the leet view (which turns `0` into `o`) made the
caller's own id look like a mismatch and blocked it.

**Documented misses** (each asserted by a test as behaving that way): a PIN spelled in
words, a PIN partially disclosed ("ends in 21"), a base64-wrapped bare name (below the
decoder's minimum run length), and a semantic paraphrase ("another customer on the Plus
plan pays more"). The last is the LLM leak classifier's job, whose behaviour on a real
model is **not populated** here.

## Consequences

- Name matching on first names is a low-precision signal in a population with common
  names; it is a deliberate fail-closed choice, bounded by the shared-name exclusion.
- A per-run canary token (system-prompt-leak detection) was considered and not added:
  the specialists' prompts are versioned, public files and hold no secret, so a leaked
  prompt costs little; the value is a store value, which is what is now checked.
