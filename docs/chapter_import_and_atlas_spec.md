# Chapter Import And Atlas Spec

## Purpose

This spec defines the first expandable chapter authoring path and the macro atlas layer.

The authoring path is intentionally draft-only. It helps a human turn structured chapter knowledge into graph drafts, preview data, and quality reports. It must not publish into the formal training catalog automatically.

The atlas layer is intentionally lightweight. It shows chapter-level regions and summary counts, then lazy-loads a selected chapter through the existing challenge start flow.

## Structured Markdown Sections

The importer accepts a structured Markdown document with these sections:

- `MacroNodes`: visible chapter-level knowledge nodes.
- `MicroNodes`: visible trainable capability nodes. `type` must be one of `concept`, `trigger`, `method`, `transformation`, `calculation`, `expression`.
- `MacroChallenges`: Boss validation nodes and their covered micro nodes.
- `HiddenAbilities`: diagnostic atomic abilities with `why_exists`, `evidence_sources`, `failure_modes`, and `repair_target_node_id`.
- `CompareGuards`: misconception/contrast nodes that must connect at least two nodes and explain the contrast.
- `TransferNodes`: variant-transfer logic nodes.
- `SynthesisNodes`: comprehensive decomposition nodes, usually before Boss validation.
- `Edges`: semantic graph edges. Allowed types are `requires`, `supports`, `derives_to`, `transforms_to`, `contrasts_with`, `commonly_confused_with`, `checks`, `repairs`, `transfers_to`, `boss_checks`, and `blocks`.
- `ErrorRepairMap`: maps every declared root cause to a clear MicroNode repair target.

## Validation Gates

The importer returns:

- `publish_state: draft_only`
- `draft.challenge_graph_draft`
- `draft.logic_graph_draft`
- `preview.nodes`
- `preview.edges`
- `report.errors`
- `report.warnings`

A draft fails validation when:

- `chapter_id` is missing or unsafe.
- Any node id is missing or duplicated.
- A MicroNode references an unknown MacroNode.
- A MacroChallenge references unknown nodes.
- A HiddenAbility lacks evidence sources, reason, or a MicroNode repair target.
- A CompareGuard has fewer than two compared nodes or no contrast.
- An edge has an invalid type, self-loop, unknown endpoint, or missing required endpoint.
- No root cause repair mapping is provided.
- A MacroNode has more than 12 visible MicroNodes.

A draft may warn when:

- A MacroNode has more than 8 visible MicroNodes.
- An edge has no explanation reason.
- A logic node is not connected by semantic edges.

## Runtime Boundaries

- Draft import does not modify `backend/challenge_data`.
- Draft import does not create learner progress.
- Draft import does not alter scoring, diagnosis, rollback, or forward movement.
- Formal publishing remains a separate future step.
- The atlas endpoint must not embed `logic_overlay`, `current_question`, formal rubrics, trusted scoring fields, or full chapter detail graphs.

## Atlas Layer

`GET /api/challenge/v1/atlas` returns a course-level map:

- `atlas_version`
- `render_policy`
- `regions`
- `bridges`
- `warnings`

Each region represents one chapter galaxy and includes only summary counts and a lazy-load hint. Clicking a chapter region should call the existing challenge start endpoint with that `chapter_id`.

## Runtime Chapter Registry

`GET /api/challenge/v1/chapters/registry` returns the runtime readiness registry.

A chapter directory is not enough to make a runnable training package. The registry classifies chapters as:

- `trainable`: graph and question bank are valid, with complete MicroNode and Boss question coverage.
- `content_pending`: graph exists, but questions or coverage are missing.
- `invalid`: graph cannot be loaded.

Atlas must use this registry:

- `runtime.can_start=true` means the chapter can enter the training cabin.
- `runtime.can_start=false` means the region can be shown as an authored/published asset, but must not be started.
- The challenge `start/status/submit/reset` flow must reject non-trainable chapters even if a caller bypasses Atlas.

When `publish_manifest.json` exists, it is part of the runtime gate: the manifest must be readable and must report `candidate_quality_grade: pass`.

Current controlled publish can produce graph assets. A final runnable chapter package still requires generated `questions.yaml` with trainable, scoreable, diagnosable questions and full Boss coverage.
