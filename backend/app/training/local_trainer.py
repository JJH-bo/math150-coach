from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient

from app.api.v1.nodes import load_node_catalog
from app.challenge.engine import ChallengeEngine, ChallengeEngineError
from app.challenge.progress_store import ChallengeProgressError
from app.challenge.repository import ChallengeRepositoryError
from app.main import create_app
from app.training.coach_output import build_coach_output
from app.training.session_log import (
    SessionLogError,
    append_attempt,
    default_session_id,
    ensure_no_trusted_fields,
)


EXIT_SUCCESS = 0
EXIT_LEARNER_API_ERROR = 1
EXIT_INPUT_ERROR = 2
EXIT_SESSION_LOG_ERROR = 3
EXIT_INTERNAL_ERROR = 5

LIST_QUESTION_FIELDS = {
    "question_id",
    "node_id",
    "title",
    "difficulty",
    "answer_format",
    "response_step_mode",
}
SHOW_QUESTION_FIELDS = {
    "question_id",
    "node_id",
    "title",
    "stem",
    "prompt_markdown",
    "answer_format",
    "response_step_mode",
    "difficulty",
    "hints_public",
    "display_assets",
}


@dataclass(frozen=True)
class TrainerCliResult:
    exit_code: int
    payload: dict[str, Any]
    output_path: str | None = None
    error_message: str | None = None


class LearnerLocalClient:
    """Thin local client over the learner-safe HTTP contract."""

    def __init__(self) -> None:
        self._client = TestClient(create_app("learner"))

    def list_questions(self) -> list[dict[str, Any]]:
        questions: list[dict[str, Any]] = []
        for node in load_node_catalog():
            response = self._client.get(f"/api/learner/v1/nodes/{node.id}/questions")
            payload = self._json_or_error(response)
            for item in payload.get("questions", []):
                questions.append(_pick_fields(item, LIST_QUESTION_FIELDS))
        questions.sort(key=lambda item: str(item["question_id"]))
        return questions

    def show_question(self, question_id: str) -> dict[str, Any]:
        response = self._client.get(f"/api/learner/v1/questions/{question_id}")
        payload = self._json_or_error(response)
        return _pick_fields(payload["question"], SHOW_QUESTION_FIELDS)

    def submit_attempt(
        self,
        *,
        question_id: str,
        answer: str,
        steps: list[str] | None = None,
        explanation: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "question_id": question_id,
            "user_answer": answer,
            "response_steps": steps or [],
        }
        if explanation:
            payload["self_explanation"] = explanation
        response = self._client.post("/api/learner/v1/attempts/submit", json=payload)
        return self._json_or_error(response)

    def _json_or_error(self, response: Any) -> dict[str, Any]:
        payload = response.json()
        if response.status_code >= 400:
            detail = payload.get("detail", payload)
            if isinstance(detail, dict):
                raise LearnerApiError(detail)
            raise LearnerApiError({"error_code": "learner_api_error", "message": str(detail)})
        ensure_no_trusted_fields(payload)
        return payload


class LearnerApiError(ValueError):
    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(str(payload.get("message", "learner API error")))
        self.payload = payload


def run_list(args: argparse.Namespace) -> TrainerCliResult:
    del args
    try:
        questions = LearnerLocalClient().list_questions()
        payload = {"count": len(questions), "questions": questions}
        ensure_no_trusted_fields(payload)
        return TrainerCliResult(EXIT_SUCCESS, payload)
    except LearnerApiError as exc:
        return _learner_api_error(exc)
    except SessionLogError as exc:
        return _session_log_error(exc)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc)


def run_show(args: argparse.Namespace) -> TrainerCliResult:
    try:
        question = LearnerLocalClient().show_question(args.question_id)
        payload = {"question": question}
        ensure_no_trusted_fields(payload)
        return TrainerCliResult(EXIT_SUCCESS, payload)
    except LearnerApiError as exc:
        return _learner_api_error(exc)
    except SessionLogError as exc:
        return _session_log_error(exc)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc)


