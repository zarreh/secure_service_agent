"""The network specialist's drafting chain (docs/PLAN.md Phase 3). Deliberate
deviation from the source notebook's ReAct-over-tools design: the model
never chooses a tool argument that could name an account — the node fetches
the plan and clause by the identity-gate-verified `account_id` and passes
them in, so the specialist can only ever draft about the context it was
handed (D-A4-5)."""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from sentinel.graph.protocols import SpecialistChain
from sentinel.prompts.loader import load_prompt
from sentinel.schemas.specialist import SpecialistResponse


def build_network_specialist_chain(model: BaseChatModel) -> SpecialistChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_prompt("network_specialist_v1")),
            (
                "human",
                "Question: {question}\n\n"
                "Policy clause {clause_id}:\n{clause_body}\n\n"
                "Prior interaction history:\n{history}",
            ),
        ]
    )
    return cast(
        SpecialistChain,
        prompt | model.with_structured_output(SpecialistResponse),
    )
