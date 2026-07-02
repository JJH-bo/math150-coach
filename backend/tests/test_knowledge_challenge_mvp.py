from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.challenge.engine import ChallengeEngine, DEFAULT_DIMENSIONS_BY_MICRO_TYPE
from app.challenge.models import ChallengeEvaluation, ChallengeStatus, MicroNodeType
from app.challenge.repository import ChallengeRepository
from app.core.enums import ErrorType, PassState, ScoreDimension
from app.main import create_app
from app.training.local_trainer import EXIT_SUCCESS, LearnerLocalClient, main
from app.training.session_log import ensure_no_trusted_fields


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
}


def test_challenge_graph_uses_knowledge_node_as_macro_node_not_macro_challenge() -> None:
    graph = ChallengeRepository().load_graph("ode_mvp")

    assert graph.macro_nodes[0].id == "ode_separable"
    assert graph.macro_nodes[0].knowledge_node_id == "ode_separable"
    assert graph.macro_challenges[0].id == "ode_separable.macro_challenge"
    assert graph.macro_challenges[0].macro_node_id == "ode_separable"
    assert "ode_separable.macro_challenge" not in graph.contains
    assert set(graph.contains["ode_separable"]) == {
        "ode_separable.concept",
        "ode_separable.trigger",
        "ode_separable.method",
        "ode_separable.transformation",
        "ode_separable.calculation",
        "ode_separable.expression",
    }


def test_default_micro_dimensions_are_six_type_mapping() -> None:
    assert DEFAULT_DIMENSIONS_BY_MICRO_TYPE[MicroNodeType.CONCEPT] == [ScoreDimension.CONCEPT]
    assert DEFAULT_DIMENSIONS_BY_MICRO_TYPE[MicroNodeType.TRIGGER] == [ScoreDimension.TRIGGER]
    assert DEFAULT_DIMENSIONS_BY_MICRO_TYPE[MicroNodeType.METHOD] == [ScoreDimension.METHOD]
    assert DEFAULT_DIMENSIONS_BY_MICRO_TYPE[MicroNodeType.TRANSFORMATION] == [ScoreDimension.TRANSFORMATION]
    assert DEFAULT_DIMENSIONS_BY_MICRO_TYPE[MicroNodeType.CALCULATION] == [ScoreDimension.CALCULATION]
    assert DEFAULT_DIMENSIONS_BY_MICRO_TYPE[MicroNodeType.EXPRESSION] == [
        ScoreDimension.EXPRESSION,
        ScoreDimension.FINAL_ANSWER,
    ]


def test_target_dimensions_can_supplement_or_override_defaults() -> None:
    engine = ChallengeEngine()
    graph = ChallengeRepository().load_graph("ode_mvp")
    questions = ChallengeRepository().load_question_bank("ode_mvp")
    concept_question = questions.questions[0]

    supplemented = concept_question.model_copy(update={"target_dimensions": [ScoreDimension.METHOD]})
    overridden = concept_question.model_copy(
        update={"target_dimensions": [ScoreDimension.METHOD], "target_dimension_mode": "override"}
    )

    assert engine._to_domain_question(graph, supplemented).tested_dimensions == [
        ScoreDimension.CONCEPT,
        ScoreDimension.METHOD,
    ]
    assert engine._to_domain_question(graph, overridden).tested_dimensions == [ScoreDimension.METHOD]


def test_challenge_start_initializes_micro_nodes_before_macro(tmp_path: Path) -> None:
    engine = ChallengeEngine(processor=QueueProcessor([]))
    payload = engine.start("ode_mvp", session_id="start-state", session_root=tmp_path)

    challenge = payload["challenge"]
    assert challenge["current_task"]["task_type"] == "micro_node"
    assert challenge["current_task"]["task_id"] == "ode_separable.concept"
    assert challenge["macro_nodes"]["ode_separable"]["status"] == "locked"
    assert challenge["macro_challenges"]["ode_separable.macro_challenge"]["status"] == "locked"
    assert challenge["micro_nodes"]["ode_separable.concept"]["status"] == "active"
    assert_no_trusted_fields(challenge)


def test_micro_node_fail_stays_on_same_micro_node_and_rotates_question(tmp_path: Path) -> None:
    engine = ChallengeEngine(processor=QueueProcessor([(PassState.FAIL, ErrorType.CONCEPT_GAP)]))
    engine.start("ode_mvp", session_id="micro-fail", session_root=tmp_path)

    payload = engine.submit(session_id="micro-fail", answer="wrong", session_root=tmp_path)

    concept = payload["challenge"]["micro_nodes"]["ode_separable.concept"]
    assert concept["status"] == "active"
    assert concept["attempts_used"] == 1
    assert payload["challenge"]["current_task"]["task_id"] == "ode_separable.concept"
    assert payload["challenge"]["current_task"]["question_id"] == "ode-mvp-sep-concept-002"
    assert payload["challenge"]["macro_nodes"]["ode_separable"]["status"] == "locked"


