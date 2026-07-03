from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.challenge.engine import ChallengeEngine  # noqa: E402
from app.challenge.models import ChallengeGraph, ChallengeQuestion, ChallengeQuestionBank, ChallengeTaskType  # noqa: E402
from app.challenge.repository import ChallengeRepository  # noqa: E402
from app.core.schemas import Attempt  # noqa: E402

DEFAULT_CASE_PATH = REPO_ROOT / "backend" / "challenge_data" / "ode_network_mvp" / "real_attempt_lab_seed.yaml"


@dataclass(frozen=True)
class RealAttemptCase:
    case_id: str
    node_id: str
    prompt_intent: str
    learner_answer: str
    learner_self_explanation: str
    expected_primary_error: str
    expected_repair_target: str
    human_coaching_note: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "RealAttemptCase":
        required = {
            "case_id",
            "node_id",
            "prompt_intent",
            "learner_answer",
            "learner_self_explanation",
            "expected_primary_error",
            "expected_repair_target",
            "human_coaching_note",
        }
        missing = sorted(required - set(data))
        if missing:
            raise ValueError(f"real attempt case is missing fields {missing}: {data!r}")
        return cls(**{field: str(data[field]) for field in required})


def load_lab_cases(path: Path) -> tuple[str, list[RealAttemptCase]]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"real attempt lab root must be a mapping: {path}")
    chapter_id = str(data.get("chapter_id") or "")
    if not chapter_id:
        raise ValueError("real attempt lab requires chapter_id")
    raw_cases = data.get("cases") or []
    if not isinstance(raw_cases, list):
        raise ValueError("real attempt lab cases must be a list")
    cases = [RealAttemptCase.from_mapping(case) for case in raw_cases]
    if not cases:
        raise ValueError("real attempt lab requires at least one case")
    return chapter_id, cases


def select_question_for_case(questions: ChallengeQuestionBank, case: RealAttemptCase) -> ChallengeQuestion:
    candidates = [
        question
        for question in questions.questions
        if question.task_type == ChallengeTaskType.MICRO_NODE and question.owner_id == case.node_id
    ]
    if not candidates:
        candidates = [question for question in questions.questions if question.node_id == case.node_id]
    if not candidates:
        raise ValueError(f"no challenge question found for real attempt case node_id={case.node_id!r}")
    return candidates[0]


def micro_node_exists(graph: ChallengeGraph, node_id: str) -> bool:
    return any(micro.id == node_id for micro in graph.micro_nodes)


def evaluate_case(engine: ChallengeEngine, graph: ChallengeGraph, questions: ChallengeQuestionBank, case: RealAttemptCase) -> dict[str, Any]:
    if not micro_node_exists(graph, case.node_id):
        raise ValueError(f"case references unknown micro node: {case.node_id}")
    if not micro_node_exists(graph, case.expected_repair_target):
        raise ValueError(f"case references unknown expected repair target: {case.expected_repair_target}")

    question_spec = select_question_for_case(questions, case)
    domain_question = engine._to_domain_question(graph, question_spec)
    micro = engine._micro(graph, case.node_id)
    node = engine._micro_node_adapter(graph, micro)
    attempt = Attempt(
        id=f"real-attempt-lab::{case.case_id}",
        question_id=domain_question.id,
        user_answer=case.learner_answer,
        response_steps=[case.learner_answer],
        self_explanation=case.learner_self_explanation,
    )
    evaluation = engine.processor(domain_question, attempt, node)

    actual_root = evaluation.root_cause.value if evaluation.root_cause else None
    actual_repair = evaluation.repair_target_node_id
    return {
        "case_id": case.case_id,
        "node_id": case.node_id,
        "question_id": domain_question.id,
        "expected_primary_error": case.expected_primary_error,
        "actual_primary_error": actual_root,
        "primary_error_match": actual_root == case.expected_primary_error,
        "expected_repair_target": case.expected_repair_target,
        "actual_repair_target": actual_repair,
        "repair_target_match": actual_repair == case.expected_repair_target,
        "pass_state": evaluation.pass_state.value,
        "human_coaching_note": case.human_coaching_note,
    }


def run_lab(case_path: Path) -> dict[str, Any]:
    chapter_id, cases = load_lab_cases(case_path)
    repository = ChallengeRepository()
    graph = repository.load_graph(chapter_id)
    questions = repository.load_question_bank(chapter_id)
    engine = ChallengeEngine(repository=repository)

    results = [evaluate_case(engine, graph, questions, case) for case in cases]
    root_matches = sum(1 for result in results if result["primary_error_match"])
    repair_matches = sum(1 for result in results if result["repair_target_match"])
    full_matches = sum(
        1 for result in results if result["primary_error_match"] and result["repair_target_match"]
    )
    return {
        "lab_id": case_path.stem,
        "chapter_id": chapter_id,
        "case_count": len(results),
        "root_cause_matches": root_matches,
        "repair_target_matches": repair_matches,
        "full_matches": full_matches,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Math150 real-attempt calibration lab.")
    parser.add_argument("--case-path", type=Path, default=DEFAULT_CASE_PATH)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="return non-zero when any case mismatches")
    args = parser.parse_args()

    report = run_lab(args.case_path)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Real Attempt Lab: {report['chapter_id']} ({report['case_count']} cases)")
        print(
            "Matches: "
            f"root={report['root_cause_matches']}/{report['case_count']}, "
            f"repair={report['repair_target_matches']}/{report['case_count']}, "
            f"full={report['full_matches']}/{report['case_count']}"
        )
        for result in report["results"]:
            marker = "PASS" if result["primary_error_match"] and result["repair_target_match"] else "MISMATCH"
            print(
                f"- [{marker}] {result['case_id']}: "
                f"root {result['actual_primary_error']} vs {result['expected_primary_error']}; "
                f"repair {result['actual_repair_target']} vs {result['expected_repair_target']}"
            )

    if args.strict and report["full_matches"] != report["case_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
