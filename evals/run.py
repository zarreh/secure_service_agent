"""`make eval` entry point (docs/PLAN.md Phase 6).

Two independently scored layers:

- **Attack scenarios** (`INPUT_ATTACK_SCENARIOS`, `OUTPUT_ATTACK_SCENARIOS`)
  run against the deterministic guardrail functions directly — no LLM, no
  API key, always runnable. This is the layer D-A4-3 says the canonical
  eval set must not depend on model variance for, so it is scored
  unconditionally.
- **Routing scenarios** (`ROUTING_SCENARIOS`) run against the real
  supervisor-routing chain — an LLM judgement call, so it needs a
  configured `SENTINEL_OPENAI_API_KEY`. If none is set, this layer is
  **skipped with a clear message, not failed** — `make eval` stays useful
  in an environment with no key (e.g. this repo's own CI, which does not
  run `make eval` at all, matching A7's precedent).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from zarreh_agentkit.evals.runner import EvalOutcome, run_eval_cli

from evals.scenarios import (
    INPUT_ATTACK_SCENARIOS,
    OUTPUT_ATTACK_SCENARIOS,
    ROUTING_SCENARIOS,
)
from sentinel.graph.chains.supervisor_route import build_supervisor_route_chain
from sentinel.graph.policies import build_fast_model
from sentinel.guardrails.input_scanner import scan_input_deterministic
from sentinel.guardrails.output_scanner import scan_output_deterministic
from sentinel.settings import get_settings


@dataclass
class ScenarioResult:
    id: str
    description: str
    expected: str
    actual: str
    passed: bool


@dataclass
class Report:
    input_results: list[ScenarioResult]
    output_results: list[ScenarioResult]
    routing_results: list[ScenarioResult] | None  # None if skipped (no API key)


def _run_input_attacks() -> list[ScenarioResult]:
    results = []
    for scenario in INPUT_ATTACK_SCENARIOS:
        verdict = scan_input_deterministic(scenario.text)
        passed = verdict.blocked == scenario.expected_blocked and (
            not scenario.expected_blocked or verdict.rule_id == scenario.expected_rule_id
        )
        results.append(
            ScenarioResult(
                id=scenario.id,
                description=scenario.description,
                expected=f"blocked={scenario.expected_blocked} rule={scenario.expected_rule_id}",
                actual=f"blocked={verdict.blocked} rule={verdict.rule_id}",
                passed=passed,
            )
        )
    return results


def _run_output_attacks() -> list[ScenarioResult]:
    results = []
    for scenario in OUTPUT_ATTACK_SCENARIOS:
        verdict = scan_output_deterministic(
            scenario.text, verified_account_id=scenario.verified_account_id
        )
        passed = verdict.blocked == scenario.expected_blocked and (
            not scenario.expected_blocked or verdict.rule_id == scenario.expected_rule_id
        )
        results.append(
            ScenarioResult(
                id=scenario.id,
                description=scenario.description,
                expected=f"blocked={scenario.expected_blocked} rule={scenario.expected_rule_id}",
                actual=f"blocked={verdict.blocked} rule={verdict.rule_id}",
                passed=passed,
            )
        )
    return results


def _run_routing() -> list[ScenarioResult] | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    chain = build_supervisor_route_chain(build_fast_model(settings))
    results = []
    for scenario in ROUTING_SCENARIOS:
        route = chain.invoke({"question": scenario.question})
        passed = route.specialist == scenario.expected_specialist
        results.append(
            ScenarioResult(
                id=scenario.id,
                description=scenario.description,
                expected=scenario.expected_specialist,
                actual=route.specialist,
                passed=passed,
            )
        )
    return results


def run_suite() -> Report:
    return Report(
        input_results=_run_input_attacks(),
        output_results=_run_output_attacks(),
        routing_results=_run_routing(),
    )


def _print_results(title: str, results: list[ScenarioResult]) -> None:
    print(f"\n{title}")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.id}: {r.description}")
        if not r.passed:
            print(f"         expected: {r.expected}")
            print(f"         actual:   {r.actual}")


def print_report(report: Report) -> None:
    _print_results(
        "Input guardrail attack scenarios (deterministic, no API key needed)", report.input_results
    )
    _print_results(
        "Output guardrail attack scenarios (deterministic, no API key needed)",
        report.output_results,
    )
    if report.routing_results is None:
        print(
            "\nRouting scenarios: SKIPPED — no SENTINEL_OPENAI_API_KEY configured. "
            "This layer needs a real model; the attack-scenario layers above do not."
        )
    else:
        _print_results("Routing scenarios (requires a configured model)", report.routing_results)


def outcomes(report: Report) -> list[EvalOutcome]:
    all_results = [*report.input_results, *report.output_results, *(report.routing_results or [])]
    return [EvalOutcome(case_id=r.id, passed=r.passed) for r in all_results]


def main() -> int:
    return run_eval_cli(run_suite, print_report, outcomes)


if __name__ == "__main__":
    sys.exit(main())
