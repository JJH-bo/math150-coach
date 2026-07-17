from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CHAPTER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,79}$")
DRAFT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,99}$")


class DraftStoreError(ValueError):
    """Base error raised by the immutable draft store."""


class DraftNotFound(DraftStoreError):
    """Raised when a draft or revision does not exist."""


class IdempotencyConflict(DraftStoreError):
    """Raised when one request ID is reused with different content."""


class RevisionConflict(DraftStoreError):
    """Raised when a caller attempts to overwrite a newer revision."""


class ChapterDraftStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create_revision(
        self,
        *,
        chapter_id: str,
        title: str,
        source_markdown: str,
        client_request_id: str,
        contract_version: str,
        validation_report: dict[str, Any],
        galaxy_asset: dict[str, Any] | None,
    ) -> dict[str, Any]:
        self._validate_chapter_id(chapter_id)
        content_hash = self.content_hash(source_markdown)
        idempotency = self._read_json(self.root / "idempotency.json", {})
        existing = idempotency.get(client_request_id)
        if existing:
            if existing.get("content_hash") != content_hash:
                raise IdempotencyConflict(client_request_id)
            return self.load(
                str(existing["draft_id"]),
                int(existing["revision"]),
            )

        digest = content_hash.removeprefix("sha256:")
        draft_id = f"{chapter_id}-{digest[:16]}"
        manifest_path = self.root / draft_id / "manifest.json"
        if manifest_path.exists():
            record = self.load(draft_id)
        else:
            now = self._now()
            manifest = {
                "draft_id": draft_id,
                "chapter_id": chapter_id,
                "title": title,
                "contract_version": contract_version,
                "status": "preview_ready" if galaxy_asset else "invalid",
                "revision": 1,
                "created_at": now,
                "updated_at": now,
            }
            self._write_revision(
                manifest,
                source_markdown,
                validation_report,
                galaxy_asset,
            )
            record = self.load(draft_id, 1)

        idempotency[client_request_id] = {
            "draft_id": draft_id,
            "revision": record["revision"],
            "content_hash": content_hash,
        }
        self._atomic_json(self.root / "idempotency.json", idempotency)
        return record

    def revise(
        self,
        draft_id: str,
        *,
        expected_revision: int,
        source_markdown: str,
        validation_report: dict[str, Any],
        galaxy_asset: dict[str, Any] | None,
    ) -> dict[str, Any]:
        manifest = self._manifest(draft_id)
        if int(manifest["revision"]) != expected_revision:
            raise RevisionConflict(draft_id)
        if manifest.get("status") == "published":
            raise RevisionConflict(f"published:{draft_id}")

        revised = {
            **manifest,
            "status": "preview_ready" if galaxy_asset else "invalid",
            "revision": expected_revision + 1,
            "updated_at": self._now(),
        }
        self._write_revision(
            revised,
            source_markdown,
            validation_report,
            galaxy_asset,
        )
        return self.load(draft_id, expected_revision + 1)

    def load(
        self,
        draft_id: str,
        revision: int | None = None,
    ) -> dict[str, Any]:
        manifest = self._manifest(draft_id)
        selected_revision = revision or int(manifest["revision"])
        revision_root = self.root / draft_id / "revisions"
        prefix = f"{selected_revision:04d}"
        markdown_path = revision_root / f"{prefix}.md"
        meta_path = revision_root / f"{prefix}.meta.json"
        if not markdown_path.exists() or not meta_path.exists():
            raise DraftNotFound(f"{draft_id}:{selected_revision}")

        revision_meta = self._read_json(meta_path, {})
        asset_path = revision_root / f"{prefix}.asset.json"
        record = {
            **manifest,
            **revision_meta,
            "source_markdown": markdown_path.read_text(encoding="utf-8"),
            "validation_report": self._read_json(
                revision_root / f"{prefix}.validation.json",
                {},
            ),
            "galaxy_asset": (
                self._read_json(asset_path, None)
                if asset_path.exists()
                else None
            ),
        }
        if (
            manifest.get("status") == "published"
            and int(manifest.get("published_revision", 0)) == selected_revision
        ):
            record["status"] = "published"
        return record

    def mark_published(
        self,
        draft_id: str,
        *,
        revision: int,
        content_hash: str,
        publish_result: dict[str, Any],
    ) -> dict[str, Any]:
        record = self.load(draft_id, revision)
        if record.get("content_hash") != content_hash:
            raise RevisionConflict(draft_id)
        if int(record["revision"]) != int(self._manifest(draft_id)["revision"]):
            raise RevisionConflict(draft_id)

        manifest = self._manifest(draft_id)
        manifest.update(
            {
                "status": "published",
                "published_revision": revision,
                "published_at": self._now(),
                "publish_result": publish_result,
            }
        )
        self._atomic_json(
            self.root / draft_id / "manifest.json",
            manifest,
        )
        return self.load(draft_id, revision)

    def mark_rejected(
        self,
        draft_id: str,
        *,
        revision: int,
        reason: str,
    ) -> dict[str, Any]:
        record = self.load(draft_id, revision)
        manifest = self._manifest(draft_id)
        if int(manifest["revision"]) != revision:
            raise RevisionConflict(draft_id)
        manifest.update(
            {
                "status": "changes_requested",
                "rejection_reason": reason,
                "updated_at": self._now(),
            }
        )
        self._atomic_json(
            self.root / draft_id / "manifest.json",
            manifest,
        )
        return {
            **record,
            "status": "changes_requested",
            "rejection_reason": reason,
        }

    def find_published_by_chapter(
        self,
        chapter_id: str,
    ) -> dict[str, Any] | None:
        self._validate_chapter_id(chapter_id)
        matches: list[dict[str, Any]] = []
        for manifest_path in self.root.glob("*/manifest.json"):
            manifest = self._read_json(manifest_path, {})
            if (
                manifest.get("chapter_id") == chapter_id
                and manifest.get("status") == "published"
            ):
                matches.append(manifest)
        if not matches:
            return None
        latest = max(
            matches,
            key=lambda item: str(item.get("published_at", "")),
        )
        return self.load(
            str(latest["draft_id"]),
            int(latest["published_revision"]),
        )

    @staticmethod
    def content_hash(markdown: str) -> str:
        digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    def _write_revision(
        self,
        manifest: dict[str, Any],
        markdown: str,
        validation: dict[str, Any],
        asset: dict[str, Any] | None,
    ) -> None:
        root = self.root / str(manifest["draft_id"])
        revisions = root / "revisions"
        revisions.mkdir(parents=True, exist_ok=True)
        revision = int(manifest["revision"])
        prefix = f"{revision:04d}"
        markdown_path = revisions / f"{prefix}.md"
        meta_path = revisions / f"{prefix}.meta.json"
        if markdown_path.exists() or meta_path.exists():
            raise RevisionConflict(str(manifest["draft_id"]))

        revision_meta = {
            "revision": revision,
            "content_hash": self.content_hash(markdown),
            "status": manifest["status"],
            "created_at": manifest["updated_at"],
        }
        self._atomic_text(markdown_path, markdown)
        self._atomic_json(meta_path, revision_meta)
        self._atomic_json(
            revisions / f"{prefix}.validation.json",
            validation,
        )
        if asset is not None:
            self._atomic_json(
                revisions / f"{prefix}.asset.json",
                asset,
            )
        self._atomic_json(root / "manifest.json", manifest)

    def _manifest(self, draft_id: str) -> dict[str, Any]:
        self._validate_draft_id(draft_id)
        path = self.root / draft_id / "manifest.json"
        if not path.exists():
            raise DraftNotFound(draft_id)
        return self._read_json(path, {})

    @staticmethod
    def _validate_chapter_id(value: str) -> None:
        if not CHAPTER_ID_PATTERN.fullmatch(value):
            raise DraftNotFound(value)

    @staticmethod
    def _validate_draft_id(value: str) -> None:
        if not DRAFT_ID_PATTERN.fullmatch(value):
            raise DraftNotFound(value)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _atomic_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            text,
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(path)

    @classmethod
    def _atomic_json(cls, path: Path, payload: Any) -> None:
        cls._atomic_text(
            path,
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )
