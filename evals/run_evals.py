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

from app.core.enums import ForwardLevel, QuestionType, ScoreDimension  # noqa: E402
from app.core.schemas import Attempt, KnowledgeNode, Question  # noqa: E402
from app.services.composite_scoring_engine import CompositeScoringEngine  # noqa: E402
from app.services.diagnosis_engine import DiagnosisEngine  # noqa: E402
from app.services.forward_engine import ForwardEngine  # noqa: E402
from app.services.rollback_engine import RollbackEngine  # noqa: E402


REQUIRED_CASE_FIELDS = {
    "id",
    "category",
    "scoring_path",
    "question",
    "user_answer",
    "expected_scores",
    "expected_errors",
    "expected_pass_state",
    "expected_rollback_behavior",
}

REQUIRED_QUESTION_FIELDS = {"id", "node_id", "question_type", "prompt"}
REQUIRED_ROLLBACK_FIELDS = {"target_nodes", "explanation"}
REQUIRED_ERROR_FIELDS = {
    "error_type",
    "weight",
    "related_dimensions",
    "evidence",
    "is_primary",
    "suggested_rollback_level",
}

EXPECTED_SCORERS_BY_PATH = {
    "manual_override": {"ManualOverrideScorer"},
    "rubric": {"RubricScorer"},
    "rubric_plus_rule": {"RubricScorer", "RuleScorer"},
    "rubric_plus_math_validator": {"RubricScorer", "MathValidatorScorer"},
    "rule_only_weak_signal": {"RuleScorer"},
}

EXPECTED_DIAGNOSIS_SCORERS_BY_PATH = {
    **EXPECTED_SCORERS_BY_PATH,
    "math_validator": {"MathValidatorScorer"},
}

EXPECTED_MOVEMENT_SCORERS_BY_PATH = {
    **EXPECTED_DIAGNOSIS_SCORERS_BY_PATH,
    "no_signal": set(),
}

REQUIRED_DIAGNOSIS_CASE_FIELDS = {
    "id",
    "category",
    "scoring_path",
    "question",
    "user_answer",
    "expected_root_cause",
    "expected_primary_errors",
    "expected_secondary_errors",
    "expected_derived_errors",
    "expected_pass_state",
    "expected_learner_explanation_keywords",
    "expected_confidence_band",
    "expected_recommended_actions",
}

REQUIRED_MOVEMENT_CASE_FIELDS = {
    "id",
    "category",
    "scoring_path",
    "question",
    "user_answer",
    "expected_pass_state",
    "expected_root_cause",
    "expected_rollback_level",
    "expected_forward_level",
    "expected_next_action_type",
    "should_not_return_all_prerequisites",
    "should_not_strong_forward",
}


def load_golden_cases(path: Path | None = None) -> list[dict[str, Any]]:
    case_path = path or Path(__file__).parent / "golden_cases" / "ode_scoring_cases.yaml"
    with case_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data.get("cases", [])


def load_diagnosis_cases(path: Path | None = None) -> list[dict[str, Any]]:
    case_path = path or Path(__file__).parent / "golden_cases" / "ode_diagnosis_cases.yaml"
    with case_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data.get("cases", [])


def load_movement_cases(path: Path | None = None) -> list[dict[str, Any]]:
    case_path = path or Path(__file__).parent / "golden_cases" / "ode_movement_cases.yaml"
    with case_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data.get("cases", [])


def load_nodes(path: Path | None = None) -> dict[str, KnowledgeNode]:
    nodes_path = path or PROJECT_ROOT / "backend" / "app" / "seed" / "ode_nodes.yaml"
    with nodes_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return {node["id"]: KnowledgeNode(**node) for node in data.get("nodes", [])}


