from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from app.challenge.engine import ChallengeEngine
from app.challenge.models import ChallengeGraph, ChallengeQuestion, ChallengeQuestionBank, ChallengeTaskType
from app.challenge.repository import ChallengeRepository
from app.core.enums import ErrorType
from app.core.schemas import Attempt

CalibrationGrade = Literal["pass", "warn", "fail"]


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
        required = (
            "case_id",
            "node_id",
            "prompt_intent",
            "learner_answer",
            "learner_self_explanation",
            "expected_primary_error",
            "expected_repair_target",
            "human_coaching_note",
        )
        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"real attempt case is missing fields {missing}: {data!r}")
        return cls(**{field: str(data[field]).strip() for field in required})


@dataclass(frozen=True)
class RealAttemptLabSpec:
    lab_id: str
    chapter_id: str
    purpose: str
    status: str
    cases: list[RealAttemptCase]


@dataclass(frozen=True)
class RealAttemptCaseResult:
    case_id: str
    node_id: str
    question_id: str
    expected_primary_error: str
    actual_primary_error: str | None
    expected_repair_target: str
    actual_repair_target: str | None
    pass_state: str
    root_cause_match: bool
    repair_target_match: bool
    exact_match: bool
    severity: CalibrationGrade
    mismatch_reasons: list[str]
    human_coaching_note: str
    learner_explanation: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "node_id": self.node_id,
            "question_id": self.question_id,
            "expected_primary_error": self.expected_primary_error,
            "actual_primary_error": self.actual_primary_error,
            "expected_repair_target": self.expected_repair_target,
            "actual_repair_target": self.actual_repair_target,
            "pass_state": self.pass_state,
            "root_cause_match": self.root_cause_match,
            "repair_target_match": self.repair_target_match,
            "exact_match": self.exact_match,
            "severity": self.severity,
            "mismatch_reasons": list(self.mismatch_reasons),
            "human_coaching_note": self.human_coaching_note,
            "learner_explanation": self.learner_explanation,
        }


@dataclass(frozen=True)
class RealAttemptLabReport:
    lab_id: str
    chapter_id: str
    case_count: int
    root_cause_matches: int
    repair_target_matches: int
    exact_matches: int
    fail_count: int
    warn_count: int
    calibration_grade: CalibrationGrade
    results: list[RealAttemptCaseResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "lab_id": self.lab_id,
            "chapter_id": self.chapter_id,
            "case_count": self.case_count,
            "root_cause_matches": self.root_cause_matches,
            "repair_target_matches": self.repair_target_matches,
            "exact_matches": self.exact_matches,
            "fail_count": self.fail_count,
            "warn_count": self.warn_count,
            "calibration_grade": self.calibration_grade,
            "results": [result.to_dict() for result in self.results],
        }


class RealAttemptLabError(ValueError):
    """Raised when the real-attempt calibration lab cannot run safely."""


def load_real_attempt_lab_file(path: Path) -> RealAttemptLabSpec:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise RealAttemptLabError(f"real attempt lab root must be a mapping: {path}")

    lab_id = str(data.get("lab_id") or path.stem).strip()
    chapter_id = str(data.get("chapter_id") or "").strip()
    if not chapter_id:
        raise RealAttemptLabError("real attempt lab requires chapter_id")

    raw_cases = data.get("cases") or []
    if not isinstance(raw_cases, list):
        raise RealAttemptLabError("real attempt lab cases must be a list")
    cases = [RealAttemptCase.from_mapping(case) for case in raw_cases]
    if not cases:
        raise RealAttemptLabError("real attempt lab requires at least one case")
    _ensure_unique_case_ids(cases)

    return RealAttemptLabSpec(
        lab_id=lab_id,
        chapter_id=chapter_id,
        purpose=str(data.get("purpose") or "").strip(),
        status=str(data.get("status") or "draft_seed").strip(),
        cases=cases,
    )


def validate_real_attempt_lab_spec(spec: RealAttemptLabSpec, graph: ChallengeGraph, questions: ChallengeQuestionBank) -> None:
    micro_ids = {micro.id for micro in graph.micro_nodes}
    error_values = {error.value for error in ErrorType}

    for case in spec.cases:
        if case.node_id not in micro_ids:
            raise RealAttemptLabError(f"case references unknown node_id: {case.case_id} -> {case.node_id}")
        if case.expected_repair_target not in micro_ids:
            raise RealAttemptLabError(
                f"case references unknown expected_repair_target: {case.case_id} -> {case.expected_repair_target}"
            )
        if case.expected_primary_error not in error_values:
            raise RealAttemptLabError(
                f"case references unknown expected_primary_error: {case.case_id} -> {case.expected_primary_error}"
            )
        _select_question_for_case(questions, case)


