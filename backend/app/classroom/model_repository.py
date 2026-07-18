from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.classroom.model_contracts import (
    ModelDraftRecord,
    PreviewJobRecord,
    RegisteredModelRecord,
    TeachingModelManifest,
    model_content_hash,
    model_version,
)


SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
SAFE_ARTIFACT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,159}$")


class ModelRepositoryError(RuntimeError):
    pass


class ModelNotFoundError(ModelRepositoryError):
    pass


class ModelConflictError(ModelRepositoryError):
    pass


class TeachingModelRepository:
    def __init__(self, root: Path, *, seed_root: Path | None = None) -> None:
        self.root = Path(root)
        self.seed_root = Path(seed_root) if seed_root is not None else None

    def create_draft(
        self,
        draft_id: str,
        manifest: TeachingModelManifest,
        source: str,
    ) -> ModelDraftRecord:
        path = self._draft_path(draft_id)
        if path.exists():
            raise ModelConflictError(f"model draft {draft_id!r} already exists")
        record = ModelDraftRecord(
            draft_id=draft_id,
            revision=1,
            content_hash=model_content_hash(manifest, source),
            manifest=manifest,
            source=source,
        )
        self._write_json(path, record)
        return record

    def get_draft(self, draft_id: str) -> ModelDraftRecord:
        path = self._draft_path(draft_id)
        if not path.exists():
            raise ModelNotFoundError(f"model draft {draft_id!r} was not found")
        return ModelDraftRecord.model_validate(self._read_json(path))

    def update_draft(
        self,
        draft_id: str,
        *,
        expected_revision: int,
        manifest: TeachingModelManifest,
        source: str,
    ) -> ModelDraftRecord:
        current = self.get_draft(draft_id)
        if current.revision != expected_revision:
            raise ModelConflictError(
                f"model draft {draft_id!r} expected revision {expected_revision}, "
                f"but current revision is {current.revision}"
            )
        updated = ModelDraftRecord(
            draft_id=draft_id,
            revision=current.revision + 1,
            content_hash=model_content_hash(manifest, source),
            manifest=manifest,
            source=source,
        )
        self._write_json(self._draft_path(draft_id), updated)
        return updated

    def register(
        self,
        draft: ModelDraftRecord,
        *,
        validation: dict[str, Any],
        preview_job_id: str,
    ) -> RegisteredModelRecord:
        version = model_version(draft.manifest, draft.source)
        directory = self._version_directory(draft.manifest.model_id, version)
        record_path = directory / "record.json"
        if record_path.exists():
            existing = RegisteredModelRecord.model_validate(self._read_json(record_path))
            if existing.content_hash != draft.content_hash:
                raise ModelConflictError(
                    f"registered model version {version!r} has different content"
                )
            return existing

        record = RegisteredModelRecord(
            model_id=draft.manifest.model_id,
            version=version,
            content_hash=draft.content_hash,
            manifest=draft.manifest,
            source=draft.source,
            validation=validation,
            preview_job_id=preview_job_id,
        )
        directory.mkdir(parents=True, exist_ok=True)
        self._write_json(directory / "manifest.json", draft.manifest)
        self._write_text(directory / "source.js", draft.source)
        self._write_json(record_path, record)
        return record

    def get_registered(self, model_id: str, version: str) -> RegisteredModelRecord:
        directory = self._version_directory(model_id, version)
        record_path = directory / "record.json"
        if record_path.exists():
            return RegisteredModelRecord.model_validate(self._read_json(record_path))

        seeded = self._seed_record(model_id)
        if seeded is not None and seeded.version == version:
            return seeded
        raise ModelNotFoundError(
            f"registered model {model_id!r} version {version!r} was not found"
        )

    def list_registered(self) -> list[RegisteredModelRecord]:
        records: dict[tuple[str, str], RegisteredModelRecord] = {}
        models_root = self.root / "models"
        if models_root.exists():
            for record_path in models_root.glob("*/versions/*/record.json"):
                record = RegisteredModelRecord.model_validate(
                    self._read_json(record_path)
                )
                records[(record.model_id, record.version)] = record
        if self.seed_root is not None and self.seed_root.exists():
            for model_directory in self.seed_root.iterdir():
                if not model_directory.is_dir():
                    continue
                record = self._seed_record(model_directory.name)
                if record is not None:
                    records.setdefault((record.model_id, record.version), record)
        return sorted(records.values(), key=lambda item: (item.model_id, item.version))

    def put_preview_job(self, job: PreviewJobRecord) -> PreviewJobRecord:
        self._write_json(self._preview_job_path(job.job_id), job)
        return job

    def get_preview_job(self, job_id: str) -> PreviewJobRecord:
        path = self._preview_job_path(job_id)
        if not path.exists():
            raise ModelNotFoundError(f"preview job {job_id!r} was not found")
        return PreviewJobRecord.model_validate(self._read_json(path))

    def find_successful_preview(
        self,
        draft_content_hash: str,
    ) -> PreviewJobRecord | None:
        jobs_root = self.root / "preview-jobs"
        if not jobs_root.exists():
            return None
        matches: list[PreviewJobRecord] = []
        for path in jobs_root.glob("*.json"):
            job = PreviewJobRecord.model_validate(self._read_json(path))
            if (
                job.status == "succeeded"
                and job.draft_content_hash == draft_content_hash
            ):
                matches.append(job)
        return sorted(matches, key=lambda item: item.updated_at)[-1] if matches else None

    def artifact_path(self, job_id: str, name: str) -> Path:
        self._safe_id(job_id)
        if not SAFE_ARTIFACT.fullmatch(name):
            raise ValueError(f"artifact name {name!r} is not safe")
        directory = self.root / "preview-artifacts" / job_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory / name

    def _draft_path(self, draft_id: str) -> Path:
        return self.root / "model-drafts" / f"{self._safe_id(draft_id)}.json"

    def _preview_job_path(self, job_id: str) -> Path:
        return self.root / "preview-jobs" / f"{self._safe_id(job_id)}.json"

    def _version_directory(self, model_id: str, version: str) -> Path:
        return (
            self.root
            / "models"
            / self._safe_id(model_id)
            / "versions"
            / self._safe_id(version)
        )

    def _seed_record(self, model_id: str) -> RegisteredModelRecord | None:
        self._safe_id(model_id)
        if self.seed_root is None:
            return None
        directory = self.seed_root / model_id
        manifest_path = directory / "manifest.json"
        source_path = directory / "source.js"
        if not manifest_path.exists() or not source_path.exists():
            return None
        manifest = TeachingModelManifest.model_validate(self._read_json(manifest_path))
        source = source_path.read_text(encoding="utf-8")
        return RegisteredModelRecord(
            model_id=manifest.model_id,
            version=model_version(manifest, source),
            content_hash=model_content_hash(manifest, source),
            manifest=manifest,
            source=source,
            validation={"passed": True, "issues": [], "source": "checked-in-seed"},
            preview_job_id="checked-in-seed",
        )

    @staticmethod
    def _safe_id(value: str) -> str:
        if not SAFE_ID.fullmatch(value):
            raise ValueError(f"identifier {value!r} is not safe")
        return value

    @staticmethod
    def _read_json(path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelRepositoryError(f"could not read {path}: {exc}") from exc

    def _write_json(self, path: Path, value: BaseModel | dict[str, Any]) -> None:
        payload = (
            value.model_dump(mode="json", exclude_none=True)
            if isinstance(value, BaseModel)
            else value
        )
        text = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        self._write_text(path, f"{text}\n")

    @staticmethod
    def _write_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            temporary.write_text(text, encoding="utf-8", newline="\n")
            temporary.replace(path)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise ModelRepositoryError(f"could not write {path}: {exc}") from exc
