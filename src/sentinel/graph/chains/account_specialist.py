"""The account specialist's drafting chain (docs/PLAN.md Phase 3, D-A4-5)."""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from sentinel.graph.protocols import SpecialistChain
from sentinel.prompts.loader import load_prompt
from sentinel.schemas.specialist import SpecialistResponse


def build_account_specialist_chain(model: BaseChatModel) -> SpecialistChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_prompt("account_specialist_v1")),
            (
                "human",
                "Question: {question}\n\n"
                "Policy clause {clause_id}:\n{clause_body}\n\n"
                "Account record:\n{account}\n\nPlan record:\n{plan}",
            ),
        ]
    )
    return cast(
        SpecialistChain,
        prompt | model.with_structured_output(SpecialistResponse),
    )
