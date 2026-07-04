from __future__ import annotations

from fastapi.testclient import TestClient

from app.challenge.chapter_feedback_optimizer import (
    build_chapter_feedback_optimization_dry_run,
    build_chapter_feedback_optimization_from_sessions_dry_run,
)
from app.challenge.chapter_intelligent_importer import build_intelligent_chapter_draft
from app.challenge.models import ChallengeQuestionBank
from app.main import create_app
from app.training.session_log import append_attempt


def test_feedback_optimizer_identifies_revision_signals_from_training_attempts() -> None:
    candidate, question_package = _candidate_and_question_package()
    questions = _questions_by_kind(question_package)
    calculation = questions["calculation_execution"]
    compare = questions["confusion_compare"]
    transfer = questions["transfer_variant"]
    boss = questions["boss_acceptance"]

    payload = build_chapter_feedback_optimization_dry_run(
        candidate,
        question_package=question_package,
        attempt_records=[
            *_attempts(
                calculation,
                [
                    ("false_pass", "calculation_error", ["process", "calculation"]),
                    ("false_pass", "expression_weakness", ["expression"]),
                    ("fail", "transformation_error", ["transformation"]),
                    ("false_pass", "calculation_error", ["calculation"]),
                ],
            ),
            *_attempts(
                compare,
                [
                    ("false_pass", "knowledge_confusion", ["concept"]),
                    ("fail", "knowledge_confusion", ["trigger"]),
                    ("false_pass", "knowledge_confusion", ["method"]),
                ],
            ),
            *_attempts(
                transfer,
                [
                    ("fail", "migration_failure", ["migration"]),
                    ("fail", "migration_failure", ["method"]),
                    ("false_pass", "migration_failure", ["migration"]),
                ],
            ),
            *_attempts(
                boss,
                [
                    ("fail", "synthesis_failure", ["process"]),
                    ("fail", "calculation_error", ["calculation"]),
                    ("false_pass", "expression_weakness", ["expression"]),
                ],
            ),
        ],
        analyst="codex-feedback-test",
    )

    assert payload["mode"] == "chapter_feedback_optimization_dry_run"
    assert payload["dry_run_only"] is True
    assert payload["formal_publish_allowed"] is False
    assert payload["feedback_record"]["status"] == "needs_revision"
    assert payload["quality_gate"]["grade"] == "fail"

    signal_codes = {signal["code"] for signal in payload["revision_signals"]}
    assert {
        "false_pass_excess",
        "diagnosis_instability",
        "rubric_evidence_insufficient",
        "compare_guard_not_blocking_confusion",
        "migration_variant_weak",
        "boss_feedback_gap",
        "repair_path_ineffective",
    } <= signal_codes

    plan = payload["regeneration_plan"]
    assert calculation["id"] in plan["question_ids"]
    assert compare["id"] in plan["question_ids"]
    assert transfer["id"] in plan["question_ids"]
    assert boss["id"] in plan["question_ids"]
    assert calculation["node_id"] in plan["node_ids"]
    assert "questions.yaml" in plan["assets"]
    assert "rubric" in plan["assets"]
    assert "error_repair_map" in plan["assets"]
    assert "candidate_quality_report" in plan["assets"]
    assert plan["can_start_correction_dry_run"] is True
    assert payload["recommended_correction_operations"]


