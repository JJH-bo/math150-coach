from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.enums import ErrorType, QuestionType, ScoreDimension  # noqa: E402
from app.core.schemas import Attempt, KnowledgeNode, Question  # noqa: E402
from app.logic_graph.evidence_engine import LogicEvidenceEngine  # noqa: E402
from app.services.composite_scoring_engine import CompositeScoringEngine  # noqa: E402
from app.services.diagnosis_engine import DiagnosisEngine  # noqa: E402


CASE_PATH = Path(__file__).parent / "synthetic_cases" / "ode_diagnosis_synthetic_cases.yaml"

REQUIRED_CASE_FIELDS = {
    "id",
    "category",
    "purpose",
    "scoring_path",
    "question",
    "user_answer",
    "expected_pass_state",
    "expected_root_cause",
    "expected_recommended_action",
}
REQUIRED_QUESTION_FIELDS = {"id", "node_id", "question_type", "prompt"}

EXPECTED_SCORERS_BY_PATH = {
    "manual_override": {"ManualOverrideScorer"},
    "rubric": {"RubricScorer"},
    "math_validator": {"MathValidatorScorer"},
    "rubric_plus_math_validator": {"RubricScorer", "MathValidatorScorer"},
    "rubric_plus_rule": {"RubricScorer", "RuleScorer"},
    "rule_only_weak_signal": {"RuleScorer"},
    "no_signal": set(),
}


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    case_path = path or CASE_PATH
    with case_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data.get("cases", [])


def load_nodes(path: Path | None = None) -> dict[str, KnowledgeNode]:
    nodes_path = path or PROJECT_ROOT / "backend" / "app" / "seed" / "ode_nodes.yaml"
    with nodes_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return {node["id"]: KnowledgeNode(**node) for node in data.get("nodes", [])}


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    if len(cases) < 12:
        errors.append(f"synthetic lab should contain at least 12 cases, got {len(cases)}")
    for case in cases:
        case_id = str(case.get("id", "<unknown>"))
        if case_id in ids:
            errors.append(f"duplicate case id: {case_id}")
        ids.add(case_id)

        missing = REQUIRED_CASE_FIELDS - set(case)
        if missing:
            errors.append(f"{case_id} missing fields: {sorted(missing)}")
            continue
        question_missing = REQUIRED_QUESTION_FIELDS - set(case["question"])
        if question_missing:
            errors.append(f"{case_id} question missing fields: {sorted(question_missing)}")
        scoring_path = case["scoring_path"]
        if scoring_path not in EXPECTED_SCORERS_BY_PATH:
            errors.append(f"{case_id} unsupported scoring_path: {scoring_path}")
        if scoring_path == "manual_override" and not case.get("score_overrides"):
            errors.append(f"{case_id} manual_override case must define score_overrides")
        if scoring_path != "manual_override" and "score_overrides" in case:
            errors.append(f"{case_id} non-manual case must not define score_overrides")
    return errors


