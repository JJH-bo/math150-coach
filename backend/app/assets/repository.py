from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.assets.models import AssetRecord


ASSET_ID = re.compile(r"^a-([a-f0-9]{64})$")
SAFE_FILENAME_CHARACTER = re.compile(r"[^A-Za-z0-9._-]+")
MEDIA_EXTENSIONS = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}


class AssetRepositoryError(ValueError):
    pass


class AssetNotFoundError(AssetRepositoryError):
    pass


class AssetPathError(AssetRepositoryError):
    pass


class AssetCorruptionError(AssetRepositoryError):
    pass


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class AssetRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve() / "assets"

    def put(
        self,
        data: bytes,
        *,
        media_type: str,
        extension: str,
        width: int,
        height: int,
        display_filename: str,
    ) -> tuple[AssetRecord, bool]:
        if not isinstance(data, bytes) or not 0 < len(data) <= 8 * 1024 * 1024:
            raise AssetRepositoryError(
                "asset bytes must contain from 1 to 8388608 bytes"
            )
        expected_extension = MEDIA_EXTENSIONS.get(media_type)
        if expected_extension is None or extension != expected_extension:
            raise AssetRepositoryError(
                "asset media type and extension must be a supported matching pair"
            )
        if not isinstance(width, int) or not isinstance(height, int):
            raise AssetRepositoryError("asset dimensions must be integers")
        if not 1 <= width <= 6000 or not 1 <= height <= 6000:
            raise AssetRepositoryError("asset dimensions must be from 1 to 6000")

        digest = hashlib.sha256(data).hexdigest()
        asset_id = f"a-{digest}"
        directory = self._asset_directory(asset_id)
        asset_path = directory / f"asset.{extension}"
        record_path = directory / "record.json"
        if asset_path.exists() or record_path.exists():
            if not asset_path.is_file() or not record_path.is_file():
                raise AssetCorruptionError(
                    f"asset {asset_id} has an incomplete repository record"
                )
            return self.get(asset_id), True

        safe_filename = self._safe_filename(display_filename, extension)
        payload: dict[str, Any] = {
            "asset_id": asset_id,
            "content_hash": f"sha256:{digest}",
            "media_type": media_type,
            "extension": extension,
            "width": width,
            "height": height,
            "size_bytes": len(data),
            "display_filename": safe_filename,
            "uri": f"/api/classroom/v1/assets/{asset_id}",
            "created_at": utc_now(),
        }
        payload["metadata_hash"] = self._metadata_hash(payload)
        record = AssetRecord.model_validate(payload)
        directory.mkdir(parents=True, exist_ok=True)
        byte_tmp = directory / f".asset.{uuid.uuid4().hex}.tmp"
        record_tmp = directory / f".record.{uuid.uuid4().hex}.tmp"
        try:
            byte_tmp.write_bytes(data)
            record_tmp.write_text(
                json.dumps(
                    record.model_dump(mode="json"),
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            os.replace(byte_tmp, asset_path)
            os.replace(record_tmp, record_path)
        finally:
            byte_tmp.unlink(missing_ok=True)
            record_tmp.unlink(missing_ok=True)
        return record, False

    def get(self, asset_id: str) -> AssetRecord:
        directory = self._asset_directory(asset_id)
        record_path = directory / "record.json"
        if not record_path.is_file():
            raise AssetNotFoundError(f"asset {asset_id} was not found")
        try:
            payload = json.loads(record_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("record root is not an object")
            record = AssetRecord.model_validate(payload)
        except (OSError, ValueError, json.JSONDecodeError, ValidationError) as exc:
            raise AssetCorruptionError(
                f"asset {asset_id} metadata is invalid"
            ) from exc
        metadata = record.model_dump(mode="json")
        stored_metadata_hash = metadata.pop("metadata_hash")
        if stored_metadata_hash != self._metadata_hash(metadata):
            raise AssetCorruptionError(
                f"asset {asset_id} metadata hash does not match"
            )
        if record.asset_id != asset_id:
            raise AssetCorruptionError(
                f"asset {asset_id} metadata identifies a different asset"
            )
        asset_path = directory / f"asset.{record.extension}"
        if not asset_path.is_file():
            raise AssetCorruptionError(f"asset {asset_id} bytes are missing")
        size = asset_path.stat().st_size
        if size != record.size_bytes:
            raise AssetCorruptionError(
                f"asset {asset_id} size does not match metadata"
            )
        digest = self._sha256(asset_path)
        if record.content_hash != f"sha256:{digest}" or asset_id != f"a-{digest}":
            raise AssetCorruptionError(f"asset {asset_id} hash does not match")
        return record

    def path(self, asset_id: str) -> Path:
        record = self.get(asset_id)
        return self._asset_directory(asset_id) / f"asset.{record.extension}"

    def _asset_directory(self, asset_id: str) -> Path:
        match = ASSET_ID.fullmatch(asset_id)
        if match is None:
            raise AssetPathError(f"unsafe asset identifier: {asset_id!r}")
        digest = match.group(1)
        directory = (self.root / "sha256" / digest[:2] / digest).resolve()
        try:
            directory.relative_to(self.root)
        except ValueError as exc:
            raise AssetPathError(f"asset path escapes repository: {asset_id!r}") from exc
        return directory

    @staticmethod
    def _safe_filename(value: str, extension: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AssetRepositoryError("display filename must be nonblank")
        basename = value.replace("\\", "/").split("/")[-1].strip()
        stem = basename.rsplit(".", 1)[0] if "." in basename else basename
        stem = SAFE_FILENAME_CHARACTER.sub("-", stem).strip(".-_")
        if not stem:
            stem = "asset"
        maximum_stem = 119 - len(extension)
        return f"{stem[:maximum_stem]}.{extension}"

    @staticmethod
    def _metadata_hash(payload: dict[str, Any]) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(canonical).hexdigest()}"

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
