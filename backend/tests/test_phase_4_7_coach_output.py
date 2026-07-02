from __future__ import annotations

import inspect
import json
from argparse import Namespace
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

import app.training.local_trainer as local_trainer_module
from app.main import create_app
from app.training.coach_output import (
    build_coach_output,
    build_evidence_gaps,
    build_next_step_plan,
    build_progression_advice,
    build_status_label,
    build_unscored_dimensions,
    sanitize_score_vector_summary,
)
from app.training.local_trainer import EXIT_SUCCESS, main, run_submit


NEAR_CORRECT_ANSWER = (
    "This is a separable differential equation. Separate variables as dy/y = 2x dx, "
    "then integrate to get ln|y| = x^2 + C, so y = C e^{x^2}."
)
INCOMPLETE_ANSWER = "It is separable. I separate variables and integrate."
WRONG_ANSWER = "Use the characteristic equation and solve for roots."
RAW_SCORER_NAMES = ("RubricScorer", "MathValidatorScorer", "RuleScorer")
TRUSTED_FIELDS = (
    "expected_answer",
    "answer_aliases",
    "rubric",
    "solution_outline",
    "validator_config",
    "trusted_scoring",
    "scorer_results",
    "diagnosis_trace",
    "evidence_sources",
    "raw_rollback_level",
    "raw_forward_level",
)


def test_status_label_maps_false_pass() -> None:
    assert build_status_label("false_pass") == "疑似会做但证据不足"


def test_status_label_maps_pass_and_fail() -> None:
    assert build_status_label("pass") == "稳定通过"
    assert build_status_label("fail") == "未通过"


def test_status_label_maps_unknown() -> None:
    assert build_status_label(None) == "状态不明确"


def test_false_pass_forward_advice_is_not_stable_pass() -> None:
    advice = build_progression_advice({"pass_state": "false_pass", "forward_allowed": True, "rollback_required": False})

    assert "弱推进" in advice
    assert "不能视为稳定掌握" in advice
    assert "稳定通过" not in advice


def test_rollback_advice_blocks_forward() -> None:
    advice = build_progression_advice({"pass_state": "fail", "forward_allowed": False, "rollback_required": True})

    assert "先修复当前节点" in advice
    assert "不建议推进" in advice


def test_sanitize_score_vector_summary_removes_raw_scorer_names() -> None:
    sanitized = sanitize_score_vector_summary(
        {
            "trigger": {
                "score": 86,
                "notes": "Merged by confidence from ['RubricScorer', 'RuleScorer'].",
            },
            "final_answer": {
                "score": 95,
                "notes": "Merged by confidence from ['MathValidatorScorer'].",
            },
        }
    )

    assert_no_raw_scorer_names(sanitized)
    assert "题目评分规则" in json.dumps(sanitized, ensure_ascii=False)
    assert "答案/计算校验" in json.dumps(sanitized, ensure_ascii=False)


def test_build_coach_output_keeps_original_decision_fields() -> None:
    payload = build_coach_output(sample_false_pass_payload())

    assert payload["pass_state"] == "false_pass"
    assert payload["forward_allowed"] is True
    assert payload["rollback_required"] is False
    assert payload["next_action_hint"] == "补证据"


def test_build_coach_output_adds_required_learner_fields() -> None:
    payload = build_coach_output(sample_false_pass_payload())

    for field in (
        "coach_summary",
        "status_label",
        "progression_advice",
        "evidence_gaps",
        "friendly_score_summary",
        "next_step_plan",
        "response_evidence_present",
        "unscored_dimensions",
    ):
        assert field in payload


def test_missing_process_concept_expression_create_evidence_gaps_without_response_evidence() -> None:
    gaps = build_evidence_gaps(sample_false_pass_payload()["score_vector_summary"])
    joined = "\n".join(gaps)

    assert "关键步骤" in joined
    assert "为什么本题适用" in joined
    assert "通解形式" in joined


