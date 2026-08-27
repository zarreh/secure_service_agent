"""The supervisor's routing decision (docs/PLAN.md Phase 3) — a single LLM
call, never a tool-calling loop: the graph decides which specialist runs,
the specialist never gets to redirect itself."""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from sentinel.graph.protocols import SupervisorRouteChain
from sentinel.prompts.loader import load_prompt
from sentinel.schemas.supervisor import SupervisorRoute


def build_supervisor_route_chain(model: BaseChatModel) -> SupervisorRouteChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_prompt("supervisor_route_v1")),
            ("human", "{question}"),
        ]
    )
    return cast(
        SupervisorRouteChain,
        prompt | model.with_structured_output(SupervisorRoute),
    )
