from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.classroom.model_contracts import (
    ModelDraftRecord,
    PreviewJobRecord,
    TeachingModelManifest,
    model_content_hash,
    model_version,
)


def manifest_payload() -> dict:
    return {
        "contract_version": "teaching_model_v1",
        "model_id": "limit-neighborhood-2d",
        "title": "极限邻域观察器",
        "purpose": "连接函数图像、邻域和目标值。",
        "domains": ["calculus"],
        "parameters": [
            {
                "id": "delta",
                "type": "number",
                "default": 0.5,
                "minimum": 0.05,
                "maximum": 2.0,
            },
            {
                "id": "theme",
                "type": "choice",
                "default": "cyan",
                "choices": ["cyan", "amber"],
            },
        ],
        "states": [
            {"id": "overview", "title": "整体观察"},
            {"id": "approach", "title": "逼近过程"},
        ],
        "actions": [
            {
                "id": "highlight-target",
                "title": "突出目标值",
                "payload_fields": [],
            }
        ],
        "targets": ["curve", "hole", "target-value"],
        "interactions": ["parameter_change"],
        "viewport_modes": ["inline", "fullscreen"],
        "quality_profiles": ["balanced"],
        "scenarios": [
            {
                "id": "approach-target",
                "title": "从邻域观察目标值",
                "initial_state": "overview",
                "parameters": {"delta": 0.5, "theme": "cyan"},
                "commands": [
                    {
                        "kind": "set_state",
                        "target": "approach",
                    },
                    {
                        "kind": "perform_action",
                        "target": "highlight-target",
                        "payload": {},
                    },
                ],
            }
        ],
        "fallback_description": "函数值趋近目标值的二维静态示意图。",
    }


def source() -> str:
    return """
export function createTeachingModel(context) {
  return {
    mount(initialState) {},
    update(nextState) {},
    perform(action, payload) {},
    pause() {},
    resume() {},
    reset() {},
    snapshot() { return {}; },
    dispose() {},
  };
}
""".strip()


def test_manifest_accepts_self_describing_model_vocabulary() -> None:
    manifest = TeachingModelManifest.model_validate(manifest_payload())

    assert manifest.model_id == "limit-neighborhood-2d"
    assert manifest.parameters[0].default == 0.5
    assert manifest.scenarios[0].commands[1].target == "highlight-target"


@pytest.mark.parametrize(
    ("parameter", "message"),
    [
        (
            {
                "id": "delta",
                "type": "number",
                "default": 5,
                "minimum": 0,
                "maximum": 2,
            },
            "default must be at most maximum",
        ),
        (
            {
                "id": "theme",
                "type": "choice",
                "default": "violet",
                "choices": ["cyan", "amber"],
            },
            "choice default must be declared",
        ),
    ],
)
def test_parameter_defaults_must_match_declared_contract(
    parameter: dict,
    message: str,
) -> None:
    payload = manifest_payload()
    payload["parameters"] = [parameter]

    with pytest.raises(ValidationError, match=message):
        TeachingModelManifest.model_validate(payload)


def test_manifest_rejects_duplicate_state_and_action_ids() -> None:
    payload = manifest_payload()
    payload["states"].append(deepcopy(payload["states"][0]))

    with pytest.raises(ValidationError, match="duplicate state id"):
        TeachingModelManifest.model_validate(payload)

    payload = manifest_payload()
    payload["actions"].append(deepcopy(payload["actions"][0]))

    with pytest.raises(ValidationError, match="duplicate action id"):
        TeachingModelManifest.model_validate(payload)


def test_model_version_is_deterministic_and_source_sensitive() -> None:
    manifest = TeachingModelManifest.model_validate(manifest_payload())
    first_hash = model_content_hash(manifest, source())

    assert first_hash == model_content_hash(manifest, source())
    assert model_version(manifest, source()).startswith("m-")
    assert model_version(manifest, source()) != model_version(
        manifest,
        f"{source()}\n// changed",
    )


def test_draft_and_preview_records_capture_recovery_context() -> None:
    manifest = TeachingModelManifest.model_validate(manifest_payload())
    draft = ModelDraftRecord(
        draft_id="limit-draft",
        revision=1,
        content_hash=model_content_hash(manifest, source()),
        manifest=manifest,
        source=source(),
    )
    job = PreviewJobRecord(
        job_id="preview-1",
        draft_id=draft.draft_id,
        draft_revision=draft.revision,
        draft_content_hash=draft.content_hash,
        model_id=manifest.model_id,
        scenario_id="approach-target",
        viewport={"width": 1280, "height": 800, "device_scale_factor": 1},
        status="queued",
    )

    assert draft.source.startswith("export function")
    assert job.status == "queued"
    assert job.artifacts == []