def validate_golden_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for case in cases:
        case_id = case.get("id", "<unknown>")
        missing = REQUIRED_CASE_FIELDS - set(case)
        if missing:
            errors.append(f"{case_id} missing fields: {sorted(missing)}")
            continue

        scoring_path = case["scoring_path"]
        if scoring_path not in EXPECTED_SCORERS_BY_PATH:
            errors.append(f"{case_id} has unsupported scoring_path: {scoring_path}")

        question_missing = REQUIRED_QUESTION_FIELDS - set(case["question"])
        if question_missing:
            errors.append(f"{case_id} question missing fields: {sorted(question_missing)}")

        rollback_missing = REQUIRED_ROLLBACK_FIELDS - set(case["expected_rollback_behavior"])
        if rollback_missing:
            errors.append(f"{case_id} expected_rollback_behavior missing fields: {sorted(rollback_missing)}")

        if not isinstance(case["expected_scores"], dict) or not case["expected_scores"]:
            errors.append(f"{case_id} expected_scores must be a non-empty mapping")

        if not isinstance(case["expected_errors"], list):
            errors.append(f"{case_id} expected_errors must be a list")

        for index, error in enumerate(case["expected_errors"]):
            error_missing = REQUIRED_ERROR_FIELDS - set(error)
            if error_missing:
                errors.append(f"{case_id} expected_errors[{index}] missing fields: {sorted(error_missing)}")

        if scoring_path != "manual_override":
            metadata = case.get("attempt_metadata", {})
            if "score_overrides" in metadata:
                errors.append(f"{case_id} non-manual case must not contain score_overrides")
    return errors


def validate_diagnosis_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if len(cases) < 25:
        errors.append(f"diagnosis cases must contain at least 25 cases, got {len(cases)}")
    for case in cases:
        case_id = case.get("id", "<unknown>")
        missing = REQUIRED_DIAGNOSIS_CASE_FIELDS - set(case)
        if missing:
            errors.append(f"{case_id} missing fields: {sorted(missing)}")
            continue
        scoring_path = case["scoring_path"]
        if scoring_path not in EXPECTED_DIAGNOSIS_SCORERS_BY_PATH:
            errors.append(f"{case_id} has unsupported diagnosis scoring_path: {scoring_path}")
        question_missing = REQUIRED_QUESTION_FIELDS - set(case["question"])
        if question_missing:
            errors.append(f"{case_id} question missing fields: {sorted(question_missing)}")
        if not isinstance(case["expected_learner_explanation_keywords"], list):
            errors.append(f"{case_id} expected_learner_explanation_keywords must be a list")
        if not isinstance(case["expected_recommended_actions"], list):
            errors.append(f"{case_id} expected_recommended_actions must be a list")
    return errors


def validate_movement_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not 10 <= len(cases) <= 12:
        errors.append(f"movement cases must contain 10-12 cases, got {len(cases)}")
    for case in cases:
        case_id = case.get("id", "<unknown>")
        missing = REQUIRED_MOVEMENT_CASE_FIELDS - set(case)
        if missing:
            errors.append(f"{case_id} missing fields: {sorted(missing)}")
            continue
        scoring_path = case["scoring_path"]
        if scoring_path not in EXPECTED_MOVEMENT_SCORERS_BY_PATH:
            errors.append(f"{case_id} has unsupported movement scoring_path: {scoring_path}")
        question_missing = REQUIRED_QUESTION_FIELDS - set(case["question"])
        if question_missing:
            errors.append(f"{case_id} question missing fields: {sorted(question_missing)}")
        if scoring_path == "manual_override" and "score_overrides" not in case:
            errors.append(f"{case_id} manual movement case must contain score_overrides")
        if scoring_path != "manual_override" and "score_overrides" in case:
            errors.append(f"{case_id} non-manual movement case must not contain score_overrides")
    return errors


def category_counts(cases: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(case.get("category", "<missing_category>")) for case in cases)


def scoring_path_counts(cases: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(case.get("scoring_path", "<missing_scoring_path>")) for case in cases)


