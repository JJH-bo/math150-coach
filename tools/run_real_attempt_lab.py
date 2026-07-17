from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.challenge.real_attempt_lab import run_real_attempt_lab  # noqa: E402

DEFAULT_CASE_PATH = REPO_ROOT / "backend" / "challenge_data" / "ode_network_mvp" / "real_attempt_lab_seed.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Math150 real-attempt calibration lab.")
    parser.add_argument("--case-path", type=Path, default=DEFAULT_CASE_PATH)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="return non-zero when any case mismatches")
    args = parser.parse_args()

    report = run_real_attempt_lab(args.case_path)
    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Real Attempt Lab: {report.chapter_id} ({report.case_count} cases)")
        print(
            "Matches: "
            f"root={report.root_cause_matches}/{report.case_count}, "
            f"repair={report.repair_target_matches}/{report.case_count}, "
            f"exact={report.exact_matches}/{report.case_count}; "
            f"grade={report.calibration_grade}"
        )
        for result in report.results:
            marker = result.severity.upper()
            print(
                f"- [{marker}] {result.case_id}: "
                f"root {result.actual_primary_error} vs {result.expected_primary_error}; "
                f"repair {result.actual_repair_target} vs {result.expected_repair_target}"
            )

    if args.strict and report.calibration_grade != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
