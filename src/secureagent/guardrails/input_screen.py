"""The deterministic input screen (docs/PLAN.md §5.1).

Fast, free, exact and auditable. It is **not** the defence: it is a cheap first
pass that removes the crude attacks before any model is spent on them, and the
architecture holds when it fails (D-A4-1). Its limits are measured and published,
including the paraphrase attacks it cannot see.

Design rules, all about precision:

- A verb alone never matches. `ignore` matches only near an *instruction-like
  target* (`ignore ... instructions`), so "please do not ignore my ticket" passes.
- `block` is reserved for high-confidence categories. Ambiguous signals (a literal
  `[system]` tag, an internal tool name, another account's id) only `flag`: the
  message goes on to the layer-2 classifier rather than being refused outright.
- Every rule runs over *every* normalised view (plain, spaced, leetspeak, decoded),
  and the match records which view it hit.

Patterns are lowercase: views are case-folded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from secureagent.guardrails.normalise import views
from secureagent.schemas.verdicts import ScreenMatch, ScreenResult, Severity

_TARGET = (
    r"(?:instructions?|rules?|guidelines?|directives?|prompts?|programming|restrictions?|"
    r"safeguards?|safety|verification|authentication|identity check|filters?|polic(?:y|ies)|"
    r"guardrails?|training)"
)
_QUALIFIER = (
    r"(?:all|any|every|your|the|these|those|previous|prior|above|earlier|"
    r"system|safety|security|content)"
)
_ABOUT_YOU = r"(?:your|the assistant'?s|the ai'?s|the bot'?s|the model'?s)"
_HIDDEN = r"(?:system|hidden|initial|original|secret|internal|underlying)"
_PROMPTY = r"(?:prompts?|instructions?|rules|guidelines|configuration|message)"
_FICTIONAL_SELF = (
    r"(?:unrestricted|unfiltered|uncensored|jailbroken|dan|(?:system\s+)?admin(?:istrator)?|root|"
    r"developer|evil|different|another ai|a different)"
)


@dataclass(frozen=True)
class Rule:
    category: str
    severity: Severity
    pattern: re.Pattern[str]


def _rule(category: str, severity: Severity, pattern: str) -> Rule:
    return Rule(category, severity, re.compile(pattern))


RULES: tuple[Rule, ...] = (
    _rule(
        "instruction_override",
        "block",
        rf"\b(?:ignore|disregard|forget|override|bypass|circumvent|skip|drop|discard)\b"
        rf"[^.!?\n]{{0,30}}\b(?:{_QUALIFIER}\s+){{0,3}}{_TARGET}\b",
    ),
    _rule(
        "role_hijack",
        "block",
        rf"\b(?:you\s+are\s+now|from\s+now\s+on\s+you\s+are|you\s+will\s+now\s+act\s+as)\s+"
        rf"(?:an?\s+)?{_FICTIONAL_SELF}\b|"
        rf"\bpretend\s+(?:that\s+)?(?:you\s+are|to\s+be)\s+(?:an?\s+|the\s+)?{_FICTIONAL_SELF}\b|"
        rf"\bact\s+as\s+(?:if\s+you\s+(?:were|are)\s+)?(?:an?\s+)?{_FICTIONAL_SELF}\b|"
        r"\byou\s+are\s+no\s+longer\s+(?:bound|restricted|limited|an?\s+assistant)\b",
    ),
    _rule(
        "prompt_extraction",
        "block",
        rf"\b(?:reveal|print|repeat|output|leak|dump|expose|display|show\s+me|share)\b"
        rf"[^.!?\n]{{0,25}}\b(?:your|the)\s+{_HIDDEN}\s+{_PROMPTY}\b|"
        rf"\b(?:what\s+(?:is|are|were)|tell\s+me|give\s+me|recite)\s+{_ABOUT_YOU}\s+"
        rf"(?:{_HIDDEN}\s+)?{_PROMPTY}\b|"
        r"\b(?:repeat|print|output)\s+(?:everything|all\s+text)\s+(?:above|before)\b",
    ),
    _rule(
        "jailbreak_terms",
        "block",
        r"\b(?:enable|activate|enter|switch\s+to|turn\s+on)\s+(?:dan|developer|god|sudo|"
        r"unrestricted|admin|jailbreak)\s+mode\b|"
        r"\bdo\s+anything\s+now\b|\bdan\s+mode\b|\bjailbreak(?:ed)?\s+(?:mode|prompt)\b",
    ),
    _rule(
        "credential_or_bulk_disclosure",
        "block",
        r"\b(?:what\s+is|tell\s+me|give\s+me|read\s+out|show\s+me|list|dump|export)\b"
        r"[^.!?\n]{0,30}\b(?:pin|passcode|password)s?\b[^.!?\n]{0,20}\b(?:of|for)\b"
        r"[^.!?\n]{0,20}\b(?:account|acct|customer|user|someone|another|his|her|their)\b|"
        r"\b(?:list|show|read\s+out|give\s+me|dump|export)\b[^.!?\n]{0,25}"
        r"\b(?:all|every|other|another)\b[^.!?\n]{0,15}"
        r"\b(?:customers?|accounts?|users?|phone\s+numbers?|pins?)\b",
    ),
    # --- ambiguous: flag for the layer-2 classifier, never a block on their own ---
    _rule(
        "marker_tags",
        "flag",
        r"\[\s*(?:system|assistant|admin|developer|inst)\s*\]|<\|?\s*(?:system|im_start|im_end)"
        r"\s*\|?>|##\s*system\b|\{\{\s*system\s*\}\}|<<\s*sys\s*>>",
    ),
    _rule(
        "tool_name_mention",
        "flag",
        r"\b(?:get_plan|get_usage|get_bills|list_outages|search_policy|raise_network_ticket|"
        r"escalate_to_human|request_sensitive_action)\b|\b(?:call|invoke|run)\s+(?:the\s+)?tool\b",
    ),
    _rule(
        "other_account_reference",
        "flag",
        r"\bacct[_\-\s]?\d{3,}\b|\b555[\-\s.]?01\d{2}\b",
    ),
)


def _to_collapsed(source: str) -> str:
    """Derive the boundary-free form of a rule from its source pattern.

    The `collapsed` view exists only when a message shows letter spacing
    (`i g n o r e ...`); with single spaces between letters *and* words, word
    boundaries are unrecoverable, so the same rule must match run-together text.
    Deriving it mechanically, rather than maintaining a second hand-written copy, is
    what removes the drift that let two held-out sets each find a different rule
    missing from the copy (data/attacks_heldout_v2.py).
    """
    out = source.replace(r"\b", "")
    out = out.replace(r"\s+", "").replace(r"\s*", "")
    out = out.replace("[^.!?\\n]", "[^!?]")  # the filler class, minus whitespace
    return out.replace(" ", "")


COLLAPSED_RULES: tuple[Rule, ...] = tuple(
    _rule(rule.category, rule.severity, _to_collapsed(rule.pattern.pattern))
    for rule in RULES
    if rule.severity == "block"
)


def screen(text: str) -> ScreenResult:
    matches: list[ScreenMatch] = []
    seen: set[tuple[str, str]] = set()
    for view_name, view in views(text).items():
        rules = COLLAPSED_RULES if view_name == "collapsed" else RULES
        for rule in rules:
            found = rule.pattern.search(view)
            if found is None or (rule.category, view_name) in seen:
                continue
            seen.add((rule.category, view_name))
            matches.append(
                ScreenMatch(
                    category=rule.category,
                    severity=rule.severity,
                    view=view_name,
                    span=found.group(0)[:80],
                )
            )
    if any(m.severity == "block" for m in matches):
        return ScreenResult(verdict="block", matches=matches)
    if matches:
        return ScreenResult(verdict="flag", matches=matches)
    return ScreenResult(verdict="allow")
