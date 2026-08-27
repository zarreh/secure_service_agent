"""The input guardrail's LLM layer (docs/PLAN.md Phase 2) — catches
paraphrased or novel injection attempts the deterministic deny-list
(`sentinel.guardrails.input_scanner`) cannot express. Returns an
`InjectionScanResult` via `with_structured_output`, never free text.
"""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from sentinel.graph.protocols import InjectionScanChain
from sentinel.prompts.loader import load_prompt
from sentinel.schemas.guardrail import InjectionScanResult


def build_injection_scan_chain(model: BaseChatModel) -> InjectionScanChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_prompt("injection_scan_v1")),
            ("human", "{message}"),
        ]
    )
    return cast(
        InjectionScanChain,
        prompt | model.with_structured_output(InjectionScanResult),
    )
