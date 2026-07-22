from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.classroom.hashing import content_hash
from app.classroom.models import (
    AssetReference,
    ClassroomPackage,
    ContentBlock,
    CoreModule,
)
from app.classroom.repository import ClassroomNotFoundError, ClassroomRepository
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


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,119}$")
ROOT_FIELDS = {"draft_id", "expected_revision", "operations"}
OPERATION_FIELDS = {
    "replace_block": {"op", "block_id", "block"},
    "insert_block": {"op", "container_id", "index", "block"},
    "remove_block": {"op", "block_id"},
    "replace_module": {"op", "module_id", "module"},
    "replace_assets": {"op", "assets"},
}


class ClassroomPatchInputError(ValueError):
    pass


class ClassroomPatchAdapter:
    definition = ToolDefinition(
        tool_id="classroom.patch",
        version="1.0.0",
        title="Prepare a typed revision-safe classroom page patch",
        description=(
            "Read one exact classroom draft revision and apply typed block, module, "
            "or asset-declaration edits to a candidate copy. Emits the complete "
            "structurally valid candidate package and semantic validation report. "
            "This tool never mutates the draft; apply the candidate with the existing "
            "revision-safe updateClassroomDraft Action after inspecting the report."
        ),
        category="classroom",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.AUTHOR,
        execution_mode=ToolExecutionMode.SYNC,
        deterministic=True,
        cacheable=False,
        timeout_seconds=30,
        max_artifacts=2,
        max_artifact_bytes=32 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["draft_id", "expected_revision", "operations"],
            "properties": {
                "draft_id": {
                    "type": "string",
                    "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]{0,119}$",
                },
                "expected_revision": {"type": "integer", "minimum": 1},
                "operations": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 100,
                    "items": {
                        "type": "object",
                        "required": ["op"],
                        "properties": {
                            "op": {
                                "type": "string",
                                "enum": [
                                    "replace_block",
                                    "insert_block",
                                    "remove_block",
                                    "replace_module",
                                    "replace_assets",
                                ],
                            },
                            "block_id": {"type": "string"},
                            "container_id": {"type": "string"},
                            "module_id": {"type": "string"},
                            "index": {"type": "integer", "minimum": 0},
                            "block": {"type": "object"},
                            "module": {"type": "object"},
                            "assets": {"type": "array"},
                        },
                    },
                },
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": [
                "draft_id",
                "source_revision",
                "source_content_hash",
                "candidate_content_hash",
                "operation_count",
                "changed_ids",
                "applied",
                "publish_ready",
                "validation",
            ],
            "properties": {
                "draft_id": {"type": "string"},
                "source_revision": {"type": "integer"},
                "source_content_hash": {"type": "string"},
                "candidate_content_hash": {"type": "string"},
                "operation_count": {"type": "integer"},
                "changed_ids": {"type": "array", "items": {"type": "string"}},
                "applied": {"type": "boolean"},
                "publish_ready": {"type": "boolean"},
                "validation": {"type": "object"},
            },
        },
        output_media_types=["application/json"],
        quality_gates=[
            "exact_draft_revision",
            "typed_id_targeted_operations",
            "unique_existing_targets",
            "replacement_identity_preserved",
            "structurally_valid_candidate_package",
            "semantic_publish_validation_reported",
            "non_mutating_candidate_generation",
            "content_hash_diff",
        ],
        upstream_project="Project Classroom Package v1 and Pydantic v2",
        license="Project-owned / MIT",
    )

    def __init__(
        self,
        repository: ClassroomRepository,
        validator: ClassroomPackageValidator,
    ) -> None:
        self.repository = repository
        self.validator = validator

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        values = self._normalize(arguments)
        try:
            draft = self.repository.get_draft(values["draft_id"])
        except ClassroomNotFoundError as exc:
            raise ClassroomPatchInputError("classroom draft was not found") from exc
        if draft.revision != values["expected_revision"]:
            raise ClassroomPatchInputError(
                f"draft revision conflict: expected {values['expected_revision']}, "
                f"current revision is {draft.revision}"
            )
        candidate = draft.package.model_dump(mode="json", exclude_none=True)
        changed_ids: list[str] = []
        for operation in values["operations"]:
            changed_ids.extend(self._apply(candidate, operation))
        try:
            package = ClassroomPackage.model_validate(candidate)
        except ValidationError as exc:
            raise ClassroomPatchInputError(
                f"patched classroom package is structurally invalid: {exc}"
            ) from exc
        validation = self.validator.validate(package)
        validation_payload = validation.model_dump(mode="json", exclude_none=True)
        candidate_hash = content_hash(package)
        work_dir = context.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        package_path = work_dir / "patched-package.json"
        report_path = work_dir / "patch-report.json"
        package_path.write_text(
            json.dumps(
                package.model_dump(mode="json", exclude_none=True),
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        result = {
            "draft_id": draft.draft_id,
            "source_revision": draft.revision,
            "source_content_hash": draft.content_hash,
            "candidate_content_hash": candidate_hash,
            "operation_count": len(values["operations"]),
            "changed_ids": list(dict.fromkeys(changed_ids)),
            "applied": False,
            "publish_ready": validation.passed,
            "validation": validation_payload,
        }
        report_path.write_text(
            json.dumps(
                {
                    **result,
                    "next_action": (
                        "Call updateClassroomDraft with this package and source_revision."
                        if validation.passed
                        else "Repair every validation error before updating or publishing."
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
                "Candidate is structurally valid but not publish-ready; repair validation issues."
            )
        return ToolExecutionResult(
            result=result,
            warnings=warnings,
            artifacts=[
                self._artifact(package_path),
                self._artifact(report_path),
            ],
            metrics={
                "operation_count": len(values["operations"]),
                "changed_object_count": len(set(changed_ids)),
                "validation_issue_count": len(validation.issues),
                "package_bytes": package_path.stat().st_size,
            },
        )

    def _normalize(self, arguments: Any) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise ClassroomPatchInputError("classroom patch arguments must be an object")
        unknown = set(arguments) - ROOT_FIELDS
        if unknown:
            raise ClassroomPatchInputError(f"unsupported classroom patch fields: {sorted(unknown)}")
        draft_id = arguments.get("draft_id")
        if not isinstance(draft_id, str) or SAFE_ID.fullmatch(draft_id) is None:
            raise ClassroomPatchInputError("draft_id is invalid")
        revision = arguments.get("expected_revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise ClassroomPatchInputError("expected_revision must be a positive integer")
        operations = arguments.get("operations")
        if not isinstance(operations, list) or not 1 <= len(operations) <= 100:
            raise ClassroomPatchInputError("operations must contain 1 to 100 items")
        normalized = [self._operation(value, index) for index, value in enumerate(operations)]
        return {
            "draft_id": draft_id,
            "expected_revision": revision,
            "operations": normalized,
        }

    def _operation(self, raw: Any, index: int) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise ClassroomPatchInputError(f"operation {index} must be an object")
        kind = raw.get("op")
        expected = OPERATION_FIELDS.get(kind)
        if expected is None:
            raise ClassroomPatchInputError(f"operation {index} has an unsupported op")
        if set(raw) != expected:
            raise ClassroomPatchInputError(
                f"operation {index} fields must be exactly {sorted(expected)}"
            )
        if kind in {"replace_block", "remove_block"}:
            self._identifier(raw["block_id"], f"operation {index} block_id")
        if kind == "insert_block":
            self._identifier(raw["container_id"], f"operation {index} container_id")
            if (
                isinstance(raw["index"], bool)
                or not isinstance(raw["index"], int)
                or raw["index"] < 0
            ):
                raise ClassroomPatchInputError(
                    f"operation {index} index must be a nonnegative integer"
                )
        if kind in {"replace_block", "insert_block"}:
            try:
                block = ContentBlock.model_validate(raw["block"])
            except ValidationError as exc:
                raise ClassroomPatchInputError(
                    f"operation {index} block is structurally invalid: {exc}"
                ) from exc
            if kind == "replace_block" and block.id != raw["block_id"]:
                raise ClassroomPatchInputError(
                    f"operation {index} must preserve the replaced block ID"
                )
            return {**raw, "block": block.model_dump(mode="json", exclude_none=True)}
        if kind == "replace_module":
            self._identifier(raw["module_id"], f"operation {index} module_id")
            try:
                module = CoreModule.model_validate(raw["module"])
            except ValidationError as exc:
                raise ClassroomPatchInputError(
                    f"operation {index} module is structurally invalid: {exc}"
                ) from exc
            if module.id != raw["module_id"]:
                raise ClassroomPatchInputError(
                    f"operation {index} must preserve the replaced module ID"
                )
            return {**raw, "module": module.model_dump(mode="json", exclude_none=True)}
        if kind == "replace_assets":
            if not isinstance(raw["assets"], list) or len(raw["assets"]) > 500:
                raise ClassroomPatchInputError(
                    f"operation {index} assets must contain at most 500 items"
                )
            try:
                assets = [AssetReference.model_validate(value) for value in raw["assets"]]
            except ValidationError as exc:
                raise ClassroomPatchInputError(
                    f"operation {index} asset declaration is invalid: {exc}"
                ) from exc
            return {
                **raw,
                "assets": [
                    asset.model_dump(mode="json", exclude_none=True) for asset in assets
                ],
            }
        return dict(raw)

    def _apply(self, package: dict[str, Any], operation: dict[str, Any]) -> list[str]:
        kind = operation["op"]
        if kind == "replace_assets":
            package["assets"] = operation["assets"]
            return [asset["asset_id"] for asset in operation["assets"]]
        if kind == "replace_module":
            matches = self._module_locations(package, operation["module_id"])
            self._require_one(matches, "module", operation["module_id"])
            modules, index = matches[0]
            modules[index] = operation["module"]
            return [operation["module_id"]]
        if kind == "insert_block":
            matches = self._container_locations(package, operation["container_id"])
            self._require_one(matches, "block container", operation["container_id"])
            blocks = matches[0]
            if operation["index"] > len(blocks):
                raise ClassroomPatchInputError("insert block index exceeds container length")
            blocks.insert(operation["index"], operation["block"])
            return [operation["container_id"], operation["block"]["id"]]
        matches = self._block_locations(package, operation["block_id"])
        self._require_one(matches, "block", operation["block_id"])
        blocks, index = matches[0]
        if kind == "replace_block":
            blocks[index] = operation["block"]
        else:
            blocks.pop(index)
        return [operation["block_id"]]

    @classmethod
    def _module_locations(
        cls, package: dict[str, Any], module_id: str
    ) -> list[tuple[list[dict[str, Any]], int]]:
        matches = []
        for course in package.get("courses", []):
            for chapter in course.get("chapters", []):
                modules = chapter.get("modules", [])
                matches.extend(
                    (modules, index)
                    for index, module in enumerate(modules)
                    if module.get("id") == module_id
                )
        return matches

    @classmethod
    def _container_locations(
        cls, package: dict[str, Any], container_id: str
    ) -> list[list[dict[str, Any]]]:
        matches = []
        for course in package.get("courses", []):
            for chapter in course.get("chapters", []):
                for module in chapter.get("modules", []):
                    if module.get("id") == container_id:
                        matches.append(module.get("blocks", []))
                    for segment in module.get("segments", []):
                        if segment.get("id") == container_id:
                            matches.append(segment.get("blocks", []))
                        cls._collect_branch_containers(
                            segment.get("blocks", []), container_id, matches
                        )
                    cls._collect_branch_containers(
                        module.get("blocks", []), container_id, matches
                    )
        return matches

    @classmethod
    def _collect_branch_containers(
        cls,
        blocks: list[dict[str, Any]],
        container_id: str,
        matches: list[list[dict[str, Any]]],
    ) -> None:
        for block in blocks:
            for branch in block.get("detail_branches", []):
                branch_blocks = branch.get("blocks", [])
                if branch.get("id") == container_id:
                    matches.append(branch_blocks)
                cls._collect_branch_containers(branch_blocks, container_id, matches)

    @classmethod
    def _block_locations(
        cls, package: dict[str, Any], block_id: str
    ) -> list[tuple[list[dict[str, Any]], int]]:
        matches = []
        for course in package.get("courses", []):
            for chapter in course.get("chapters", []):
                for module in chapter.get("modules", []):
                    cls._collect_block_locations(module.get("blocks", []), block_id, matches)
                    for segment in module.get("segments", []):
                        cls._collect_block_locations(
                            segment.get("blocks", []), block_id, matches
                        )
        return matches

    @classmethod
    def _collect_block_locations(
        cls,
        blocks: list[dict[str, Any]],
        block_id: str,
        matches: list[tuple[list[dict[str, Any]], int]],
    ) -> None:
        for index, block in enumerate(blocks):
            if block.get("id") == block_id:
                matches.append((blocks, index))
            for branch in block.get("detail_branches", []):
                cls._collect_block_locations(
                    branch.get("blocks", []), block_id, matches
                )

    @staticmethod
    def _require_one(matches: list[Any], kind: str, object_id: str) -> None:
        if not matches:
            raise ClassroomPatchInputError(f"{kind} {object_id!r} was not found")
        if len(matches) > 1:
            raise ClassroomPatchInputError(f"{kind} {object_id!r} is not unique")

    @staticmethod
    def _identifier(value: Any, name: str) -> str:
        if not isinstance(value, str) or SAFE_ID.fullmatch(value) is None:
            raise ClassroomPatchInputError(f"{name} is invalid")
        return value

    @staticmethod
    def _artifact(path: Path) -> ToolProducedArtifact:
        return ToolProducedArtifact(
            name=path.name,
            media_type="application/json",
            source_path=path.name,
        )
