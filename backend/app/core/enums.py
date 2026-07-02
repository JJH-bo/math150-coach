from __future__ import annotations

from enum import Enum


class StableStrEnum(str, Enum):
    """String enum with stable values for YAML, API, and tests."""

    def __str__(self) -> str:
        return self.value


class NodeType(StableStrEnum):
    CONCEPT = "concept"
    METHOD = "method"
    TRANSFORMATION = "transformation"
    CALCULATION = "calculation"
    SYNTHESIS = "synthesis"
    APPLICATION = "application"


class NodeStatus(StableStrEnum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"
    REVIEW = "review"


class QuestionType(StableStrEnum):
    DIAGNOSTIC = "diagnostic"
    PRACTICE = "practice"
    VARIANT = "variant"
    REVIEW = "review"
    EXAM = "exam"


class ScoreDimension(StableStrEnum):
    CONCEPT = "concept"
    TRIGGER = "trigger"
    METHOD = "method"
    TRANSFORMATION = "transformation"
    PROCESS = "process"
    CALCULATION = "calculation"
    FINAL_ANSWER = "final_answer"
    EXPRESSION = "expression"
    MIGRATION = "migration"


class ErrorType(StableStrEnum):
    CONCEPT_GAP = "concept_gap"
    TRIGGER_FAILURE = "trigger_failure"
    METHOD_ERROR = "method_error"
    TRANSFORMATION_ERROR = "transformation_error"
    PROCESS_GAP = "process_gap"
    CALCULATION_ERROR = "calculation_error"
    CONDITION_MISS = "condition_miss"
    FORMULA_MEMORY_ERROR = "formula_memory_error"
    KNOWLEDGE_CONFUSION = "knowledge_confusion"
    EXPRESSION_WEAKNESS = "expression_weakness"
    MIGRATION_FAILURE = "migration_failure"
    SYNTHESIS_FAILURE = "synthesis_failure"


class PassState(StableStrEnum):
    FAIL = "fail"
    PARTIAL_PASS = "partial_pass"
    FALSE_PASS = "false_pass"
    PASS = "pass"


class RollbackLevel(StableStrEnum):
    R1_INTERNAL = "r1_internal"
    R2_PREREQUISITE = "r2_prerequisite"
    R3_CROSS_CHAPTER = "r3_cross_chapter"
    R4_CHAPTER_FRAMEWORK = "r4_chapter_framework"


class ForwardLevel(StableStrEnum):
    P0_NONE = "p0_none"
    P1_PARTIAL = "p1_partial"
    P2_NORMAL = "p2_normal"
    P3_STRONG = "p3_strong"
