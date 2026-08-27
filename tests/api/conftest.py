from __future__ import annotations

from collections.abc import Iterator

import pytest

from tests.api._sentinel_client import reset_sentinel_overrides


@pytest.fixture(autouse=True)
def _clear_sentinel_overrides() -> Iterator[None]:
    """Every API test starts and ends with a clean dependency-override table,
    so the stubbed graph one test installs never leaks into another."""
    reset_sentinel_overrides()
    yield
    reset_sentinel_overrides()
