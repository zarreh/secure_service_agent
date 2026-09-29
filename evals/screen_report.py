"""Reproduce the input screen's measured figures (D-A4-8).

`python -m evals.screen_report` runs the deterministic screen over the benign corpus,
the development attacks and the current held-out set and prints each rate with a 95%
Wilson interval. Held-out v3 is deliberately *not* pinned by a test: it is the current
estimate, and a set is held out only until its first failure is acted on.
"""

from __future__ import annotations

import math

from data.attacks import ATTACKS
from data.attacks_heldout_v3 import HELD_OUT_V3
from data.benign_corpus import BENIGN_CORPUS
from sentinel.guardrails.input_screen import screen


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / denom, (centre + margin) / denom


def _blocked(text: str) -> bool:
    return screen(text).verdict == "block"


def _row(label: str, texts: list[str], *, want_blocked: bool) -> str:
    hits = sum(_blocked(t) == want_blocked for t in texts)
    low, high = wilson(hits, len(texts))
    rate = f"{hits / len(texts):6.1%}"
    return f"{label:52} {hits:>3}/{len(texts):<3} = {rate}  95% Wilson [{low:.1%}, {high:.1%}]"


def main() -> None:
    plain = [a.text for a in ATTACKS if a.group == "known"]
    obfuscated = [a.text for a in ATTACKS if a.group == "obfuscated"]
    print("Input screen (deterministic layer only; no model involved)")
    print(_row("dev attacks, plain: blocked", plain, want_blocked=True))
    print(_row("dev attacks, obfuscated: blocked", obfuscated, want_blocked=True))
    print(
        _row(
            "held-out v3 (current estimate): blocked",
            [a.text for a in HELD_OUT_V3],
            want_blocked=True,
        )
    )
    print(_row("benign messages: NOT blocked", [m.text for m in BENIGN_CORPUS], want_blocked=False))
    flagged = sum(screen(m.text).verdict == "flag" for m in BENIGN_CORPUS)
    print(f"benign messages flagged for the LLM classifier: {flagged}/{len(BENIGN_CORPUS)}")


if __name__ == "__main__":
    main()
