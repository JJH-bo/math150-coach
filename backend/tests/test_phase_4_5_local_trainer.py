from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.training.local_trainer import (
    EXIT_LEARNER_API_ERROR,
    EXIT_SESSION_LOG_ERROR,
    EXIT_SUCCESS,
    LearnerLocalClient,
    main,
    run_list,
    run_show,
    run_submit,
)
from app.training.session_log import (
    SessionLogError,
    append_attempt,
    ensure_no_trusted_fields,
    resolve_session_root,
    validate_session_id,
)


GOOD_ANSWER = "This is separable; separate variables; dy/y = 2x dx; integrate; ln|y|=x^2+C."
TRUSTED_FIELDS = {
    "expected_answer",
    "answer_aliases",
    "rubric",
    "solution_outline",
    "validator_config",
    "trusted_scoring",
    "answer_key",
    "scorer_results",
    "diagnosis_trace",
    "debug_trace",
    "evidence_sources",
    "raw_rollback_level",
    "raw_forward_level",
    "score_overrides",
    "evidence_overrides",
    "manual_override",
    "scenario",
    "include_debug",
    "source_metadata",
    "validation_report",
    "review_checklist",
}


def test_local_client_lists_learner_visible_questions_only() -> None:
    questions = LearnerLocalClient().list_questions()

    assert any(item["question_id"] == "ode-sep-001" for item in questions)
    assert "ode-sep-draft-001" not in {item["question_id"] for item in questions}
    assert "ode-sep-internal-001" not in {item["question_id"] for item in questions}


def test_list_payload_uses_public_summary_fields_only() -> None:
    result = run_list(Namespace())

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["count"] >= 1
    assert set(result.payload["questions"][0]) == {
        "answer_format",
        "difficulty",
        "node_id",
        "question_id",
        "response_step_mode",
        "title",
    }
    assert_no_trusted_fields(result.payload)


def test_show_question_returns_public_question_only() -> None:
    result = run_show(Namespace(question_id="ode-sep-001"))

    assert result.exit_code == EXIT_SUCCESS
    question = result.payload["question"]
    assert question["question_id"] == "ode-sep-001"
    assert "prompt_markdown" in question
    assert "hints_public" in question
    assert_no_trusted_fields(result.payload)


def test_show_unknown_question_returns_json_error_payload() -> None:
    result = run_show(Namespace(question_id="missing-001"))

    assert result.exit_code == EXIT_LEARNER_API_ERROR
    assert result.payload["error_code"] == "question_not_found"
    assert result.payload["field_path"] == "question_id"


def test_submit_uses_learner_safe_api_shape(tmp_path: Path) -> None:
    result = submit_result(tmp_path)

    assert result.exit_code == EXIT_SUCCESS
    payload = result.payload
    assert payload["question_id"] == "ode-sep-001"
    assert payload["session_log_written"] is True
    assert payload["session_id"] == "safe-session"
    assert set(payload) == {
        "coach_summary",
        "evidence_gaps",
        "forward_allowed",
        "forward_nodes",
        "friendly_score_summary",
        "learner_explanation",
        "next_action_hint",
        "next_step_plan",
        "pass_state",
        "progression_advice",
        "question_id",
        "recommended_actions",
        "response_evidence_present",
        "rollback_nodes",
        "rollback_required",
        "score_vector_summary",
        "session_id",
        "session_log_written",
        "status_label",
        "unscored_dimensions",
    }
    assert_no_trusted_fields(payload)


def test_submit_writes_local_jsonl_session_log(tmp_path: Path) -> None:
    result = submit_result(tmp_path)
    log_path = tmp_path / "sessions" / "safe-session.jsonl"

    assert result.exit_code == EXIT_SUCCESS
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["question_id"] == "ode-sep-001"
    assert rows[0]["node_id"] == "ode_separable"
    assert rows[0]["user_answer"] == GOOD_ANSWER
    assert_no_trusted_fields(rows[0])


def test_submit_log_records_steps_and_explanation(tmp_path: Path) -> None:
    result = run_submit(
        Namespace(
            question_id="ode-sep-001",
            answer=GOOD_ANSWER,
            steps=["separate variables", "integrate"],
            explanation="I separated x and y terms.",
            session_id="with-steps",
            session_root=str(tmp_path / "sessions"),
            debug=False,
        )
    )

    assert result.exit_code == EXIT_SUCCESS
    row = json.loads((tmp_path / "sessions" / "with-steps.jsonl").read_text(encoding="utf-8"))
    assert row["response_steps"] == ["separate variables", "integrate"]
    assert row["self_explanation"] == "I separated x and y terms."


def test_submit_unknown_question_does_not_write_session_log(tmp_path: Path) -> None:
    result = run_submit(
        Namespace(
            question_id="missing-001",
            answer=GOOD_ANSWER,
            steps=None,
            explanation=None,
            session_id="missing",
            session_root=str(tmp_path / "sessions"),
            debug=False,
        )
    )

    assert result.exit_code == EXIT_LEARNER_API_ERROR
    assert not (tmp_path / "sessions").exists()


