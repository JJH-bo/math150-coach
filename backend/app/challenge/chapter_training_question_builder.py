from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError

from app.challenge.models import (
    ChallengeGraph,
    ChallengeQuestionBank,
    ChallengeTaskType,
    GuideNodeKind,
    MicroNodeSpec,
    MicroNodeType,
)
from app.core.enums import ErrorType, ScoreDimension


TRAINING_QUESTION_PACKAGE_SCHEMA_VERSION = "chapter_training_question_package_v1"

ALL_SCORE_DIMENSIONS = [
    "concept",
    "trigger",
    "method",
    "transformation",
    "process",
    "calculation",
    "final_answer",
    "expression",
    "migration",
]

QUESTION_KIND_BY_MICRO_TYPE = {
    MicroNodeType.CONCEPT: "concept_judgement",
    MicroNodeType.TRIGGER: "trigger_identification",
    MicroNodeType.METHOD: "method_selection",
    MicroNodeType.TRANSFORMATION: "condition_transformation",
    MicroNodeType.CALCULATION: "calculation_execution",
    MicroNodeType.EXPRESSION: "expression_standard",
}

DEFAULT_DIMENSIONS_BY_MICRO_TYPE = {
    MicroNodeType.CONCEPT: ["concept"],
    MicroNodeType.TRIGGER: ["trigger"],
    MicroNodeType.METHOD: ["method"],
    MicroNodeType.TRANSFORMATION: ["transformation", "process"],
    MicroNodeType.CALCULATION: ["calculation", "process", "final_answer"],
    MicroNodeType.EXPRESSION: ["expression", "final_answer"],
}

ROOT_CAUSE_BY_MICRO_TYPE = {
    MicroNodeType.CONCEPT: "concept_gap",
    MicroNodeType.TRIGGER: "trigger_failure",
    MicroNodeType.METHOD: "method_error",
    MicroNodeType.TRANSFORMATION: "transformation_error",
    MicroNodeType.CALCULATION: "calculation_error",
    MicroNodeType.EXPRESSION: "expression_weakness",
}


def build_chapter_training_question_package(candidate: dict[str, Any]) -> dict[str, Any]:
    """Generate a deterministic runtime question bank from a chapter candidate."""

    graph_payload = candidate.get("challenge_graph") if isinstance(candidate, dict) else None
    if not isinstance(graph_payload, dict):
        return _blocked_package("chapter_candidate_missing_challenge_graph")

    try:
        graph = ChallengeGraph.model_validate(graph_payload)
    except (ValidationError, ValueError):
        return _blocked_package("challenge_graph_runtime_validation_failed")

    material_evidence = _material_evidence(candidate)
    question_bank = _question_bank(graph, material_evidence)
    report = _quality_report(graph, question_bank, material_evidence)
    return {
        "mode": "chapter_training_question_package",
        "question_package_schema_version": TRAINING_QUESTION_PACKAGE_SCHEMA_VERSION,
        "chapter_id": graph.chapter_id,
        "material_evidence": material_evidence,
        "question_bank": question_bank,
        "mastery_criteria": _mastery_criteria(graph),
        "quality_report": report,
    }


