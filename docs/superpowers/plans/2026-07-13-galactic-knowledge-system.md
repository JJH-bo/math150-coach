# Galactic Knowledge System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the small cartoon knowledge graph with a large, physically grounded planetary knowledge system.

**Architecture:** Keep the existing Three.js scene and challenge identifiers, but centralize galaxy scale, planetary hierarchy, procedural PBR texture generation, and route styling in `frontend/space/space.js`. Automated source-contract tests protect the required visual architecture; browser screenshots validate the result.

**Tech Stack:** Three.js, CanvasTexture, MeshPhysicalMaterial, LineDashedMaterial, FastAPI TestClient, pytest.

## Global Constraints

- Preserve all API endpoints, task ids, challenge state behavior, and encounter interaction.
- Macro radii must span 38 to 56 world units; micro orbits must span at least 120 world units.
- Route rendering must not use TubeGeometry.
- State colors may affect navigation accents but must not recolor PBR planet surfaces.

---

### Task 1: Lock The Galactic Visual Contract

**Files:**
- Modify: `backend/tests/test_challenge_frontend_api.py`

**Interfaces:**
- Consumes: `/trainer/space/space.js` static response.
- Produces: `test_space_trainer_uses_galactic_scale_and_physical_routes`.

- [ ] **Step 1: Write the failing test**

Assert the script contains `macroRadiusFor`, `createPlanetSurfaceMaps`, `LineDashedMaterial`, `GALAXY_SCALE`, `orbitBase = 120`, and does not contain `new THREE.TubeGeometry`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest backend\tests\test_challenge_frontend_api.py -q -k galactic_scale`

Expected: FAIL because the new visual architecture is absent.

- [ ] **Step 3: Keep the test unchanged while implementing Tasks 2 and 3**

The test is the shared acceptance contract for layout, materials, and routes.

### Task 2: Expand The Planetary Hierarchy

**Files:**
- Modify: `frontend/space/space.js`

**Interfaces:**
- Consumes: existing `macroDefinitions`, `microTypes`, `createSpaceObject`, and `flyToObject`.
- Produces: `GALAXY_SCALE`, `scaledKnowledgePosition(position)`, and `macroRadiusFor(index)`.

- [ ] **Step 1: Add scale helpers**

Add `const GALAXY_SCALE = 1.95`, scale macro/guide/compare positions during scene construction, and return radii from `[56, 48, 52, 42, 46, 50, 44, 40]`.

- [ ] **Step 2: Rebuild satellite systems**

Set `orbitBase = 120`, distribute 12 micro nodes over three orbital shells up to 210 units, vary moon radii from 4.8 to 8.2, and scale boss gates to 18 units.

- [ ] **Step 3: Update camera and interaction framing**

Increase camera far plane to 5200, reduce fog density to 0.00034, and let `flyToObject` approach macro planets from 3.0 to 3.8 radii away.

### Task 3: Replace Cartoon Materials And Neon Tubes

**Files:**
- Modify: `frontend/space/space.js`
- Modify: `frontend/space/index.html`

**Interfaces:**
- Consumes: `realisticBodyProfile(definition)` and deterministic `mulberry32`/`hashString` helpers.
- Produces: `createPlanetSurfaceMaps(THREE, profile, kind, seedValue)` returning `{ colorMap, bumpMap, roughnessMap, emissiveMap }` and line-based `addRoute`.

- [ ] **Step 1: Generate deterministic surface maps**

Create 1024x512 macro maps and 512x256 moon maps from layered value noise, ridged terrain, latitude variation, craters, roughness, and sparse emissive night details.

- [ ] **Step 2: Wire PBR maps into planets**

Use `MeshPhysicalMaterial` with the generated color, bump, roughness, and emissive maps. Keep metalness below 0.04, roughness above 0.68, and atmosphere opacity subtle.

- [ ] **Step 3: Replace route tubes**

Use `THREE.BufferGeometry().setFromPoints(curve.getPoints(96))` with `THREE.LineDashedMaterial`, low opacity, dash sizes based on route length, and `computeLineDistances()`.

- [ ] **Step 4: Reduce ornamental rings**

Render broad translucent `RingGeometry` bands only on selected macro planets; keep current-task marker rings separate.

- [ ] **Step 5: Bump cache version**

Change the `space.js` query version to `20260713-galactic-planetary-system`.

### Task 4: Verify And Publish

**Files:**
- Test: `backend/tests/test_challenge_frontend_api.py`

**Interfaces:**
- Consumes: completed scene implementation.
- Produces: screenshots, test evidence, and pushed commit.

- [ ] **Step 1: Run targeted and full verification**

Run the galactic-scale test, `node --check frontend/space/space.js`, full pytest, golden evals, and synthetic diagnosis lab.

- [ ] **Step 2: Verify desktop and mobile WebGL output**

Capture 1280x720 and 390x844 screenshots. Confirm nonblank canvas pixels, no fallback state, no horizontal overflow, and no incoherent UI overlap.

- [ ] **Step 3: Commit and push**

Commit only the design, plan, implementation, and tests with message `Rebuild knowledge graph as planetary systems`, then push the current branch.
