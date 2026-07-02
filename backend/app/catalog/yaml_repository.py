from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.api.v1.nodes import load_node_catalog
from app.catalog.models import CatalogQuestionRecord, validate_question_id
from app.catalog.repository import CatalogValidationError, QuestionCatalogRepository
from app.catalog.validator import CatalogValidator


DEFAULT_CATALOG_ROOT = Path(__file__).resolve().parents[2] / "catalog_data"


class YamlQuestionCatalogRepository(QuestionCatalogRepository):
    def __init__(self, catalog_root: Path | str = DEFAULT_CATALOG_ROOT) -> None:
        self.catalog_root = Path(catalog_root)
        self._records_by_id: dict[str, CatalogQuestionRecord] | None = None

    def get_published(self, question_id: str) -> CatalogQuestionRecord | None:
        try:
            validate_question_id(question_id)
        except ValueError:
            return None
        records = self._records()
        record = records.get(question_id)
        if record and record.is_learner_visible():
            return record
        return None

    def list_published_by_node(self, node_id: str) -> list[CatalogQuestionRecord]:
        return [
            record
            for record in self._records().values()
            if record.manifest.node_id == node_id and record.is_learner_visible()
        ]

    def validate_catalog(self) -> None:
        self._records(force_reload=True)

    def _records(self, *, force_reload: bool = False) -> dict[str, CatalogQuestionRecord]:
        if self._records_by_id is None or force_reload:
            self._records_by_id = self._load_records()
        return self._records_by_id

    def _load_records(self) -> dict[str, CatalogQuestionRecord]:
        manifest = self._load_yaml(self.catalog_root / "manifest.yaml")
        question_paths = manifest.get("questions", []) if isinstance(manifest, dict) else []
        if not isinstance(question_paths, list):
            raise CatalogValidationError("catalog manifest questions must be a list")

        node_catalog = load_node_catalog()
        records: dict[str, CatalogQuestionRecord] = {}
        for raw_path in question_paths:
            if not isinstance(raw_path, str):
                raise CatalogValidationError("catalog manifest question paths must be strings", error_code="catalog_identity_error")
            record = self._load_record(raw_path)
            question_id = record.manifest.question_id
            if question_id in records:
                raise CatalogValidationError(f"duplicate question_id: {question_id}", error_code="catalog_identity_error")
            records[question_id] = record
        CatalogValidator().validate_catalog(records, node_catalog)
        return records

    def _load_record(self, manifest_path: str) -> CatalogQuestionRecord:
        question_path = (self.catalog_root / manifest_path).resolve()
        catalog_root = self.catalog_root.resolve()
        if not self._is_inside(question_path, catalog_root):
            raise CatalogValidationError("catalog question path escapes catalog root")
        data = self._load_yaml(question_path)
        try:
            return CatalogQuestionRecord.model_validate(data)
        except ValidationError as exc:
            raise CatalogValidationError(str(exc), error_code="catalog_validation_error") from exc

    def _load_yaml(self, path: Path) -> Any:
        if not path.exists():
            raise CatalogValidationError(f"catalog file not found: {path.name}")
        with path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    def _is_inside(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True


_DEFAULT_REPOSITORY = YamlQuestionCatalogRepository()


def get_catalog_repository() -> YamlQuestionCatalogRepository:
    return _DEFAULT_REPOSITORY


def reset_catalog_repository_for_tests(repository: YamlQuestionCatalogRepository | None = None) -> None:
    global _DEFAULT_REPOSITORY
    _DEFAULT_REPOSITORY = repository or YamlQuestionCatalogRepository()