def run_case(case: dict[str, Any], nodes: dict[str, KnowledgeNode]) -> list[str]:
    failures: list[str] = []
    case_id = case["id"]
    node = nodes.get(case["question"]["node_id"])
    if node is None:
        return [f"{case_id}: unknown node_id {case['question']['node_id']}"]

    question = build_question(case["question"], node)
    attempt = build_attempt(case, question)
    composite_result = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    diagnosis_result = DiagnosisEngine().diagnose_detailed(composite_result, question, attempt, node)
    logic_insight = LogicEvidenceEngine().analyze(question, attempt, composite_result, diagnosis_result)

    active_scorers = {result.scorer_name for result in composite_result.scorer_results if result.is_active}
    expected_scorers = EXPECTED_SCORERS_BY_PATH[case["scoring_path"]]
    missing_scorers = expected_scorers - active_scorers
    if missing_scorers:
        failures.append(f"missing active scorers {sorted(missing_scorers)}; active={sorted(active_scorers)}")
    if case["scoring_path"] != "manual_override" and "ManualOverrideScorer" in active_scorers:
        failures.append("non-manual synthetic case used ManualOverrideScorer")

    actual_root = diagnosis_result.root_cause.value if diagnosis_result.root_cause else None
    if actual_root != case["expected_root_cause"]:
        failures.append(f"root_cause expected {case['expected_root_cause']}, got {actual_root}")
    if diagnosis_result.pass_state.value != case["expected_pass_state"]:
        failures.append(f"pass_state expected {case['expected_pass_state']}, got {diagnosis_result.pass_state.value}")

    actual_actions = [action.action_type for action in diagnosis_result.recommended_actions]
    if not actual_actions or actual_actions[0] != case["expected_recommended_action"]:
        failures.append(f"recommended_action expected {case['expected_recommended_action']}, got {actual_actions}")

    expected_primary = set(case.get("expected_primary_errors", []))
    actual_primary = {error.value for error in diagnosis_result.primary_errors}
    if not expected_primary.issubset(actual_primary):
        failures.append(f"primary errors expected {sorted(expected_primary)}, got {sorted(actual_primary)}")

    expected_derived = set(case.get("expected_derived_errors", []))
    actual_derived = {error.value for error in diagnosis_result.derived_errors}
    if not expected_derived.issubset(actual_derived):
        failures.append(f"derived errors expected {sorted(expected_derived)}, got {sorted(actual_derived)}")

    expected_ability_state = case.get("expected_ability_state")
    if expected_ability_state and diagnosis_result.ability_state != expected_ability_state:
        failures.append(f"ability_state expected {expected_ability_state}, got {diagnosis_result.ability_state}")

    expected_repair_target = case.get("expected_repair_target_node_id")
    if expected_repair_target and logic_insight.primary_target_node_id != expected_repair_target:
        failures.append(
            f"logic repair target expected {expected_repair_target}, got {logic_insight.primary_target_node_id}"
        )

    trace = diagnosis_result.diagnosis_trace
    if trace is None:
        failures.append("diagnosis_trace is missing")
    else:
        if case.get("expected_surface_keyword_only") is not None:
            if trace.surface_keyword_only is not bool(case["expected_surface_keyword_only"]):
                failures.append(
                    f"surface_keyword_only expected {case['expected_surface_keyword_only']}, got {trace.surface_keyword_only}"
                )
        if case.get("expected_logic_contradiction"):
            if not trace.logic_contradictions:
                failures.append("expected hidden logic contradiction but trace had none")

    if case.get("expected_confidence_band") and not confidence_in_band(
        diagnosis_result.confidence,
        case["expected_confidence_band"],
    ):
        failures.append(
            f"confidence {diagnosis_result.confidence:.2f} outside expected band {case['expected_confidence_band']}"
        )

    return [f"{case_id}: {failure}" for failure in failures]


def build_question(payload: dict[str, Any], node: KnowledgeNode) -> Question:
    return Question(
        id=payload["id"],
        node_id=payload["node_id"],
        question_type=QuestionType(payload["question_type"]),
        prompt=payload["prompt"],
        expected_answer=payload.get("expected_answer"),
        tested_dimensions=[
            ScoreDimension(dimension)
            for dimension in payload.get("tested_dimensions", node.core_dimensions)
        ],
        solution_outline=payload.get("solution_outline"),
        rubric=payload.get("rubric"),
        expected_key_points=payload.get("expected_key_points", []),
        expected_patterns=payload.get("expected_patterns", []),
        metadata=payload.get("metadata", {}),
    )


def build_attempt(case: dict[str, Any], question: Question) -> Attempt:
    metadata = dict(case.get("attempt_metadata", {}))
    if case["scoring_path"] == "manual_override":
        scores = {dimension: score for dimension, score in case["score_overrides"].items() if score is not None}
        metadata["score_overrides"] = scores
        metadata["evidence_overrides"] = {
            dimension: f"Synthetic lab imported score for {case['id']}:{dimension}."
            for dimension in scores
        }
    return Attempt(
        id=f"synthetic_{case['id']}",
        question_id=question.id,
        user_answer=case["user_answer"],
        response_steps=list(case.get("response_steps", [])),
        self_explanation=case.get("self_explanation"),
        metadata=metadata,
    )


def category_counts(cases: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(case.get("category", "<missing>")) for case in cases)


def scoring_path_counts(cases: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(case.get("scoring_path", "<missing>")) for case in cases)


def confidence_in_band(confidence: float, band: str) -> bool:
    if band == "low":
        return confidence <= 0.35
    if band == "medium":
        return 0.35 < confidence < 0.75
    if band == "high":
        return confidence >= 0.75
    return False


def main() -> int:
    cases = load_cases()
    structure_errors = validate_cases(cases)
    if structure_errors:
        print("Synthetic diagnosis lab structure failures:")
        for error in structure_errors:
            print(f"- {error}")
        return 1

    nodes = load_nodes()
    failures: list[str] = []
    for case in cases:
        failures.extend(run_case(case, nodes))

    passed = len(cases) - len({failure.split(':', 1)[0] for failure in failures})
    print(f"Synthetic diagnosis lab: {passed}/{len(cases)} passed")
    print("Synthetic scoring path counts:")
    for path, count in sorted(scoring_path_counts(cases).items()):
        print(f"- {path}: {count}")
    print("Synthetic category counts:")
    for category, count in sorted(category_counts(cases).items()):
        print(f"- {category}: {count}")

    if failures:
        print("Synthetic failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("All synthetic diagnosis lab cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
