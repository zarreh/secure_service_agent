"""The layer-2 injection classifier (docs/PLAN.md §5.1): a pure LCEL runnable.

One structured-output call on the fast model, with the customer's message wrapped as
untrusted data. Behind a `Protocol`, so tests use a stub. This is defence in depth,
not the defence: the architecture holds when this is wrong (D-A4-1), and its
behaviour on a real model is reported as not populated until one exists.
"""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from secureagent.graph.protocols import InjectionClassifierChain
from secureagent.prompts import load_prompt
from secureagent.schemas.verdicts import InjectionAssessment


def build_injection_classifier_chain(model: BaseChatModel) -> InjectionClassifierChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_prompt("injection_classifier_v1")),
            ("human", "<customer_message>\n{message}\n</customer_message>"),
        ]
    )
    return cast(
        InjectionClassifierChain, prompt | model.with_structured_output(InjectionAssessment)
    )
