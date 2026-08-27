"""The escalation handoff builder (docs/PLAN.md Phase 3), producing an
`EscalationHandoff` instead of a `SpecialistResponse` — it summarizes for a
human, it does not answer the customer."""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from sentinel.graph.protocols import EscalationChain
from sentinel.prompts.loader import load_prompt
from sentinel.schemas.escalation import EscalationHandoff


def build_escalation_specialist_chain(model: BaseChatModel) -> EscalationChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_prompt("escalation_specialist_v1")),
            (
                "human",
                "Question: {question}\n\nEscalation trigger: {trigger}\n\n"
                "Prior interaction history:\n{history}",
            ),
        ]
    )
    return cast(
        EscalationChain,
        prompt | model.with_structured_output(EscalationHandoff),
    )