def run_submit(args: argparse.Namespace) -> TrainerCliResult:
    try:
        client = LearnerLocalClient()
        question = client.show_question(args.question_id)
        response = client.submit_attempt(
            question_id=args.question_id,
            answer=args.answer,
            steps=args.steps,
            explanation=args.explanation,
        )
        payload = build_coach_output(
            _submit_payload(
                args.question_id,
                response,
                response_evidence_present=_response_evidence_present(args.steps, args.explanation),
            )
        )
        session_id = args.session_id or default_session_id()
        log_record = _session_log_record(
            session_id=session_id,
            question=question,
            user_answer=args.answer,
            steps=args.steps or [],
            explanation=args.explanation,
            payload=payload,
        )
        append_attempt(log_record, session_id=session_id, session_root=args.session_root)
        payload["session_log_written"] = True
        payload["session_id"] = session_id
        if args.debug:
            payload["debug"] = {"local_trainer": "learner_api_only", "session_root_custom": args.session_root is not None}
        ensure_no_trusted_fields(payload)
        return TrainerCliResult(EXIT_SUCCESS, payload)
    except LearnerApiError as exc:
        return _learner_api_error(exc)
    except SessionLogError as exc:
        return _session_log_error(exc)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc)


def run_challenge_start(args: argparse.Namespace) -> TrainerCliResult:
    try:
        payload = ChallengeEngine().start(
            args.chapter_id,
            session_id=args.session_id,
            session_root=args.session_root,
        )
        ensure_no_trusted_fields(payload)
        return TrainerCliResult(EXIT_SUCCESS, payload)
    except (ChallengeEngineError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        return _challenge_error(exc)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc)


def run_challenge_status(args: argparse.Namespace) -> TrainerCliResult:
    try:
        payload = ChallengeEngine().status(
            session_id=args.session_id,
            session_root=args.session_root,
        )
        ensure_no_trusted_fields(payload)
        return TrainerCliResult(EXIT_SUCCESS, payload)
    except (ChallengeEngineError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        return _challenge_error(exc)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc)


def run_challenge_submit(args: argparse.Namespace) -> TrainerCliResult:
    try:
        payload = ChallengeEngine().submit(
            session_id=args.session_id,
            answer=args.answer,
            steps=args.steps,
            explanation=args.explanation,
            session_root=args.session_root,
        )
        ensure_no_trusted_fields(payload)
        return TrainerCliResult(EXIT_SUCCESS, payload)
    except (ChallengeEngineError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        return _challenge_error(exc)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc)


