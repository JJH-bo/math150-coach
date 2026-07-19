from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.classroom.hashing import content_hash
from app.classroom.models import (
    ActivationReceipt,
    ClassroomPackage,
    DraftRecord,
    ReleaseRecord,
    utc_now,
)


SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")


class ClassroomRepositoryError(ValueError):
    pass


class ClassroomNotFoundError(ClassroomRepositoryError):
    pass


class ClassroomConflictError(ClassroomRepositoryError):
    pass


class ClassroomPathError(ClassroomRepositoryError):
    pass


class ClassroomRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def create_draft(self, draft_id: str, package: ClassroomPackage) -> DraftRecord:
        path = self._draft_path(draft_id)
        if path.exists():
            raise ClassroomConflictError(f"draft already exists: {draft_id}")
        record = DraftRecord(
            draft_id=draft_id,
            revision=1,
            content_hash=content_hash(package),
            package=package,
            updated_at=utc_now(),
        )
        self._write_json(path, record)
        return record

    def get_draft(self, draft_id: str) -> DraftRecord:
        return DraftRecord.model_validate(self._read_json(self._draft_path(draft_id)))

    def list_drafts(self) -> list[DraftRecord]:
        drafts_root = self.root / "drafts"
        if not drafts_root.exists():
            return []
        drafts = [
            DraftRecord.model_validate(self._read_json(path))
            for path in drafts_root.glob("*.json")
        ]
        return sorted(drafts, key=lambda item: item.draft_id)

    def update_draft(
        self,
        draft_id: str,
        expected_revision: int,
        package: ClassroomPackage,
    ) -> DraftRecord:
        current = self.get_draft(draft_id)
        if current.revision != expected_revision:
            raise ClassroomConflictError(
                f"draft {draft_id} is revision {current.revision}; "
                f"expected revision {expected_revision}"
            )
        record = DraftRecord(
            draft_id=draft_id,
            revision=current.revision + 1,
            content_hash=content_hash(package),
            package=package,
            updated_at=utc_now(),
        )
        self._write_json(self._draft_path(draft_id), record)
        return record

    def publish(self, draft_id: str, expected_revision: int) -> ActivationReceipt:
        draft = self.get_draft(draft_id)
        if draft.revision != expected_revision:
            raise ClassroomConflictError(
                f"draft {draft_id} is revision {draft.revision}; "
                f"expected revision {expected_revision}"
            )
        version = f"r-{draft.content_hash.removeprefix('sha256:')[:16]}"
        release = ReleaseRecord(
            package_id=draft.package.package_id,
            version=version,
            content_hash=draft.content_hash,
            package=draft.package,
        )
        release_path = self._release_path(draft.package.package_id, version)
        if not release_path.exists():
            self._write_json(release_path, release)
        previous = self._read_active_version(draft.package.package_id)
        receipt = ActivationReceipt(
            action="publish",
            package_id=draft.package.package_id,
            active_version=version,
            previous_version=previous,
            content_hash=draft.content_hash,
        )
        self._write_active_pointer(receipt)
        return receipt

    def rollback(self, package_id: str, version: str) -> ActivationReceipt:
        target = ReleaseRecord.model_validate(
            self._read_json(self._release_path(package_id, version))
        )
        previous = self._read_active_version(package_id)
        receipt = ActivationReceipt(
            action="rollback",
            package_id=package_id,
            active_version=target.version,
            previous_version=previous,
            content_hash=target.content_hash,
        )
        self._write_active_pointer(receipt)
        return receipt

    def get_active_release(self, package_id: str) -> ReleaseRecord:
        version = self._read_active_version(package_id)
        if version is None:
            raise ClassroomNotFoundError(f"active package not found: {package_id}")
        return ReleaseRecord.model_validate(
            self._read_json(self._release_path(package_id, version))
        )

    def list_active_releases(self) -> list[ReleaseRecord]:
        active_root = self.root / "active"
        if not active_root.exists():
            return []
        releases = [
            self.get_active_release(path.stem)
            for path in active_root.glob("*.json")
        ]
        return sorted(releases, key=lambda item: item.package_id)

    def _draft_path(self, draft_id: str) -> Path:
        return self.root / "drafts" / f"{self._safe_id(draft_id)}.json"

    def _release_path(self, package_id: str, version: str) -> Path:
        return (
            self.root
            / "packages"
            / self._safe_id(package_id)
            / "releases"
            / f"{self._safe_id(version)}.json"
        )

    def _active_path(self, package_id: str) -> Path:
        return self.root / "active" / f"{self._safe_id(package_id)}.json"

    def _safe_id(self, value: str) -> str:
        if not SAFE_ID.fullmatch(value):
            raise ClassroomPathError(f"unsafe classroom identifier: {value}")
        return value

    def _read_active_version(self, package_id: str) -> str | None:
        path = self._active_path(package_id)
        if not path.exists():
            return None
        return str(self._read_json(path)["active_version"])

    def _write_active_pointer(self, receipt: ActivationReceipt) -> None:
        self._write_json(
            self._active_path(receipt.package_id),
            {
                "package_id": receipt.package_id,
                "active_version": receipt.active_version,
                "content_hash": receipt.content_hash,
                "activated_at": receipt.activated_at,
            },
        )

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise ClassroomNotFoundError(f"classroom artifact not found: {path.name}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ClassroomRepositoryError(
                f"invalid classroom artifact: {path.name}"
            ) from exc
        if not isinstance(value, dict):
            raise ClassroomRepositoryError(
                f"classroom artifact root must be an object: {path.name}"
            )
        return value

    def _write_json(self, path: Path, value: BaseModel | dict[str, Any]) -> None:
        payload = (
            value.model_dump(mode="json", exclude_none=True)
            if isinstance(value, BaseModel)
            else value
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f"{path.suffix}.{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
