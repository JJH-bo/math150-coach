from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from app.assets.images import AssetImageError, normalize_image, transform_image
from app.assets.models import AssetRecord
from app.assets.repository import (
    AssetNotFoundError,
    AssetRepository,
    AssetRepositoryError,
)
from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolJobState,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)
from app.tools.repository import ToolJobRepository, ToolJobRepositoryError


JOB_ID = re.compile(r"^tj-[a-f0-9]{24}$")
ARTIFACT_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
SUPPORTED_MEDIA = {"image/png", "image/jpeg", "image/webp"}
INGEST_FIELDS = {
    "filename",
    "alt_text",
    "output_format",
    "quality",
    "background",
    "declared_media_type",
    "content_base64",
    "source_job_id",
    "source_artifact_name",
}
TRANSFORM_FIELDS = {
    "asset_id",
    "width",
    "height",
    "mode",
    "output_format",
    "quality",
    "allow_upscale",
    "background",
}


class AssetToolInputError(ValueError):
    pass


ASSET_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "asset_id",
        "content_hash",
        "media_type",
        "extension",
        "width",
        "height",
        "size_bytes",
        "display_filename",
        "uri",
    ],
    "properties": {
        "asset_id": {"type": "string", "pattern": "^a-[a-f0-9]{64}$"},
        "content_hash": {
            "type": "string",
            "pattern": "^sha256:[a-f0-9]{64}$",
        },
        "media_type": {
            "type": "string",
            "enum": ["image/png", "image/jpeg", "image/webp"],
        },
        "extension": {"type": "string", "enum": ["png", "jpg", "webp"]},
        "width": {"type": "integer", "minimum": 1, "maximum": 6000},
        "height": {"type": "integer", "minimum": 1, "maximum": 6000},
        "size_bytes": {"type": "integer", "minimum": 1, "maximum": 8388608},
        "display_filename": {"type": "string"},
        "uri": {"type": "string", "pattern": "^/api/classroom/v1/assets/a-"},
    },
}
VALIDATION_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "required": [
        "source_kind",
        "metadata_removed",
        "second_decode_verified",
    ],
    "properties": {
        "source_kind": {"type": "string"},
        "metadata_removed": {"type": "boolean"},
        "second_decode_verified": {"type": "boolean"},
    },
}
ASSET_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["asset", "duplicate", "validation"],
    "properties": {
        "asset": ASSET_SCHEMA,
        "duplicate": {"type": "boolean"},
        "validation": VALIDATION_SCHEMA,
    },
}
TRANSFORM_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["asset", "source_asset_id", "duplicate", "validation"],
    "properties": {
        "asset": ASSET_SCHEMA,
        "source_asset_id": {"type": "string", "pattern": "^a-[a-f0-9]{64}$"},
        "duplicate": {"type": "boolean"},
        "validation": VALIDATION_SCHEMA,
    },
}


