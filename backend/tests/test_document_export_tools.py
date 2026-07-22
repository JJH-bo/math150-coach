from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import zipfile
from pathlib import Path, PurePosixPath

import pytest
from PIL import Image, ImageStat
from pypdf import PdfReader

from app.tools.adapters.html_export import HtmlExportAdapter
from app.tools.adapters.package_export import PackageExportAdapter
from app.tools.adapters.pdf_export import PdfExportAdapter
from app.tools.contracts import ToolExecutionContext
from test_semantic_lesson import lesson_payload


def require_runtime() -> None:
    if not (os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")):
        pytest.skip("Node runtime is unavailable")
    if not os.getenv("NODE_PATH"):
        pytest.skip("NODE_PATH is unavailable")


def execute(adapter, tmp_path: Path):
    require_runtime()
    return adapter.execute(
        lesson_payload(),
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def test_document_export_definitions_are_verified_and_independent() -> None:
    definitions = [
        PdfExportAdapter().definition,
        HtmlExportAdapter().definition,
        PackageExportAdapter().definition,
    ]

    assert [definition.tool_id for definition in definitions] == [
        "export.pdf",
        "export.html",
        "export.package",
    ]
    assert all(definition.quality_tier.value == "verified" for definition in definitions)
    assert all(definition.required_scope.value == "studio.render" for definition in definitions)


def test_pdf_export_has_metadata_text_pages_and_rendered_evidence(tmp_path: Path) -> None:
    output = execute(PdfExportAdapter(), tmp_path)

    assert [artifact.name for artifact in output.artifacts] == [
        "lesson-spec.json",
        "lesson.pdf",
        "pdf-report.json",
        "page-001.png",
        "page-002.png",
        "page-003.png",
        "page-004.png",
    ]
    report = output.result["pdf_report"]
    assert report["passed"] is True
    assert report["page_count"] == 4
    assert report["missing_text"] == []
    reader = PdfReader(tmp_path / "lesson.pdf")
    assert reader.metadata.title == lesson_payload()["title"]
    assert reader.metadata.author == "Math150 Coach"
    assert reader.metadata.subject == output.result["content_hash"]
    for index in range(1, 5):
        with Image.open(tmp_path / f"page-{index:03d}.png") as image:
            assert image.size == (1280, 720)
            assert sum(ImageStat.Stat(image.convert("RGB")).var) > 1


def test_html_export_is_self_contained_and_audited(tmp_path: Path) -> None:
    output = execute(HtmlExportAdapter(), tmp_path)

    assert [artifact.name for artifact in output.artifacts] == [
        "lesson-spec.json",
        "lesson.html",
        "html-audit.json",
        "slide-001.png",
        "slide-002.png",
        "slide-003.png",
        "slide-004.png",
    ]
    audit = output.result["html_audit"]
    assert audit["passed"] is True
    assert audit["external_resource_urls"] == []
    assert audit["content_hash_matches"] is True
    html = (tmp_path / "lesson.html").read_text(encoding="utf-8")
    assert re.search(r"<(?:script|link|img)[^>]+(?:src|href)=\"https?://", html) is None
    assert "STUDIO_API_KEY" not in html
    assert str(tmp_path) not in html


def test_portable_package_manifest_hashes_paths_and_cross_format_identity(
    tmp_path: Path,
) -> None:
    pdf = execute(PdfExportAdapter(), tmp_path / "pdf")
    html = execute(HtmlExportAdapter(), tmp_path / "html")
    package = execute(PackageExportAdapter(), tmp_path / "package")

    assert pdf.result["content_hash"] == html.result["content_hash"]
    assert html.result["content_hash"] == package.result["content_hash"]
    assert [artifact.name for artifact in package.artifacts] == [
        "lesson-spec.json",
        "lesson-package.zip",
        "package-manifest.json",
    ]
    manifest = json.loads(
        (tmp_path / "package" / "package-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["content_hash"] == package.result["content_hash"]
    assert manifest["schema_version"] == "lesson_package_v1"
    with zipfile.ZipFile(tmp_path / "package" / "lesson-package.zip") as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert "package-manifest.json" in names
        for name in names:
            path = PurePosixPath(name)
            assert not path.is_absolute()
            assert ".." not in path.parts
        for item in manifest["files"]:
            assert sha256(archive.read(item["path"])) == item["sha256"]
        packaged_manifest = json.loads(archive.read("package-manifest.json"))
        assert packaged_manifest == manifest