def test_session_id_rejects_unsafe_characters() -> None:
    with pytest.raises(SessionLogError):
        validate_session_id("../outside")


def test_submit_rejects_unsafe_session_id(tmp_path: Path) -> None:
    result = run_submit(
        Namespace(
            question_id="ode-sep-001",
            answer=GOOD_ANSWER,
            steps=None,
            explanation=None,
            session_id="../outside",
            session_root=str(tmp_path / "sessions"),
            debug=False,
        )
    )

    assert result.exit_code == EXIT_SESSION_LOG_ERROR
    assert result.payload["error_code"] == "session_log_error"


def test_session_root_rejects_parent_escape() -> None:
    with pytest.raises(SessionLogError):
        resolve_session_root("../outside")


def test_session_root_rejects_formal_catalog_path() -> None:
    with pytest.raises(SessionLogError):
        resolve_session_root(formal_catalog_root())


def test_session_root_rejects_docs_path() -> None:
    with pytest.raises(SessionLogError):
        resolve_session_root(repo_root() / "docs")


def test_append_attempt_rejects_trusted_fields(tmp_path: Path) -> None:
    with pytest.raises(SessionLogError):
        append_attempt({"question_id": "ode-sep-001", "expected_answer": "secret"}, "safe", tmp_path / "sessions")


def test_ensure_no_trusted_fields_scans_nested_values() -> None:
    with pytest.raises(SessionLogError):
        ensure_no_trusted_fields({"outer": [{"rubric": {"items": []}}]})


def test_main_list_stdout_is_json(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["list"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == EXIT_SUCCESS
    assert payload["count"] >= 1
    assert_no_trusted_fields(payload)


def test_main_show_stdout_is_json(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["show", "ode-sep-001"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == EXIT_SUCCESS
    assert payload["question"]["question_id"] == "ode-sep-001"
    assert_no_trusted_fields(payload)


def test_main_submit_stdout_is_json_and_writes_log(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "submit",
            "ode-sep-001",
            "--answer",
            GOOD_ANSWER,
            "--session-id",
            "stdout-json",
            "--session-root",
            str(tmp_path / "sessions"),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == EXIT_SUCCESS
    assert payload["session_log_written"] is True
    assert payload["session_id"] == "stdout-json"
    assert (tmp_path / "sessions" / "stdout-json.jsonl").exists()
    assert_no_trusted_fields(payload)


def test_main_error_stdout_is_json(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["show", "missing-001"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == EXIT_LEARNER_API_ERROR
    assert payload["error_code"] == "question_not_found"
    assert "'error_code':" not in capsys.readouterr().err


def test_main_argument_error_still_outputs_json(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["submit", "ode-sep-001"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["error_code"] == "cli_argument_error"


def test_debug_output_contains_only_local_trainer_debug(tmp_path: Path) -> None:
    result = run_submit(
        Namespace(
            question_id="ode-sep-001",
            answer=GOOD_ANSWER,
            steps=None,
            explanation=None,
            session_id="debug-safe",
            session_root=str(tmp_path / "sessions"),
            debug=True,
        )
    )

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["debug"]["local_trainer"] == "learner_api_only"
    assert "diagnosis_trace" not in json.dumps(result.payload)


def test_formal_catalog_manifest_unchanged_after_submit(tmp_path: Path) -> None:
    before = formal_manifest_text()

    result = submit_result(tmp_path)

    assert result.exit_code == EXIT_SUCCESS
    assert formal_manifest_text() == before


def test_local_trainer_does_not_change_api_profile_gating() -> None:
    learner = TestClient(create_app("learner"))
    internal = TestClient(create_app("internal"))

    assert learner.get("/api/learner/v1/health").status_code == 200
    assert learner.get("/api/v1/health").status_code == 404
    assert internal.get("/api/v1/health").status_code == 200
    assert internal.get("/api/learner/v1/health").status_code == 404


def test_learner_api_contract_still_rejects_trusted_attempt_fields() -> None:
    response = TestClient(create_app("learner")).post(
        "/api/learner/v1/attempts/submit",
        json={
            "question_id": "ode-sep-001",
            "user_answer": GOOD_ANSWER,
            "expected_answer": "secret",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "forbidden_learner_api_field"


def test_trainer_never_returns_python_repr(capsys: pytest.CaptureFixture[str]) -> None:
    main(["list"])
    stdout = capsys.readouterr().out

    assert json.loads(stdout)["count"] >= 1
    assert "'questions':" not in stdout


def submit_result(tmp_path: Path) -> Any:
    return run_submit(
        Namespace(
            question_id="ode-sep-001",
            answer=GOOD_ANSWER,
            steps=None,
            explanation=None,
            session_id="safe-session",
            session_root=str(tmp_path / "sessions"),
            debug=False,
        )
    )


def assert_no_trusted_fields(value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False)
    for field in TRUSTED_FIELDS:
        assert field not in text


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def formal_catalog_root() -> Path:
    return repo_root() / "backend" / "catalog_data"


def formal_manifest_text() -> str:
    return (formal_catalog_root() / "manifest.yaml").read_text(encoding="utf-8")