def _question_bank(graph: ChallengeGraph, material_evidence: dict[str, Any]) -> dict[str, Any]:
    questions: list[dict[str, Any]] = []
    for micro in graph.micro_nodes:
        questions.append(_micro_question(graph, micro, material_evidence))

    for compare in graph.compare_nodes:
        owner_id = _first_micro_id(graph, compare.node_ids)
        if owner_id:
            questions.append(
                _advisory_micro_question(
                    graph,
                    owner_id=owner_id,
                    node_id=owner_id,
                    question_id=f"{graph.chapter_id}.{_safe_token(compare.id)}.compare",
                    title=f"{compare.title} compare guard",
                    question_kind="confusion_compare",
                    dimensions=[dimension.value for dimension in compare.focus_dimensions] or ["concept", "trigger", "method"],
                    training_goal="Distinguish nearby concepts or methods before selecting a solution path.",
                    stem=f"Compare these easily confused nodes: {', '.join(compare.node_ids)}.",
                    prompt="Explain the boundary between the two options and name the signal that chooses one over the other.",
                    repair_target_node_id=owner_id,
                    variant_relation={"relation_type": "compare_guard", "source_id": compare.id, "related_node_ids": compare.node_ids},
                    material_evidence=material_evidence,
                )
            )

    for guide in graph.guide_nodes:
        if guide.kind == GuideNodeKind.BRIDGE:
            owner_id = _first_micro_id(graph, guide.related_node_ids) or _first_micro_id(graph, [guide.id])
            if owner_id:
                questions.append(
                    _advisory_micro_question(
                        graph,
                        owner_id=owner_id,
                        node_id=owner_id,
                        question_id=f"{graph.chapter_id}.{_safe_token(guide.id)}.transfer",
                        title=f"{guide.title} transfer variant",
                        question_kind="transfer_variant",
                        dimensions=[dimension.value for dimension in guide.focus_dimensions] or ["migration", "method"],
                        training_goal="Check whether the learner can transfer the method beyond the original surface form.",
                        stem=f"Use the same ability in a variant setting related to {guide.title}.",
                        prompt="State what changes, what stays invariant, and which method signal transfers.",
                        repair_target_node_id=owner_id,
                        variant_relation={"relation_type": "transfer_node", "source_id": guide.id, "related_node_ids": guide.related_node_ids},
                        material_evidence=material_evidence,
                    )
                )
            continue
        if guide.kind == GuideNodeKind.BOSS_GATE:
            challenge_id = _first_challenge_id(graph, guide.related_node_ids)
            challenge = _challenge_by_id(graph, challenge_id) if challenge_id else None
            if challenge:
                questions.append(_boss_question(graph, challenge, question_kind="synthesis_decomposition", source_id=guide.id, material_evidence=material_evidence))

    for challenge in graph.macro_challenges:
        questions.append(_boss_question(graph, challenge, question_kind="boss_acceptance", source_id=challenge.id, material_evidence=material_evidence))

    return {
        "chapter_id": graph.chapter_id,
        "questions": questions,
    }


def _micro_question(graph: ChallengeGraph, micro: MicroNodeSpec, material_evidence: dict[str, Any]) -> dict[str, Any]:
    question_kind = QUESTION_KIND_BY_MICRO_TYPE[micro.type]
    dimensions = [dimension.value for dimension in micro.default_dimensions] or DEFAULT_DIMENSIONS_BY_MICRO_TYPE[micro.type]
    repair_target = _repair_target_for_micro(graph, micro)
    evidence_slice = _evidence_for_micro_type(material_evidence, micro.type)
    context = _material_context_sentence(evidence_slice)
    return _base_question(
        question_id=f"{graph.chapter_id}.{_safe_token(micro.id)}.{question_kind}",
        owner_id=micro.id,
        task_type=ChallengeTaskType.MICRO_NODE.value,
        node_id=micro.id,
        title=f"{micro.title} training check",
        stem=_join_sentences(f"Target ability: {micro.title}.", context),
        prompt=_join_sentences(
            f"Answer this {question_kind} task. Give the conclusion, the trigger evidence, and the minimal reasoning chain.",
            _material_prompt_instruction(evidence_slice),
        ),
        dimensions=dimensions,
        question_kind=question_kind,
        training_goal=f"Train {micro.type.value} ability for {micro.title}.",
        repair_target_node_id=repair_target,
        variant_relation={"relation_type": "base_micro_training", "source_node_id": micro.id, "material_evidence_keys": sorted(evidence_slice)},
        expected_answer=_join_sentences(f"Correctly identify and justify {micro.title}.", _expected_material_answer(evidence_slice)),
        solution_outline=_join_sentences(
            f"Name the ability, cite the decisive evidence, execute the required step, and state the final conclusion for {micro.title}.",
            _material_solution_outline(evidence_slice),
        ),
        difficulty="standard",
        material_evidence=evidence_slice,
    )


def _advisory_micro_question(
    graph: ChallengeGraph,
    *,
    owner_id: str,
    node_id: str,
    question_id: str,
    title: str,
    question_kind: str,
    dimensions: list[str],
    training_goal: str,
    stem: str,
    prompt: str,
    repair_target_node_id: str,
    variant_relation: dict[str, Any],
    material_evidence: dict[str, Any],
) -> dict[str, Any]:
    evidence_slice = _evidence_for_question_kind(material_evidence, question_kind)
    return _base_question(
        question_id=question_id,
        owner_id=owner_id,
        task_type=ChallengeTaskType.MICRO_NODE.value,
        node_id=node_id,
        title=title,
        stem=_join_sentences(stem, _material_context_sentence(evidence_slice)),
        prompt=_join_sentences(prompt, _material_prompt_instruction(evidence_slice)),
        dimensions=dimensions,
        question_kind=question_kind,
        training_goal=training_goal,
        repair_target_node_id=repair_target_node_id,
        variant_relation=variant_relation,
        expected_answer=_join_sentences("A complete answer states the distinguishing signal and applies it to the variant.", _expected_material_answer(evidence_slice)),
        solution_outline=_join_sentences("Compare the candidate signals, choose the correct path, and explain why the other path is not valid here.", _material_solution_outline(evidence_slice)),
        difficulty="standard",
        material_evidence=evidence_slice,
    )