def test_response_evidence_moves_none_dimensions_to_unscored_dimensions() -> None:
    payload = sample_false_pass_payload(response_evidence=True)
    gaps = build_evidence_gaps(payload["score_vector_summary"], payload["response_evidence_present"])
    unscored = build_unscored_dimensions(payload["score_vector_summary"], payload["response_evidence_present"])
    dimensions = {item["dimension"] for item in unscored}

    assert "请写出关键步骤" not in "\n".join(gaps)
    assert "请说明为什么本题适用" not in "\n".join(gaps)
    assert {"process", "concept", "expression"}.issubset(dimensions)
    reason_by_dimension = {item["dimension"]: item["reason"] for item in unscored}
    assert "不等于" in reason_by_dimension["process"]
    assert "不等于" in reason_by_dimension["concept"]
    assert "当前评分还没有" in reason_by_dimension["expression"]


def test_migration_none_is_not_action_gap() -> None:
    payload = sample_false_pass_payload()
    gaps = build_evidence_gaps(payload["score_vector_summary"])
    unscored = build_unscored_dimensions(payload["score_vector_summary"])

    assert "变式迁移" not in "\n".join(gaps)
    assert "migration" in {item["dimension"] for item in unscored}


def test_low_transformation_creates_transformation_gap() -> None:
    gaps = build_evidence_gaps({"transformation": {"score": 0, "notes": "x"}})

    assert any("条件转化" in gap or "标准形" in gap for gap in gaps)


def test_next_step_plan_maps_transformation_drill() -> None:
    plan = build_next_step_plan({"recommended_actions": [{"action_type": "transformation_drill"}]})

    assert "条件转化" in plan
    assert "标准形" in plan


def test_next_step_plan_with_response_evidence_does_not_ask_to_repeat_steps() -> None:
    plan = build_next_step_plan(
        {
            "recommended_actions": [{"action_type": "need_more_evidence"}],
            "response_evidence_present": {
                "has_response_steps": True,
                "response_step_count": 2,
                "has_self_explanation": True,
            },
        }
    )

    assert "不是简单重复写步骤" in plan
    assert "同节点诊断题" in plan


def test_near_correct_submit_outputs_coach_summary(tmp_path: Path) -> None:
    result = submit_result(tmp_path, NEAR_CORRECT_ANSWER, "near-correct")

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["pass_state"] == "false_pass"
    assert result.payload["status_label"] == "疑似会做但证据不足"
    assert "稳定掌握" in result.payload["coach_summary"]


def test_near_correct_submit_preserves_forward_allowed(tmp_path: Path) -> None:
    result = submit_result(tmp_path, NEAR_CORRECT_ANSWER, "forward-preserved")

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["forward_allowed"] is True
    assert "弱推进" in result.payload["progression_advice"]


def test_submit_with_steps_and_explanation_outputs_response_evidence_present(tmp_path: Path) -> None:
    result = submit_result(
        tmp_path,
        NEAR_CORRECT_ANSWER,
        "response-evidence",
        steps=["state separable", "separate variables", "integrate", "write general solution"],
        explanation="I used separation because x and y factors can be separated.",
    )

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["response_evidence_present"] == {
        "has_response_steps": True,
        "response_step_count": 4,
        "has_self_explanation": True,
    }


def test_steps_and_explanation_do_not_change_core_decisions_or_scores(tmp_path: Path) -> None:
    without_evidence = submit_result(tmp_path, NEAR_CORRECT_ANSWER, "without-evidence")
    with_evidence = submit_result(
        tmp_path,
        NEAR_CORRECT_ANSWER,
        "with-evidence",
        steps=["state separable", "separate variables", "integrate"],
        explanation="I used separation because x and y factors can be separated.",
    )

    assert with_evidence.payload["pass_state"] == without_evidence.payload["pass_state"] == "false_pass"
    assert with_evidence.payload["forward_allowed"] == without_evidence.payload["forward_allowed"] is True
    assert with_evidence.payload["score_vector_summary"] == without_evidence.payload["score_vector_summary"]


