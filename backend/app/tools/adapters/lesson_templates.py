from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)


INTENTS = ("concept_building", "worked_practice", "visual_mechanism", "discussion_proof")
OUTPUT_MODES = ("browser", "presentation", "document", "mixed")
CATALOG = [
    {
        "template_id": "concept_journey",
        "title": "Concept journey",
        "intents": ["concept_building"],
        "output_modes": ["browser", "presentation", "document", "mixed"],
        "interactive": False,
        "narrative_arc": "question_analysis_answer",
        "slide_blueprints": [
            {"kind": "opening", "job": "Create a concrete question and expose the need for the concept."},
            {"kind": "concept", "job": "Name the central idea and connect every symbol or term."},
            {"kind": "comparison", "job": "Separate the new concept from a nearby misconception."},
            {"kind": "example", "job": "Apply the concept in one fully explained case."},
            {"kind": "synthesis", "job": "Resolve the opening question and state the transferable idea."},
        ],
    },
    {
        "template_id": "worked_examples",
        "title": "Worked-example progression",
        "intents": ["worked_practice"],
        "output_modes": ["browser", "presentation", "document", "mixed"],
        "interactive": True,
        "narrative_arc": "learning_progression",
        "slide_blueprints": [
            {"kind": "opening", "job": "Pose a representative problem and identify what makes it difficult."},
            {"kind": "steps", "job": "Expose the reusable method before calculating."},
            {"kind": "example", "job": "Solve a basic case with every transformation justified."},
            {"kind": "example", "job": "Solve a contrasting case and call out the decision points."},
            {"kind": "comparison", "job": "Compare a correct path with a plausible wrong path."},
            {"kind": "synthesis", "job": "Turn the worked cases into a checkable procedure."},
        ],
    },
    {
        "template_id": "visual_explainer",
        "title": "Visual mechanism lab",
        "intents": ["visual_mechanism", "concept_building"],
        "output_modes": ["browser", "presentation", "mixed"],
        "interactive": True,
        "narrative_arc": "claim_evidence_consequence",
        "slide_blueprints": [
            {"kind": "opening", "job": "Ask learners to predict how the mechanism changes."},
            {"kind": "visual", "job": "Introduce the visual model and map every visible object to meaning."},
            {"kind": "steps", "job": "Vary one parameter while holding the comparison baseline fixed."},
            {"kind": "comparison", "job": "Compare two states and identify the invariant and the change."},
            {"kind": "example", "job": "Use the model to explain or calculate a concrete result."},
            {"kind": "synthesis", "job": "Connect the observed mechanism back to the formal statement."},
        ],
    },
    {
        "template_id": "seminar",
        "title": "Claim and proof seminar",
        "intents": ["discussion_proof"],
        "output_modes": ["browser", "presentation", "document", "mixed"],
        "interactive": False,
        "narrative_arc": "claim_evidence_consequence",
        "slide_blueprints": [
            {"kind": "opening", "job": "State a debatable claim and make its assumptions visible."},
            {"kind": "concept", "job": "Define the objects and conditions used by the claim."},
            {"kind": "steps", "job": "Build the proof or argument in dependency order."},
            {"kind": "comparison", "job": "Test a boundary case, counterexample, or alternative argument."},
            {"kind": "synthesis", "job": "State exactly what has been established and what remains conditional."},
        ],
    },
]
CATALOG_BY_ID = {item["template_id"]: item for item in CATALOG}


class TemplateInputError(ValueError):
    pass


def artifact(path: Path) -> ToolProducedArtifact:
    return ToolProducedArtifact(name=path.name, media_type="application/json", source_path=path.name)


