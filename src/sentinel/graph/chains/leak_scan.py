"""The output guardrail's LLM layer (docs/PLAN.md Phase 2) — catches
paraphrased leaks the deterministic regex layer
(`sentinel.guardrails.output_scanner`) cannot express. Returns a
`LeakScanResult` via `with_structured_output`, never free text.
"""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from sentinel.graph.protocols import LeakScanChain
from sentinel.prompts.loader import load_prompt
from sentinel.schemas.guardrail import LeakScanResult


def build_leak_scan_chain(model: BaseChatModel) -> LeakScanChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_prompt("leak_scan_v1")),
            ("human", "Verified account: {verified_account_id}\n\nDraft response:\n{draft}"),
        ]
    )
    return cast(
        LeakScanChain,
        prompt | model.with_structured_output(LeakScanResult),
    )
