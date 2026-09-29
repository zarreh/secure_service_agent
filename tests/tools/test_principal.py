"""The principal type: an unverified caller cannot be promoted or given an account."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from secureagent.schemas.principal import UNVERIFIED, Principal
from secureagent.tools.base import ToolContext


def test_a_verified_principal_must_name_an_account() -> None:
    with pytest.raises(ValidationError):
        Principal(verified=True)


def test_an_unverified_principal_must_not_carry_an_account() -> None:
    with pytest.raises(ValidationError):
        Principal(account_id="ACCT_1000", verified=False)


def test_a_principal_is_frozen() -> None:
    principal = Principal(account_id="ACCT_1000", verified=True)
    with pytest.raises(ValidationError):
        principal.verified = False
    with pytest.raises(ValidationError):
        UNVERIFIED.account_id = "ACCT_1000"


def test_the_default_principal_is_unverified() -> None:
    assert not UNVERIFIED.verified and UNVERIFIED.account_id is None


def test_a_tool_context_refuses_to_yield_an_account_for_an_unverified_caller() -> None:
    ctx = ToolContext(principal=UNVERIFIED, run_id="r", row_cap=5)
    with pytest.raises(PermissionError):
        _ = ctx.account_id
