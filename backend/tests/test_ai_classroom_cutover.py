from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REMOVED_ROUTE_PREFIXES = (
    "/api/v1",
    "/api/learner/v1",
    "/api/challenge/v1",
    "/trainer",
)
REMOVED_PRODUCT_PATHS = (
    "backend/app/api/v1",
    "backend/app/api/learner",
    "backend/app/api/challenge",
    "backend/app/catalog",
    "backend/app/challenge",
    "backend/app/core",
    "backend/app/logic_graph",
    "backend/app/services",
    "backend/app/training",
    "backend/catalog_authoring",
    "backend/catalog_data",
    "backend/challenge_data",
    "evals",
    "frontend/space",
    "frontend/app.js",
    "frontend/index.html",
    "frontend/styles.css",
    "tools/run_real_attempt_lab.py",
)


def test_mixed_root_is_the_canonical_classroom_entry() -> None:
    client = TestClient(create_app("mixed"), follow_redirects=False)

    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/classroom/"
    assert client.get("/classroom/").status_code == 200


def test_profiles_expose_only_studio_and_classroom_surfaces() -> None:
    internal_paths = set(create_app("internal").openapi()["paths"])
    learner_paths = set(create_app("learner").openapi()["paths"])
    mixed_paths = set(create_app("mixed").openapi()["paths"])

    assert any(path.startswith("/api/studio/v1") for path in internal_paths)
    assert not any(path.startswith("/api/classroom/v1") for path in internal_paths)
    assert any(path.startswith("/api/classroom/v1") for path in learner_paths)
    assert not any(path.startswith("/api/studio/v1") for path in learner_paths)
    assert any(path.startswith("/api/studio/v1") for path in mixed_paths)
    assert any(path.startswith("/api/classroom/v1") for path in mixed_paths)

    for paths in (internal_paths, learner_paths, mixed_paths):
        assert not any(
            path.startswith(prefix)
            for prefix in REMOVED_ROUTE_PREFIXES
            for path in paths
        )


def test_removed_product_entries_are_not_served() -> None:
    client = TestClient(create_app("mixed"))

    for path in (
        "/trainer/",
        "/api/v1/health",
        "/api/learner/v1/questions",
        "/api/challenge/v1/health",
    ):
        assert client.get(path).status_code == 404


def test_training_product_implementation_is_absent() -> None:
    for relative_path in REMOVED_PRODUCT_PATHS:
        assert not (REPOSITORY_ROOT / relative_path).exists(), relative_path


def test_retained_application_has_no_legacy_imports() -> None:
    retained_roots = (
        REPOSITORY_ROOT / "backend/app/classroom",
        REPOSITORY_ROOT / "backend/app/api/classroom",
        REPOSITORY_ROOT / "backend/app/api/studio",
    )
    forbidden = (
        "app.api.v1",
        "app.api.learner",
        "app.api.challenge",
        "app.catalog",
        "app.challenge",
        "app.logic_graph",
        "app.services",
        "app.training",
    )

    for root in retained_roots:
        for source_path in root.rglob("*.py"):
            source = source_path.read_text(encoding="utf-8")
            for import_name in forbidden:
                assert import_name not in source, f"{source_path}: {import_name}"
