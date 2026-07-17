from __future__ import annotations

import json
from pathlib import Path

import yaml

from app.challenge.gpt_authoring_contract import chapter_authoring_contract


ACTION_SCHEMA = Path("docs/custom-gpt/chapter-authoring-actions.openapi.yaml")


def test_custom_gpt_action_schema_exposes_only_draft_operations() -> None:
    schema = yaml.safe_load(ACTION_SCHEMA.read_text(encoding="utf-8"))
    operation_ids = {
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    }

    assert schema["openapi"] == "3.1.0"
    assert schema["servers"] == [{"url": "https://your-domain.example"}]
    assert operation_ids == {
        "getProjectContract",
        "createChapterDraft",
        "updateChapterDraft",
        "getChapterDraft",
        "validateChapterDraft",
    }
    serialized = json.dumps(schema).lower()
    assert "approve" not in serialized
    assert "publish" not in serialized


def test_custom_gpt_action_schema_uses_bearer_auth_and_bounded_markdown() -> None:
    schema = yaml.safe_load(ACTION_SCHEMA.read_text(encoding="utf-8"))
    bearer = schema["components"]["securitySchemes"]["GptAuthoringBearer"]
    create_schema = schema["components"]["schemas"]["DraftCreateRequest"]
    markdown = create_schema["properties"]["source_markdown"]

    assert bearer == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "opaque",
    }
    assert schema["security"] == [{"GptAuthoringBearer": []}]
    assert markdown["minLength"] == 1
    assert markdown["maxLength"] == 750000
    assert create_schema["properties"]["contract_version"]["const"] == (
        "chapter-galaxy-v1"
    )


def test_authoring_contract_requires_complete_chapter_sections() -> None:
    required = set(chapter_authoring_contract()["required_sections"])

    assert required == {
        "GalaxyPlan",
        "GalaxyBoss",
        "MacroNodes",
        "MicroNodes",
        "MacroChallenges",
        "HiddenAbilities",
        "TransferNodes",
        "SynthesisNodes",
        "Edges",
        "TrainingAssets",
        "BossTrainingAsset",
        "ErrorRepairMap",
    }


def test_example_environment_contains_no_real_secret() -> None:
    text = Path(".env.example").read_text(encoding="utf-8")

    assert "GPT_AUTHORING_KEY=replace-with-a-long-random-secret" in text
    assert (
        "CHAPTER_REVIEW_KEY=replace-with-a-different-long-random-secret"
        in text
    )
    assert "sk-" not in text


def test_copy_ready_instructions_cover_the_safe_draft_loop() -> None:
    text = Path(
        "docs/custom-gpt/chapter-authoring-instructions.md"
    ).read_text(encoding="utf-8")

    for required_phrase in (
        "getProjectContract",
        "createChapterDraft",
        "validateChapterDraft",
        "updateChapterDraft",
        "preview_ready",
        "preview_url",
        "API Key",
    ):
        assert required_phrase in text