def _boss_question(
    graph: ChallengeGraph,
    challenge: Any,
    *,
    question_kind: str,
    source_id: str,
    material_evidence: dict[str, Any],
) -> dict[str, Any]:
    dimensions = [dimension.value for dimension in challenge.target_dimensions] or ALL_SCORE_DIMENSIONS
    repair_target = _first_micro_id(graph, challenge.covers_micro_nodes) or challenge.covers_micro_nodes[0]
    evidence_slice = _evidence_for_boss(material_evidence)
    return _base_question(
        question_id=f"{graph.chapter_id}.{_safe_token(source_id)}.{question_kind}",
        owner_id=challenge.id,
        task_type=ChallengeTaskType.MACRO_CHALLENGE.value,
        node_id=challenge.id,
        title=f"{challenge.title} {question_kind}",
        stem=_join_sentences(f"Integrated Boss task for {challenge.title}.", _material_context_sentence(evidence_slice)),
        prompt=_join_sentences(
            "Solve the integrated task. Show concept, trigger, method, transformation, process, calculation, final answer, expression, and transfer judgment.",
            _material_prompt_instruction(evidence_slice),
        ),
        dimensions=_dedupe([*dimensions, *ALL_SCORE_DIMENSIONS]),
        question_kind=question_kind,
        training_goal="Verify integrated mastery across the MacroNode rather than a local MicroNode only.",
        repair_target_node_id=repair_target,
        variant_relation={"relation_type": question_kind, "source_id": source_id, "covered_micro_nodes": challenge.covers_micro_nodes, "material_evidence_keys": sorted(evidence_slice)},
        expected_answer=_join_sentences("A Boss-level answer gives the complete reasoning chain and a normalized final conclusion.", _expected_material_answer(evidence_slice)),
        solution_outline=_join_sentences(
            "Classify the problem, choose the method, transform conditions, execute calculation, normalize expression, and justify transfer or boundary decisions.",
            _material_solution_outline(evidence_slice),
        ),
        difficulty="boss",
        material_evidence=evidence_slice,
    )


def _base_question(
    *,
    question_id: str,
    owner_id: str,
    task_type: str,
    node_id: str,
    title: str,
    stem: str,
    prompt: str,
    dimensions: list[str],
    question_kind: str,
    training_goal: str,
    repair_target_node_id: str,
    variant_relation: dict[str, Any],
    expected_answer: str,
    solution_outline: str,
    difficulty: str,
    material_evidence: dict[str, Any],
) -> dict[str, Any]:
    clean_dimensions = _dedupe([dimension for dimension in dimensions if dimension in ALL_SCORE_DIMENSIONS])
    if not clean_dimensions:
        clean_dimensions = ["concept"]
    return {
        "id": question_id,
        "owner_id": owner_id,
        "task_type": task_type,
        "node_id": node_id,
        "title": title,
        "stem": stem,
        "prompt_markdown": prompt,
        "answer_format": "text_with_reasoning",
        "response_step_mode": "required",
        "difficulty": difficulty,
        "hints_public": ["Write the evidence chain, not only the final answer."],
        "target_dimensions": clean_dimensions,
        "target_dimension_mode": "override",
        "expected_answer": expected_answer,
        "answer_aliases": [title],
        "rubric": _rubric(question_id, clean_dimensions, question_kind, material_evidence),
        "solution_outline": solution_outline,
        "validator_config": {
            "generated_by": TRAINING_QUESTION_PACKAGE_SCHEMA_VERSION,
            "question_kind": question_kind,
            "training_goal": training_goal,
            "necessary_process": _necessary_process(clean_dimensions),
            "common_errors": _dedupe([*_common_errors(clean_dimensions), *_material_list(material_evidence, "common_errors")]),
            "false_pass_risks": _dedupe([*_false_pass_risks(clean_dimensions), *_material_list(material_evidence, "false_pass_risks")]),
            "repair_target_node_id": repair_target_node_id,
            "error_repair_map": _question_error_repair_map(clean_dimensions, repair_target_node_id),
            "variant_relation": variant_relation,
            "mastery_signal": "micro_evidence" if task_type == ChallengeTaskType.MICRO_NODE.value else "boss_acceptance",
            "source_material_evidence": material_evidence,
        },
    }


