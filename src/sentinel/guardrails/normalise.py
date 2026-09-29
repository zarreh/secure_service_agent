"""Text normalisation for the input screen (docs/PLAN.md §5.1).

Detection patterns are only as good as the text they see. `1gn0re`, zero-width
characters, Cyrillic look-alikes, `i g n o r e` and base64 payloads all defeat a
regex run over raw input. This produces several *views* of a message; the screen
scans every view, and reports which one matched so a block is attributable.

Bounded on purpose: decoding is capped in depth, candidates and size, so the
normaliser cannot itself be turned into a resource-exhaustion vector (OWASP LLM10).
"""

from __future__ import annotations

import base64
import binascii
import re
import unicodedata

MAX_INPUT_CHARS = 4_000
MAX_DECODE_CANDIDATES = 4
MAX_DECODE_DEPTH = 2
MIN_ENCODED_LEN = 16
MAX_ENCODED_LEN = 1_024

# Zero-width and bidirectional-control characters an attacker inserts to split a
# keyword without changing how it reads. Category Cf covers most; the rest are listed.
_INVISIBLE = {
    "\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad", "\u180e",
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069",
}  # fmt: skip

# Look-alikes from other scripts that render like Latin letters. NFKC does not fold
# these (they are distinct letters, not compatibility forms), so they are listed.
_HOMOGLYPHS = str.maketrans(
    {
        "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i",
        "ј": "j", "ѕ": "s", "һ": "h", "ԁ": "d", "ɡ": "g", "ո": "n",
        "α": "a", "ε": "e", "ο": "o", "ρ": "p", "ι": "i", "ν": "v", "τ": "t", "κ": "k",
    }
)  # fmt: skip

_LEET = str.maketrans(
    {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"}
)

_SPACED_LETTERS = re.compile(r"(?<![a-z0-9])((?:[a-z][\s.\-_*]){3,}[a-z])(?![a-z0-9])")
_B64 = re.compile(rf"[A-Za-z0-9+/]{{{MIN_ENCODED_LEN},{MAX_ENCODED_LEN}}}={{0,2}}")
_HEX = re.compile(rf"(?:[0-9a-fA-F]{{2}}){{{MIN_ENCODED_LEN // 2},{MAX_ENCODED_LEN // 2}}}")


def _strip_invisible(text: str) -> str:
    return "".join(
        ch
        for ch in text
        if ch not in _INVISIBLE and (ch in "\n\t" or not unicodedata.category(ch).startswith("C"))
    )


def _collapse_spaced_letters(text: str) -> str:
    """`i g n o r e` and `i.g.n.o.r.e` become `ignore`."""
    return _SPACED_LETTERS.sub(lambda m: re.sub(r"[\s.\-_*]", "", m.group(1)), text)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _printable(data: bytes) -> str | None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if len(text) < 6 or sum(ch.isprintable() or ch.isspace() for ch in text) / len(text) < 0.9:
        return None
    return text


def _decode_candidates(text: str) -> list[str]:
    found: list[str] = []
    for match in _B64.findall(text):
        try:
            decoded = _printable(base64.b64decode(match + "=" * (-len(match) % 4), validate=True))
        except (binascii.Error, ValueError):
            continue
        if decoded:
            found.append(decoded)
    for match in _HEX.findall(text):
        try:
            decoded = _printable(bytes.fromhex(match))
        except ValueError:
            continue
        if decoded:
            found.append(decoded)
    return found[:MAX_DECODE_CANDIDATES]


def base_view(text: str) -> str:
    """NFKC, invisible characters removed, homoglyphs folded, case-folded."""
    return _squash(_raw_clean(text).translate(_HOMOGLYPHS).casefold())


def _raw_clean(text: str) -> str:
    """NFKC and invisible characters removed, **case preserved**.

    Base64 is case-sensitive, so anything that decodes must start from this, not
    from the case-folded view: folding first destroys every encoded payload.
    """
    return _strip_invisible(unicodedata.normalize("NFKC", text[:MAX_INPUT_CHARS]))


_LETTER_SPACING = re.compile(r"(?:[a-z][\s.\-_*]){6,}[a-z]")


def has_letter_spacing(view: str) -> bool:
    """Six or more single letters in a row separated by spaces or punctuation."""
    return _LETTER_SPACING.search(view) is not None


def views(text: str) -> dict[str, str]:
    """Named views of one message, most-conservative first. Duplicates are dropped so
    a clean message costs one scan, not several.

    `collapsed` (all separators removed) exists only when the message shows letter
    spacing: with single spaces between letters *and* words, word boundaries are
    unrecoverable, so it is scanned with boundary-free variants of the rules.
    """
    base = base_view(text)
    out: dict[str, str] = {"plain": base}

    for name, candidate in (
        ("spaced", _squash(_collapse_spaced_letters(base))),
        ("leet", _squash(base.translate(_LEET))),
    ):
        if candidate not in out.values():
            out[name] = candidate

    if has_letter_spacing(base):
        out["collapsed"] = re.sub(r"[\s.\-_*]", "", base)

    pending = [(1, _raw_clean(text))]
    seen: set[str] = set()
    while pending and len(out) < 12:
        depth, current = pending.pop(0)
        for decoded in _decode_candidates(current):
            view = base_view(decoded)
            if view in seen:
                continue
            seen.add(view)
            name = f"decoded{depth}"
            out[name if name not in out else f"{name}_{len(out)}"] = view
            if depth < MAX_DECODE_DEPTH:
                pending.append((depth + 1, _raw_clean(decoded)))
    return out
