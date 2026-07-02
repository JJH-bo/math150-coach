from __future__ import annotations

import re
from typing import Any, Iterable

from pydantic import BaseModel

from app.catalog.models import CatalogQuestionRecord, RESERVED_VALIDATOR_CONFIG_KEYS
from app.catalog.repository import CatalogValidationError
from app.core.enums import ScoreDimension
from app.core.schemas import KnowledgeNode, RubricItem


ALLOWED_ANSWER_FORMATS = {"expression", "equation", "free_text", "expression_with_reasoning"}
ALLOWED_RESPONSE_STEP_MODES = {"none", "optional", "required"}
ALLOWED_DIFFICULTIES = {"basic", "standard", "comprehensive"}
ALLOWED_VALIDATOR_CONFIG_KEYS = {"requires_constant", "requires_initial_condition", "answer_equivalence_mode"}
ALLOWED_ANSWER_EQUIVALENCE_MODES = {"exact", "normalized", "symbolic"}
ALLOWED_DIMENSION_EXTENSIONS = {
    ScoreDimension.CALCULATION,
    ScoreDimension.FINAL_ANSWER,
    ScoreDimension.EXPRESSION,
}
VERSION_PATTERN = re.compile(r"^\d+(?:\.\d+){0,2}$")
CONTENT_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
TRUSTED_FIELD_NAMES = {
    "expected_answer",
    "answer_aliases",
    "rubric",
    "solution_outline",
    "validator_config",
    "scoring_notes_internal",
    "golden_case_refs",
    "authoring_metadata",
    "score_overrides",
    "evidence_overrides",
    "manual_override",
    "scenario",
    "include_debug",
    "diagnosis_trace",
    "evidence_sources",
    "raw_rollback_level",
    "raw_forward_level",
}
MATH_LEAK_MARKERS = ("=", "+", "-", "^", "/", "|", "(", ")", "ln", "sin", "cos", "tan", "exp", "sqrt", "lim", "int")


