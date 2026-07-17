# U2B Draft Preview Graph Implementation Plan

## Goal

Render a compact, draft-only graph preview inside the chapter import panel so future chapter expansion can be visually inspected before any formal publish workflow exists.

## Boundaries

- Do not add concrete chapter content.
- Do not write formal catalog data.
- Do not change scoring, diagnosis, movement, or mastery logic.
- Do not add persistence, auth, database, or LLM integration.
- Use only the existing `payload.preview.nodes` and `payload.preview.edges` returned by draft validation.

## Task 1: Frontend Contract

- [x] Add a frontend contract test requiring `renderDraftPreviewGraph`, `draft-preview-graph`, `draft-preview-node`, and `draft-preview-edge`.
- [x] Run the focused test and confirm it fails before implementation.

## Task 2: Preview Rendering

- [x] Add a display-only draft graph renderer to `frontend/app.js`.
- [x] Position MacroNodes, MicroNodes, logic nodes, and MacroChallenges in stable layers.
- [x] Draw preview edges with SVG lines using the existing preview edge IDs.
- [x] Insert the graph into the import report after the readiness projection.

## Task 3: Styling

- [x] Add compact styles for `.draft-preview-graph`, `.draft-preview-node`, and `.draft-preview-edge`.
- [x] Use distinct but restrained tones for macro, micro, logic, and boss/challenge nodes.
- [x] Keep dimensions stable across desktop and mobile modal widths.

## Task 4: Verification

- [x] Run focused frontend contract tests.
- [x] Run bundled Node syntax check.
- [x] Run focused U2 tests.
- [x] Run full pytest and evals.
- [x] Commit as `feat: add draft preview graph`.
