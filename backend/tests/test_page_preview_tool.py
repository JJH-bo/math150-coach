from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from app.tools.adapters.page_preview import PagePreviewAdapter, PagePreviewInputError
from app.tools.contracts import ToolExecutionContext
from classroom_fixtures import classroom_package_payload


def published_repository(tmp_path: Path) -> ClassroomRepository:
    repository = ClassroomRepository(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())
    draft = repository.create_draft("page-preview", package)
    repository.publish(draft.draft_id, draft.revision)
    return repository


def arguments(**changes) -> dict:
    payload = {
        "package_id": "calculus-foundations",
        "module_id": "limit-core",
        "viewports": "both",
        "reveal_steps": 2,
        "open_first_detail": True,
        "quality_profile": "standard",
    }
    payload.update(changes)
    return payload


def fake_worker(request_path: Path, report_path: Path, work_dir: Path) -> None:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    viewport_reports = []
    for viewport in request["viewports"]:
        screenshot = work_dir / f"{viewport['name']}.png"
        image = Image.new("RGB", (viewport["width"], viewport["height"]), "#101923")
        draw = ImageDraw.Draw(image)
        for index in range(30):
            color = (20 + index * 5, 80 + index * 3, 210 - index * 4)
            draw.rectangle(
                (20 + index * 3, 20, 22 + index * 3, viewport["height"] - 20),
                fill=color,
            )
        draw.rectangle((120, 20, viewport["width"] - 20, 160), fill="#33c3ff")
        draw.text((40, 60), "Verified learner preview", fill="#101923")
        image.save(screenshot)
        viewport_reports.append(
            {
                "name": viewport["name"],
                "viewport_width": viewport["width"],
                "viewport_height": viewport["height"],
                "screenshot": screenshot.name,
                "module_title": "Limit mechanism",
                "baseline_steps": 2,
                "formula_count": 1,
                "unrendered_math": 0,
                "model_expected": request["model_expected"],
                "model_canvas_visible": request["model_expected"],
                "horizontal_overflow": 0,
                "clipped_text": [],
                "accessibility_issues": [],
                "console_errors": [],
                "failed_requests": [],
            }
        )
    report_path.write_text(
        json.dumps(
            {
                "passed": True,
                "runtime": "classroom_runtime_v1",
                "package_id": request["package_id"],
                "module_id": request["module_id"],
                "release_version": request["release_version"],
                "viewports": viewport_reports,
            }
        ),
        encoding="utf-8",
    )


def execute(tmp_path: Path, monkeypatch, payload: dict | None = None):
    adapter = PagePreviewAdapter(
        published_repository(tmp_path / "data"),
        public_origin="https://classroom.example",
    )
    monkeypatch.setattr(adapter, "_run_worker", fake_worker)
    return adapter.execute(
        payload or arguments(),
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path / "work",
        ),
    )


def test_definition_is_verified_real_runtime_page_preview(tmp_path: Path) -> None:
    definition = PagePreviewAdapter(
        published_repository(tmp_path),
        public_origin="https://classroom.example",
    ).definition

    assert definition.tool_id == "page.preview"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.render"
    assert "url" not in definition.input_schema["properties"]
    assert "html" not in definition.input_schema["properties"]
    assert "real_learner_runtime" in definition.quality_gates


def test_page_preview_emits_desktop_mobile_and_quality_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    output = execute(tmp_path, monkeypatch)

    assert output.result["package_id"] == "calculus-foundations"
    assert output.result["module_id"] == "limit-core"
    assert output.result["viewport_count"] == 2
    assert output.result["validation"]["passed"] is True
    assert [artifact.name for artifact in output.artifacts] == [
        "preview-request.json",
        "desktop.png",
        "mobile.png",
        "preview-report.json",
    ]
    request = json.loads(
        (tmp_path / "work" / "preview-request.json").read_text(encoding="utf-8")
    )
    assert request["viewports"] == [
        {"name": "desktop", "width": 1440, "height": 960},
        {"name": "mobile", "width": 390, "height": 844},
    ]
    assert "origin" not in request


@pytest.mark.parametrize(
    "payload",
    [
        arguments(url="https://evil.example"),
        arguments(package_id="missing-package"),
        arguments(module_id="missing-module"),
        arguments(reveal_steps=21),
        arguments(viewports="tablet"),
        arguments(quality_profile="unbounded"),
    ],
)
def test_page_preview_rejects_external_or_unknown_targets(
    tmp_path: Path, monkeypatch, payload: dict
) -> None:
    adapter = PagePreviewAdapter(
        published_repository(tmp_path),
        public_origin="https://classroom.example",
    )
    monkeypatch.setattr(adapter, "_run_worker", fake_worker)

    with pytest.raises(PagePreviewInputError):
        adapter.execute(
            payload,
            ToolExecutionContext(
                job_id="tj-000000000000000000000000",
                work_dir=tmp_path / "work",
            ),
        )


def test_page_preview_rejects_nonlocal_plain_http_origin(tmp_path: Path) -> None:
    adapter = PagePreviewAdapter(
        published_repository(tmp_path),
        public_origin="http://classroom.example",
    )

    with pytest.raises(PagePreviewInputError, match="HTTPS"):
        adapter.execute(
            arguments(),
            ToolExecutionContext(
                job_id="tj-000000000000000000000000",
                work_dir=tmp_path / "work",
            ),
        )