def test_micro_node_five_fails_auto_resets_attempt_count_and_records_cycle(tmp_path: Path) -> None:
    engine = ChallengeEngine(
        processor=QueueProcessor([(PassState.FAIL, ErrorType.CONCEPT_GAP)] * 5)
    )
    engine.start("ode_mvp", session_id="micro-five-fails", session_root=tmp_path)

    for _ in range(5):
        payload = engine.submit(session_id="micro-five-fails", answer="wrong", session_root=tmp_path)

    concept = payload["challenge"]["micro_nodes"]["ode_separable.concept"]
    assert concept["status"] == "active"
    assert concept["attempts_used"] == 0
    assert concept["failed_cycles"] == 1
    assert payload["challenge"]["macro_nodes"]["ode_separable"]["status"] == "locked"


def test_all_micro_nodes_mastered_unlocks_macro_challenge(tmp_path: Path) -> None:
    engine = ChallengeEngine(processor=QueueProcessor([(PassState.PASS, None)] * 6))
    engine.start("ode_mvp", session_id="unlock-macro", session_root=tmp_path)

    for _ in range(6):
        payload = engine.submit(session_id="unlock-macro", answer="pass", session_root=tmp_path)

    assert all(node["status"] == "mastered" for node in payload["challenge"]["micro_nodes"].values())
    assert payload["challenge"]["macro_nodes"]["ode_separable"]["status"] == "active"
    assert payload["challenge"]["macro_challenges"]["ode_separable.macro_challenge"]["status"] == "active"
    assert payload["challenge"]["current_task"]["task_type"] == "macro_challenge"


def test_macro_challenge_pass_lights_macro_node(tmp_path: Path) -> None:
    engine = ChallengeEngine(processor=QueueProcessor([(PassState.PASS, None)] * 7))
    engine.start("ode_mvp", session_id="macro-pass", session_root=tmp_path)

    for _ in range(7):
        payload = engine.submit(session_id="macro-pass", answer="pass", session_root=tmp_path)

    assert payload["challenge"]["macro_nodes"]["ode_separable"]["status"] == "mastered"
    assert payload["challenge"]["macro_challenges"]["ode_separable.macro_challenge"]["status"] == "mastered"
    assert payload["challenge"]["completed"] is True
    assert payload["challenge"]["current_task"] is None


def test_macro_challenge_fail_maps_root_cause_to_one_micro_node(tmp_path: Path) -> None:
    outcomes = [(PassState.PASS, None)] * 6 + [(PassState.FAIL, ErrorType.CALCULATION_ERROR)]
    engine = ChallengeEngine(processor=QueueProcessor(outcomes))
    engine.start("ode_mvp", session_id="macro-fail-map", session_root=tmp_path)

    for _ in range(7):
        payload = engine.submit(session_id="macro-fail-map", answer="attempt", session_root=tmp_path)

    assert payload["challenge"]["macro_nodes"]["ode_separable"]["status"] == "active"
    assert payload["challenge"]["macro_challenges"]["ode_separable.macro_challenge"]["attempts_used"] == 1
    assert payload["challenge"]["current_task"]["task_id"] == "ode_separable.calculation"
    assert payload["challenge"]["micro_nodes"]["ode_separable.calculation"]["status"] == "active"
    active_micro_nodes = [
        node_id
        for node_id, progress in payload["challenge"]["micro_nodes"].items()
        if progress["status"] == "active"
    ]
    assert active_micro_nodes == ["ode_separable.calculation"]


def test_macro_challenge_three_fails_marks_macro_failed(tmp_path: Path) -> None:
    outcomes = (
        [(PassState.PASS, None)] * 6
        + [(PassState.FAIL, ErrorType.CALCULATION_ERROR)]
        + [(PassState.PASS, None)]
        + [(PassState.FAIL, ErrorType.CALCULATION_ERROR)]
        + [(PassState.PASS, None)]
        + [(PassState.FAIL, ErrorType.CALCULATION_ERROR)]
    )
    engine = ChallengeEngine(processor=QueueProcessor(outcomes))
    engine.start("ode_mvp", session_id="macro-exhaust", session_root=tmp_path)

    for _ in range(len(outcomes)):
        payload = engine.submit(session_id="macro-exhaust", answer="attempt", session_root=tmp_path)

    assert payload["challenge"]["macro_nodes"]["ode_separable"]["status"] == "failed"
    assert payload["challenge"]["macro_challenges"]["ode_separable.macro_challenge"]["status"] == "failed"
    assert payload["challenge"]["macro_challenges"]["ode_separable.macro_challenge"]["attempts_used"] == 3
    assert payload["challenge"]["current_task"] is None


