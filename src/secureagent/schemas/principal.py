"""The caller's proven identity (docs/PLAN.md §4.2, D-A4-2).

A `Principal` is produced only by `secureagent.identity` and only after a PIN has
been checked. It lives here, at the bottom of the layering, so the graph and the
tools can carry and read it without ever importing the module that verifies
credentials. It is frozen: nothing downstream can promote an unverified caller.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)

    account_id: str | None = None
    verified: bool = False
    verified_at: str | None = None

    @model_validator(mode="after")
    def _verified_means_an_account(self) -> Principal:
        if self.verified and not self.account_id:
            raise ValueError("a verified principal must name an account")
        if not self.verified and self.account_id is not None:
            raise ValueError("an unverified principal must not carry an account")
        return self


UNVERIFIED = Principal()
