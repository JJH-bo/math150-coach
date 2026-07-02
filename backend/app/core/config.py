from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import ErrorType, RollbackLevel, ScoreDimension


@dataclass(frozen=True)
class EngineConfig:
    primary_error_threshold: float = 0.7
    secondary_error_threshold: float = 0.4
    default_pass_overall: float = 80.0
    default_required_dimension_min: float = 70.0
    false_pass_final_answer_min: float = 85.0
    false_pass_dimension_max: float = 60.0
    max_rollback_nodes: int = 2

    dimension_error_map: dict[ScoreDimension, ErrorType] = field(
        default_factory=lambda: {
            ScoreDimension.CONCEPT: ErrorType.CONCEPT_GAP,
            ScoreDimension.TRIGGER: ErrorType.TRIGGER_FAILURE,
            ScoreDimension.METHOD: ErrorType.METHOD_ERROR,
            ScoreDimension.TRANSFORMATION: ErrorType.TRANSFORMATION_ERROR,
            ScoreDimension.PROCESS: ErrorType.PROCESS_GAP,
            ScoreDimension.CALCULATION: ErrorType.CALCULATION_ERROR,
            ScoreDimension.EXPRESSION: ErrorType.EXPRESSION_WEAKNESS,
            ScoreDimension.MIGRATION: ErrorType.MIGRATION_FAILURE,
        }
    )
    default_rollback_level_by_error: dict[ErrorType, RollbackLevel] = field(
        default_factory=lambda: {
            ErrorType.CONCEPT_GAP: RollbackLevel.R2_PREREQUISITE,
            ErrorType.TRIGGER_FAILURE: RollbackLevel.R1_INTERNAL,
            ErrorType.METHOD_ERROR: RollbackLevel.R2_PREREQUISITE,
            ErrorType.TRANSFORMATION_ERROR: RollbackLevel.R1_INTERNAL,
            ErrorType.PROCESS_GAP: RollbackLevel.R1_INTERNAL,
            ErrorType.CALCULATION_ERROR: RollbackLevel.R1_INTERNAL,
            ErrorType.CONDITION_MISS: RollbackLevel.R1_INTERNAL,
            ErrorType.FORMULA_MEMORY_ERROR: RollbackLevel.R2_PREREQUISITE,
            ErrorType.KNOWLEDGE_CONFUSION: RollbackLevel.R4_CHAPTER_FRAMEWORK,
            ErrorType.EXPRESSION_WEAKNESS: RollbackLevel.R1_INTERNAL,
            ErrorType.MIGRATION_FAILURE: RollbackLevel.R1_INTERNAL,
            ErrorType.SYNTHESIS_FAILURE: RollbackLevel.R4_CHAPTER_FRAMEWORK,
        }
    )


DEFAULT_ENGINE_CONFIG = EngineConfig()