def test_steps_and_explanation_stop_misleading_missing_gap_messages(tmp_path: Path) -> None:
    result = submit_result(
        tmp_path,
        NEAR_CORRECT_ANSWER,
        "not-misleading",
        steps=["state separable", "separate variables", "integrate"],
        explanation="I used separation because x and y factors can be separated.",
    )
    joined = "\n".join(result.payload["evidence_gaps"])

    assert "请写出关键步骤" not in joined
    assert "请说明为什么本题适用" not in joined
    assert "请规范写出通解形式" not in joined
    assert "process" in {item["dimension"] for item in result.payload["unscored_dimensions"]}
    assert "concept" in {item["dimension"] for item in result.payload["unscored_dimensions"]}
    assert "expression" in {item["dimension"] for item in result.payload["unscored_dimensions"]}


def test_submit_without_steps_keeps_original_evidence_gap_behavior(tmp_path: Path) -> None:
    result = submit_result(tmp_path, NEAR_CORRECT_ANSWER, "old-gaps")
    joined = "\n".join(result.payload["evidence_gaps"])

    assert "请写出关键步骤" in joined
    assert "请说明为什么本题适用" in joined
    assert "请规范写出通解形式" in joined


def test_session_log_contains_response_evidence_and_unscored_dimensions(tmp_path: Path) -> None:
    result = submit_result(
        tmp_path,
        NEAR_CORRECT_ANSWER,
        "session-evidence",
        steps=["state separable", "separate variables"],
        explanation="I separated x and y terms.",
    )
    row = json.loads((tmp_path / "sessions" / "session-evidence.jsonl").read_text(encoding="utf-8"))

    assert result.exit_code == EXIT_SUCCESS
    assert row["response_evidence_present"]["has_response_steps"] is True
    assert row["response_evidence_present"]["response_step_count"] == 2
    assert row["response_evidence_present"]["has_self_explanation"] is True
    assert {"process", "concept", "expression", "migration"}.issubset(
        {item["dimension"] for item in row["unscored_dimensions"]}
    )


def test_incomplete_answer_outputs_transformation_next_step(tmp_path: Path) -> None:
    result = submit_result(tmp_path, INCOMPLETE_ANSWER, "incomplete")

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["pass_state"] == "fail"
    assert "条件转化" in result.payload["next_step_plan"]


def test_wrong_answer_outputs_trigger_next_step(tmp_path: Path) -> None:
    result = submit_result(tmp_path, WRONG_ANSWER, "wrong")

    assert result.exit_code == EXIT_SUCCESS
    assert "题眼识别" in result.payload["next_step_plan"]


def test_stdout_contains_no_raw_scorer_names(tmp_path: Path, capsys: Any) -> None:
    exit_code = main(
        [
            "submit",
            "ode-sep-001",
            "--answer",
            NEAR_CORRECT_ANSWER,
            "--steps",
            "state separable",
            "--explanation",
            "I separated variables.",
            "--session-id",
            "stdout-clean",
            "--session-root",
            str(tmp_path / "sessions"),
        ]
    )
    stdout = capsys.readouterr().out

    assert exit_code == EXIT_SUCCESS
    json.loads(stdout)
    assert_no_raw_scorer_names(stdout)


def test_session_log_contains_friendly_fields_and_no_raw_scorer_names(tmp_path: Path) -> None:
    result = submit_result(tmp_path, NEAR_CORRECT_ANSWER, "session-clean")
    row = json.loads((tmp_path / "sessions" / "session-clean.jsonl").read_text(encoding="utf-8"))

    assert result.exit_code == EXIT_SUCCESS
    assert row["coach_summary"]
    assert row["friendly_score_summary"]
    assert row["next_step_plan"]
    assert_no_raw_scorer_names(row)


def test_friendly_score_summary_contains_no_raw_scorer_names(tmp_path: Path) -> None:
    result = submit_result(tmp_path, NEAR_CORRECT_ANSWER, "friendly-clean")

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["friendly_score_summary"]["trigger"]["label"] == "题眼识别"
    assert_no_raw_scorer_names(result.payload["friendly_score_summary"])


def test_friendly_score_summary_marks_unscored_not_missing_when_response_evidence_exists(tmp_path: Path) -> None:
    result = submit_result(
        tmp_path,
        NEAR_CORRECT_ANSWER,
        "friendly-unscored",
        steps=["state separable"],
        explanation="I explained the trigger.",
    )

    assert result.payload["friendly_score_summary"]["process"]["status"] == "当前未评分"
    assert "不等于你没有写过程" in result.payload["friendly_score_summary"]["process"]["comment"]


