"""`make eval` entry point.

Empty until Phase 6 builds the canonical scenario set (legitimate requests per
specialist) and the labelled attack set (docs/PLAN.md). Uses
`zarreh_agentkit.evals.run_eval_cli` as the run/print/gate shell, per
docs/HARVEST.md #14.
"""

import sys


def main() -> int:
    print("No evaluation scenarios yet — see docs/PLAN.md Phase 6.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