def build_question(question_payload: dict[str, Any], node: KnowledgeNode) -> Question:
    return Question(
        id=question_payload["id"],
        node_id=question_payload["node_id"],
        question_type=QuestionType(question_payload["question_type"]),
        prompt=question_payload["prompt"],
        expected_answer=question_payload.get("expected_answer"),
        tested_dimensions=[ScoreDimension(dimension) for dimension in question_payload.get("tested_dimensions", node.core_dimensions)],
        solution_outline=question_payload.get("solution_outline"),
        rubric=question_payload.get("rubric"),
        expected_key_points=question_payload.get("expected_key_points", []),
        expected_patterns=question_payload.get("expected_patterns", []),
        metadata=question_payload.get("metadata", {}),
    )


def run_case(case: dict[str, Any], nodes: dict[str, KnowledgeNode]) -> list[str]:
    failures: list[str] = []
    case_id = case["id"]
    question_payload = case["question"]
    node = nodes.get(question_payload["node_id"])
    if node is None:
        return [f"{case_id}: unknown node_id {question_payload['node_id']}"]

    expected_scores = {
        dimension: score
        for dimension, score in case["expected_scores"].items()
        if score is not None
    }
    question = build_question(question_payload, node)

    attempt_metadata = dict(case.get("attempt_metadata", {}))
    if case["scoring_path"] == "manual_override":
        attempt_metadata["score_overrides"] = expected_scores
        attempt_metadata["evidence_overrides"] = {
            dimension: f"Golden eval imported/manual override score for {case_id}:{dimension}."
            for dimension in expected_scores
        }

    attempt = Attempt(
        id=f"attempt_{case_id}",
        question_id=question.id,
        user_answer=case["user_answer"],
        metadata=attempt_metadata,
    )

    scoring_engine = CompositeScoringEngine()
    diagnosis_engine = DiagnosisEngine()
    rollback_engine = RollbackEngine()
    forward_engine = ForwardEngine()

    composite_result = scoring_engine.evaluate_detailed(question, attempt, node)
    score_vector = composite_result.score_vector
    error_vector = diagnosis_engine.diagnose(score_vector, question, attempt, node)
    pass_state = diagnosis_engine.classify_pass_state(score_vector, error_vector, node)
    rollback_decision = rollback_engine.decide_rollback(error_vector, node)
    forward_decision = forward_engine.decide_forward(score_vector, error_vector, node)

    active_scorers = {result.scorer_name for result in composite_result.scorer_results if result.is_active}
    expected_scorers = EXPECTED_SCORERS_BY_PATH[case["scoring_path"]]
    missing_scorers = expected_scorers - active_scorers
    if missing_scorers:
        failures.append(f"missing expected active scorers: {sorted(missing_scorers)}; active={sorted(active_scorers)}")

    if case["scoring_path"] != "manual_override" and "ManualOverrideScorer" in active_scorers:
        failures.append("non-manual case was scored by ManualOverrideScorer")

    for dimension, dimension_score in score_vector.as_dimension_map().items():
        if dimension_score is not None and not dimension_score.evidence:
            failures.append(f"{dimension.value} has a score but no evidence")

    for raw_dimension, expected_score in expected_scores.items():
        dimension_score = score_vector.get_dimension(raw_dimension)
        if dimension_score is None or dimension_score.score is None:
            failures.append(f"{raw_dimension} expected score {expected_score}, got None")
            continue
        if abs(dimension_score.score - expected_score) > 12:
            failures.append(f"{raw_dimension} expected near {expected_score}, got {dimension_score.score:.1f}")

    expected_pass_state = case["expected_pass_state"]
    if pass_state.value != expected_pass_state:
        failures.append(f"pass_state expected {expected_pass_state}, got {pass_state.value}")

    expected_primary_errors = {
        error["error_type"]
        for error in case["expected_errors"]
        if error.get("is_primary")
    }
    actual_primary_errors = {error.error_type.value for error in error_vector.primary_errors()}
    missing_primary = expected_primary_errors - actual_primary_errors
    if missing_primary:
        failures.append(f"missing primary errors: {sorted(missing_primary)}; actual={sorted(actual_primary_errors)}")

    behavior = case["expected_rollback_behavior"]
    expected_forward_level = behavior.get("forward_level")
    if expected_forward_level and forward_decision.level.value != expected_forward_level:
        failures.append(f"forward_level expected {expected_forward_level}, got {forward_decision.level.value}")

    expected_rollback_level = behavior.get("rollback_level")
    if expected_rollback_level and rollback_decision.level.value != expected_rollback_level:
        failures.append(f"rollback_level expected {expected_rollback_level}, got {rollback_decision.level.value}")

    if behavior.get("should_not_return_all_prerequisites"):
        if node.prerequisites and set(rollback_decision.rollback_nodes) == set(node.prerequisites):
            failures.append("rollback returned all prerequisites despite should_not_return_all_prerequisites=true")

    if behavior.get("should_not_strong_forward"):
        if forward_decision.level == ForwardLevel.P3_STRONG:
            failures.append("forward decision was P3 despite should_not_strong_forward=true")

    return [f"{case_id}: {failure}" for failure in failures]