def test_score_vector_summary_notes_are_learner_friendly(tmp_path: Path) -> None:
    result = submit_result(tmp_path, NEAR_CORRECT_ANSWER, "score-summary-clean")

    assert result.exit_code == EXIT_SUCCESS
    assert "题目评分规则" in json.dumps(result.payload["score_vector_summary"], ensure_ascii=False)
    assert_no_raw_scorer_names(result.payload["score_vector_summary"])


def test_submit_output_still_has_no_trusted_fields(tmp_path: Path) -> None:
    result = submit_result(tmp_path, NEAR_CORRECT_ANSWER, "trusted-clean")

    assert result.exit_code == EXIT_SUCCESS
    assert_no_trusted_fields(result.payload)


def test_session_log_still_has_no_trusted_fields(tmp_path: Path) -> None:
    result = submit_result(tmp_path, NEAR_CORRECT_ANSWER, "trusted-log-clean")
    row = json.loads((tmp_path / "sessions" / "trusted-log-clean.jsonl").read_text(encoding="utf-8"))

    assert result.exit_code == EXIT_SUCCESS
    assert_no_trusted_fields(row)


def test_local_trainer_still_does_not_import_core_engines() -> None:
    source = inspect.getsource(local_trainer_module)

    for forbidden in ("CompositeScoringEngine", "DiagnosisEngine", "RollbackEngine", "ForwardEngine", "LearningOrchestrator"):
        assert forbidden not in source


def test_app_profile_regression_still_passes() -> None:
    learner = TestClient(create_app("learner"))
    internal = TestClient(create_app("internal"))

    assert learner.get("/api/learner/v1/health").status_code == 200
    assert learner.get("/api/v1/health").status_code == 404
    assert internal.get("/api/v1/health").status_code == 200
    assert internal.get("/api/learner/v1/health").status_code == 404


def sample_false_pass_payload(response_evidence: bool = False) -> dict[str, Any]:
    return {
        "question_id": "ode-sep-001",
        "pass_state": "false_pass",
        "score_vector_summary": {
            "concept": None,
            "trigger": {"score": 86.25, "notes": "Merged by confidence from ['RubricScorer', 'RuleScorer']."},
            "method": {"score": 86.25, "notes": "Merged by confidence from ['RubricScorer', 'RuleScorer']."},
            "transformation": {"score": 100.0, "notes": "Merged by confidence from ['RubricScorer']."},
            "process": None,
            "calculation": {"score": 92.28, "notes": "Merged by confidence from ['RubricScorer', 'MathValidatorScorer']."},
            "final_answer": {"score": 95.0, "notes": "Merged by confidence from ['MathValidatorScorer']."},
            "expression": None,
            "migration": None,
        },
        "learner_explanation": "证据不足。",
        "recommended_actions": [{"action_type": "need_more_evidence"}],
        "rollback_required": False,
        "rollback_nodes": [],
        "forward_allowed": True,
        "forward_nodes": ["ode_homogeneous_first_order"],
        "next_action_hint": "补证据",
        "response_evidence_present": {
            "has_response_steps": response_evidence,
            "response_step_count": 2 if response_evidence else 0,
            "has_self_explanation": response_evidence,
        },
    }


def submit_result(
    tmp_path: Path,
    answer: str,
    session_id: str,
    *,
    steps: list[str] | None = None,
    explanation: str | None = None,
) -> Any:
    return run_submit(
        Namespace(
            question_id="ode-sep-001",
            answer=answer,
            steps=steps,
            explanation=explanation,
            session_id=session_id,
            session_root=str(tmp_path / "sessions"),
            debug=False,
        )
    )


def assert_no_raw_scorer_names(value: Any) -> None:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    for raw_name in RAW_SCORER_NAMES:
        assert raw_name not in text


def assert_no_trusted_fields(value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False)
    for field in TRUSTED_FIELDS:
        assert field not in text
