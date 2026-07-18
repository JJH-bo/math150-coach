from __future__ import annotations

from app.classroom.model_contracts import (
    RegisteredModelRecord,
    TeachingModelManifest,
    model_content_hash,
    model_version,
)
from app.classroom.models import ClassroomPackage
from app.classroom.validation import ClassroomPackageValidator
from classroom_fixtures import classroom_package_payload
from test_teaching_model_contracts import manifest_payload, source


def registered_model() -> RegisteredModelRecord:
    manifest = TeachingModelManifest.model_validate(manifest_payload())
    return RegisteredModelRecord(
        model_id=manifest.model_id,
        version=model_version(manifest, source()),
        content_hash=model_content_hash(manifest, source()),
        manifest=manifest,
        source=source(),
        preview_job_id="preview-1",
    )


def bound_package_payload() -> dict:
    record = registered_model()
    payload = classroom_package_payload()
    payload["model_instances"] = [
        {
            "instance_id": "limit-view",
            "model_id": record.model_id,
            "model_version": record.version,
            "initial_state": "overview",
            "parameters": {"delta": 0.5, "theme": "cyan"},
            "viewport_mode": "inline",
            "quality_profile": "balanced",
            "allowed_interactions": ["parameter_change"],
            "fallback_description": "极限邻域静态图。",
        }
    ]
    payload["model_bindings"] = [
        {
            "id": "formula-enters",
            "content_id": "limit-formula",
            "instance_id": "limit-view",
            "trigger": {"kind": "block_enter"},
            "effect": {"kind": "set_state", "target": "approach"},
            "restore_previous": True,
        }
    ]
    return payload


def validate(payload: dict, record: RegisteredModelRecord | None = None):
    package = ClassroomPackage.model_validate(payload)
    available = record or registered_model()

    def resolve(model_id: str, version: str) -> RegisteredModelRecord:
        if model_id == available.model_id and version == available.version:
            return available
        raise LookupError("not registered")

    return ClassroomPackageValidator(model_resolver=resolve).validate(package)


def test_registered_model_instance_and_binding_validate() -> None:
    report = validate(bound_package_payload())

    assert report.passed is True
    assert report.issues == []


def test_binding_rejects_unknown_content_and_instance_targets() -> None:
    payload = bound_package_payload()
    payload["model_bindings"][0]["content_id"] = "missing-block"
    payload["model_bindings"][0]["instance_id"] = "missing-instance"

    report = validate(payload)

    assert {issue.code for issue in report.issues} == {
        "unknown_binding_content",
        "unknown_binding_instance",
    }


def test_instance_rejects_unregistered_version_and_invalid_parameter() -> None:
    payload = bound_package_payload()
    payload["model_instances"][0]["model_version"] = "m-missing"
    unregistered = validate(payload)

    payload = bound_package_payload()
    payload["model_instances"][0]["parameters"]["delta"] = 99
    invalid_parameter = validate(payload)

    assert unregistered.issues[0].code == "unregistered_model_version"
    assert invalid_parameter.issues[0].code == "invalid_model_parameter"


def test_binding_effect_must_use_declared_state_action_or_target() -> None:
    expected = {
        "set_state": "unknown_model_state",
        "perform_action": "unknown_model_action",
        "highlight_target": "unknown_model_target",
    }
    for kind, code in expected.items():
        payload = bound_package_payload()
        payload["model_bindings"][0]["effect"] = {
            "kind": kind,
            "target": "not-declared",
        }

        report = validate(payload)

        assert report.issues[0].code == code


def test_temporary_detail_binding_requires_return_behavior() -> None:
    payload = bound_package_payload()
    payload["model_bindings"][0]["trigger"] = {
        "kind": "detail_branch_open",
        "detail_branch_id": "limit-intro-detail",
    }
    payload["model_bindings"][0]["restore_previous"] = False

    report = validate(payload)

    assert report.issues[0].code == "binding_return_behavior_required"
