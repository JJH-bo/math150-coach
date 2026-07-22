from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.tools.adapters.animation_visualization import AnimationAdapter
from app.api.studio.v1.router import default_tool_service
from app.tools.contracts import ToolQualityTier
from tools.verify_production_runtime import EXPECTED_VERIFIED_TOOLS, validate_registry_payload


ROOT = Path(__file__).resolve().parents[2]


def test_smoke_catalog_matches_the_registered_production_catalog(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("CLASSROOM_DATA_ROOT", str(tmp_path))

    registered = {
        definition.tool_id
        for definition in default_tool_service().registry.list(
            quality_tier=ToolQualityTier.VERIFIED
        )
    }

    assert EXPECTED_VERIFIED_TOOLS == registered


def test_production_registry_requires_the_complete_verified_catalog() -> None:
    payload = {
        "total": len(EXPECTED_VERIFIED_TOOLS),
        "tools": [
            {"tool_id": tool_id, "quality_tier": "verified"}
            for tool_id in sorted(EXPECTED_VERIFIED_TOOLS)
        ],
    }

    validate_registry_payload(payload)


def test_production_registry_rejects_a_missing_tool() -> None:
    payload = {
        "total": len(EXPECTED_VERIFIED_TOOLS) - 1,
        "tools": [
            {"tool_id": tool_id, "quality_tier": "verified"}
            for tool_id in sorted(EXPECTED_VERIFIED_TOOLS - {"visualization.animation"})
        ],
    }

    with pytest.raises(AssertionError, match="verified tool catalog mismatch"):
        validate_registry_payload(payload)


def test_production_animation_fixture_satisfies_the_public_tool_contract() -> None:
    specification = json.loads(
        (ROOT / "tools" / "fixtures" / "production-animation.json").read_text(
            encoding="utf-8"
        )
    )

    normalized = AnimationAdapter()._normalize(specification)

    assert normalized["output_format"] == "mp4"
    assert len(normalized["objects"]) == 3
    assert len(normalized["timeline"]) == 6


def test_production_workflow_builds_starts_and_exercises_the_image() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "production-image.yml"
    ).read_text(encoding="utf-8")

    assert 'docker build --tag "$IMAGE_NAME" .' in workflow
    assert "python -m manim --version" in workflow
    assert "http://127.0.0.1:8000/health" in workflow
    assert "python tools/verify_production_runtime.py" in workflow
    assert "docker rm --force" in workflow
