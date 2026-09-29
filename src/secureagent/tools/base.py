"""Tool infrastructure: a spec, and the context a tool runs in.

A `ToolSpec` says what the *model* may see (`args_model`, which never contains an
identity field) and what the *caller* must have (`requires_verified`). The
principal reaches a tool only through `ToolContext`, built by the executor.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from secureagent.schemas.principal import Principal


@dataclass(frozen=True)
class ToolContext:
    principal: Principal
    run_id: str
    row_cap: int

    @property
    def account_id(self) -> str:
        """The verified account. Raises for an unverified principal, which the
        scope should have made unreachable long before a tool asked."""
        if not self.principal.verified or self.principal.account_id is None:
            raise PermissionError("this tool requires a verified account")
        return self.principal.account_id


ToolFn = Callable[[ToolContext, BaseModel], BaseModel]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_model: type[BaseModel]
    fn: ToolFn
    requires_verified: bool

    def to_langchain(self) -> StructuredTool:
        """A schema-only tool for `bind_tools`. Never executed by LangChain: the
        scoped executor runs every call, so this function refuses to run."""

        def _never_run(**_: object) -> str:
            raise RuntimeError(f"{self.name} must be executed by the scoped executor")

        return StructuredTool.from_function(
            func=_never_run,
            name=self.name,
            description=self.description,
            args_schema=self.args_model,
        )
