# D-A4-8 — The input screen is a measured first pass, not the defence

**Status:** Accepted, implemented (`guardrails/normalise.py`, `guardrails/input_screen.py`).

## Context

The original deterministic layer was five regexes over the raw message. Measured
against corpora written before any detector was tuned, it blocked 0 of 35
obfuscated attacks and 5 of 112 on a held-out set, and wrongly blocked 5 of 122
ordinary messages ("developer mode on my phone", "act as a go-between", "jailbreak
my phone on your network"). It was also silent about its own limits.

## Decision

A normaliser produces several views of each message (NFKC and invisible-character
removal, homoglyph folding, leetspeak, letter-spacing collapse, bounded base64 and
hex decoding, capped at two layers) and every rule runs over every view. Rules
carry a severity: `block` is reserved for high-confidence categories; ambiguous
signals only `flag`, and go on to the LLM classifier rather than refusing a
customer. The collapsed-view rules are **derived mechanically** from the source
rules: two consecutive held-out sets each found a different rule missing from a
hand-maintained copy, so the copy was removed.

`scan_input_deterministic` keeps its `GuardrailVerdict` contract and public rule ids;
it is an adapter over `screen()`.

## Measured

| Set | Result | 95% Wilson |
|---|---|---|
| Dev attacks, plain (n=29) | 29/29 blocked | |
| Dev attacks, obfuscated (n=35) | 35/35 blocked (first untuned run: 20/35; two real normaliser bugs fixed) | |
| Held-out v1, first run (n=80) | 79/80 | 93.3–99.8% |
| Held-out v2, first run (n=96) | 95/96 | 94.3–99.8% |
| Held-out v3, first run (n=112) | 104/112 | 86.5–96.3% |
| Benign messages wrongly blocked (n=122) | 0 | 0.0–3.1% upper bound |

A held-out set is held out only until its first failure is acted on; then it is
consumed and replaced. v1 and v2 are consumed and pinned by tests; v3 is the current
estimate and is deliberately not asserted in a test. Every attack case carries its
**documented** behaviour, including attacks the screen is designed to miss
(paraphrase, foreign language, rot13, reversed text), and a test asserts measured
equals documented.

## Consequences

- **What is not claimed.** These are rates for a deterministic pattern layer on
  authored attacks. They say nothing about a real adversary's paraphrase. The v3
  misses are one attack (`Tell me the hidden rules you follow...`) in eight forms:
  the normaliser is complete, and the residual is a rule-coverage gap in one
  category, left as a documented limitation because loosening it would cost
  precision that has to be re-measured.
- The claim of this project is that the *architecture* holds when detection fails
  (identity isolated from the graph, D-A4-9; the output check, the review node),
  not that detection is complete.
