"""The grounding + scope review over a specialist's draft (docs/PLAN.md
Phase 3) — the centrepiece the reader should notice, the same way A2's
validator node is: it re-reads the draft against its own context rather than
trusting the specialist that wrote it."""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from sentinel.graph.protocols import SupervisorReviewChain
from sentinel.prompts.loader import load_prompt
from sentinel.schemas.review import ReviewResult


def build_supervisor_review_chain(model: BaseChatModel) -> SupervisorReviewChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_prompt("supervisor_review_v1")),
            (
                "human",
                "Draft response:\n{draft}\n\nCited clause(s):\n{citations}\n\n"
                "Context the specialist was given:\n{context}",
            ),
        ]
    )
    return cast(
        SupervisorReviewChain,
        prompt | model.with_structured_output(ReviewResult),
    )
