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

## Multi-Material Intelligent Input

`POST /api/challenge/v1/authoring/chapter-draft/intelligent-generate` accepts either `source_text` or a `materials` array.

Each material item may provide:

- `material_type`: `text`, `markdown`, `notes`, `wrong_answers`, `problem_solution`, `framework`, `pdf`, `docx`, or `pptx`;
- `filename`;
- plain `text`;
- `content_base64` for binary material.

The material understanding layer reads mixed materials and extracts training-ability evidence:

- core concepts;
- core formulas;
- theorem statements;
- typical problem types;
- entry triggers;
- method choices;
- key transformations;
- confusions;
- common errors;
- prerequisites;
- downstream uses;
- Mathematics I score value;
- false-pass risks.

This evidence is returned as a public summary and carried into `knowledge_network.source_evidence`.

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

Current controlled publish can produce graph assets plus generated `questions.yaml`. The generated question package is deterministic and runtime-valid: it covers MicroNodes, Boss checks, rubrics, repair targets, false-pass risks, variants, and mastery criteria metadata.

The material input layer can now extract formulas, theorem wording, user notes, and wrong-answer evidence from multi-file source materials.

The generated training question package now carries extracted evidence into stems, expected answers, rubrics, validator config, false-pass risks, common-error cues, and variant metadata.

## Correction And Regeneration Dry Run

`POST /api/challenge/v1/authoring/chapter-package/correction-dry-run` accepts a generated candidate package plus a list of correction operations.

Supported correction operation shape:

- `op`: currently `replace`;
- `target`: `chapter`, `material_evidence`, `micro_node`, `macro_node`, `macro_challenge`, `atom_node`, `compare_node`, `guide_node`, `typed_edge`, or `error_repair_map`;
- `id`: required for graph collection targets;
- `field`: field to replace;
- `value`: replacement value.

The correction dry run returns:

- `correction_record` with editor, notes, operations, changed paths, operation errors, and accepted/blocked status;
- `before.candidate_content_hash`;
- `after.candidate_content_hash`;
- corrected candidate preview;
- runtime validation report;
- candidate quality report;
- regenerated training question package;
- changed question ids;
- affected node ids;
- regeneration scope.

This endpoint is still preview-only:

- it does not write `backend/challenge_data`;
- it does not mutate learner state;
- it does not unlock formal publish;
- it does not replace the publish plan or controlled publish executor.

The remaining final-version work is to add a front-end diff editor, persisted authoring history, rollback metadata, training-feedback-derived correction proposals, and deeper worked-example parsing beyond deterministic templates.

## Training Feedback Optimization Dry Run

`POST /api/challenge/v1/authoring/chapter-package/feedback-optimization-dry-run` accepts:

- a candidate package;
- its generated question package;
- real or simulated attempt records;
- an analyst id;
- optional `min_sample_size`.

The analyzer aggregates attempts by question and returns revision signals such as:

- excessive false passes;
- abnormal pass rate;
- unstable diagnosis root causes;
- insufficient rubric evidence;
- CompareGuard not stopping confusion;
- transfer variant weakness;
- Boss feedback gaps;
- ineffective repair routing;
- missing HiddenAbility support.

The response includes:

- `feedback_record`;
- `quality_gate`;
- `revision_signals`;
- `regeneration_plan`;
- `recommended_correction_operations`;
- per-question feedback summaries.

This endpoint is also preview-only:

- it does not mutate the candidate;
- it does not write runtime files;
- it does not persist feedback history;
- it does not replace correction dry-run.

Feedback optimization identifies what should be revised. Correction dry-run applies concrete human or AI-reviewed edits and regenerates the affected assets.

`POST /api/challenge/v1/authoring/chapter-package/feedback-optimization-from-sessions-dry-run` runs the same analysis from real local session logs.

The request provides:

- a candidate package;
- its generated question package;
- optional `session_ids`;
- an analyst id;
- optional `min_sample_size`.

The endpoint reads JSONL logs from the configured challenge session root:

- `CHALLENGE_SESSION_ROOT` when set;
- otherwise the default local challenge API training session directory.

It does not accept a raw filesystem path from request JSON. This keeps authoring feedback analysis tied to the same local training-session boundary used by the challenge engine.

The response adds `feedback_source` with loaded session ids, source log files, loaded attempt count, ignored record count, and invalid line count.
