from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.classroom.model_contracts import (
    PreviewArtifact,
    PreviewError,
    PreviewJobRecord,
    PreviewViewport,
    utc_now,
)
from app.classroom.model_repository import TeachingModelRepository


PreviewRunner = Callable[[Path, Path], dict[str, Any]]


class TeachingModelPreviewService:
    def __init__(
        self,
        repository: TeachingModelRepository,
        *,
        runner: PreviewRunner | None = None,
        frontend_root: Path | None = None,
        worker_path: Path | None = None,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        self.repository = repository
        self.runner = runner or self._subprocess_runner
        self.frontend_root = frontend_root or repository_root / "frontend" / "model-runtime"
        self.worker_path = worker_path or repository_root / "tools" / "capture_model_preview.cjs"

    def request_preview(
        self,
        draft_id: str,
        *,
        scenario_id: str,
        viewport: PreviewViewport | dict[str, Any],
    ) -> PreviewJobRecord:
        draft = self.repository.get_draft(draft_id)
        if scenario_id not in {scenario.id for scenario in draft.manifest.scenarios}:
            raise ValueError(
                f"scenario {scenario_id!r} is not declared by model draft {draft_id!r}"
            )
        job = PreviewJobRecord(
            job_id=f"preview-{uuid4().hex[:20]}",
            draft_id=draft_id,
            draft_revision=draft.revision,
            draft_content_hash=draft.content_hash,
            model_id=draft.manifest.model_id,
            scenario_id=scenario_id,
            viewport=PreviewViewport.model_validate(viewport),
            status="queued",
        )
        return self.repository.put_preview_job(job)

    def run_preview(self, job_id: str) -> PreviewJobRecord:
        job = self.repository.get_preview_job(job_id)
        running = job.model_copy(update={"status": "running", "updated_at": utc_now()})
        self.repository.put_preview_job(running)
        artifact_dir = self.repository.artifact_path(job_id, "request.json").parent
        try:
            request_path = self._prepare_artifacts(running, artifact_dir)
            report = self.runner(request_path, artifact_dir)
            report_path = artifact_dir / "report.json"
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            artifacts = self._describe_artifacts(artifact_dir)
            result = running.model_copy(
                update={
                    "status": "succeeded",
                    "report": report,
                    "artifacts": artifacts,
                    "error": None,
                    "updated_at": utc_now(),
                }
            )
        except FileNotFoundError as exc:
            result = running.model_copy(
                update={
                    "status": "failed",
                    "error": PreviewError(
                        code="preview_environment_unavailable",
                        message=str(exc),
                        retryable=True,
                    ),
                    "updated_at": utc_now(),
                }
            )
        except Exception as exc:  # browser failures must become durable job state
            result = running.model_copy(
                update={
                    "status": "failed",
                    "error": PreviewError(
                        code="preview_execution_failed",
                        message=str(exc),
                        retryable=False,
                    ),
                    "updated_at": utc_now(),
                }
            )
        return self.repository.put_preview_job(result)

    def get_preview(self, job_id: str) -> PreviewJobRecord:
        return self.repository.get_preview_job(job_id)

    def artifact(self, job_id: str, name: str) -> Path:
        path = self.repository.artifact_path(job_id, name)
        if not path.is_file():
            raise FileNotFoundError(f"preview artifact {name!r} was not found")
        return path

    def _prepare_artifacts(
        self,
        job: PreviewJobRecord,
        artifact_dir: Path,
    ) -> Path:
        draft = self.repository.get_draft(job.draft_id)
        if draft.revision != job.draft_revision or draft.content_hash != job.draft_content_hash:
            raise ValueError("preview job source revision no longer matches its draft")
        scenario = next(
            scenario
            for scenario in draft.manifest.scenarios
            if scenario.id == job.scenario_id
        )
        for name in ("host.js", "preview.js", "preview.css"):
            shutil.copyfile(self.frontend_root / name, artifact_dir / name)
        html = (self.frontend_root / "preview.html").read_text(encoding="utf-8")
        html = html.replace(
            '<script type="module" src="./preview.js"></script>',
            '<script src="./request.js"></script>\n  '
            '<script type="module" src="./preview.js"></script>',
        )
        (artifact_dir / "preview.html").write_text(
            html,
            encoding="utf-8",
            newline="\n",
        )
        browser_request = {
            "manifest": draft.manifest.model_dump(mode="json", exclude_none=True),
            "source": draft.source,
            "scenario": scenario.model_dump(mode="json", exclude_none=True),
            "viewport": job.viewport.model_dump(mode="json"),
        }
        (artifact_dir / "request.js").write_text(
            "window.__TEACHING_PREVIEW_REQUEST__ = "
            + json.dumps(browser_request, ensure_ascii=False)
            + ";\n",
            encoding="utf-8",
            newline="\n",
        )
        request = {
            "job_id": job.job_id,
            "draft_id": job.draft_id,
            "draft_revision": job.draft_revision,
            "draft_content_hash": job.draft_content_hash,
            "model_id": job.model_id,
            "scenario_id": job.scenario_id,
            "viewport": job.viewport.model_dump(mode="json"),
            "preview_html": str((artifact_dir / "preview.html").resolve()),
            "screenshot_path": str((artifact_dir / "screenshot.png").resolve()),
        }
        request_path = artifact_dir / "request.json"
        request_path.write_text(
            json.dumps(request, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return request_path

    def _subprocess_runner(self, request_path: Path, artifact_dir: Path) -> dict:
        node = os.getenv("MODEL_PREVIEW_NODE", "node")
        completed = subprocess.run(
            [node, str(self.worker_path), str(request_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
        return json.loads(completed.stdout)

    @staticmethod
    def _describe_artifacts(artifact_dir: Path) -> list[PreviewArtifact]:
        artifacts = []
        media_types = {
            ".html": "text/html",
            ".js": "application/javascript",
            ".css": "text/css",
            ".json": "application/json",
            ".png": "image/png",
        }
        for path in sorted(artifact_dir.iterdir()):
            if not path.is_file():
                continue
            data = path.read_bytes()
            artifacts.append(
                PreviewArtifact(
                    name=path.name,
                    media_type=media_types.get(path.suffix, "application/octet-stream"),
                    size=len(data),
                    content_hash=f"sha256:{hashlib.sha256(data).hexdigest()}",
                )
            )
        return artifacts