def test_challenge_reset_all_restarts_graph(tmp_path: Path) -> None:
    engine = ChallengeEngine(processor=QueueProcessor([(PassState.PASS, None)]))
    engine.start("ode_mvp", session_id="reset-all", session_root=tmp_path)
    engine.submit(session_id="reset-all", answer="pass", session_root=tmp_path)

    payload = engine.reset(session_id="reset-all", reset_all=True, session_root=tmp_path)

    assert payload["challenge"]["current_task"]["task_id"] == "ode_separable.concept"
    assert payload["challenge"]["micro_nodes"]["ode_separable.concept"]["status"] == "active"
    assert payload["challenge"]["macro_nodes"]["ode_separable"]["status"] == "locked"


def test_local_trainer_challenge_start_and_status_stdout_are_json(tmp_path: Path, capsys: Any) -> None:
    exit_code = main(
        [
            "challenge-start",
            "ode_mvp",
            "--session-id",
            "cli-challenge",
            "--session-root",
            str(tmp_path / "sessions"),
        ]
    )
    start_payload = json.loads(capsys.readouterr().out)

    assert exit_code == EXIT_SUCCESS
    assert start_payload["challenge"]["current_task"]["task_id"] == "ode_separable.concept"
    assert_no_trusted_fields(start_payload)

    exit_code = main(
        [
            "challenge-status",
            "--session-id",
            "cli-challenge",
            "--session-root",
            str(tmp_path / "sessions"),
        ]
    )
    status_payload = json.loads(capsys.readouterr().out)

    assert exit_code == EXIT_SUCCESS
    assert status_payload["challenge"]["session_id"] == "cli-challenge"
    assert_no_trusted_fields(status_payload)


def test_challenge_progress_json_and_session_log_have_no_trusted_fields(tmp_path: Path) -> None:
    engine = ChallengeEngine(processor=QueueProcessor([(PassState.FAIL, ErrorType.CONCEPT_GAP)]))
    engine.start("ode_mvp", session_id="safe-progress", session_root=tmp_path)
    payload = engine.submit(session_id="safe-progress", answer="wrong", session_root=tmp_path)

    progress_path = tmp_path / "safe-progress.challenge_progress.json"
    log_path = tmp_path / "safe-progress.jsonl"

    assert progress_path.exists()
    assert log_path.exists()
    assert_no_trusted_fields(json.loads(progress_path.read_text(encoding="utf-8")))
    assert_no_trusted_fields(json.loads(log_path.read_text(encoding="utf-8").splitlines()[0]))
    assert_no_trusted_fields(payload)


def test_formal_catalog_and_learner_api_exposure_remain_unchanged(tmp_path: Path) -> None:
    before = formal_manifest_text()
    engine = ChallengeEngine(processor=QueueProcessor([]))

    engine.start("ode_mvp", session_id="catalog-boundary", session_root=tmp_path)

    assert formal_manifest_text() == before
    questions = LearnerLocalClient().list_questions()
    assert {question["question_id"] for question in questions} == {"ode-sep-001"}
    assert TestClient(create_app("learner")).get("/api/learner/v1/questions/ode-mvp-sep-concept-001").status_code == 404


class QueueProcessor:
    def __init__(self, outcomes: list[tuple[PassState, ErrorType | None]]) -> None:
        self.outcomes = list(outcomes)

    def __call__(self, question: Any, attempt: Any, node: Any) -> ChallengeEvaluation:
        del attempt, node
        if not self.outcomes:
            raise AssertionError("QueueProcessor has no remaining outcomes")
        pass_state, root_cause = self.outcomes.pop(0)
        return ChallengeEvaluation(
            pass_state=pass_state,
            root_cause=root_cause,
            coach_payload={
                "question_id": question.id,
                "pass_state": pass_state.value,
                "score_vector_summary": {},
                "learner_explanation": "fake challenge evaluation",
                "recommended_actions": [],
                "rollback_required": False,
                "rollback_nodes": [],
                "forward_allowed": False,
                "forward_nodes": [],
                "next_action_hint": "fake next action",
                "response_evidence_present": {
                    "has_response_steps": False,
                    "response_step_count": 0,
                    "has_self_explanation": False,
                },
                "session_log_written": False,
                "session_id": None,
            },
        )


def assert_no_trusted_fields(value: Any) -> None:
    ensure_no_trusted_fields(value)
    text = json.dumps(value, ensure_ascii=False)
    for field in TRUSTED_FIELDS:
        assert field not in text


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def formal_manifest_text() -> str:
    return (repo_root() / "backend" / "catalog_data" / "manifest.yaml").read_text(encoding="utf-8")