def test_feedback_optimizer_api_returns_revision_preview() -> None:
    candidate, question_package = _candidate_and_question_package()
    calculation = _questions_by_kind(question_package)["calculation_execution"]
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-package/feedback-optimization-dry-run",
        json={
            "candidate": candidate,
            "question_package": question_package,
            "attempt_records": _attempts(
                calculation,
                [
                    ("false_pass", "calculation_error", ["process"]),
                    ("false_pass", "calculation_error", ["calculation"]),
                    ("fail", "expression_weakness", ["expression"]),
                ],
            ),
            "analyst": "api-feedback-test",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "chapter_feedback_optimization_dry_run"
    assert payload["dry_run_only"] is True
    assert payload["formal_publish_allowed"] is False
    assert payload["feedback_record"]["status"] == "needs_revision"
    assert {signal["code"] for signal in payload["revision_signals"]} >= {
        "false_pass_excess",
        "rubric_evidence_insufficient",
    }


def test_feedback_optimizer_reads_real_session_logs_for_chapter_feedback(tmp_path) -> None:
    candidate, question_package = _candidate_and_question_package()
    calculation = _questions_by_kind(question_package)["calculation_execution"]
    session_id = "real-feedback-session"
    for attempt in _attempts(
        calculation,
        [
            ("false_pass", "calculation_error", ["process"]),
            ("false_pass", "calculation_error", ["calculation"]),
            ("fail", "expression_weakness", ["expression"]),
        ],
    ):
        append_attempt(
            {
                **attempt,
                "session_id": session_id,
                "challenge_chapter_id": candidate["chapter_id"],
                "challenge_task_type": attempt["task_type"],
            },
            session_id=session_id,
            session_root=tmp_path,
        )
    append_attempt(
        {
            **_attempts(calculation, [("pass", "calculation_error", [])])[0],
            "session_id": "other-session",
            "challenge_chapter_id": "other_chapter",
        },
        session_id="other-session",
        session_root=tmp_path,
    )

    payload = build_chapter_feedback_optimization_from_sessions_dry_run(
        candidate,
        question_package=question_package,
        session_root=tmp_path,
        session_ids=[session_id],
        analyst="session-log-test",
    )

    assert payload["mode"] == "chapter_feedback_optimization_dry_run"
    assert payload["feedback_source"]["source_type"] == "session_logs"
    assert payload["feedback_source"]["session_ids"] == [session_id]
    assert payload["feedback_source"]["loaded_attempt_count"] == 3
    assert payload["feedback_record"]["attempt_count"] == 3
    assert payload["feedback_record"]["status"] == "needs_revision"
    assert {signal["code"] for signal in payload["revision_signals"]} >= {
        "false_pass_excess",
        "rubric_evidence_insufficient",
    }


def test_feedback_optimizer_session_api_uses_configured_session_root(tmp_path, monkeypatch) -> None:
    candidate, question_package = _candidate_and_question_package()
    calculation = _questions_by_kind(question_package)["calculation_execution"]
    session_id = "api-real-feedback"
    for attempt in _attempts(
        calculation,
        [
            ("false_pass", "calculation_error", ["process"]),
            ("false_pass", "calculation_error", ["calculation"]),
            ("fail", "expression_weakness", ["expression"]),
        ],
    ):
        append_attempt(
            {
                **attempt,
                "session_id": session_id,
                "challenge_chapter_id": candidate["chapter_id"],
                "challenge_task_type": attempt["task_type"],
            },
            session_id=session_id,
            session_root=tmp_path,
        )
    monkeypatch.setenv("CHALLENGE_SESSION_ROOT", str(tmp_path))
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-package/feedback-optimization-from-sessions-dry-run",
        json={
            "candidate": candidate,
            "question_package": question_package,
            "session_ids": [session_id],
            "analyst": "api-session-feedback",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["feedback_source"]["source_type"] == "session_logs"
    assert payload["feedback_source"]["loaded_attempt_count"] == 3
    assert payload["feedback_record"]["status"] == "needs_revision"


def _candidate_and_question_package() -> tuple[dict, dict]:
    generated = build_intelligent_chapter_draft(
        source_text=None,
        chapter_id="feedback_pkg",
        title="Feedback Package",
        materials=[
            {
                "material_type": "markdown",
                "filename": "feedback.md",
                "text": "\n".join(
                    [
                        "# Feedback optimization material",
                        "core concepts: partial derivative;",
                        "formula: dz=f_x dx+f_y dy;",
                        "theorem: differentiability implies continuity;",
                        "typical problems: composite function differential;",
                        "trigger: z=f(u,v), u=x+y, v=xy;",
                        "method: chain rule;",
                        "transformation: draw dependency chain before differentiating;",
                        "confusion: partial derivative existence vs differentiability;",
                        "common errors: final answer only, false pass;",
                        "prerequisite: derivative rules;",
                        "downstream: tangent plane;",
                        "math1 value: high;",
                    ]
                ),
            }
        ],
        build_candidate=True,
    )
    candidate = generated["candidate_preview"]["candidate"]
    question_package = generated["candidate_preview"].get("question_package") or generated["training_question_package"]
    if not isinstance(question_package, dict) or "question_bank" not in question_package:
        from app.challenge.chapter_training_question_builder import build_chapter_training_question_package

        question_package = build_chapter_training_question_package(candidate)
    assert question_package["quality_report"]["grade"] == "pass"
    return candidate, question_package


def _questions_by_kind(question_package: dict) -> dict[str, dict]:
    question_bank = ChallengeQuestionBank.model_validate(question_package["question_bank"])
    return {
        str(question.validator_config["question_kind"]): question.model_dump(mode="json")
        for question in question_bank.questions
    }


def _attempts(question: dict, outcomes: list[tuple[str, str, list[str]]]) -> list[dict]:
    return [
        {
            "attempt_id": f"{question['id']}.{index}",
            "question_id": question["id"],
            "node_id": question["node_id"],
            "owner_id": question["owner_id"],
            "task_type": question["task_type"],
            "question_kind": question["validator_config"]["question_kind"],
            "pass_state": pass_state,
            "root_cause": root_cause,
            "repair_target_node_id": question["validator_config"]["repair_target_node_id"],
            "weak_dimensions": weak_dimensions,
            "evidence_gaps": weak_dimensions,
        }
        for index, (pass_state, root_cause, weak_dimensions) in enumerate(outcomes, start=1)
    ]
