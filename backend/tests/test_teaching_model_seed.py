from __future__ import annotations

import json
from pathlib import Path

from app.classroom.model_repository import TeachingModelRepository
from app.classroom.models import ClassroomPackage
from app.classroom.validation import ClassroomPackageValidator
from tools.register_seed_models import install_seed_models


ROOT = Path(__file__).resolve().parents[2]
SEED_ROOT = ROOT / "backend" / "classroom_data" / "model_seed"


def test_reference_models_install_with_deterministic_versions(tmp_path) -> None:
    receipts = install_seed_models(tmp_path, SEED_ROOT)

    assert [(item["model_id"], item["version"]) for item in receipts] == [
        ("binary-search-array", "m-f68d8ad029754c37"),
        ("limit-neighborhood-2d", "m-9d599c49d7916566"),
    ]


def test_sample_classroom_pins_and_validates_limit_model(tmp_path) -> None:
    install_seed_models(tmp_path, SEED_ROOT)
    repository = TeachingModelRepository(tmp_path)
    package = ClassroomPackage.model_validate(
        json.loads(
            (
                ROOT
                / "backend"
                / "classroom_data"
                / "seed"
                / "calculus-foundations.json"
            ).read_text(encoding="utf-8")
        )
    )

    report = ClassroomPackageValidator(
        model_resolver=repository.get_registered
    ).validate(package)

    assert report.passed is True
    assert package.model_instances[0].model_version == "m-9d599c49d7916566"
    assert len(package.model_bindings) == 2
