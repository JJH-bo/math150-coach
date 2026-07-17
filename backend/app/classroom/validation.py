from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.classroom.models import ClassroomPackage, ContentBlock


FORBIDDEN_LEARNER_ANALYSIS_KEYS = {
    "mastery_state",
    "diagnosis",
    "review_schedule",
    "question_bank",
    "boss_challenge",
    "learner_profile",
    "recommended_next_step",
    "ability_profile",
}


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Literal["error", "warning"]
    code: str
    path: str
    message: str


class ClassroomValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    issues: list[ValidationIssue]


RecordId = Callable[[str, str], None]


class ClassroomPackageValidator:
    def validate(self, package: ClassroomPackage) -> ClassroomValidationReport:
        issues: list[ValidationIssue] = []
        seen_ids: dict[str, str] = {}

        def record_id(object_id: str, path: str) -> None:
            previous = seen_ids.get(object_id)
            if previous is not None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="duplicate_object_id",
                        path=path,
                        message=f"Object id {object_id!r} is already used at {previous}.",
                    )
                )
            else:
                seen_ids[object_id] = path

        for course_index, course in enumerate(package.courses):
            course_path = f"courses[{course_index}]"
            record_id(course.id, f"{course_path}.id")
            for chapter_index, chapter in enumerate(course.chapters):
                chapter_path = f"{course_path}.chapters[{chapter_index}]"
                record_id(chapter.id, f"{chapter_path}.id")
                module_ids = {module.id for module in chapter.modules}
                for module_index, module in enumerate(chapter.modules):
                    module_path = f"{chapter_path}.modules[{module_index}]"
                    record_id(module.id, f"{module_path}.id")
                    for block_index, block in enumerate(module.blocks):
                        self._validate_block(
                            block,
                            f"{module_path}.blocks[{block_index}]",
                            record_id,
                            issues,
                        )
                    for segment_index, segment in enumerate(module.segments):
                        segment_path = f"{module_path}.segments[{segment_index}]"
                        record_id(segment.id, f"{segment_path}.id")
                        for block_index, block in enumerate(segment.blocks):
                            self._validate_block(
                                block,
                                f"{segment_path}.blocks[{block_index}]",
                                record_id,
                                issues,
                            )
                for relation_index, relation in enumerate(chapter.relations):
                    relation_path = f"{chapter_path}.relations[{relation_index}]"
                    record_id(relation.id, f"{relation_path}.id")
                    if relation.source_module_id not in module_ids:
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                code="unknown_relation_source",
                                path=f"{relation_path}.source_module_id",
                                message="Relation source module does not exist in this chapter.",
                            )
                        )
                    if relation.target_module_id not in module_ids:
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                code="unknown_relation_target",
                                path=f"{relation_path}.target_module_id",
                                message="Relation target module does not exist in this chapter.",
                            )
                        )

        return ClassroomValidationReport(
            passed=not any(issue.severity == "error" for issue in issues),
            issues=issues,
        )

    def _validate_block(
        self,
        block: ContentBlock,
        path: str,
        record_id: RecordId,
        issues: list[ValidationIssue],
    ) -> None:
        record_id(block.id, f"{path}.id")
        self._find_forbidden_keys(block.data, f"{path}.data", issues)
        for branch_index, branch in enumerate(block.detail_branches):
            branch_path = f"{path}.detail_branches[{branch_index}]"
            record_id(branch.id, f"{branch_path}.id")
            for block_index, child in enumerate(branch.blocks):
                self._validate_block(
                    child,
                    f"{branch_path}.blocks[{block_index}]",
                    record_id,
                    issues,
                )

    def _find_forbidden_keys(
        self,
        value: Any,
        path: str,
        issues: list[ValidationIssue],
    ) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in FORBIDDEN_LEARNER_ANALYSIS_KEYS:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="learner_analysis_field_forbidden",
                            path=child_path,
                            message=f"Classroom content cannot contain learner-analysis field {key!r}.",
                        )
                    )
                self._find_forbidden_keys(child, child_path, issues)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._find_forbidden_keys(child, f"{path}[{index}]", issues)
