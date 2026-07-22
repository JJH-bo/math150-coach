from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.classroom.hashing import content_hash
from app.classroom.models import ClassroomPackage, ContentBlock
from app.classroom.validation import ClassroomPackageValidator
from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)


ROOT_FIELDS = {"package"}


class ClassroomComposeInputError(ValueError):
    pass


class ClassroomComposeAdapter:
    definition = ToolDefinition(
        tool_id="classroom.compose",
        version="1.0.0",
        title="Compose and verify a complete classroom package",
        description=(
            "Normalize one complete classroom_package_v1 candidate, validate its "
            "coverage evidence, teaching structure, assets, models, bindings, and "
            "stable IDs, and emit a canonical package plus repair-oriented report. "
            "The operation is non-mutating; a publish-ready artifact is applied only "
            "through the revision-safe classroom draft Actions."
        ),
        category="classroom",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.AUTHOR,
        execution_mode=ToolExecutionMode.SYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=30,
        max_artifacts=2,
        max_artifact_bytes=64 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["package"],
            "properties": {
                "package": {
                    "type": "object",
                    "description": "A complete classroom_package_v1 candidate.",
                }
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": [
                "package_id",
                "schema_version",
                "package_content_hash",
                "counts",
                "applied",
                "publish_ready",
                "validation",
            ],
            "properties": {
                "package_id": {"type": "string"},
                "schema_version": {"type": "string"},
                "package_content_hash": {"type": "string"},
                "counts": {"type": "object"},
                "applied": {"type": "boolean"},
                "publish_ready": {"type": "boolean"},
                "validation": {"type": "object"},
            },
        },
        output_media_types=["application/json"],
        quality_gates=[
            "complete_classroom_package_v1",
            "pydantic_structural_validation",
            "semantic_publish_validation",
            "coverage_and_teaching_contracts",
            "registered_asset_and_model_resolution",
            "canonical_content_hash",
            "non_mutating_candidate_generation",
            "repair_oriented_validation_report",
        ],
        upstream_project="Project Classroom Package v1 and Pydantic v2",
        license="Project-owned / MIT",
    )

    def __init__(self, validator: ClassroomPackageValidator) -> None:
        self.validator = validator

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        if not isinstance(arguments, dict):
            raise ClassroomComposeInputError("classroom compose arguments must be an object")
        unknown = set(arguments) - ROOT_FIELDS
        if unknown:
            raise ClassroomComposeInputError(
                f"unsupported classroom compose fields: {sorted(unknown)}"
            )
        if set(arguments) != ROOT_FIELDS:
            raise ClassroomComposeInputError("package is required")
        try:
            package = ClassroomPackage.model_validate(arguments["package"])
        except ValidationError as exc:
            raise ClassroomComposeInputError(
                f"classroom package is structurally invalid: {exc}"
            ) from exc

        validation = self.validator.validate(package)
        validation_payload = validation.model_dump(mode="json", exclude_none=True)
        package_payload = package.model_dump(mode="json", exclude_none=True)
        result = {
            "package_id": package.package_id,
            "schema_version": package.schema_version,
            "package_content_hash": content_hash(package),
            "counts": self._counts(package),
            "applied": False,
            "publish_ready": validation.passed,
            "validation": validation_payload,
        }
        work_dir = context.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        package_path = work_dir / "composed-package.json"
        report_path = work_dir / "composition-report.json"
        package_path.write_text(
            json.dumps(
                package_payload,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        report_path.write_text(
            json.dumps(
                {
                    **result,
                    "next_action": (
                        "Call createClassroomDraft or updateClassroomDraft with composed-package.json."
                        if validation.passed
                        else "Repair every validation error and run classroom.compose again."
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        warnings = []
        if not validation.passed:
            warnings.append(
                "Composed package is structurally valid but not publish-ready; repair every validation error."
            )
        return ToolExecutionResult(
            result=result,
            warnings=warnings,
            artifacts=[self._artifact(package_path), self._artifact(report_path)],
            metrics={
                **result["counts"],
                "validation_issue_count": len(validation.issues),
                "package_bytes": package_path.stat().st_size,
            },
        )

    @classmethod
    def _counts(cls, package: ClassroomPackage) -> dict[str, int]:
        courses = len(package.courses)
        chapters = sum(len(course.chapters) for course in package.courses)
        modules = 0
        segments = 0
        blocks = 0
        detail_branches = 0
        knowledge_points = 0
        for course in package.courses:
            for chapter in course.chapters:
                modules += len(chapter.modules)
                knowledge_points += len(chapter.knowledge_points)
                for module in chapter.modules:
                    segments += len(module.segments)
                    block_count, branch_count = cls._block_counts(module.blocks)
                    blocks += block_count
                    detail_branches += branch_count
                    for segment in module.segments:
                        block_count, branch_count = cls._block_counts(segment.blocks)
                        blocks += block_count
                        detail_branches += branch_count
        return {
            "courses": courses,
            "chapters": chapters,
            "modules": modules,
            "segments": segments,
            "blocks": blocks,
            "detail_branches": detail_branches,
            "knowledge_points": knowledge_points,
            "assets": len(package.assets),
            "model_instances": len(package.model_instances),
            "bindings": len(package.model_bindings),
        }

    @classmethod
    def _block_counts(cls, values: list[ContentBlock]) -> tuple[int, int]:
        blocks = len(values)
        branches = 0
        for block in values:
            branches += len(block.detail_branches)
            for branch in block.detail_branches:
                nested_blocks, nested_branches = cls._block_counts(branch.blocks)
                blocks += nested_blocks
                branches += nested_branches
        return blocks, branches

    @staticmethod
    def _artifact(path: Path) -> ToolProducedArtifact:
        return ToolProducedArtifact(
            name=path.name,
            media_type="application/json",
            source_path=path.name,
        )
