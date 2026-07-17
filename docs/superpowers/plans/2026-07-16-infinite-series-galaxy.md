# Infinite Series Galaxy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import the approved infinite-series chapter content into the accepted Boss-centered observatory as ten learning systems across four uncrowded sectors, with node-to-training transit interaction.

**Architecture:** Keep the approved sky, black-hole compositor, stellar shader, and bounded Boss-centered camera. Add a deterministic build-time Markdown adapter, a browser chapter-scene module that groups systems into four sectors, and a thin interaction layer in the existing galaxy lab. The browser consumes generated static data and never reparses the full source document.

**Tech Stack:** Python 3, pytest, JavaScript ES modules, Node test runner, WebGL2, existing embedded cosmos and Boss labs.

## Global Constraints

- Preserve the approved Boss, stellar material, field-link material, sky, bloom, and camera behavior.
- Render exactly one visual Boss for the whole chapter.
- Keep every system at 3–5 visible training planets; this chapter contains 43 planets across 10 systems.
- Show at most three systems and fifteen planets in one sector.
- Reuse the existing 920ms transit overlay and training-observatory interaction language.
- Do not implement scoring, persistence, unlock writes, or a generic chapter-authoring product in this task.

---

### Task 1: Deterministic chapter asset builder

**Files:**
- Create: `tools/chapter_galaxy_builder.py`
- Create: `backend/tests/test_chapter_galaxy_builder.py`
- Generate: `frontend/space/galaxy-lab/infinite-series-data.mjs`

**Interfaces:**
- Consumes: structured Markdown with `GalaxyPlan`, `GalaxyBoss`, `MacroNodes`, `MicroNodes`, `TrainingAssets`, and `BossTrainingAsset`.
- Produces: `build_chapter_asset(markdown: str) -> dict` and an ES-module data file exporting that dictionary.

- [ ] **Step 1: Write the failing parser test**

Create a minimal two-system Markdown fixture in the test. Assert that `build_chapter_asset` preserves system order, attaches MicroNodes to their owner system, extracts literal `stem` blocks, and returns one Boss.

- [ ] **Step 2: Run the parser test and verify RED**

Run: `python -m pytest backend/tests/test_chapter_galaxy_builder.py -q`

Expected: collection/import failure because `tools.chapter_galaxy_builder` does not exist.

- [ ] **Step 3: Implement the minimal parser and module writer**

Implement table parsing with exact section names, literal-block extraction for the fields needed by the training panel, count validation, and deterministic JSON serialization prefixed by `export default`.

- [ ] **Step 4: Run the parser test and verify GREEN**

Run: `python -m pytest backend/tests/test_chapter_galaxy_builder.py -q`

Expected: all builder tests pass.

### Task 2: Correct and import the chapter source

**Files:**
- Create: `docs/chapter_inputs/infinite_series.md`
- Generate: `frontend/space/galaxy-lab/infinite-series-data.mjs`

**Interfaces:**
- Consumes: `C:/Users/jjh/OneDrive/Desktop/infinite_series.md`.
- Produces: a repository-owned corrected source and a browser asset containing 10 systems, 43 planets, 43 core questions, and one Boss question.

- [ ] **Step 1: Import the source mechanically**

Use the builder's import command so the 188 KB source is copied without manual retyping.

- [ ] **Step 2: Correct the six one-node CompareGuards**

Add the nearest semantically distinct comparison target for group/sign change, term/series, formula/sum function, odd-even/periodic extension, function/Fourier sum, and period/angle.

- [ ] **Step 3: Add CompareGuard semantic edges**

Add `contrasts_with` edges from every CompareGuard to both compared nodes so no logic node is orphaned.

- [ ] **Step 4: Validate the corrected source**

Run the existing `validate_chapter_markdown` entrypoint.

Expected: 0 blocking errors, max 5 MicroNodes per MacroNode.

- [ ] **Step 5: Generate the browser asset**

Run the builder against the corrected repository source and assert the generated payload reports `systemCount=10`, `planetCount=43`, and `bossCount=1`.

### Task 3: Sector and interaction geometry

**Files:**
- Create: `frontend/space/galaxy-lab/infinite-series-scene.mjs`
- Create: `frontend/space/galaxy-lab/infinite-series-scene.test.mjs`

**Interfaces:**
- Consumes: generated chapter asset.
- Produces: `buildInfiniteSeriesSectors(chapter)`, `createSectorSceneConfig(chapter, sectorId)`, and `pickSceneTarget(frame, point, viewport)`.

- [ ] **Step 1: Write failing sector tests**

Assert four sector IDs, system distribution `[3,2,3,2]`, unique coverage of all ten systems and 43 planets, a maximum of 15 planets per sector, and exactly one shared Boss.

- [ ] **Step 2: Write failing hit-test tests**

Assert clicks inside a projected planet or Boss return its metadata, clicks outside return `null`, and drag-distance rejection is handled by the caller.

- [ ] **Step 3: Run the Node tests and verify RED**

Run: `node --test frontend/space/galaxy-lab/infinite-series-scene.test.mjs`

Expected: module-not-found failure.

- [ ] **Step 4: Implement sector grouping, local planet layouts, and picking**

Use the fixed sector groups `1–3`, `4–5`, `6–8`, and `9–10`. Produce 4-planet and 5-planet local layouts without shrinking the base radii.

- [ ] **Step 5: Run the Node tests and verify GREEN**

Run: `node --test frontend/space/galaxy-lab/infinite-series-scene.test.mjs`

Expected: all sector and hit-test tests pass.

### Task 4: Data-driven observatory projection

**Files:**
- Modify: `frontend/space/galaxy-lab/observatory-camera.mjs`
- Modify: `frontend/space/galaxy-lab/observatory-camera.test.mjs`

**Interfaces:**
- Consumes: optional scene configuration containing system centers, per-system planets, and internal links.
- Produces: projected `planets`, `systems`, and `routes` retaining `id`, `title`, and training metadata.

- [ ] **Step 1: Add a failing custom-scene projection test**

Pass a system with five planets and assert five projected planets retain IDs, route count is valid, and the Boss projection remains unchanged.

- [ ] **Step 2: Run the camera test and verify RED**

Run: `node --test frontend/space/galaxy-lab/observatory-camera.test.mjs`

Expected: custom scene configuration is ignored or metadata is absent.

- [ ] **Step 3: Generalize `createSceneFrame` minimally**

Accept an optional scene configuration while preserving the existing default constants and all current no-argument behavior.

- [ ] **Step 4: Run the camera tests and verify GREEN**

Run: `node --test frontend/space/galaxy-lab/observatory-camera.test.mjs`

Expected: existing and custom-scene tests pass.

### Task 5: Galaxy-lab chapter UI and transit

**Files:**
- Modify: `frontend/space/galaxy-lab/index.html`
- Modify: `backend/tests/test_challenge_frontend_api.py`

**Interfaces:**
- Consumes: sector scene configuration, projected hit targets, node training metadata.
- Produces: sector buttons, system labels, click transit, node training dialog, and Boss training dialog.

- [ ] **Step 1: Add failing frontend contract assertions**

Assert the served page imports `infinite-series-data.mjs` and `infinite-series-scene.mjs`, contains sector navigation, transit overlay, training dialog, and a close control.

- [ ] **Step 2: Run the focused API test and verify RED**

Run: `python -m pytest backend/tests/test_challenge_frontend_api.py -q`

Expected: new page contract assertions fail.

- [ ] **Step 3: Extend shader capacity without altering material equations**

Increase planet arrays and loops from 12 to 15, clear unused packed slots each frame, and retain the current 15-route and 3-system limits.

- [ ] **Step 4: Add sector HUD and screen labels**

Render four sector buttons and update labels from `sceneFrame.systems` on every camera frame.

- [ ] **Step 5: Add click-versus-drag handling**

Record pointer-down position, treat movement over 6 px as camera drag, and call `pickSceneTarget` only for a click.

- [ ] **Step 6: Reuse the training transit sequence**

Open the aperture at the selected target, wait 920ms or 80ms for reduced motion, then show the safe text-only training dialog. Closing returns to the same sector and camera state.

- [ ] **Step 7: Run the frontend contract and Node tests**

Run:

```text
python -m pytest backend/tests/test_challenge_frontend_api.py -q
node --test frontend/space/galaxy-lab/*.test.mjs
```

Expected: all focused tests pass.

### Task 6: Final verification and publication

**Files:**
- Verify all files changed by Tasks 1–5.

- [ ] **Step 1: Run chapter validation and count audit**

Expected: 10 systems, 43 planets, 43 core questions, one GalaxyBoss, and 0 blocking importer errors.

- [ ] **Step 2: Run focused Python and Node suites**

Expected: all relevant tests pass with no warnings introduced by this work.

- [ ] **Step 3: Inspect Git diff and repository scope**

Confirm no unrelated visual, camera, Boss, or sky files changed.

- [ ] **Step 4: Commit implementation and push**

Commit the completed chapter integration separately from the design and plan commits, then push `stellar-material-proof` to GitHub.
