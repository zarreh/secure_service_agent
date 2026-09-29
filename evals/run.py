"""Layer 1 canonical regression runner (docs/PLAN.md §6, §9 Phase 8).

Phase 0 ships the entry point so `make eval` and the CI gate exist from the
start; the canonical cases and the attack suite arrive with the phases that
make each of them meaningful. Uses the library's run/print/gate shell.
"""

import sys

from zarreh_agentkit.evals import EvalOutcome, run_eval_cli


def _run_suite() -> list[EvalOutcome]:
    return []


def _print_report(outcomes: list[EvalOutcome]) -> None:
    print(f"Layer 1 canonical eval and attack suite — {len(outcomes)} cases registered (Phase 0).")


def main() -> int:
    return run_eval_cli(_run_suite, _print_report, lambda outcomes: outcomes)


if __name__ == "__main__":
    sys.exit(main())