class CatalogValidator:
    """Fail-fast validation for server-side catalog records."""

    def validate_catalog(
        self,
        records: dict[str, CatalogQuestionRecord],
        node_catalog: Iterable[KnowledgeNode],
    ) -> None:
        node_by_id = {node.id: node for node in node_catalog}
        all_question_ids = set(records)
        for question_id, record in records.items():
            if question_id != record.manifest.question_id:
                raise self._error(
                    "catalog_identity_error",
                    f"record index question_id does not match manifest.question_id: {question_id}",
                )
            self.validate_record(record, node_by_id, all_question_ids)

    def validate_record(
        self,
        record: CatalogQuestionRecord,
        node_by_id: dict[str, KnowledgeNode],
        all_question_ids: set[str],
    ) -> None:
        self.validate_identity(record, node_by_id, all_question_ids)
        self.validate_public_layer(record)
        self.validate_trusted_layer(record)
        self.validate_rubric(record)
        self.validate_dimension_consistency(record, node_by_id[record.manifest.node_id])
        self.validate_leak_boundary(record)
        self.validate_content_hash_format(record)

    def validate_identity(
        self,
        record: CatalogQuestionRecord,
        node_by_id: dict[str, KnowledgeNode],
        all_question_ids: set[str],
    ) -> None:
        manifest = record.manifest
        presentation = record.presentation
        if manifest.question_id != presentation.question_id:
            raise self._error("catalog_identity_error", "manifest.question_id must match presentation.question_id")
        if manifest.node_id != presentation.node_id:
            raise self._error("catalog_identity_error", "manifest.node_id must match presentation.node_id")
        if manifest.node_id not in node_by_id:
            raise self._error("catalog_identity_error", f"unknown node_id for question {manifest.question_id}: {manifest.node_id}")
        if manifest.supersedes:
            if manifest.supersedes == manifest.question_id:
                raise self._error("catalog_identity_error", "supersedes must not reference the same question_id")
            if manifest.supersedes not in all_question_ids:
                raise self._error("catalog_identity_error", "supersedes must reference an existing catalog question_id")
        self._validate_version(manifest.question_version, "question_version")
        self._validate_version(manifest.rubric_version, "rubric_version")
        self._validate_version(manifest.answer_key_version, "answer_key_version")
        self._validate_version(manifest.catalog_schema_version, "catalog_schema_version")

    def validate_public_layer(self, record: CatalogQuestionRecord) -> None:
        presentation = record.presentation
        self._require_nonblank(presentation.title, "title", "catalog_public_layer_error")
        self._require_nonblank(presentation.stem, "stem", "catalog_public_layer_error")
        self._require_nonblank(presentation.prompt_markdown, "prompt_markdown", "catalog_public_layer_error")
        if presentation.answer_format not in ALLOWED_ANSWER_FORMATS:
            raise self._error("catalog_public_layer_error", f"invalid answer_format: {presentation.answer_format}")
        if presentation.response_step_mode not in ALLOWED_RESPONSE_STEP_MODES:
            raise self._error("catalog_public_layer_error", f"invalid response_step_mode: {presentation.response_step_mode}")
        if presentation.difficulty not in ALLOWED_DIFFICULTIES:
            raise self._error("catalog_public_layer_error", f"invalid difficulty: {presentation.difficulty}")
        for asset in presentation.display_assets:
            self._assert_no_trusted_field_names(asset, "display_assets")

    def validate_trusted_layer(self, record: CatalogQuestionRecord) -> None:
        if not record.is_learner_visible():
            self._validate_validator_config(record.trusted_scoring.validator_config)
            return

        trusted = record.trusted_scoring
        self._require_nonblank(trusted.expected_answer, "expected_answer", "catalog_trusted_layer_error")
        self._require_nonblank(trusted.solution_outline, "solution_outline", "catalog_trusted_layer_error")
        normalized_aliases: set[str] = set()
        for alias in trusted.answer_aliases:
            stripped = alias.strip()
            if not stripped:
                raise self._error("catalog_trusted_layer_error", "answer_aliases must not contain blank values")
            normalized = self._normalize_text(stripped)
            if normalized in normalized_aliases:
                raise self._error("catalog_trusted_layer_error", "answer_aliases must not contain duplicates")
            normalized_aliases.add(normalized)
        if trusted.rubric is None:
            raise self._error("catalog_trusted_layer_error", "published learner question must include rubric")
        self._validate_validator_config(trusted.validator_config)

    def validate_rubric(self, record: CatalogQuestionRecord) -> None:
        rubric = record.trusted_scoring.rubric
        if rubric is None:
            return
        if record.is_learner_visible() and not rubric.items:
            raise self._error("catalog_rubric_error", "published learner rubric must include at least one item")
        seen_ids: set[str] = set()
        has_required = False
        for item in rubric.items:
            self._validate_rubric_item(item, seen_ids)
            has_required = has_required or item.required
        if record.is_learner_visible() and not has_required:
            raise self._error("catalog_rubric_error", "published learner rubric must include at least one required item")

    def validate_dimension_consistency(self, record: CatalogQuestionRecord, node: KnowledgeNode) -> None:
        rubric = record.trusted_scoring.rubric
        if rubric is None:
            return
        node_dimensions = set(node.core_dimensions)
        allowed_dimensions = node_dimensions | ALLOWED_DIMENSION_EXTENSIONS
        covered_core_dimensions: set[ScoreDimension] = set()
        for item in rubric.items:
            for dimension in item.target_dimensions:
                if dimension not in allowed_dimensions:
                    raise self._error(
                        "catalog_dimension_error",
                        f"rubric dimension {dimension.value} is not a core or allowed extension dimension for node {node.id}",
                    )
                if dimension in node_dimensions:
                    covered_core_dimensions.add(dimension)
        if record.is_learner_visible() and not covered_core_dimensions:
            raise self._error("catalog_dimension_error", "published learner rubric must cover at least one node core dimension")

    def validate_leak_boundary(self, record: CatalogQuestionRecord) -> None:
        public_payload = record.presentation.model_dump(mode="json")
        self._assert_no_trusted_field_names(public_payload, "public presentation")
        expected_answer = record.trusted_scoring.expected_answer
        if not self._should_check_exact_answer_leak(expected_answer):
            return
        expected = self._normalize_text(expected_answer or "")
        public_texts = [record.presentation.prompt_markdown, *record.presentation.hints_public]
        for text in public_texts:
            if expected and expected in self._normalize_text(text):
                raise self._error("catalog_leak_error", "public presentation leaks exact expected_answer")

    def validate_content_hash_format(self, record: CatalogQuestionRecord) -> None:
        content_hash = record.manifest.content_hash
        if content_hash and not CONTENT_HASH_PATTERN.fullmatch(content_hash):
            raise self._error("catalog_hash_error", "content_hash must match sha256:<64 lowercase hex chars>")

    def _validate_rubric_item(self, item: RubricItem, seen_ids: set[str]) -> None:
        self._require_nonblank(item.id, "rubric item id", "catalog_rubric_error")
        if item.id in seen_ids:
            raise self._error("catalog_rubric_error", f"duplicate rubric item id: {item.id}")
        seen_ids.add(item.id)
        self._require_nonblank(item.description, "rubric item description", "catalog_rubric_error")
        if not item.target_dimensions:
            raise self._error("catalog_rubric_error", "rubric item target_dimensions must not be empty")
        if item.weight <= 0:
            raise self._error("catalog_rubric_error", "rubric item weight must be > 0")
        self._require_nonblank(item.evidence_on_hit, "evidence_on_hit", "catalog_rubric_error")
        self._require_nonblank(item.evidence_on_miss, "evidence_on_miss", "catalog_rubric_error")
        if item.required and not item.required_keywords and not item.expected_patterns:
            raise self._error(
                "catalog_rubric_error",
                "required rubric item must include required_keywords or expected_patterns",
            )

    def _validate_validator_config(self, config: dict[str, Any]) -> None:
        reserved = sorted(set(config) & RESERVED_VALIDATOR_CONFIG_KEYS)
        if reserved:
            raise self._error("catalog_trusted_layer_error", f"validator_config contains reserved metadata keys: {reserved}")
        unknown = sorted(set(config) - ALLOWED_VALIDATOR_CONFIG_KEYS)
        if unknown:
            raise self._error("catalog_trusted_layer_error", f"validator_config contains unknown keys: {unknown}")
        for key in ("requires_constant", "requires_initial_condition"):
            if key in config and not isinstance(config[key], bool):
                raise self._error("catalog_trusted_layer_error", f"validator_config.{key} must be a boolean")
        if "answer_equivalence_mode" in config and config["answer_equivalence_mode"] not in ALLOWED_ANSWER_EQUIVALENCE_MODES:
            raise self._error("catalog_trusted_layer_error", "validator_config.answer_equivalence_mode is invalid")

    def _validate_version(self, version: str, field_name: str) -> None:
        if not version or not version.strip():
            raise self._error("catalog_version_error", f"{field_name} must not be blank")
        if not VERSION_PATTERN.fullmatch(version.strip()):
            raise self._error("catalog_version_error", f"{field_name} must be semver-like")

    def _assert_no_trusted_field_names(self, value: Any, label: str) -> None:
        if isinstance(value, BaseModel):
            value = value.model_dump(mode="json")
        if isinstance(value, dict):
            for key, child in value.items():
                if key in TRUSTED_FIELD_NAMES:
                    raise self._error("catalog_leak_error", f"{label} contains trusted field name: {key}")
                self._assert_no_trusted_field_names(child, label)
        elif isinstance(value, list):
            for child in value:
                self._assert_no_trusted_field_names(child, label)

    def _should_check_exact_answer_leak(self, expected_answer: str | None) -> bool:
        if not expected_answer:
            return False
        normalized = self._normalize_text(expected_answer)
        return len(normalized) >= 6 or any(marker in normalized for marker in MATH_LEAK_MARKERS)

    def _normalize_text(self, value: str) -> str:
        normalized = value.lower().strip()
        normalized = re.sub(r"[*_`$\\{}]", "", normalized)
        normalized = re.sub(r"\s+", "", normalized)
        return normalized

    def _require_nonblank(self, value: str | None, field_name: str, error_code: str) -> None:
        if value is None or not value.strip():
            raise self._error(error_code, f"{field_name} must not be blank")

    def _error(self, error_code: str, message: str) -> CatalogValidationError:
        return CatalogValidationError(message, error_code=error_code)

