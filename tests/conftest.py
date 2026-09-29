from __future__ import annotations

from pathlib import Path

import pytest

from data.generate_synthetic import generate

ACCOUNTS = 12


@pytest.fixture(scope="session")
def service_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A freshly generated database. Generated rather than committed: the generator
    is deterministic, so there is no fixture to drift away from it."""
    path = tmp_path_factory.mktemp("service") / "service.db"
    generate(path, accounts=ACCOUNTS)
    return path


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
