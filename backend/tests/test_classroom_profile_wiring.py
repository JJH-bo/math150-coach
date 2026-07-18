from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def paths(profile: str) -> set[str]:
    return set(TestClient(create_app(profile)).get("/openapi.json").json()["paths"])


def test_internal_and_mixed_profiles_expose_studio() -> None:
    assert "/api/studio/v1/capabilities" in paths("internal")
    assert "/api/studio/v1/capabilities" in paths("mixed")
    assert "/api/studio/v1/capabilities" not in paths("learner")


def test_learner_and_mixed_profiles_expose_classroom_runtime() -> None:
    assert "/api/classroom/v1/catalog" in paths("learner")
    assert "/api/classroom/v1/catalog" in paths("mixed")
    assert "/api/classroom/v1/catalog" not in paths("internal")


def test_mixed_profile_contains_only_current_product_api_namespaces() -> None:
    mixed = paths("mixed")

    assert "/api/classroom/v1/catalog" in mixed
    assert "/api/studio/v1/capabilities" in mixed
    assert not any(path.startswith("/api/v1") for path in mixed)
    assert not any(path.startswith("/api/learner/v1") for path in mixed)
    assert not any(path.startswith("/api/challenge/v1") for path in mixed)
