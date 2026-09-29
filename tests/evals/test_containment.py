"""The assume-breach containment suite (D-A4-12): with every model compromised, the
architecture holds, and each control is load-bearing for exactly what it is documented
to contain."""

from __future__ import annotations

from pathlib import Path

import pytest

from evals.containment import ABLATIONS, EXPECTED_BREACHES, SCENARIOS, breaches, measure_all, render

PAGE = Path(__file__).parents[2] / "docs" / "evidence" / "containment.md"


@pytest.fixture(scope="module")
def matrix() -> dict[str | None, dict[str, bool]]:
    return measure_all()


def test_with_every_model_compromised_nothing_leaves(
    matrix: dict[str | None, dict[str, bool]],
) -> None:
    assert [sid for sid, held in matrix[None].items() if not held] == []


@pytest.mark.parametrize("control", list(EXPECTED_BREACHES))
def test_removing_a_control_breaches_exactly_what_it_is_documented_to_contain(
    matrix: dict[str | None, dict[str, bool]], control: str
) -> None:
    assert breaches(matrix, control) == EXPECTED_BREACHES[control]


def test_every_control_is_documented_and_every_scenario_is_attributed_or_structural(
    matrix: dict[str | None, dict[str, bool]],
) -> None:
    assert set(ABLATIONS) == set(EXPECTED_BREACHES)
    attributed = set().union(*EXPECTED_BREACHES.values())
    unattributed = {s.id for s in SCENARIOS} - attributed
    # A scenario no ablation can breach is structural, and must say so on the page.
    assert unattributed == {"model-cannot-choose-the-account"}


def test_the_evidence_page_is_the_measured_matrix(
    matrix: dict[str | None, dict[str, bool]],
) -> None:
    assert PAGE.read_text(encoding="utf-8") == render(matrix)
