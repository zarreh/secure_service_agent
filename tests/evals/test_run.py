"""The eval harness's own scoring logic — run offline, with no API key,
against the same scenarios `make eval` uses (docs/PLAN.md Phase 6). This
proves the harness is correct; it does not prove live model accuracy on the
routing layer, which is exactly what `_run_routing` skips without a key."""

import pytest

from evals.run import _run_input_attacks, _run_output_attacks, _run_routing
from sentinel.settings import get_settings


def test_every_input_attack_scenario_matches_its_expected_outcome() -> None:
    results = _run_input_attacks()
    assert results
    assert all(r.passed for r in results), [r for r in results if not r.passed]


def test_every_output_attack_scenario_matches_its_expected_outcome() -> None:
    results = _run_output_attacks()
    assert results
    assert all(r.passed for r in results), [r for r in results if not r.passed]


def test_routing_is_skipped_without_an_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SENTINEL_OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        assert _run_routing() is None
    finally:
        get_settings.cache_clear()
