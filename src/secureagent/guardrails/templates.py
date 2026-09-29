"""Templated responses (docs/PLAN.md §5.1): a block is never model-written.

A refusal drafted by a model could itself be steered, could leak what the screen
matched, or could argue with the attacker. These are fixed strings. They also say
nothing about *why* a message was held, so an attacker cannot use the response to
tune the next attempt (the reason is in the audit log, not the reply).
"""

from __future__ import annotations

from typing import Literal

TemplateId = Literal["input_blocked", "output_fallback", "throttled", "review_failed"]


def input_blocked() -> str:
    return (
        "I can't help with that request. A member of our support team can look at it "
        "with you -- I've flagged it for a human agent."
    )


def output_fallback() -> str:
    return (
        "I'm sorry, I can't give you a reliable answer to that right now. A specialist will "
        "follow up with you shortly."
    )


def throttled(retry_after_seconds: float) -> str:
    minutes = max(1, round(retry_after_seconds / 60))
    return (
        "For your security, we've paused sign-in attempts for now. Please try again in about "
        f"{minutes} minute{'s' if minutes != 1 else ''}, or ask for a human agent."
    )


def review_failed() -> str:
    return (
        "I wasn't able to complete that safely. I've passed it to a human agent, who will "
        "be in touch."
    )


def render(template_id: TemplateId, *, retry_after_seconds: float = 0.0) -> str:
    if template_id == "input_blocked":
        return input_blocked()
    if template_id == "output_fallback":
        return output_fallback()
    if template_id == "throttled":
        return throttled(retry_after_seconds)
    return review_failed()
