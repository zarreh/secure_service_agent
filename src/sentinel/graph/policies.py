"""Model selection per node — never inline in a node (docs/PLAN.md §9.3).

Two profiles, the same split carried across the portfolio: a cheap `fast`
model for high-volume classification (the injection/leak scanners,
supervisor routing) and a stronger `reasoning` model for graded judgements
(supervisor review, added Phase 3).
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from sentinel.settings import Settings

FAST_MODEL = "gpt-4o-mini"
REASONING_MODEL = "gpt-4o"


def _api_key(settings: Settings) -> SecretStr | None:
    return SecretStr(settings.openai_api_key) if settings.openai_api_key else None


def build_fast_model(settings: Settings) -> ChatOpenAI:
    """Injection scanner, leak scanner, supervisor routing — cheap, high-volume."""
    return ChatOpenAI(model=FAST_MODEL, temperature=0, api_key=_api_key(settings))


def build_reasoning_model(settings: Settings) -> ChatOpenAI:
    """Supervisor review (Phase 3) — the judgement the response is graded on."""
    return ChatOpenAI(model=REASONING_MODEL, temperature=0, api_key=_api_key(settings))
