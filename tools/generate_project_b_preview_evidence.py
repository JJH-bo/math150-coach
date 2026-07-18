from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from app.classroom.model_contracts import TeachingModelManifest
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.preview import TeachingModelPreviewService


CASES = (
    ("limit-neighborhood-2d", "approach-target", 1280, 800, "limit-desktop"),
    ("binary-search-array", "find-23", 390, 844, "binary-search-mobile"),
)


def generate(seed_root: Path, output_root: Path) -> list[dict]:
    output_root.mkdir(parents=True, exist_ok=True)
    summary = []
    with tempfile.TemporaryDirectory(prefix="classroom-preview-") as temporary:
        repository = TeachingModelRepository(Path(temporary))
        service = TeachingModelPreviewService(repository)
        for model_id, scenario_id, width, height, artifact_name in CASES:
            directory = seed_root / model_id
            manifest = TeachingModelManifest.model_validate(
                json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            )
            source = (directory / "source.js").read_text(encoding="utf-8")
            draft = repository.create_draft(
                f"{model_id}-evidence",
                manifest,
                source,
            )
            job = service.request_preview(
                draft.draft_id,
                scenario_id=scenario_id,
                viewport={"width": width, "height": height},
            )
            result = service.run_preview(job.job_id)
            if result.status != "succeeded":
                raise RuntimeError(result.error)
            screenshot_name = f"{artifact_name}.png"
            report_name = f"{artifact_name}.json"
            shutil.copyfile(
                service.artifact(job.job_id, "screenshot.png"),
                output_root / screenshot_name,
            )
            durable_report = {
                **result.report,
                "job_id": "<generated-preview-job>",
            }
            (output_root / report_name).write_text(
                json.dumps(
                    durable_report,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            summary.append(
                {
                    "model_id": model_id,
                    "scenario_id": scenario_id,
                    "viewport": {"width": width, "height": height},
                    "screenshot": screenshot_name,
                    "report": report_name,
                    "draft_content_hash": draft.content_hash,
                }
            )
    (output_root / "summary.json").write_text(
        json.dumps({"artifacts": summary}, ensure_ascii=False, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return summary


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seed-root",
        type=Path,
        default=root / "backend" / "classroom_data" / "model_seed",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=root / "docs" / "preview-artifacts" / "project-b",
    )
    args = parser.parse_args()
    print(json.dumps(generate(args.seed_root, args.output_root), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