def run_diagnosis_case(case: dict[str, Any], nodes: dict[str, KnowledgeNode]) -> list[str]:
    failures: list[str] = []
    case_id = case["id"]
    question_payload = case["question"]
    node = nodes.get(question_payload["node_id"])
    if node is None:
        return [f"{case_id}: unknown node_id {question_payload['node_id']}"]

    question = build_question(question_payload, node)
    attempt_metadata = dict(case.get("attempt_metadata", {}))
    if case["scoring_path"] == "manual_override":
        expected_scores = {
            dimension: score
            for dimension, score in case.get("score_overrides", case.get("expected_scores", {})).items()
            if score is not None
        }
        attempt_metadata["score_overrides"] = expected_scores
        attempt_metadata["evidence_overrides"] = {
            dimension: f"Diagnosis golden imported/manual override score for {case_id}:{dimension}."
            for dimension in expected_scores
        }

    attempt = Attempt(
        id=f"attempt_{case_id}",
        question_id=question.id,
        user_answer=case["user_answer"],
        metadata=attempt_metadata,
    )

    composite_result = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    diagnosis_result = DiagnosisEngine().diagnose_detailed(composite_result, question, attempt, node)

    active_scorers = {result.scorer_name for result in composite_result.scorer_results if result.is_active}
    expected_scorers = EXPECTED_DIAGNOSIS_SCORERS_BY_PATH[case["scoring_path"]]
    missing_scorers = expected_scorers - active_scorers
    if missing_scorers:
        failures.append(f"missing expected active scorers: {sorted(missing_scorers)}; active={sorted(active_scorers)}")
    if case["scoring_path"] != "manual_override" and "ManualOverrideScorer" in active_scorers:
        failures.append("non-manual diagnosis case was scored by ManualOverrideScorer")

    expected_root = case["expected_root_cause"]
    actual_root = diagnosis_result.root_cause.value if diagnosis_result.root_cause else None
    if actual_root != expected_root:
        failures.append(f"root_cause expected {expected_root}, got {actual_root}")

    expected_pass_state = case["expected_pass_state"]
    if diagnosis_result.pass_state.value != expected_pass_state:
        failures.append(f"pass_state expected {expected_pass_state}, got {diagnosis_result.pass_state.value}")

    actual_primary = {error.value for error in diagnosis_result.primary_errors}
    missing_primary = set(case["expected_primary_errors"]) - actual_primary
    if missing_primary:
        failures.append(f"missing primary errors: {sorted(missing_primary)}; actual={sorted(actual_primary)}")

    actual_secondary = {error.value for error in diagnosis_result.secondary_errors}
    missing_secondary = set(case["expected_secondary_errors"]) - actual_secondary
    if missing_secondary:
        failures.append(f"missing secondary errors: {sorted(missing_secondary)}; actual={sorted(actual_secondary)}")

    actual_derived = {error.value for error in diagnosis_result.derived_errors}
    missing_derived = set(case["expected_derived_errors"]) - actual_derived
    if missing_derived:
        failures.append(f"missing derived errors: {sorted(missing_derived)}; actual={sorted(actual_derived)}")

    learner_text = diagnosis_result.learner_explanation.lower()
    for keyword in case["expected_learner_explanation_keywords"]:
        if keyword.lower() not in learner_text:
            failures.append(f"learner_explanation missing keyword: {keyword}")

    expected_actions = set(case["expected_recommended_actions"])
    actual_actions = {action.action_type for action in diagnosis_result.recommended_actions}
    missing_actions = expected_actions - actual_actions
    if missing_actions:
        failures.append(f"missing recommended actions: {sorted(missing_actions)}; actual={sorted(actual_actions)}")

    if not _confidence_in_band(diagnosis_result.confidence, case["expected_confidence_band"]):
        failures.append(f"confidence {diagnosis_result.confidence:.2f} outside expected band {case['expected_confidence_band']}")

    return [f"{case_id}: {failure}" for failure in failures]


