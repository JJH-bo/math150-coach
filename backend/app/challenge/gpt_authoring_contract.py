from __future__ import annotations

from typing import Any

from app.challenge.chapter_draft_importer import ChapterDraftImporter


CONTRACT_VERSION = "chapter-galaxy-v1"


def chapter_authoring_contract() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "workflow": [
            "read_contract",
            "submit_complete_draft",
            "repair_validation_issues",
            "return_preview_url",
        ],
        "constraints": {
            "planets_per_system": {
                "minimum": 3,
                "maximum": 5,
            },
            "chapter_boss_count": 1,
            "allowed_micro_types": [
                "concept",
                "trigger",
                "method",
                "transformation",
                "calculation",
                "expression",
            ],
            "gpt_can_publish": False,
            "project_owns_visual_layout": True,
        },
        "required_sections": [
            "GalaxyPlan",
            "GalaxyBoss",
            "MacroNodes",
            "MicroNodes",
            "Edges",
            "TrainingAssets",
            "BossTrainingAsset",
            "ErrorRepairMap",
        ],
        "structured_import_template": ChapterDraftImporter.template(),
    }