class TemplateListAdapter:
    definition = ToolDefinition(
        tool_id="template.list",
        version="1.0.0",
        title="Rank teaching templates by learning intent",
        description="Discover verified lesson structures ranked by learning intent, output mode, and interaction need instead of school subject.",
        category="template",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.READ,
        execution_mode=ToolExecutionMode.SYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=10,
        max_artifacts=2,
        max_artifact_bytes=2 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["learning_intent"],
            "properties": {
                "learning_intent": {"type": "string", "enum": list(INTENTS)},
                "output_mode": {"type": "string", "enum": list(OUTPUT_MODES)},
                "interaction_required": {"type": "boolean"},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 4},
            },
        },
        output_schema={"type": "object", "properties": {"recommendations": {"type": "array"}, "selection_basis": {"type": "array"}}, "required": ["recommendations", "selection_basis"]},
        output_media_types=["application/json"],
        quality_gates=["intent_based_ranking", "complete_narrative_sequence", "compatible_output_mode", "explicit_interaction_fit"],
        upstream_project="Project semantic lesson template catalog",
        license="Project-owned",
    )

    def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        allowed = {"learning_intent", "output_mode", "interaction_required", "max_results"}
        if not isinstance(arguments, dict) or set(arguments) - allowed:
            raise TemplateInputError("template query contains unsupported fields")
        intent = arguments.get("learning_intent")
        output_mode = arguments.get("output_mode", "mixed")
        interaction_required = arguments.get("interaction_required", False)
        max_results = arguments.get("max_results", 4)
        if intent not in INTENTS or output_mode not in OUTPUT_MODES or not isinstance(interaction_required, bool):
            raise TemplateInputError("template intent, output mode, or interaction flag is invalid")
        if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= 4:
            raise TemplateInputError("max_results must be from 1 to 4")
        ranked = []
        for item in CATALOG:
            if output_mode not in item["output_modes"]:
                continue
            score = 10
            reasons = []
            if intent in item["intents"]:
                score += 60
                reasons.append("direct learning-intent match")
            if output_mode in item["output_modes"]:
                score += 20
                reasons.append("supports requested output mode")
            if interaction_required and item["interactive"]:
                score += 15
                reasons.append("designed for learner interaction")
            elif not interaction_required:
                score += 5
                reasons.append("works without mandatory interaction")
            ranked.append({**item, "score": score, "reasons": reasons})
        ranked.sort(key=lambda item: (-item["score"], item["template_id"]))
        result = {
            "recommendations": ranked[:max_results],
            "selection_basis": ["learning_intent", "output_mode", "interaction_required"],
        }
        path = context.work_dir / "template-catalog.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"templates": CATALOG}, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return ToolExecutionResult(result=result, artifacts=[artifact(path)], metrics={"template_count": len(CATALOG)})


class TemplateInstantiateAdapter:
    definition = ToolDefinition(
        tool_id="template.instantiate",
        version="1.0.0",
        title="Instantiate a semantic lesson blueprint",
        description="Create an authoring blueprint from a verified teaching template without pretending placeholder content is a finished lesson.",
        category="template",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.AUTHOR,
        execution_mode=ToolExecutionMode.SYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=10,
        max_artifacts=2,
        max_artifact_bytes=2 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["template_id", "title", "audience", "learning_objective", "output_mode"],
            "properties": {
                "template_id": {"type": "string", "enum": sorted(CATALOG_BY_ID)},
                "title": {"type": "string", "minLength": 1, "maxLength": 80},
                "audience": {"type": "string", "minLength": 8, "maxLength": 300},
                "learning_objective": {"type": "string", "minLength": 16, "maxLength": 600},
                "output_mode": {"type": "string", "enum": list(OUTPUT_MODES)},
            },
        },
        output_schema={"type": "object", "properties": {"blueprint": {"type": "object"}, "required_next_step": {"type": "string"}}, "required": ["blueprint", "required_next_step"]},
        output_media_types=["application/json"],
        quality_gates=["known_verified_template", "opening_to_synthesis_sequence", "no_placeholder_publication", "semantic_lesson_next_step"],
        upstream_project="Project semantic lesson template catalog",
        license="Project-owned",
    )

    def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        required = {"template_id", "title", "audience", "learning_objective", "output_mode"}
        if not isinstance(arguments, dict) or set(arguments) != required:
            raise TemplateInputError(f"template instantiation requires exactly {sorted(required)}")
        template = CATALOG_BY_ID.get(arguments["template_id"])
        if template is None or arguments["output_mode"] not in OUTPUT_MODES:
            raise TemplateInputError("template ID or output mode is invalid")
        title = self._text(arguments["title"], "title", 1, 80)
        audience = self._text(arguments["audience"], "audience", 8, 300)
        objective = self._text(arguments["learning_objective"], "learning_objective", 16, 600)
        blueprint = {
            "schema_version": "semantic_lesson_blueprint_v1",
            "title": title,
            "audience": audience,
            "learning_objective": objective,
            "semantic_template": template["template_id"],
            "narrative_arc": template["narrative_arc"],
            "output_mode": arguments["output_mode"],
            "requires_interactive_model": template["interactive"],
            "slide_blueprints": template["slide_blueprints"],
            "publication_ready": False,
        }
        result = {"blueprint": blueprint, "required_next_step": "author_and_validate_semantic_lesson_v1"}
        path = context.work_dir / "lesson-blueprint.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(blueprint, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return ToolExecutionResult(result=result, artifacts=[artifact(path)], metrics={"slide_blueprint_count": len(template["slide_blueprints"])})

    @staticmethod
    def _text(raw: Any, name: str, minimum: int, maximum: int) -> str:
        if not isinstance(raw, str) or not minimum <= len(raw.strip()) <= maximum or any(token in raw for token in ("<", ">", "`", "\x00")):
            raise TemplateInputError(f"{name} is invalid")
        return raw.strip()