def run_real_attempt_lab(case_path: Path, repository: ChallengeRepository | None = None) -> RealAttemptLabReport:
    spec = load_real_attempt_lab_file(case_path)
    repository = repository or ChallengeRepository()
    graph = repository.load_graph(spec.chapter_id)
    questions = repository.load_question_bank(spec.chapter_id)
    validate_real_attempt_lab_spec(spec, graph, questions)

    engine = ChallengeEngine(repository=repository)
    results = [_evaluate_case(engine, graph, questions, case) for case in spec.cases]
    return summarize_real_attempt_results(spec.lab_id, spec.chapter_id, results)


def summarize_real_attempt_results(
    lab_id: str,
    chapter_id: str,
    results: list[RealAttemptCaseResult],
) -> RealAttemptLabReport:
    case_count = len(results)
    root_cause_matches = sum(1 for result in results if result.root_cause_match)
    repair_target_matches = sum(1 for result in results if result.repair_target_match)
    exact_matches = sum(1 for result in results if result.exact_match)
    fail_count = sum(1 for result in results if result.severity == "fail")
    warn_count = sum(1 for result in results if result.severity == "warn")
    return RealAttemptLabReport(
        lab_id=lab_id,
        chapter_id=chapter_id,
        case_count=case_count,
        root_cause_matches=root_cause_matches,
        repair_target_matches=repair_target_matches,
        exact_matches=exact_matches,
        fail_count=fail_count,
        warn_count=warn_count,
        calibration_grade=_calibration_grade(case_count, fail_count, warn_count),
        results=results,
    )


def build_case_result(
    *,
    case: RealAttemptCase,
    question_id: str,
    actual_primary_error: str | None,
    actual_repair_target: str | None,
    pass_state: str,
    learner_explanation: str | None,
) -> RealAttemptCaseResult:
    root_match = actual_primary_error == case.expected_primary_error
    repair_match = actual_repair_target == case.expected_repair_target
    mismatch_reasons: list[str] = []
    if not root_match:
        mismatch_reasons.append("root_cause_mismatch")
    if not repair_match:
        mismatch_reasons.append("repair_target_mismatch")
    severity = _case_severity(root_match, repair_match)
    return RealAttemptCaseResult(
        case_id=case.case_id,
        node_id=case.node_id,
        question_id=question_id,
        expected_primary_error=case.expected_primary_error,
        actual_primary_error=actual_primary_error,
        expected_repair_target=case.expected_repair_target,
        actual_repair_target=actual_repair_target,
        pass_state=pass_state,
        root_cause_match=root_match,
        repair_target_match=repair_match,
        exact_match=root_match and repair_match,
        severity=severity,
        mismatch_reasons=mismatch_reasons,
        human_coaching_note=case.human_coaching_note,
        learner_explanation=learner_explanation,
    )


def _evaluate_case(
    engine: ChallengeEngine,
    graph: ChallengeGraph,
    questions: ChallengeQuestionBank,
    case: RealAttemptCase,
) -> RealAttemptCaseResult:
    question_spec = _select_question_for_case(questions, case)
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
    payload = evaluation.coach_payload or {}
    return build_case_result(
        case=case,
        question_id=domain_question.id,
        actual_primary_error=evaluation.root_cause.value if evaluation.root_cause else None,
        actual_repair_target=evaluation.repair_target_node_id,
        pass_state=evaluation.pass_state.value,
        learner_explanation=(payload.get("learner_explanation") or payload.get("coach_summary")),
    )


def _select_question_for_case(questions: ChallengeQuestionBank, case: RealAttemptCase) -> ChallengeQuestion:
    candidates = [
        question
        for question in questions.questions
        if question.task_type == ChallengeTaskType.MICRO_NODE and question.owner_id == case.node_id
    ]
    if not candidates:
        candidates = [question for question in questions.questions if question.node_id == case.node_id]
    if not candidates:
        raise RealAttemptLabError(f"no challenge question found for case {case.case_id} on node {case.node_id}")
    return candidates[0]


def _ensure_unique_case_ids(cases: list[RealAttemptCase]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for case in cases:
        if case.case_id in seen:
            duplicates.append(case.case_id)
        seen.add(case.case_id)
    if duplicates:
        raise RealAttemptLabError(f"duplicate real attempt case ids: {sorted(set(duplicates))}")


def _case_severity(root_match: bool, repair_match: bool) -> CalibrationGrade:
    if root_match and repair_match:
        return "pass"
    if repair_match:
        return "warn"
    return "fail"


def _calibration_grade(case_count: int, fail_count: int, warn_count: int) -> CalibrationGrade:
    if case_count == 0 or fail_count > 0:
        return "fail"
    if warn_count > 0:
        return "warn"
    return "pass"
