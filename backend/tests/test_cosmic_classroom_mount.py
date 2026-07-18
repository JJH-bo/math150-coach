from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.classroom.model_repository import TeachingModelRepository
from app.classroom.repository import ClassroomRepository
from app.classroom.runtime import ClassroomRuntimeService
from app.main import create_app
from tools.bootstrap_ai_classroom import bootstrap


ROOT = Path(__file__).resolve().parents[2]


def test_learner_and_mixed_mount_classroom_but_internal_does_not() -> None:
    learner = TestClient(create_app("learner"))
    mixed = TestClient(create_app("mixed"))
    internal = TestClient(create_app("internal"))

    assert learner.get("/classroom/").status_code == 200
    assert mixed.get("/classroom/app.js").status_code == 200
    assert learner.get("/classroom-runtime/host.js").status_code == 200
    assert internal.get("/classroom/").status_code == 404
    assert internal.get("/classroom-runtime/host.js").status_code == 404


def test_new_classroom_frontend_does_not_call_legacy_api() -> None:
    source = TestClient(create_app("learner")).get("/classroom/app.js").text.lower()

    assert "/api/classroom/v1" in source
    assert "/api/challenge" not in source


def test_bootstrap_publishes_bound_sample_and_is_idempotent(tmp_path) -> None:
    first = bootstrap(
        tmp_path,
        seed_package_path=ROOT
        / "backend"
        / "classroom_data"
        / "seed"
        / "calculus-foundations.json",
        model_seed_root=ROOT / "backend" / "classroom_data" / "model_seed",
    )
    second = bootstrap(
        tmp_path,
        seed_package_path=ROOT
        / "backend"
        / "classroom_data"
        / "seed"
        / "calculus-foundations.json",
        model_seed_root=ROOT / "backend" / "classroom_data" / "model_seed",
    )
    runtime = ClassroomRuntimeService(
        ClassroomRepository(tmp_path),
        model_repository=TeachingModelRepository(tmp_path),
    )
    module = runtime.module("calculus-foundations", "limit-core")

    assert first["active_version"] == second["active_version"]
    assert runtime.catalog()["packages"][0]["package_id"] == "calculus-foundations"
    assert module["model_instances"][0]["model_id"] == "limit-neighborhood-2d"
    assert len(module["model_bindings"]) == 2
