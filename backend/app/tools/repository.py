from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.tools.contracts import ToolArtifact, ToolJob, ToolProducedArtifact


SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")


class ToolJobRepositoryError(ValueError):
    pass


class ToolJobNotFoundError(ToolJobRepositoryError):
    pass


class ToolJobConflictError(ToolJobRepositoryError):
    pass


class ToolArtifactConflictError(ToolJobRepositoryError):
    pass


class ToolArtifactLimitError(ToolJobRepositoryError):
    pass


class ToolPathError(ToolJobRepositoryError):
    pass


class ToolJobRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve() / "tool-jobs"

    def create(self, job: ToolJob) -> ToolJob:
        path = self._job_path(job.job_id)
        if path.exists():
            raise ToolJobConflictError(f"tool job {job.job_id} already exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.work_dir(job.job_id)
        self._artifacts_dir(job.job_id).mkdir(parents=True, exist_ok=True)
        self._write_json(path, job.model_dump(mode="json", exclude_none=True))
        return job

    def get(self, job_id: str) -> ToolJob:
        path = self._job_path(job_id)
        if not path.is_file():
            raise ToolJobNotFoundError(f"tool job {job_id} was not found")
        return ToolJob.model_validate(self._read_json(path))

    def update(self, job: ToolJob) -> ToolJob:
        existing = self.get(job.job_id)
        immutable_fields = (
            "tool_id",
            "tool_version",
            "required_scope",
            "argument_hash",
            "arguments",
            "created_at",
        )
        for field in immutable_fields:
            if getattr(existing, field) != getattr(job, field):
                raise ToolJobConflictError(
                    f"tool job {job.job_id} cannot change immutable field {field}"
                )
        self._write_json(
            self._job_path(job.job_id),
            job.model_dump(mode="json", exclude_none=True),
        )
        return job

    def request_cancel(self, job_id: str) -> ToolJob:
        job = self.get(job_id)
        if job.cancellation_requested:
            return job
        return self.update(job.model_copy(update={"cancellation_requested": True}))

    def work_dir(self, job_id: str) -> Path:
        path = self._job_dir(job_id) / "work"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def promote_artifact(
        self,
        job_id: str,
        produced: ToolProducedArtifact,
        *,
        max_artifact_bytes: int,
    ) -> ToolArtifact:
        self.get(job_id)
        work = self.work_dir(job_id).resolve()
        source = (work / produced.source_path).resolve()
        if not self._is_within(source, work):
            raise ToolPathError(
                f"artifact source must stay inside tool job work directory: {produced.source_path}"
            )
        if not source.is_file():
            raise ToolPathError(f"artifact source does not exist: {produced.source_path}")
        size = source.stat().st_size
        if size > max_artifact_bytes:
            raise ToolArtifactLimitError(
                f"artifact {produced.name} is {size} bytes, limit is {max_artifact_bytes}"
            )

        digest = self._sha256(source)
        artifacts = self._artifacts_dir(job_id)
        artifacts.mkdir(parents=True, exist_ok=True)
        destination = self._safe_child(artifacts, produced.name)
        if destination.exists():
            if self._sha256(destination) != digest:
                raise ToolArtifactConflictError(
                    f"artifact {produced.name} is immutable and already exists"
                )
        else:
            temporary = destination.with_name(
                f".{destination.name}.{uuid.uuid4().hex}.tmp"
            )
            shutil.copyfile(source, temporary)
            os.replace(temporary, destination)

        return ToolArtifact(
            name=produced.name,
            media_type=produced.media_type,
            size_bytes=size,
            sha256=f"sha256:{digest}",
            download_path=(
                f"/api/studio/v1/tool-jobs/{job_id}/artifacts/{produced.name}"
            ),
        )

    def artifact_path(self, job_id: str, name: str) -> Path:
        self.get(job_id)
        path = self._safe_child(self._artifacts_dir(job_id), name)
        if not path.is_file():
            raise ToolJobNotFoundError(
                f"artifact {name} for tool job {job_id} was not found"
            )
        return path

    def _job_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"

    def _job_dir(self, job_id: str) -> Path:
        return self._safe_child(self.root, job_id)

    def _artifacts_dir(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "artifacts"

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def _safe_child(self, root: Path, value: str) -> Path:
        if not SAFE_ID.fullmatch(value):
            raise ToolPathError(f"unsafe tool path identifier: {value!r}")
        root = root.resolve()
        candidate = (root / value).resolve()
        if not self._is_within(candidate, root):
            raise ToolPathError(f"tool path escapes root: {value!r}")
        return candidate

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
