from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.classroom.model_contracts import (
    ModelDraftRecord,
    TeachingModelManifest,
    model_content_hash,
)
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.model_validation import TeachingModelValidator


def install_seed_models(
    data_root: Path,
    seed_root: Path,
) -> list[dict]:
    repository = TeachingModelRepository(data_root)
    validator = TeachingModelValidator()
    receipts = []
    for directory in sorted(path for path in seed_root.iterdir() if path.is_dir()):
        manifest = TeachingModelManifest.model_validate(
            json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        )
        source = (directory / "source.js").read_text(encoding="utf-8")
        report = validator.validate(manifest, source)
        if not report.passed:
            raise ValueError(
                f"seed model {manifest.model_id!r} failed validation: "
                f"{report.model_dump(mode='json')}"
            )
        draft = ModelDraftRecord(
            draft_id=f"seed-{manifest.model_id}",
            revision=1,
            content_hash=model_content_hash(manifest, source),
            manifest=manifest,
            source=source,
        )
        registered = repository.register(
            draft,
            validation=report.model_dump(mode="json"),
            preview_job_id="checked-in-seed",
        )
        receipts.append(
            {
                "model_id": registered.model_id,
                "version": registered.version,
                "content_hash": registered.content_hash,
            }
        )
    return receipts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument(
        "--seed-root",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "backend"
        / "classroom_data"
        / "model_seed",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            {"registered_models": install_seed_models(args.data_root, args.seed_root)},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