class AssetIngestAdapter:
    definition = ToolDefinition(
        tool_id="asset.ingest",
        version="1.0.0",
        title="Ingest a verified persistent classroom image",
        description=(
            "Normalize an explicit base64 image or a successful Studio job image "
            "artifact into immutable content-addressed classroom storage. Performs "
            "signature, dimensions, animation, metadata, and second-decode gates."
        ),
        category="asset",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.AUTHOR,
        execution_mode=ToolExecutionMode.SYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=30,
        max_artifacts=2,
        max_artifact_bytes=16 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["filename", "alt_text", "output_format"],
            "properties": {
                "filename": {"type": "string", "minLength": 1, "maxLength": 120},
                "alt_text": {"type": "string", "minLength": 8, "maxLength": 1000},
                "output_format": {
                    "type": "string",
                    "enum": ["png", "jpeg", "webp"],
                },
                "quality": {
                    "type": "integer",
                    "minimum": 40,
                    "maximum": 100,
                    "default": 90,
                },
                "background": {
                    "type": "string",
                    "pattern": "^#[a-fA-F0-9]{6}$",
                    "default": "#ffffff",
                },
                "declared_media_type": {
                    "type": "string",
                    "enum": ["image/png", "image/jpeg", "image/webp"],
                },
                "content_base64": {
                    "type": "string",
                    "minLength": 4,
                    "maxLength": 12 * 1024 * 1024,
                },
                "source_job_id": {
                    "type": "string",
                    "pattern": "^tj-[a-f0-9]{24}$",
                },
                "source_artifact_name": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$",
                },
            },
            "oneOf": [
                {
                    "required": ["declared_media_type", "content_base64"],
                    "not": {
                        "anyOf": [
                            {"required": ["source_job_id"]},
                            {"required": ["source_artifact_name"]},
                        ]
                    },
                },
                {
                    "required": ["source_job_id", "source_artifact_name"],
                    "not": {
                        "anyOf": [
                            {"required": ["declared_media_type"]},
                            {"required": ["content_base64"]},
                        ]
                    },
                },
            ],
        },
        output_schema=ASSET_OUTPUT_SCHEMA,
        output_media_types=[
            "image/png",
            "image/jpeg",
            "image/webp",
            "application/json",
        ],
        quality_gates=[
            "mime_signature_match",
            "bounded_still_image",
            "metadata_removed",
            "second_decode_verified",
            "content_addressed_storage",
            "artifact_hash_verified",
        ],
        upstream_project="Pillow 12.3.0 and project AssetRepository",
        license="HPND / Project-owned",
    )

    def __init__(
        self,
        assets: AssetRepository,
        jobs: ToolJobRepository,
    ) -> None:
        self.assets = assets
        self.jobs = jobs

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        values = self._validate(arguments)
        data, declared_media_type, source_kind, source_evidence = self._source(values)
        try:
            normalized = normalize_image(
                data,
                declared_media_type,
                values["output_format"],
                quality=values["quality"],
                background=values["background"],
            )
            record, duplicate = self.assets.put(
                normalized.data,
                media_type=normalized.media_type,
                extension=normalized.extension,
                width=normalized.width,
                height=normalized.height,
                display_filename=values["filename"],
            )
        except (AssetImageError, AssetRepositoryError) as exc:
            raise AssetToolInputError(str(exc)) from exc

        validation = {
            "passed": True,
            "source_kind": source_kind,
            "source_format": normalized.source_format,
            "declared_media_type": declared_media_type,
            "output_media_type": normalized.media_type,
            "width": normalized.width,
            "height": normalized.height,
            "metadata_removed": normalized.metadata_removed,
            "second_decode_verified": normalized.second_decode_verified,
            "alt_text": values["alt_text"],
            **source_evidence,
        }
        artifacts = _write_artifacts(context.work_dir, normalized.data, record, validation)
        return ToolExecutionResult(
            result={
                "asset": _public_asset(record),
                "duplicate": duplicate,
                "validation": validation,
            },
            artifacts=artifacts,
            metrics={
                "input_bytes": len(data),
                "output_bytes": len(normalized.data),
                "width": normalized.width,
                "height": normalized.height,
                "duplicate": duplicate,
            },
        )

    @staticmethod
    def _validate(arguments: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise AssetToolInputError("asset ingest arguments must be an object")
        unknown = set(arguments) - INGEST_FIELDS
        if unknown:
            raise AssetToolInputError(f"unsupported asset ingest fields: {sorted(unknown)}")
        filename = arguments.get("filename")
        alt_text = arguments.get("alt_text")
        output_format = arguments.get("output_format")
        if not isinstance(filename, str) or not 1 <= len(filename.strip()) <= 120:
            raise AssetToolInputError("filename must contain from 1 to 120 characters")
        if not isinstance(alt_text, str) or not 8 <= len(alt_text.strip()) <= 1000:
            raise AssetToolInputError("alt_text must contain from 8 to 1000 characters")
        if any(character in alt_text for character in ("<", ">", "\x00")):
            raise AssetToolInputError("alt_text contains unsafe markup")
        if output_format not in {"png", "jpeg", "webp"}:
            raise AssetToolInputError("output_format must be png, jpeg, or webp")
        has_upload = "content_base64" in arguments or "declared_media_type" in arguments
        has_job = "source_job_id" in arguments or "source_artifact_name" in arguments
        if has_upload == has_job:
            raise AssetToolInputError("asset ingest requires exactly one source")
        if has_upload and not {
            "content_base64",
            "declared_media_type",
        } <= set(arguments):
            raise AssetToolInputError(
                "base64 source requires content_base64 and declared_media_type"
            )
        if has_job and not {
            "source_job_id",
            "source_artifact_name",
        } <= set(arguments):
            raise AssetToolInputError(
                "job source requires source_job_id and source_artifact_name"
            )
        return {
            **arguments,
            "filename": filename.strip(),
            "alt_text": alt_text.strip(),
            "quality": arguments.get("quality", 90),
            "background": arguments.get("background", "#ffffff"),
        }

    def _source(
        self,
        arguments: dict[str, Any],
    ) -> tuple[bytes, str, str, dict[str, Any]]:
        if "content_base64" in arguments:
            encoded = arguments["content_base64"]
            if not isinstance(encoded, str) or not 4 <= len(encoded) <= 12 * 1024 * 1024:
                raise AssetToolInputError("content_base64 is outside the accepted size")
            try:
                data = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise AssetToolInputError("content_base64 is not strict base64") from exc
            declared = arguments["declared_media_type"]
            if declared not in SUPPORTED_MEDIA:
                raise AssetToolInputError("declared_media_type is unsupported")
            return data, declared, "base64_upload", {
                "source_sha256": "sha256:" + hashlib.sha256(data).hexdigest()
            }

        job_id = arguments["source_job_id"]
        artifact_name = arguments["source_artifact_name"]
        if not isinstance(job_id, str) or JOB_ID.fullmatch(job_id) is None:
            raise AssetToolInputError("source_job_id is invalid")
        if not isinstance(artifact_name, str) or ARTIFACT_NAME.fullmatch(artifact_name) is None:
            raise AssetToolInputError("source_artifact_name is invalid")
        try:
            job = self.jobs.get(job_id)
        except ToolJobRepositoryError as exc:
            raise AssetToolInputError(f"source job was not found: {job_id}") from exc
        if job.state != ToolJobState.SUCCEEDED:
            raise AssetToolInputError("source job must be succeeded")
        artifact = next(
            (item for item in job.artifacts if item.name == artifact_name),
            None,
        )
        if artifact is None:
            raise AssetToolInputError("source artifact was not found in the job")
        if artifact.media_type not in SUPPORTED_MEDIA:
            raise AssetToolInputError("source artifact media type is unsupported")
        try:
            data = self.jobs.artifact_path(job_id, artifact_name).read_bytes()
        except (OSError, ToolJobRepositoryError) as exc:
            raise AssetToolInputError("source artifact bytes could not be read") from exc
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        if digest != artifact.sha256:
            raise AssetToolInputError("source artifact hash does not match its job record")
        return data, artifact.media_type, "studio_job_artifact", {
            "source_job_id": job_id,
            "source_artifact_name": artifact_name,
            "source_sha256": digest,
        }


class AssetTransformAdapter:
    definition = ToolDefinition(
        tool_id="asset.transform",
        version="1.0.0",
        title="Create a verified classroom image variant",
        description=(
            "Transform an immutable classroom image with bounded contain or cover "
            "geometry, Lanczos resampling, explicit upscaling policy, safe alpha "
            "compositing, metadata removal, and persistent content addressing."
        ),
        category="asset",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.SYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=30,
        max_artifacts=2,
        max_artifact_bytes=16 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": sorted(TRANSFORM_FIELDS),
            "properties": {
                "asset_id": {"type": "string", "pattern": "^a-[a-f0-9]{64}$"},
                "width": {"type": "integer", "minimum": 32, "maximum": 4096},
                "height": {"type": "integer", "minimum": 32, "maximum": 4096},
                "mode": {"type": "string", "enum": ["contain", "cover"]},
                "output_format": {
                    "type": "string",
                    "enum": ["png", "jpeg", "webp"],
                },
                "quality": {"type": "integer", "minimum": 40, "maximum": 100},
                "allow_upscale": {"type": "boolean"},
                "background": {
                    "type": "string",
                    "pattern": "^#[a-fA-F0-9]{6}$",
                },
            },
        },
        output_schema=TRANSFORM_OUTPUT_SCHEMA,
        output_media_types=[
            "image/png",
            "image/jpeg",
            "image/webp",
            "application/json",
        ],
        quality_gates=[
            "registered_source_asset",
            "bounded_output_geometry",
            "lanczos_resampling",
            "explicit_upscale_policy",
            "metadata_removed",
            "second_decode_verified",
            "content_addressed_storage",
        ],
        upstream_project="Pillow 12.3.0 and project AssetRepository",
        license="HPND / Project-owned",
    )

    def __init__(self, assets: AssetRepository) -> None:
        self.assets = assets

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        if not isinstance(arguments, dict):
            raise AssetToolInputError("asset transform arguments must be an object")
        unknown = set(arguments) - TRANSFORM_FIELDS
        if unknown:
            raise AssetToolInputError(
                f"unsupported asset transform fields: {sorted(unknown)}"
            )
        missing = TRANSFORM_FIELDS - set(arguments)
        if missing:
            raise AssetToolInputError(
                f"asset transform fields are missing: {sorted(missing)}"
            )
        asset_id = arguments["asset_id"]
        try:
            source = self.assets.get(asset_id)
            source_path = self.assets.path(asset_id)
            normalized = transform_image(
                source_path,
                source_media_type=source.media_type,
                width=arguments["width"],
                height=arguments["height"],
                mode=arguments["mode"],
                output_format=arguments["output_format"],
                quality=arguments["quality"],
                allow_upscale=arguments["allow_upscale"],
                background=arguments["background"],
            )
            display_stem = source.display_filename.rsplit(".", 1)[0]
            record, duplicate = self.assets.put(
                normalized.data,
                media_type=normalized.media_type,
                extension=normalized.extension,
                width=normalized.width,
                height=normalized.height,
                display_filename=(
                    f"{display_stem}-{normalized.width}x{normalized.height}."
                    f"{normalized.extension}"
                ),
            )
        except AssetNotFoundError as exc:
            raise AssetToolInputError(f"source asset was not found: {asset_id}") from exc
        except (AssetImageError, AssetRepositoryError, TypeError, KeyError) as exc:
            raise AssetToolInputError(str(exc)) from exc

        validation = {
            "passed": True,
            "source_kind": "registered_asset",
            "source_asset_id": source.asset_id,
            "source_content_hash": source.content_hash,
            "source_width": source.width,
            "source_height": source.height,
            "source_render_width": normalized.source_render_width,
            "source_render_height": normalized.source_render_height,
            "width": normalized.width,
            "height": normalized.height,
            "mode": arguments["mode"],
            "allow_upscale": arguments["allow_upscale"],
            "resampling": normalized.resampling,
            "metadata_removed": normalized.metadata_removed,
            "second_decode_verified": normalized.second_decode_verified,
        }
        artifacts = _write_artifacts(context.work_dir, normalized.data, record, validation)
        return ToolExecutionResult(
            result={
                "asset": _public_asset(record),
                "source_asset_id": source.asset_id,
                "duplicate": duplicate,
                "validation": validation,
            },
            artifacts=artifacts,
            metrics={
                "source_width": source.width,
                "source_height": source.height,
                "output_width": normalized.width,
                "output_height": normalized.height,
                "output_bytes": len(normalized.data),
                "duplicate": duplicate,
            },
        )


def _public_asset(record: AssetRecord) -> dict[str, Any]:
    return {
        "asset_id": record.asset_id,
        "content_hash": record.content_hash,
        "media_type": record.media_type,
        "extension": record.extension,
        "width": record.width,
        "height": record.height,
        "size_bytes": record.size_bytes,
        "display_filename": record.display_filename,
        "uri": record.uri,
    }


def _write_artifacts(
    work_dir: Path,
    data: bytes,
    record: AssetRecord,
    validation: dict[str, Any],
) -> list[ToolProducedArtifact]:
    work_dir.mkdir(parents=True, exist_ok=True)
    asset_name = f"asset.{record.extension}"
    (work_dir / asset_name).write_bytes(data)
    (work_dir / "validation-report.json").write_text(
        json.dumps(validation, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return [
        ToolProducedArtifact(
            name=asset_name,
            media_type=record.media_type,
            source_path=asset_name,
        ),
        ToolProducedArtifact(
            name="validation-report.json",
            media_type="application/json",
            source_path="validation-report.json",
        ),
    ]
