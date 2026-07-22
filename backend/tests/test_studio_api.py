from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.studio.v1.router import create_studio_router
from app.classroom.authoring import ClassroomAuthoringService
from app.classroom.idempotency import IdempotencyLedger
from app.classroom.model_contracts import TeachingModelManifest
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.repository import ClassroomRepository
from classroom_fixtures import classroom_package_payload


def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("STUDIO_API_KEY", "studio-test-key")
    model_seed = Path(__file__).resolve().parents[1] / "classroom_data" / "model_seed"
    service = ClassroomAuthoringService(
        ClassroomRepository(tmp_path),
        IdempotencyLedger(tmp_path / "operations"),
        model_repository=TeachingModelRepository(
            tmp_path,
            seed_root=model_seed,
        ),
    )
    app = FastAPI()
    app.include_router(create_studio_router(lambda: service))
    return TestClient(app)


def headers(key: str = "studio-test-key", operation: str = "operation-1") -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Idempotency-Key": operation,
    }


def test_studio_rejects_missing_and_invalid_bearer_key(tmp_path, monkeypatch) -> None:
    studio = client(tmp_path, monkeypatch)

    assert studio.get("/api/studio/v1/capabilities").status_code == 401
    assert studio.get(
        "/api/studio/v1/capabilities",
        headers={"Authorization": "Bearer wrong"},
    ).status_code == 401