def _rubric(question_id: str, dimensions: list[str], question_kind: str, material_evidence: dict[str, Any]) -> dict[str, Any]:
    items = []
    for dimension in dimensions:
        material_keywords = _material_keywords_for_dimension(material_evidence, dimension)
        items.append(
            {
                "id": f"{_safe_token(question_id)}.{dimension}",
                "description": f"Evidence for {dimension} in {question_kind}.",
                "target_dimensions": [dimension],
                "required_keywords": _dedupe([*_keywords_for_dimension(dimension), *material_keywords]),
                "expected_patterns": _material_patterns_for_dimension(material_evidence, dimension),
                "weight": 1.0,
                "required": True,
                "partial_credit": True,
                "partial_score": 60,
                "evidence_on_hit": f"The response gives usable {dimension} evidence.",
                "evidence_on_miss": f"The response lacks enough {dimension} evidence.",
            }
        )
    return {
        "items": items,
        "dimension_weights": {dimension: 1.0 for dimension in dimensions},
        "merge_policy": {
            "strategy": "weighted_by_confidence",
            "manual_override_first": True,
            "missing_if_no_signal": True,
        },
    }


def _quality_report(graph: ChallengeGraph, question_bank: dict[str, Any], material_evidence: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    questions = question_bank["questions"]
    micro_ids = {micro.id for micro in graph.micro_nodes}
    challenge_ids = {challenge.id for challenge in graph.macro_challenges}
    micro_owners = {question["owner_id"] for question in questions if question["task_type"] == ChallengeTaskType.MICRO_NODE.value}
    challenge_owners = {question["owner_id"] for question in questions if question["task_type"] == ChallengeTaskType.MACRO_CHALLENGE.value}
    missing_micro = sorted(micro_ids - micro_owners)
    missing_challenges = sorted(challenge_ids - challenge_owners)
    if missing_micro:
        errors.append(_issue("missing_micro_node_questions", ",".join(missing_micro)))
    if missing_challenges:
        errors.append(_issue("missing_macro_challenge_questions", ",".join(missing_challenges)))
    for question in questions:
        if not question.get("target_dimensions"):
            errors.append(_issue("question_missing_dimensions", question["id"]))
        if not question.get("rubric", {}).get("items"):
            errors.append(_issue("question_missing_rubric", question["id"]))
        config = question.get("validator_config", {})
        for field in ["training_goal", "repair_target_node_id", "error_repair_map", "false_pass_risks", "variant_relation"]:
            if not config.get(field):
                errors.append(_issue(f"question_missing_{field}", question["id"]))
        if material_evidence and not config.get("source_material_evidence"):
            errors.append(_issue("question_missing_source_material_evidence", question["id"]))
    kinds = sorted({question.get("validator_config", {}).get("question_kind", "") for question in questions})
    if graph.compare_nodes and "confusion_compare" not in kinds:
        warnings.append(_issue("compare_guard_question_missing", "compare_nodes", severity="warning"))
    if any(guide.kind == GuideNodeKind.BRIDGE for guide in graph.guide_nodes) and "transfer_variant" not in kinds:
        warnings.append(_issue("transfer_question_missing", "guide_nodes", severity="warning"))
    if any(guide.kind == GuideNodeKind.BOSS_GATE for guide in graph.guide_nodes) and "synthesis_decomposition" not in kinds:
        warnings.append(_issue("synthesis_question_missing", "guide_nodes", severity="warning"))
    try:
        ChallengeQuestionBank.model_validate(question_bank)
    except ValidationError as exc:
        errors.append(_issue("question_bank_model_invalid", str(exc)))
    return {
        "passed": not errors,
        "grade": "pass" if not errors and not warnings else "warn" if not errors else "fail",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "coverage": {
            "micro_nodes_total": len(micro_ids),
            "micro_nodes_with_questions": len(micro_ids & micro_owners),
            "macro_challenges_total": len(challenge_ids),
            "macro_challenges_with_questions": len(challenge_ids & challenge_owners),
            "question_count": len(questions),
            "question_kinds": kinds,
            "rubric_dimensions": sorted({dimension for question in questions for dimension in question.get("target_dimensions", [])}),
            "material_evidence_categories": sorted(material_evidence),
        },
    }


def _mastery_criteria(graph: ChallengeGraph) -> dict[str, Any]:
    states = [
        "not_started",
        "available",
        "active",
        "evidence_insufficient",
        "partial_mastery",
        "false_pass",
        "weak",
        "repaired",
        "boss_ready",
        "boss_failed",
        "mastered",
        "review_due",
        "stable_mastered",
    ]
    return {
        "schema_version": "chapter_mastery_criteria_v1",
        "states": states,
        "micro_node_rule": "MicroNode pass provides local evidence only.",
        "macro_node_rule": "Boss/MacroChallenge pass is required before MacroNode mastery.",
        "boss_ready_rule": "All covered MicroNodes need pass evidence before Boss should be treated as ready.",
        "stable_mastered_rule": "Mastered plus review evidence and no recent weak dimensions.",
        "node_criteria": {
            **{micro.id: {"required_local_state": "repaired_or_mastered", "boss_required": False} for micro in graph.micro_nodes},
            **{challenge.id: {"required_dimensions": ALL_SCORE_DIMENSIONS, "boss_required": True} for challenge in graph.macro_challenges},
        },
    }


def _material_evidence(candidate: dict[str, Any]) -> dict[str, Any]:
    raw = candidate.get("material_evidence") if isinstance(candidate, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {
        key: value
        for key, value in raw.items()
        if value
    }


def _evidence_for_micro_type(material_evidence: dict[str, Any], micro_type: MicroNodeType) -> dict[str, Any]:
    key_map = {
        MicroNodeType.CONCEPT: ["core_concepts", "core_theorems", "common_errors", "math1_value"],
        MicroNodeType.TRIGGER: ["typical_problem_types", "entry_triggers", "confusions", "common_errors"],
        MicroNodeType.METHOD: ["method_choices", "entry_triggers", "confusions", "common_errors"],
        MicroNodeType.TRANSFORMATION: ["key_transformations", "prerequisites", "common_errors"],
        MicroNodeType.CALCULATION: ["core_formulas", "key_transformations", "common_errors", "false_pass_risks"],
        MicroNodeType.EXPRESSION: ["core_formulas", "core_theorems", "common_errors", "false_pass_risks"],
    }
    return _pick_material_evidence(material_evidence, key_map[micro_type])


def _evidence_for_question_kind(material_evidence: dict[str, Any], question_kind: str) -> dict[str, Any]:
    key_map = {
        "confusion_compare": ["confusions", "common_errors", "core_concepts", "core_theorems"],
        "transfer_variant": ["method_choices", "key_transformations", "downstream_uses", "false_pass_risks"],
        "synthesis_decomposition": ["core_concepts", "core_formulas", "core_theorems", "entry_triggers", "method_choices", "key_transformations", "common_errors"],
    }
    return _pick_material_evidence(material_evidence, key_map.get(question_kind, []))


def _evidence_for_boss(material_evidence: dict[str, Any]) -> dict[str, Any]:
    return _pick_material_evidence(
        material_evidence,
        [
            "chapter_topic",
            "subject_area",
            "core_concepts",
            "core_formulas",
            "core_theorems",
            "typical_problem_types",
            "entry_triggers",
            "method_choices",
            "key_transformations",
            "confusions",
            "common_errors",
            "prerequisites",
            "downstream_uses",
            "math1_value",
            "false_pass_risks",
        ],
    )


def _pick_material_evidence(material_evidence: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    picked = {
        key: material_evidence[key]
        for key in keys
        if material_evidence.get(key)
    }
    return picked or material_evidence


def _material_context_sentence(material_evidence: dict[str, Any]) -> str:
    if not material_evidence:
        return ""
    parts = []
    if formulas := _material_list(material_evidence, "core_formulas"):
        parts.append(f"Use source formula: {'; '.join(formulas[:2])}")
    if theorems := _material_list(material_evidence, "core_theorems"):
        parts.append(f"Use source theorem: {'; '.join(theorems[:2])}")
    if triggers := _material_list(material_evidence, "entry_triggers"):
        parts.append(f"Entry signal from material: {'; '.join(triggers[:2])}")
    if methods := _material_list(material_evidence, "method_choices"):
        parts.append(f"Method from material: {'; '.join(methods[:2])}")
    if transformations := _material_list(material_evidence, "key_transformations"):
        parts.append(f"Required transformation: {'; '.join(transformations[:2])}")
    if errors := _material_list(material_evidence, "common_errors"):
        parts.append(f"Common error to guard: {'; '.join(errors[:2])}")
    return "Source material evidence: " + "; ".join(parts) + "." if parts else ""


def _material_prompt_instruction(material_evidence: dict[str, Any]) -> str:
    if not material_evidence:
        return ""
    return "Your answer must explicitly use the source-material evidence named in the stem and explain why it applies."


def _expected_material_answer(material_evidence: dict[str, Any]) -> str:
    if not material_evidence:
        return ""
    values = _flat_material_values(material_evidence)
    return f"Must cite source-material evidence such as: {'; '.join(values[:4])}." if values else ""


def _material_solution_outline(material_evidence: dict[str, Any]) -> str:
    if not material_evidence:
        return ""
    outline = []
    if triggers := _material_list(material_evidence, "entry_triggers"):
        outline.append(f"identify the entry trigger ({triggers[0]})")
    if methods := _material_list(material_evidence, "method_choices"):
        outline.append(f"choose the method ({methods[0]})")
    if transformations := _material_list(material_evidence, "key_transformations"):
        outline.append(f"perform the transformation ({transformations[0]})")
    if formulas := _material_list(material_evidence, "core_formulas"):
        outline.append(f"use the formula ({formulas[0]})")
    if theorems := _material_list(material_evidence, "core_theorems"):
        outline.append(f"state the theorem boundary ({theorems[0]})")
    if errors := _material_list(material_evidence, "common_errors"):
        outline.append(f"avoid the known error ({errors[0]})")
    return "Material-specific path: " + ", ".join(outline) + "." if outline else ""


def _material_keywords_for_dimension(material_evidence: dict[str, Any], dimension: str) -> list[str]:
    key_map = {
        "concept": ["core_concepts", "core_theorems"],
        "trigger": ["entry_triggers", "typical_problem_types"],
        "method": ["method_choices"],
        "transformation": ["key_transformations"],
        "process": ["entry_triggers", "method_choices", "key_transformations"],
        "calculation": ["core_formulas"],
        "final_answer": ["core_formulas"],
        "expression": ["core_formulas", "core_theorems"],
        "migration": ["downstream_uses", "method_choices"],
    }
    values = []
    for key in key_map.get(dimension, []):
        values.extend(_material_list(material_evidence, key))
    return values[:4]


def _material_patterns_for_dimension(material_evidence: dict[str, Any], dimension: str) -> list[str]:
    if dimension not in {"calculation", "final_answer", "expression"}:
        return []
    return [re.escape(value) for value in _material_list(material_evidence, "core_formulas")[:2]]


def _flat_material_values(material_evidence: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for value in material_evidence.values():
        if isinstance(value, list):
            values.extend(str(item) for item in value if str(item).strip())
        elif isinstance(value, dict):
            values.extend(str(item) for item in value.values() if str(item).strip())
        elif str(value).strip():
            values.append(str(value))
    return _dedupe(values)


def _material_list(material_evidence: dict[str, Any], key: str) -> list[str]:
    value = material_evidence.get(key)
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, dict):
        return [str(item) for item in value.values() if str(item).strip()]
    if value:
        return [str(value)]
    return []


def _join_sentences(*parts: str) -> str:
    clean = [part.strip() for part in parts if part and part.strip()]
    return " ".join(clean)


def _repair_target_for_micro(graph: ChallengeGraph, micro: MicroNodeSpec) -> str:
    preferred_root = ROOT_CAUSE_BY_MICRO_TYPE[micro.type]
    for root_cause, target in graph.error_to_micro_mapping.items():
        raw_root = root_cause.value if isinstance(root_cause, ErrorType) else str(root_cause)
        if raw_root == preferred_root:
            return target
    return micro.id


def _question_error_repair_map(dimensions: list[str], repair_target_node_id: str) -> dict[str, str]:
    roots = []
    if "concept" in dimensions:
        roots.append("concept_gap")
    if "trigger" in dimensions:
        roots.append("trigger_failure")
    if "method" in dimensions:
        roots.append("method_error")
    if "transformation" in dimensions:
        roots.append("transformation_error")
    if "calculation" in dimensions or "final_answer" in dimensions:
        roots.append("calculation_error")
    if "expression" in dimensions:
        roots.append("expression_weakness")
    if "migration" in dimensions:
        roots.append("migration_failure")
    if "process" in dimensions:
        roots.append("process_gap")
    return {root: repair_target_node_id for root in _dedupe(roots)}


def _necessary_process(dimensions: list[str]) -> list[str]:
    steps = ["state the tested ability", "cite evidence from the problem statement"]
    if "method" in dimensions or "transformation" in dimensions:
        steps.append("justify the selected method before calculation")
    if "calculation" in dimensions or "final_answer" in dimensions:
        steps.append("show calculation steps and final normalization")
    if "expression" in dimensions:
        steps.append("write the result in accepted mathematical form")
    if "migration" in dimensions:
        steps.append("explain what transfers and what changes in the variant")
    return steps


def _common_errors(dimensions: list[str]) -> list[str]:
    errors = []
    if "concept" in dimensions:
        errors.append("keyword_only_concept")
    if "trigger" in dimensions:
        errors.append("wrong_entry_signal")
    if "method" in dimensions:
        errors.append("method_name_without_condition")
    if "transformation" in dimensions:
        errors.append("standard_form_not_reached")
    if "calculation" in dimensions:
        errors.append("local_calculation_slip")
    if "final_answer" in dimensions:
        errors.append("final_answer_without_process")
    if "expression" in dimensions:
        errors.append("nonstandard_expression")
    if "migration" in dimensions:
        errors.append("surface_copy_without_transfer")
    return errors or ["evidence_insufficient"]


def _false_pass_risks(dimensions: list[str]) -> list[str]:
    risks = ["correct_final_answer_without_required_evidence"]
    if "trigger" in dimensions:
        risks.append("right_method_guess_without_trigger")
    if "method" in dimensions:
        risks.append("method_keyword_without_execution")
    if "calculation" in dimensions:
        risks.append("answer_matches_but_calculation_unshown")
    if "expression" in dimensions:
        risks.append("equivalent_answer_with_weak_form")
    return risks


def _keywords_for_dimension(dimension: str) -> list[str]:
    return {
        "concept": ["concept", "definition", "why"],
        "trigger": ["signal", "condition", "recognize"],
        "method": ["method", "choose", "because"],
        "transformation": ["transform", "standard", "condition"],
        "process": ["step", "therefore", "because"],
        "calculation": ["calculate", "compute", "="],
        "final_answer": ["answer", "final", "conclusion"],
        "expression": ["form", "constant", "domain"],
        "migration": ["variant", "transfer", "changes"],
    }.get(dimension, [dimension])


def _first_micro_id(graph: ChallengeGraph, node_ids: list[str]) -> str | None:
    micro_ids = {micro.id for micro in graph.micro_nodes}
    for node_id in node_ids:
        if node_id in micro_ids:
            return node_id
    return None


def _first_challenge_id(graph: ChallengeGraph, node_ids: list[str]) -> str | None:
    challenge_ids = {challenge.id for challenge in graph.macro_challenges}
    for node_id in node_ids:
        if node_id in challenge_ids:
            return node_id
    return None


def _challenge_by_id(graph: ChallengeGraph, challenge_id: str | None) -> Any | None:
    for challenge in graph.macro_challenges:
        if challenge.id == challenge_id:
            return challenge
    return None


def _blocked_package(reason: str) -> dict[str, Any]:
    return {
        "mode": "chapter_training_question_package",
        "question_package_schema_version": TRAINING_QUESTION_PACKAGE_SCHEMA_VERSION,
        "chapter_id": None,
        "question_bank": None,
        "mastery_criteria": None,
        "quality_report": {
            "passed": False,
            "grade": "fail",
            "error_count": 1,
            "warning_count": 0,
            "errors": [_issue(reason, "candidate")],
            "warnings": [],
            "coverage": {},
        },
    }


def _issue(code: str, target: str, *, severity: str = "error") -> dict[str, str]:
    return {
        "code": code,
        "target": target,
        "severity": severity,
    }


def _safe_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._-")
    return token or "item"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