def run_movement_case(case: dict[str, Any], nodes: dict[str, KnowledgeNode]) -> list[str]:
    failures: list[str] = []
    case_id = case["id"]
    question_payload = case["question"]
    node = nodes.get(question_payload["node_id"])
    if node is None:
        return [f"{case_id}: unknown node_id {question_payload['node_id']}"]

    question = build_question(question_payload, node)
    attempt_metadata = dict(case.get("attempt_metadata", {}))
    if case["scoring_path"] == "manual_override":
        expected_scores = {
            dimension: score
            for dimension, score in case.get("score_overrides", {}).items()
            if score is not None
        }
        attempt_metadata["score_overrides"] = expected_scores
        attempt_metadata["evidence_overrides"] = {
            dimension: f"Movement golden imported/manual override score for {case_id}:{dimension}."
            for dimension in expected_scores
        }

    attempt = Attempt(
        id=f"attempt_{case_id}",
        question_id=question.id,
        user_answer=case["user_answer"],
        metadata=attempt_metadata,
    )

    composite_result = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    diagnosis_result = DiagnosisEngine().diagnose_detailed(composite_result, question, attempt, node)
    rollback_decision = RollbackEngine().decide_rollback(diagnosis_result.error_vector, node)
    forward_decision = ForwardEngine().decide_forward(diagnosis_result.score_vector, diagnosis_result.error_vector, node)

    active_scorers = {result.scorer_name for result in composite_result.scorer_results if result.is_active}
    expected_scorers = EXPECTED_MOVEMENT_SCORERS_BY_PATH[case["scoring_path"]]
    missing_scorers = expected_scorers - active_scorers
    if missing_scorers:
        failures.append(f"missing expected active scorers: {sorted(missing_scorers)}; active={sorted(active_scorers)}")
    if case["scoring_path"] != "manual_override" and "ManualOverrideScorer" in active_scorers:
        failures.append("non-manual movement case was scored by ManualOverrideScorer")

    if diagnosis_result.rollback_nodes != rollback_decision.rollback_nodes or diagnosis_result.rollback_level != rollback_decision.level:
        failures.append("rollback fields do not match RollbackEngine decision")
    if diagnosis_result.forward_nodes != forward_decision.forward_nodes or diagnosis_result.forward_level != forward_decision.level:
        failures.append("forward fields do not match ForwardEngine decision")

    expected_root = case["expected_root_cause"]
    actual_root = diagnosis_result.root_cause.value if diagnosis_result.root_cause else None
    if actual_root != expected_root:
        failures.append(f"root_cause expected {expected_root}, got {actual_root}")

    if diagnosis_result.pass_state.value != case["expected_pass_state"]:
        failures.append(f"pass_state expected {case['expected_pass_state']}, got {diagnosis_result.pass_state.value}")

    if diagnosis_result.rollback_level.value != case["expected_rollback_level"]:
        failures.append(f"rollback_level expected {case['expected_rollback_level']}, got {diagnosis_result.rollback_level.value}")

    if diagnosis_result.forward_level.value != case["expected_forward_level"]:
        failures.append(f"forward_level expected {case['expected_forward_level']}, got {diagnosis_result.forward_level.value}")

    actual_actions = [action.action_type for action in diagnosis_result.recommended_actions]
    expected_action = case["expected_next_action_type"]
    if not actual_actions or actual_actions[0] != expected_action:
        failures.append(f"next action expected {expected_action}, got {actual_actions}")

    if case["should_not_return_all_prerequisites"]:
        if node.prerequisites and set(diagnosis_result.rollback_nodes) == set(node.prerequisites):
            failures.append("rollback returned all prerequisites despite should_not_return_all_prerequisites=true")

    if case["should_not_strong_forward"] and diagnosis_result.forward_level == ForwardLevel.P3_STRONG:
        failures.append("forward decision was P3 despite should_not_strong_forward=true")

    combined_nodes = set(diagnosis_result.rollback_nodes) | set(diagnosis_result.forward_nodes)
    must_include = case.get("must_include_target_node")
    if must_include and must_include not in combined_nodes:
        failures.append(f"expected movement target {must_include} not found in rollback/forward nodes {sorted(combined_nodes)}")

    must_not_include = case.get("must_not_include_node")
    if must_not_include and must_not_include in combined_nodes:
        failures.append(f"forbidden movement target {must_not_include} appeared in rollback/forward nodes")

    return [f"{case_id}: {failure}" for failure in failures]


