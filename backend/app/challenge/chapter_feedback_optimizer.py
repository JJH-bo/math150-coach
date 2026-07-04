from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from app.challenge.chapter_candidate_builder import deterministic_content_hash
from app.challenge.models import ChallengeQuestionBank


FEEDBACK_OPTIMIZATION_SCHEMA_VERSION = "chapter_feedback_optimization_v1"
NON_PASS_STATES = {"fail", "false_pass", "partial_pass"}


def build_chapter_feedback_optimization_dry_run(
    candidate: dict[str, Any],
    *,
    question_package: dict[str, Any],
    attempt_records: list[dict[str, Any]],
    analyst: str,
    min_sample_size: int = 3,
) -> dict[str, Any]:
    """Analyze training feedback and propose chapter package revisions."""

    question_bank = _question_bank(question_package)
    question_index = {question["id"]: question for question in question_bank.get("questions", [])}
    grouped = _group_attempts(attempt_records)
    signals: list[dict[str, Any]] = []

    for question_id, attempts in grouped.items():
        question = question_index.get(question_id, {})
        if len(attempts) < min_sample_size:
            continue
        signals.extend(_signals_for_question(question_id, question, attempts))

    signals.extend(_hidden_ability_signals(candidate, grouped))
    signals = _dedupe_signals(signals)
    plan = _regeneration_plan(signals)
    grade = _grade(signals)
    status = "stable" if grade == "pass" else "needs_revision"

    return {
        "mode": "chapter_feedback_optimization_dry_run",
        "workflow_stage": "chapter_feedback_optimization",
        "feedback_schema_version": FEEDBACK_OPTIMIZATION_SCHEMA_VERSION,
        "dry_run_only": True,
        "formal_publish_allowed": False,
        "feedback_record": {
            "record_id": _record_id(candidate, question_package, attempt_records),
            "chapter_id": candidate.get("chapter_id") or question_bank.get("chapter_id"),
            "analyst": analyst,
            "status": status,
            "attempt_count": len(attempt_records),
            "question_count_with_feedback": len(grouped),
            "min_sample_size": min_sample_size,
        },
        "quality_gate": {
            "grade": grade,
            "error_count": sum(1 for signal in signals if signal["severity"] == "error"),
            "warning_count": sum(1 for signal in signals if signal["severity"] == "warning"),
            "feedback_quality_passed": grade == "pass",
            "formal_publish_allowed": False,
        },
        "revision_signals": signals,
        "regeneration_plan": plan,
        "recommended_correction_operations": _recommended_operations(signals),
        "question_feedback_summary": _question_feedback_summary(grouped, question_index),
        "required_next_action": "start_correction_dry_run_for_feedback_targets" if signals else "keep_collecting_training_feedback",
    }


def _question_bank(question_package: dict[str, Any]) -> dict[str, Any]:
    raw = question_package.get("question_bank") if isinstance(question_package, dict) else None
    if not isinstance(raw, dict):
        return {"chapter_id": None, "questions": []}
    try:
        return ChallengeQuestionBank.model_validate(raw).model_dump(mode="json")
    except Exception:
        return raw