def run_challenge_reset(args: argparse.Namespace) -> TrainerCliResult:
    try:
        payload = ChallengeEngine().reset(
            session_id=args.session_id,
            node_id=args.node_id,
            reset_all=args.all,
            session_root=args.session_root,
        )
        ensure_no_trusted_fields(payload)
        return TrainerCliResult(EXIT_SUCCESS, payload)
    except (ChallengeEngineError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        return _challenge_error(exc)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.training.local_trainer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(handler=run_list)

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("question_id")
    show_parser.set_defaults(handler=run_show)

    submit_parser = subparsers.add_parser("submit")
    submit_parser.add_argument("question_id")
    submit_parser.add_argument("--answer", required=True)
    submit_parser.add_argument("--steps", action="append")
    submit_parser.add_argument("--explanation")
    submit_parser.add_argument("--session-id")
    submit_parser.add_argument("--session-root")
    submit_parser.add_argument("--debug", action="store_true")
    submit_parser.set_defaults(handler=run_submit)

    challenge_start = subparsers.add_parser("challenge-start")
    challenge_start.add_argument("chapter_id")
    challenge_start.add_argument("--session-id", required=True)
    challenge_start.add_argument("--session-root")
    challenge_start.set_defaults(handler=run_challenge_start)

    challenge_status = subparsers.add_parser("challenge-status")
    challenge_status.add_argument("--session-id", required=True)
    challenge_status.add_argument("--session-root")
    challenge_status.set_defaults(handler=run_challenge_status)

    challenge_submit = subparsers.add_parser("challenge-submit")
    challenge_submit.add_argument("--session-id", required=True)
    challenge_submit.add_argument("--answer", required=True)
    challenge_submit.add_argument("--steps", action="append")
    challenge_submit.add_argument("--explanation")
    challenge_submit.add_argument("--session-root")
    challenge_submit.set_defaults(handler=run_challenge_submit)

    challenge_reset = subparsers.add_parser("challenge-reset")
    challenge_reset.add_argument("--session-id", required=True)
    challenge_reset.add_argument("--node-id")
    challenge_reset.add_argument("--all", action="store_true")
    challenge_reset.add_argument("--session-root")
    challenge_reset.set_defaults(handler=run_challenge_reset)

    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        result: TrainerCliResult = args.handler(args)
    except SystemExit as exc:
        payload = {"error_code": "cli_argument_error", "message": "invalid local trainer command"}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        return int(exc.code) if isinstance(exc.code, int) else EXIT_INPUT_ERROR
    payload = dict(result.payload)
    if result.output_path:
        payload["output_path"] = result.output_path
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return result.exit_code


def _pick_fields(source: dict[str, Any], allowed_fields: set[str]) -> dict[str, Any]:
    picked = {key: source[key] for key in sorted(allowed_fields) if key in source}
    ensure_no_trusted_fields(picked)
    return picked


def _submit_payload(
    question_id: str,
    response: dict[str, Any],
    *,
    response_evidence_present: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scoring = response.get("scoring", {})
    diagnosis = response.get("diagnosis", {})
    movement = response.get("movement", {})
    action = response.get("action", {})
    return {
        "question_id": question_id,
        "pass_state": diagnosis.get("pass_state"),
        "score_vector_summary": scoring.get("score_vector", {}),
        "learner_explanation": diagnosis.get("learner_explanation", ""),
        "recommended_actions": diagnosis.get("recommended_actions", []),
        "rollback_required": movement.get("rollback_required", False),
        "rollback_nodes": movement.get("rollback_nodes", []),
        "forward_allowed": movement.get("forward_allowed", False),
        "forward_nodes": movement.get("forward_nodes", []),
        "next_action_hint": action.get("next_action_hint"),
        "response_evidence_present": response_evidence_present or _response_evidence_present(None, None),
        "session_log_written": False,
        "session_id": None,
    }


def _session_log_record(
    *,
    session_id: str,
    question: dict[str, Any],
    user_answer: str,
    steps: list[str],
    explanation: str | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "question_id": payload["question_id"],
        "node_id": question.get("node_id"),
        "user_answer": user_answer,
        "response_steps": steps,
        "self_explanation": explanation,
        "pass_state": payload.get("pass_state"),
        "score_vector_summary": payload.get("score_vector_summary"),
        "learner_explanation": payload.get("learner_explanation"),
        "recommended_actions": payload.get("recommended_actions"),
        "rollback_required": payload.get("rollback_required"),
        "rollback_nodes": payload.get("rollback_nodes"),
        "forward_allowed": payload.get("forward_allowed"),
        "forward_nodes": payload.get("forward_nodes"),
        "next_action_hint": payload.get("next_action_hint"),
        "coach_summary": payload.get("coach_summary"),
        "status_label": payload.get("status_label"),
        "progression_advice": payload.get("progression_advice"),
        "evidence_gaps": payload.get("evidence_gaps"),
        "friendly_score_summary": payload.get("friendly_score_summary"),
        "next_step_plan": payload.get("next_step_plan"),
        "response_evidence_present": payload.get("response_evidence_present"),
        "unscored_dimensions": payload.get("unscored_dimensions"),
    }
    ensure_no_trusted_fields(record)
    return record


def _response_evidence_present(
    steps: list[str] | None,
    explanation: str | None,
) -> dict[str, Any]:
    step_count = len(steps or [])
    return {
        "has_response_steps": step_count > 0,
        "response_step_count": step_count,
        "has_self_explanation": bool(explanation),
    }


def _learner_api_error(exc: LearnerApiError) -> TrainerCliResult:
    payload = {
        "error_code": exc.payload.get("error_code", "learner_api_error"),
        "message": exc.payload.get("message", "learner API error"),
        "field_path": exc.payload.get("field_path"),
    }
    return TrainerCliResult(EXIT_LEARNER_API_ERROR, payload, error_message=str(exc))


def _session_log_error(exc: Exception) -> TrainerCliResult:
    return TrainerCliResult(
        EXIT_SESSION_LOG_ERROR,
        {"error_code": "session_log_error", "message": str(exc)},
        error_message=str(exc),
    )


def _challenge_error(exc: Exception) -> TrainerCliResult:
    return TrainerCliResult(
        EXIT_INPUT_ERROR,
        {"error_code": "challenge_error", "message": str(exc)},
        error_message=str(exc),
    )


def _internal_error(exc: Exception) -> TrainerCliResult:
    return TrainerCliResult(
        EXIT_INTERNAL_ERROR,
        {"error_code": "internal_unexpected_error", "message": "unexpected local trainer error"},
        error_message=str(exc),
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
