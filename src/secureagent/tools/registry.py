"""The tool registry, and the scope a principal is entitled to (docs/PLAN.md §4.2 #2).

`scope_for(principal)` is a pure function of the caller's proven identity. An
unverified caller's scope contains no account tool at all, so such a tool is
*unreachable*, not merely refused. Nothing a model says can widen a scope.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.tools import StructuredTool

from secureagent.retrieval.search import PolicySearcher
from secureagent.schemas.principal import Principal
from secureagent.schemas.scoping import ToolScope
from secureagent.store import DEFAULT_ROW_CAP, CustomerStore
from secureagent.store.ticket_store import TicketStore
from secureagent.tools.account import build_account_tools
from secureagent.tools.actions import build_action_tools
from secureagent.tools.base import ToolSpec
from secureagent.tools.public import build_public_tools


@dataclass(frozen=True)
class ToolRegistry:
    specs: dict[str, ToolSpec]

    def scope_for(self, principal: Principal, row_cap: int = DEFAULT_ROW_CAP) -> ToolScope:
        allowed = frozenset(
            name
            for name, spec in self.specs.items()
            if principal.verified or not spec.requires_verified
        )
        return ToolScope(allowed_tool_names=allowed, row_cap=row_cap)

    def langchain_tools(self, scope: ToolScope) -> list[StructuredTool]:
        """Schema-only tools for exactly the scope, so a model is never even shown
        a tool it may not call."""
        return [
            spec.to_langchain()
            for name, spec in self.specs.items()
            if name in scope.allowed_tool_names
        ]


def build_registry(
    customers: CustomerStore, tickets: TicketStore, policy: PolicySearcher
) -> ToolRegistry:
    specs = [
        *build_account_tools(customers),
        *build_public_tools(customers, policy),
        *build_action_tools(tickets),
    ]
    return ToolRegistry(specs={spec.name: spec for spec in specs})