def _group_attempts(attempt_records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for attempt in attempt_records:
        question_id = str(attempt.get("question_id") or "")
        if question_id:
            grouped[question_id].append(attempt)
    return dict(grouped)


def _signals_for_question(question_id: str, question: dict[str, Any], attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pass_states = Counter(_normal_pass_state(attempt.get("pass_state")) for attempt in attempts)
    root_causes = Counter(str(attempt.get("root_cause") or "") for attempt in attempts if attempt.get("root_cause"))
    non_pass_count = sum(pass_states[state] for state in NON_PASS_STATES)
    false_pass_rate = pass_states["false_pass"] / len(attempts)
    pass_rate = pass_states["pass"] / len(attempts)
    question_kind = _question_kind(question, attempts)
    node_id = _node_id(question, attempts)
    signals: list[dict[str, Any]] = []

    if pass_rate <= 0.25 and non_pass_count >= 3:
        signals.append(
            _signal(
                "question_pass_rate_anomaly",
                "warning",
                question_id,
                node_id,
                question_kind,
                attempts,
                f"Pass rate is {pass_rate:.2f} across {len(attempts)} attempts.",
                ["questions.yaml", "rubric"],
            )
        )
    if false_pass_rate >= 0.5:
        signals.append(
            _signal(
                "false_pass_excess",
                "error",
                question_id,
                node_id,
                question_kind,
                attempts,
                f"False-pass rate is {false_pass_rate:.2f}.",
                ["rubric", "validator_config", "false_pass_risks"],
            )
        )
    if len([root for root in root_causes if root]) >= 3:
        signals.append(
            _signal(
                "diagnosis_instability",
                "error",
                question_id,
                node_id,
                question_kind,
                attempts,
                f"Same question produced multiple root causes: {', '.join(sorted(root_causes))}.",
                ["rubric", "error_repair_map"],
            )
        )
    if any(attempt.get("evidence_gaps") or attempt.get("weak_dimensions") for attempt in attempts):
        signals.append(
            _signal(
                "rubric_evidence_insufficient",
                "warning",
                question_id,
                node_id,
                question_kind,
                attempts,
                "Attempts repeatedly expose evidence gaps or weak dimensions.",
                ["rubric", "questions.yaml"],
            )
        )
    if question_kind == "confusion_compare" and _root_rate(root_causes, "knowledge_confusion") >= 0.5:
        signals.append(
            _signal(
                "compare_guard_not_blocking_confusion",
                "error",
                question_id,
                node_id,
                question_kind,
                attempts,
                "CompareGuard feedback still clusters as knowledge_confusion.",
                ["compare_guard", "questions.yaml", "rubric"],
            )
        )
    if question_kind == "transfer_variant" and non_pass_count >= 2:
        signals.append(
            _signal(
                "migration_variant_weak",
                "error",
                question_id,
                node_id,
                question_kind,
                attempts,
                "Transfer variant attempts do not show stable migration evidence.",
                ["transfer_node", "questions.yaml", "rubric"],
            )
        )
    if question_kind in {"boss_acceptance", "synthesis_decomposition"} and non_pass_count >= 2:
        signals.append(
            _signal(
                "boss_feedback_gap",
                "error",
                question_id,
                node_id,
                question_kind,
                attempts,
                "Boss or synthesis feedback shows the integrated check is not yet reliable.",
                ["boss", "mastery_criteria", "questions.yaml", "rubric"],
            )
        )
    repair_targets = Counter(str(attempt.get("repair_target_node_id") or "") for attempt in attempts if attempt.get("repair_target_node_id"))
    if repair_targets and max(repair_targets.values()) >= 3 and non_pass_count >= 3:
        signals.append(
            _signal(
                "repair_path_ineffective",
                "error",
                question_id,
                node_id,
                question_kind,
                attempts,
                f"Repeated non-pass attempts keep routing to {repair_targets.most_common(1)[0][0]}.",
                ["error_repair_map", "repair_questions", "rubric"],
            )
        )
    return signals


def _hidden_ability_signals(candidate: dict[str, Any], grouped: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    graph = candidate.get("challenge_graph", {}) if isinstance(candidate, dict) else {}
    atom_targets = {
        atom.get("micro_node_id")
        for atom in graph.get("atom_nodes", [])
        if isinstance(atom, dict) and atom.get("micro_node_id")
    }
    signals: list[dict[str, Any]] = []
    for question_id, attempts in grouped.items():
        repair_targets = {
            str(attempt.get("repair_target_node_id") or attempt.get("node_id") or "")
            for attempt in attempts
            if _normal_pass_state(attempt.get("pass_state")) in NON_PASS_STATES
        }
        unsupported = sorted(target for target in repair_targets if target and target not in atom_targets)
        if unsupported:
            signals.append(
                _signal(
                    "hidden_ability_unsupported",
                    "error",
                    question_id,
                    unsupported[0],
                    str(attempts[0].get("question_kind") or ""),
                    attempts,
                    f"Repair target lacks HiddenAbility support: {', '.join(unsupported)}.",
                    ["hidden_ability", "semantic_edges", "rubric"],
                )
            )
    return signals


def _signal(
    code: str,
    severity: str,
    question_id: str,
    node_id: str,
    question_kind: str,
    attempts: list[dict[str, Any]],
    rationale: str,
    assets: list[str],
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "target_kind": "question",
        "target_id": question_id,
        "node_id": node_id,
        "question_kind": question_kind,
        "attempt_count": len(attempts),
        "rationale": rationale,
        "observed_pass_states": dict(Counter(_normal_pass_state(attempt.get("pass_state")) for attempt in attempts)),
        "observed_root_causes": dict(Counter(str(attempt.get("root_cause") or "") for attempt in attempts if attempt.get("root_cause"))),
        "affected_assets": assets,
    }


def _regeneration_plan(signals: list[dict[str, Any]]) -> dict[str, Any]:
    question_ids = sorted({signal["target_id"] for signal in signals if signal.get("target_id")})
    node_ids = sorted({signal["node_id"] for signal in signals if signal.get("node_id")})
    assets = sorted({asset for signal in signals for asset in signal.get("affected_assets", [])})
    if signals:
        assets = sorted({*assets, "candidate_quality_report"})
    return {
        "question_ids": question_ids,
        "node_ids": node_ids,
        "assets": assets,
        "can_start_correction_dry_run": bool(signals),
    }


def _recommended_operations(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for signal in signals:
        node_id = signal.get("node_id")
        if not node_id:
            continue
        operations.append(
            {
                "requires_editor_value": True,
                "reason": signal["code"],
                "operation_template": {
                    "op": "replace",
                    "target": "micro_node",
                    "id": node_id,
                    "field": "description",
                    "value": f"Needs revision because feedback signal {signal['code']} was observed.",
                },
            }
        )
    return operations


def _question_feedback_summary(grouped: dict[str, list[dict[str, Any]]], question_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for question_id, attempts in sorted(grouped.items()):
        pass_states = Counter(_normal_pass_state(attempt.get("pass_state")) for attempt in attempts)
        summary.append(
            {
                "question_id": question_id,
                "node_id": _node_id(question_index.get(question_id, {}), attempts),
                "question_kind": _question_kind(question_index.get(question_id, {}), attempts),
                "attempt_count": len(attempts),
                "pass_states": dict(pass_states),
                "pass_rate": pass_states["pass"] / len(attempts),
                "false_pass_rate": pass_states["false_pass"] / len(attempts),
            }
        )
    return summary


def _dedupe_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    result = []
    for signal in signals:
        key = (signal["code"], signal["target_id"])
        if key in seen:
            continue
        seen.add(key)
        result.append(signal)
    return result


def _grade(signals: list[dict[str, Any]]) -> str:
    if any(signal["severity"] == "error" for signal in signals):
        return "fail"
    if signals:
        return "warn"
    return "pass"


def _record_id(candidate: dict[str, Any], question_package: dict[str, Any], attempt_records: list[dict[str, Any]]) -> str:
    chapter_id = str(candidate.get("chapter_id") or question_package.get("chapter_id") or "chapter")
    digest = deterministic_content_hash(
        {
            "candidate_hash": deterministic_content_hash(candidate),
            "attempt_hash": deterministic_content_hash(attempt_records),
        }
    ).removeprefix("sha256:")[:12]
    return f"{chapter_id}.feedback.{digest}"


def _normal_pass_state(value: Any) -> str:
    return str(value or "").strip().lower()


def _question_kind(question: dict[str, Any], attempts: list[dict[str, Any]]) -> str:
    config = question.get("validator_config", {}) if isinstance(question, dict) else {}
    return str(config.get("question_kind") or attempts[0].get("question_kind") or "")


def _node_id(question: dict[str, Any], attempts: list[dict[str, Any]]) -> str:
    if isinstance(question, dict) and question.get("node_id"):
        return str(question["node_id"])
    return str(attempts[0].get("node_id") or attempts[0].get("repair_target_node_id") or "")


def _root_rate(root_causes: Counter[str], root_cause: str) -> float:
    total = sum(root_causes.values())
    if total == 0:
        return 0
    return root_causes[root_cause] / total