def _confidence_in_band(confidence: float, band: str) -> bool:
    if band == "low":
        return confidence <= 0.35
    if band == "medium":
        return 0.35 < confidence < 0.75
    if band == "high":
        return confidence >= 0.75
    return False


def main() -> int:
    cases = load_golden_cases()
    diagnosis_cases = load_diagnosis_cases()
    movement_cases = load_movement_cases()
    structure_errors = validate_golden_cases(cases)
    structure_errors.extend(validate_diagnosis_cases(diagnosis_cases))
    structure_errors.extend(validate_movement_cases(movement_cases))
    if structure_errors:
        print("Golden case structure failures:")
        for error in structure_errors:
            print(f"- {error}")
        return 1

    nodes = load_nodes()
    scoring_failures: list[str] = []
    for case in cases:
        scoring_failures.extend(run_case(case, nodes))

    diagnosis_failures: list[str] = []
    for case in diagnosis_cases:
        diagnosis_failures.extend(run_diagnosis_case(case, nodes))

    movement_failures: list[str] = []
    for case in movement_cases:
        movement_failures.extend(run_movement_case(case, nodes))

    print(f"Scoring eval: {len(cases) - len(scoring_failures)}/{len(cases)} passed")
    print("Scoring path counts:")
    for path, count in sorted(scoring_path_counts(cases).items()):
        print(f"- {path}: {count}")
    print("Case category counts:")
    for category, count in sorted(category_counts(cases).items()):
        print(f"- {category}: {count}")

    print(f"Diagnosis eval: {len(diagnosis_cases) - len(diagnosis_failures)}/{len(diagnosis_cases)} passed")
    print("Diagnosis path counts:")
    for path, count in sorted(scoring_path_counts(diagnosis_cases).items()):
        print(f"- {path}: {count}")
    print("Diagnosis category counts:")
    for category, count in sorted(category_counts(diagnosis_cases).items()):
        print(f"- {category}: {count}")

    print(f"Movement eval: {len(movement_cases) - len(movement_failures)}/{len(movement_cases)} passed")
    print("Movement path counts:")
    for path, count in sorted(scoring_path_counts(movement_cases).items()):
        print(f"- {path}: {count}")
    print("Movement category counts:")
    for category, count in sorted(category_counts(movement_cases).items()):
        print(f"- {category}: {count}")

    if scoring_failures or diagnosis_failures or movement_failures:
        print("Failed cases:")
        for failure in scoring_failures + diagnosis_failures + movement_failures:
            print(f"- {failure}")
        return 1

    print("All scoring, diagnosis, and movement golden eval cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
