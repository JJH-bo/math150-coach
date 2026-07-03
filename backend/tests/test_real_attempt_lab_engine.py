from __future__ import annotations

from app.challenge.real_attempt_lab import (
    RealAttemptCase,
    build_case_result,
    load_real_attempt_lab_file,
    summarize_real_attempt_results,
    validate_real_attempt_lab_spec,
)
from app.challenge.repository import ChallengeRepository

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = REPO_ROOT / "backend" / "challenge_data" / "ode_network_mvp" / "real_attempt_lab_seed.yaml"


def _case() -> RealAttemptCase:
    return RealAttemptCase(
        case_id="case-1",
        node_id="ode_separable.transformation",
        prompt_intent="test",
        learner_answer="answer",
        learner_self_explanation="explanation",
        expected_primary_error="transformation_error",
        expected_repair_target="ode_separable.transformation",
        human_coaching_note="note",
    )


def test_real_attempt_lab_spec_validates_against_current_ode_graph() -> None:
    spec = load_real_attempt_lab_file(SEED_PATH)
    repository = ChallengeRepository()
    graph = repository.load_graph(spec.chapter_id)
    questions = repository.load_question_bank(spec.chapter_id)

    validate_real_attempt_lab_spec(spec, graph, questions)


def test_real_attempt_case_result_severity_levels() -> None:
    case = _case()
    exact = build_case_result(
        case=case,
        question_id="q1",
        actual_primary_error="transformation_error",
        actual_repair_target="ode_separable.transformation",
        pass_state="fail",
        learner_explanation="engine note",
    )
    warning = build_case_result(
        case=case,
        question_id="q1",
        actual_primary_error="method_error",
        actual_repair_target="ode_separable.transformation",
        pass_state="fail",
        learner_explanation="engine note",
    )
    miss = build_case_result(
        case=case,
        question_id="q1",
        actual_primary_error="method_error",
        actual_repair_target="ode_separable.method",
        pass_state="fail",
        learner_explanation="engine note",
    )

    assert exact.severity == "pass"
    assert exact.exact_match is True
    assert warning.severity == "warn"
    assert warning.mismatch_reasons == ["root_cause_mismatch"]
    assert miss.severity == "fail"
    assert miss.mismatch_reasons == ["root_cause_mismatch", "repair_target_mismatch"]


def test_real_attempt_lab_summary_marks_repair_miss_as_lab_failure() -> None:
    case = _case()
    exact = build_case_result(
        case=case,
        question_id="q1",
        actual_primary_error="transformation_error",
        actual_repair_target="ode_separable.transformation",
        pass_state="fail",
        learner_explanation=None,
    )
    miss = build_case_result(
        case=case,
        question_id="q1",
        actual_primary_error="transformation_error",
        actual_repair_target="ode_separable.method",
        pass_state="fail",
        learner_explanation=None,
    )

    report = summarize_real_attempt_results("lab", "ode_network_mvp", [exact, miss])

    assert report.case_count == 2
    assert report.root_cause_matches == 2
    assert report.repair_target_matches == 1
    assert report.exact_matches == 1
    assert report.fail_count == 1
    assert report.calibration_grade == "fail"
