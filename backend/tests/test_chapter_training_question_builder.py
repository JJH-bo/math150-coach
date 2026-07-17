from __future__ import annotations

from app.challenge.chapter_candidate_builder import build_chapter_candidate_dry_run
from app.challenge.chapter_intelligent_importer import build_intelligent_chapter_draft
from app.challenge.chapter_training_question_builder import build_chapter_training_question_package
from app.challenge.models import ChallengeQuestionBank


REQUIRED_REVIEW_CHECKS = {
    "math_scope_checked",
    "macro_micro_structure_checked",
    "repair_targets_checked",
    "hidden_abilities_checked",
    "semantic_edges_checked",
    "boss_coverage_checked",
    "learner_surface_safe",
}

LOOSE_NOTES = """
Differential equations chapter: identify equation family first, then choose the method.
Separable equations require splitting x and y factors. First-order linear equations
use the integrating factor. Common mistakes include using the wrong entry trigger,
choosing a method before transforming to standard form, dropping constants, and
copying the original example without transfer to a variant.
"""


def test_training_question_builder_generates_complete_scoreable_question_bank() -> None:
    candidate = _candidate_from_intelligent_notes()

    package = build_chapter_training_question_package(candidate)

    assert package["quality_report"]["passed"] is True
    assert package["quality_report"]["grade"] == "pass"
    question_bank = ChallengeQuestionBank.model_validate(package["question_bank"])
    assert question_bank.chapter_id == "smart_question_pkg"

    kinds = {question.validator_config["question_kind"] for question in question_bank.questions}
    assert {
        "concept_judgement",
        "trigger_identification",
        "method_selection",
        "condition_transformation",
        "calculation_execution",
        "expression_standard",
        "confusion_compare",
        "transfer_variant",
        "synthesis_decomposition",
        "boss_acceptance",
    }.issubset(kinds)

    graph = candidate["challenge_graph"]
    micro_ids = {micro["id"] for micro in graph["micro_nodes"]}
    boss_ids = {boss["id"] for boss in graph["macro_challenges"]}
    micro_owners = {question.owner_id for question in question_bank.questions if question.task_type.value == "micro_node"}
    boss_owners = {question.owner_id for question in question_bank.questions if question.task_type.value == "macro_challenge"}
    assert micro_ids <= micro_owners
    assert boss_ids <= boss_owners

    for question in question_bank.questions:
        assert question.target_dimensions
        assert question.rubric is not None
        assert question.rubric.items
        assert question.expected_answer
        assert question.solution_outline
        assert question.validator_config["training_goal"]
        assert question.validator_config["repair_target_node_id"]
        assert question.validator_config["error_repair_map"]
        assert question.validator_config["false_pass_risks"]
        assert question.validator_config["variant_relation"]

    states = package["mastery_criteria"]["states"]
    assert "boss_ready" in states
    assert "stable_mastered" in states


def test_training_question_builder_uses_material_evidence_in_questions() -> None:
    generated = build_intelligent_chapter_draft(
        source_text=None,
        chapter_id="material_question_pkg",
        title="Material Aware Question Package",
        materials=[
            {
                "material_type": "markdown",
                "filename": "multi-variable.md",
                "text": (
                    "核心概念：偏导数。核心公式：dz=f_x dx+f_y dy。"
                    "核心定理：可微推出连续。典型题型：复合函数求偏导。"
                    "题眼入口：看到 z=f(u,v), u=x+y, v=xy 先画依赖链。"
                    "方法选择：链式法则。关键转化：写出中间变量依赖图。"
                    "常见错误：把偏导存在当可微。错题材料：只写最终答案，解释不足，false pass。"
                    "考研数学一得分价值：高。"
                ),
            }
        ],
        build_candidate=True,
    )
    candidate = generated["candidate_preview"]["candidate"]

    assert candidate["material_evidence"]["core_formulas"] == ["dz=f_x dx+f_y dy"]
    assert candidate["material_evidence"]["core_theorems"] == ["可微推出连续"]

    package = build_chapter_training_question_package(candidate)
    question_bank = ChallengeQuestionBank.model_validate(package["question_bank"])
    serialized_questions = "\n".join(
        field
        for question in question_bank.questions
        for field in [
            question.stem,
            question.prompt_markdown,
            question.expected_answer or "",
            question.solution_outline or "",
            str(question.validator_config),
        ]
    )

    assert "dz=f_x dx+f_y dy" in serialized_questions
    assert "可微推出连续" in serialized_questions
    assert "把偏导存在当可微" in serialized_questions
    assert "看到 z=f(u,v), u=x+y, v=xy 先画依赖链" in serialized_questions
    assert any(
        question.validator_config.get("source_material_evidence", {}).get("core_formulas") == ["dz=f_x dx+f_y dy"]
        for question in question_bank.questions
    )


def _candidate_from_intelligent_notes() -> dict:
    generated = build_intelligent_chapter_draft(
        LOOSE_NOTES,
        chapter_id="smart_question_pkg",
        title="Smart Question Package",
        build_candidate=False,
    )
    candidate = build_chapter_candidate_dry_run(
        generated["generated_markdown"],
        reviewer="question-builder-test",
        decision="approve_for_candidate",
        checklist={code: True for code in REQUIRED_REVIEW_CHECKS},
        notes="ready",
    )
    assert candidate["candidate_build_allowed"] is True
    assert candidate["candidate_quality"]["grade"] == "pass"
    return candidate["candidate"]