def test_capabilities_describe_free_modules_and_no_analysis_systems(
    tmp_path, monkeypatch
) -> None:
    response = client(tmp_path, monkeypatch).get(
        "/api/studio/v1/capabilities",
        headers=headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "classroom_package_v1"
    assert payload["module_structure"] == "free_composition"
    assert "formula_explanation" in payload["content_block_kinds"]
    assert payload["learner_analysis_capabilities"] == []
    assert payload["quality_contract_version"] == "learning_quality_v1"
    assert payload["chapter_authoring"] == {
        "requires_source_sections": True,
        "requires_knowledge_ledger": True,
        "requires_exact_coverage": True,
        "requires_chapter_overview": True,
        "core_modules_are_indispensable_questions": True,
        "requires_problem_progression": True,
        "requires_beginner_bridges": True,
        "requires_detailed_expansion_per_module": True,
        "rejects_shallow_expansions": True,
    }
    assert payload["teaching_model_workshop"][
        "requires_semantic_visual_evidence"
    ] is True
    assert payload["teaching_model_workshop"][
        "requires_interaction_change_evidence"
    ] is True
    assert payload["autonomous_authoring"] == {
        "starts_from_uploaded_material": True,
        "asks_for_routine_confirmation": False,
        "asks_learner_for_internal_identifiers": False,
        "repairs_validation_and_preview_failures": True,
    }


def test_workspace_discovers_existing_authoring_targets(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv(
        "AI_CLASSROOM_PUBLIC_ORIGIN",
        "https://classroom.example/",
    )
    studio = client(tmp_path, monkeypatch)
    studio.post(
        "/api/studio/v1/drafts",
        headers=headers(operation="create-workspace-draft"),
        json={"draft_id": "limits", "package": classroom_package_payload()},
    )
    studio.post(
        "/api/studio/v1/drafts/limits/publish",
        headers=headers(operation="publish-workspace-draft"),
        json={"expected_revision": 1},
    )

    response = studio.get(
        "/api/studio/v1/workspace",
        headers={"Authorization": "Bearer studio-test-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["public_origin"] == "https://classroom.example"
    assert payload["learner_entry_url"] == "https://classroom.example/classroom/"
    assert payload["active_packages"][0]["package_id"] == "calculus-foundations"
    assert payload["active_packages"][0]["learner_entry_url"] == (
        "https://classroom.example/classroom/"
        "?package_id=calculus-foundations"
    )
    assert payload["active_packages"][0]["courses"][0]["chapters"][0][
        "modules"
    ][0]["id"] == "limit-core"
    assert payload["drafts"][0]["draft_id"] == "limits"
    assert payload["drafts"][0]["revision"] == 1
    assert payload["drafts"][0]["matches_active_content"] is True
    assert payload["drafts"][0]["recommended_for_update"] is True
    assert payload["registered_models"]
    assert all(
        model["recommended_for_use"] is True
        for model in payload["registered_models"]
    )
    assert payload["pagination"]["drafts"] == {
        "total": 1,
        "returned": 1,
        "has_more": False,
        "next_offset": None,
    }
    assert payload["authoring_policy"] == {
        "routine_authoring_requires_confirmation": False,
        "publish_after_validation": True,
        "discover_identifiers_before_writes": True,
        "ask_user_for_internal_identifiers": False,
        "autonomous_from_uploaded_material": True,
        "complete_chapter_coverage_required": True,
        "interactive_models_require_semantic_preview": True,
        "learner_analysis_capabilities": [],
        "rollback_scope": "explicit_request_or_failed_just_published_release",
    }


def test_workspace_is_bounded_and_marks_one_recommended_duplicate_draft(
    tmp_path, monkeypatch
) -> None:
    studio = client(tmp_path, monkeypatch)
    for index in range(3):
        package = classroom_package_payload()
        package["package_id"] = f"package-{index}"
        package["title"] = f"Package {index}"
        studio.post(
            "/api/studio/v1/drafts",
            headers=headers(operation=f"create-package-{index}"),
            json={"draft_id": f"draft-{index}", "package": package},
        )
    for suffix in ("primary", "alternate"):
        studio.post(
            "/api/studio/v1/drafts",
            headers=headers(operation=f"create-{suffix}"),
            json={
                "draft_id": f"limits-{suffix}",
                "package": classroom_package_payload(),
            },
        )

    first_page = studio.get(
        "/api/studio/v1/workspace?offset=0&limit=2",
        headers={"Authorization": "Bearer studio-test-key"},
    ).json()
    second_page = studio.get(
        "/api/studio/v1/workspace?offset=2&limit=2",
        headers={"Authorization": "Bearer studio-test-key"},
    ).json()
    third_page = studio.get(
        "/api/studio/v1/workspace?offset=4&limit=2",
        headers={"Authorization": "Bearer studio-test-key"},
    ).json()

    assert len(first_page["drafts"]) == 2
    assert first_page["pagination"]["drafts"] == {
        "total": 5,
        "returned": 2,
        "has_more": True,
        "next_offset": 2,
    }
    assert len(second_page["drafts"]) == 2
    assert second_page["pagination"]["drafts"]["has_more"] is True
    assert len(third_page["drafts"]) == 1
    assert third_page["pagination"]["drafts"]["has_more"] is False
    all_drafts = (
        first_page["drafts"]
        + second_page["drafts"]
        + third_page["drafts"]
    )
    calculus_drafts = [
        draft
        for draft in all_drafts
        if draft["package_id"] == "calculus-foundations"
    ]
    assert len(calculus_drafts) == 2
    assert sum(draft["recommended_for_update"] for draft in calculus_drafts) == 1
    assert all(draft["candidate_count"] == 2 for draft in calculus_drafts)


def test_workspace_recommends_latest_registered_model_version(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("STUDIO_API_KEY", "studio-test-key")
    seed = Path(__file__).resolve().parents[1] / "classroom_data" / "model_seed"
    manifest = TeachingModelManifest.model_validate(
        json.loads(
            (seed / "limit-neighborhood-2d" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
    )
    source = (seed / "limit-neighborhood-2d" / "source.js").read_text(
        encoding="utf-8"
    )
    model_repository = TeachingModelRepository(tmp_path)
    first = model_repository.create_draft("model-first", manifest, source)
    model_repository.register(
        first,
        validation={"passed": True},
        preview_job_id="preview-first",
    )
    second = model_repository.create_draft(
        "model-second",
        manifest,
        f"{source}\n// second version\n",
    )
    latest = model_repository.register(
        second,
        validation={"passed": True},
        preview_job_id="preview-second",
    )
    service = ClassroomAuthoringService(
        ClassroomRepository(tmp_path),
        IdempotencyLedger(tmp_path / "operations"),
        model_repository=model_repository,
    )
    app = FastAPI()
    app.include_router(create_studio_router(lambda: service))

    payload = TestClient(app).get(
        "/api/studio/v1/workspace",
        headers={"Authorization": "Bearer studio-test-key"},
    ).json()
    versions = [
        model
        for model in payload["registered_models"]
        if model["model_id"] == manifest.model_id
    ]

    assert len(versions) == 2
    assert sum(model["recommended_for_use"] for model in versions) == 1
    assert next(
        model for model in versions if model["recommended_for_use"]
    )["version"] == latest.version


def test_create_validate_publish_and_rollback_workflow(tmp_path, monkeypatch) -> None:
    studio = client(tmp_path, monkeypatch)
    created = studio.post(
        "/api/studio/v1/drafts",
        headers=headers(operation="create"),
        json={"draft_id": "limits", "package": classroom_package_payload()},
    )
    validated = studio.post(
        "/api/studio/v1/drafts/limits/validate",
        headers={"Authorization": "Bearer studio-test-key"},
    )
    published = studio.post(
        "/api/studio/v1/drafts/limits/publish",
        headers=headers(operation="publish"),
        json={"expected_revision": 1},
    )
    version = published.json()["active_version"]
    rolled_back = studio.post(
        "/api/studio/v1/packages/calculus-foundations/rollback",
        headers=headers(operation="rollback"),
        json={"version": version},
    )

    assert created.status_code == 201
    assert validated.json()["passed"] is True
    assert published.status_code == 200
    assert rolled_back.json()["active_version"] == version


def test_update_requires_correct_revision_and_idempotency_key(
    tmp_path, monkeypatch
) -> None:
    studio = client(tmp_path, monkeypatch)
    studio.post(
        "/api/studio/v1/drafts",
        headers=headers(operation="create"),
        json={"draft_id": "limits", "package": classroom_package_payload()},
    )
    payload = classroom_package_payload()
    payload["title"] = "更新后的课堂"

    stale = studio.put(
        "/api/studio/v1/drafts/limits",
        headers=headers(operation="update"),
        json={"expected_revision": 2, "package": payload},
    )

    assert stale.status_code == 409
    assert stale.json()["detail"]["error_code"] == "classroom_revision_conflict"


def test_openapi_has_stable_action_operation_ids(tmp_path, monkeypatch) -> None:
    schema = client(tmp_path, monkeypatch).get("/openapi.json").json()
    operations = {
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }

    assert {
        "getStudioCapabilities",
        "getStudioWorkspace",
        "createClassroomDraft",
        "getClassroomDraft",
        "updateClassroomDraft",
        "validateClassroomDraft",
        "publishClassroomDraft",
        "rollbackClassroomPackage",
    } <= operations
