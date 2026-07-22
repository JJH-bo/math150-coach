from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from app.tools.adapters.pdf_export import normalize_pdf_metadata
from app.tools.adapters.reveal_export import RevealExportAdapter
from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)
from app.tools.lesson_contracts import SemanticLesson
from app.tools.lesson_validation import normalize_lesson


class PackageExportError(ValueError):
    pass


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class PackageExportAdapter:
    definition = ToolDefinition(
        tool_id="export.package",
        version="1.0.0",
        title="Verified portable lesson package export",
        description=(
            "Bundle one semantic lesson, self-contained HTML, normalized PDF, "
            "render evidence, and a cryptographic manifest into a deterministic "
            "path-safe ZIP for archival or transfer."
        ),
        category="export",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=120,
        max_artifacts=8,
        max_artifact_bytes=256 * 1024 * 1024,
        input_schema=SemanticLesson.model_json_schema(),
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["schema_version", "content_hash", "slide_count", "manifest"],
            "properties": {
                "schema_version": {"type": "string"},
                "content_hash": {"type": "string"},
                "slide_count": {"type": "integer"},
                "manifest": {"type": "object"},
            },
        },
        output_media_types=["application/json", "application/zip"],
        quality_gates=[
            "semantic_lesson_contract",
            "cross_format_content_identity",
            "cryptographic_file_manifest",
            "zip_path_containment",
            "deterministic_archive_metadata",
        ],
        upstream_project="Python standard library zipfile",
        license="PSF-2.0",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        lesson = normalize_lesson(arguments)
        reveal = RevealExportAdapter().execute(arguments, context)
        content_hash = reveal.result["content_hash"]
        pdf_path = context.work_dir / "lesson.pdf"
        normalize_pdf_metadata(pdf_path, lesson.title, content_hash)
        source_paths = [
            context.work_dir / "lesson-spec.json",
            context.work_dir / "lesson.html",
            pdf_path,
            context.work_dir / "render-report.json",
            *[
                context.work_dir / f"slide-{index:03d}.png"
                for index in range(1, len(lesson.slides) + 1)
            ],
        ]
        media_types = {
            ".json": "application/json",
            ".html": "text/html",
            ".pdf": "application/pdf",
            ".png": "image/png",
        }
        files = [
            {
                "path": path.name,
                "media_type": media_types[path.suffix],
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
            for path in sorted(source_paths, key=lambda item: item.name)
        ]
        manifest = {
            "schema_version": "lesson_package_v1",
            "content_hash": content_hash,
            "lesson_schema_version": lesson.schema_version,
            "slide_count": len(lesson.slides),
            "files": files,
        }
        manifest_payload = (
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8")
        manifest_path = context.work_dir / "package-manifest.json"
        manifest_path.write_bytes(manifest_payload)
        archive_path = context.work_dir / "lesson-package.zip"
        entries: list[tuple[str, bytes]] = [
            (path.name, path.read_bytes()) for path in source_paths
        ]
        entries.append((manifest_path.name, manifest_payload))
        with zipfile.ZipFile(
            archive_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for name, payload in sorted(entries, key=lambda item: item[0]):
                if Path(name).is_absolute() or ".." in Path(name).parts:
                    raise PackageExportError(f"unsafe package path: {name}")
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, payload, compresslevel=9)
        if not archive_path.is_file() or archive_path.stat().st_size == 0:
            raise PackageExportError("portable lesson package was not created")
        return ToolExecutionResult(
            result={
                "schema_version": "lesson_package_v1",
                "content_hash": content_hash,
                "slide_count": len(lesson.slides),
                "manifest": manifest,
            },
            artifacts=[
                ToolProducedArtifact(
                    name="lesson-spec.json",
                    media_type="application/json",
                    source_path="lesson-spec.json",
                ),
                ToolProducedArtifact(
                    name="lesson-package.zip",
                    media_type="application/zip",
                    source_path="lesson-package.zip",
                ),
                ToolProducedArtifact(
                    name="package-manifest.json",
                    media_type="application/json",
                    source_path="package-manifest.json",
                ),
            ],
            metrics={
                "slide_count": len(lesson.slides),
                "packaged_file_count": len(files) + 1,
                "archive_bytes": archive_path.stat().st_size,
            },
        )
