from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.classroom.hashing import content_hash
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.models import ClassroomPackage
from app.classroom.repository import (
    ClassroomNotFoundError,
    ClassroomRepository,
)
from app.classroom.validation import ClassroomPackageValidator
from tools.register_seed_models import install_seed_models


def bootstrap(
    data_root: Path,
    *,
    seed_package_path: Path,
    model_seed_root: Path,
) -> dict:
    data_root = Path(data_root)
    install_seed_models(data_root, model_seed_root)
    models = TeachingModelRepository(data_root)
    package = ClassroomPackage.model_validate(
        json.loads(Path(seed_package_path).read_text(encoding="utf-8"))
    )
    report = ClassroomPackageValidator(
        model_resolver=models.get_registered
    ).validate(package)
    if not report.passed:
        raise ValueError(
            f"sample classroom validation failed: {report.model_dump(mode='json')}"
        )
    repository = ClassroomRepository(data_root)
    package_hash = content_hash(package)
    try:
        active = repository.get_active_release(package.package_id)
        if active.content_hash == package_hash:
            return {
                "action": "bootstrap_reuse",
                "package_id": active.package_id,
                "active_version": active.version,
                "content_hash": active.content_hash,
            }
    except ClassroomNotFoundError:
        pass

    draft_id = f"seed-{package.package_id}"
    try:
        draft = repository.get_draft(draft_id)
        if draft.content_hash != package_hash:
            draft = repository.update_draft(
                draft_id,
                draft.revision,
                package,
            )
    except ClassroomNotFoundError:
        draft = repository.create_draft(draft_id, package)
    receipt = repository.publish(draft_id, draft.revision)
    return receipt.model_dump(mode="json", exclude_none=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument(
        "--seed-package",
        type=Path,
        default=root
        / "backend"
        / "classroom_data"
        / "seed"
        / "calculus-foundations.json",
    )
    parser.add_argument(
        "--model-seeds",
        type=Path,
        default=root / "backend" / "classroom_data" / "model_seed",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            bootstrap(
                args.data_root,
                seed_package_path=args.seed_package,
                model_seed_root=args.model_seeds,
            ),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
