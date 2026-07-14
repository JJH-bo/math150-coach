# Stellar System And Boss Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the exposed three-chapter progression lane with one compact separable-equations stellar system containing six learning stars and exactly one oppressive boss endpoint.

**Architecture:** Keep backend learning semantics unchanged and apply a presentation projection in `cosmos-graph.js` only when the known ODE pilot ids are present. The projection filters the visible graph to the separable system, assigns a hand-tuned three-dimensional constellation layout, dispatches every learning node to `stellar-renderer.js`, and replaces persistent tube corridors with thin gravitational filaments.

**Tech Stack:** Three.js ES modules, GLSL `ShaderMaterial`, Node test runner, FastAPI static-contract tests, headless Chrome WebGL screenshots.

## Global Constraints

- Show six separable-equations learning nodes as stars, not portals.
- Show exactly one `ode_separable.macro_challenge` boss and no other boss in the pilot scene.
- Preserve the existing singularity/boss renderer; change composition and scale, not its visual identity.
- The six learning stars must occupy multiple X, Y, and Z shells and must not form a straight lane.
- Remove permanent `TubeGeometry` and torus gates from progression-route rendering.
- Do not change ids, scoring, diagnosis, mastery, rollback, unlock policy, or API payloads.

---

### Task 1: Project The ODE Data Into One Stellar System

**Files:**
- Modify: `frontend/space/cosmos-graph.js`
- Modify: `frontend/space/cosmos-graph.test.mjs`

**Interfaces:**
- Produces: `buildStellarSystemPilotLayout(network): PilotLayout`
- `PilotLayout` exposes `active`, `macroId`, `learningIds`, `bossId`, `visibleIds`, `positions`, and `frontFrame`.
- `buildCosmosGraph(challenge)` returns `presentationMode: "stellar-system-pilot"` and `systemMeta` when the pilot projection is active.

- [ ] **Step 1: Write a failing graph test**

Add a fixture containing the three real ODE macro ids, all six `ode_separable.*` learning ids, three macro challenges, and progression edges. Assert:

```js
const graph = buildCosmosGraph(challenge);
assert.equal(graph.presentationMode, "stellar-system-pilot");
assert.equal(graph.objects.filter((node) => node.role === "boss").length, 1);
assert.deepEqual(
  graph.objects.filter((node) => node.kind === "micro").map((node) => node.id).sort(),
  SIX_SEPARABLE_IDS.toSorted(),
);
assert.equal(graph.objects.length, 7);
assert.ok(new Set(graph.objects.map((node) => node.position[0])).size >= 5);
assert.ok(graph.byId.get("ode_separable.macro_challenge").radius >= 110);
```

- [ ] **Step 2: Run the graph test and verify it fails**

Run: `node --test frontend/space/cosmos-graph.test.mjs`
Expected: FAIL because `buildCosmosGraph` still returns all three chapters and bosses.

- [ ] **Step 3: Implement the presentation projection**

Add the six fixed learning ids and a hand-tuned position map:

```js
const STELLAR_SYSTEM_POSITIONS = new Map([
  ["ode_separable.concept", [-260, 65, -680]],
  ["ode_separable.trigger", [-80, -95, -740]],
  ["ode_separable.method", [90, 95, -805]],
  ["ode_separable.transformation", [220, -25, -870]],
  ["ode_separable.calculation", [40, -145, -935]],
  ["ode_separable.expression", [-150, 40, -1000]],
  ["ode_separable.macro_challenge", [430, 30, -1130]],
]);
```

Build all semantic objects as before, then filter presentation objects/edges to the seven visible ids, override positions, set boss radius `118`, and return the system overview camera `[0, 80, 60]` looking toward `[20, -10, -860]`.

- [ ] **Step 4: Run the graph test and verify it passes**

Run: `node --test frontend/space/cosmos-graph.test.mjs`
Expected: all graph tests pass.

- [ ] **Step 5: Commit**

```powershell
git add frontend/space/cosmos-graph.js frontend/space/cosmos-graph.test.mjs
git commit -m "Compose one compact stellar learning system"
```

---

### Task 2: Render Every Learning Node As A Living Star

**Files:**
- Modify: `frontend/space/stellar-renderer.js`
- Modify: `frontend/space/stellar-renderer.test.mjs`

**Interfaces:**
- `isStellarMaterialPilotNode(definition)` returns true for all six separable micro nodes with role `training`.
- `stellarProfileFor(definition, qualityLevel)` retains one stellar family while varying radius, activity, temperature colors, granulation, and prominences deterministically.

- [ ] **Step 1: Extend the failing predicate/profile tests**

Assert all six learning ids enter the stellar renderer, the macro challenge does not, and at least three distinct profile radii/activity combinations are produced.

- [ ] **Step 2: Run the stellar tests and verify they fail**

Run: `node --test frontend/space/stellar-renderer.test.mjs`
Expected: FAIL because only `ode_separable.concept` currently matches.

- [ ] **Step 3: Generalize the stellar predicate and deterministic profiles**

Replace the one-id constant with a six-id set and derive restrained temperature/radius variation from `definition.type`, `difficulty`, and the existing id hash. Do not add bitmap textures or glossy materials.

- [ ] **Step 4: Run tests and syntax checks**

Run: `node --test frontend/space/stellar-renderer.test.mjs`
Run: `node --check frontend/space/stellar-renderer.js`
Expected: all tests pass and syntax exits `0`.

- [ ] **Step 5: Commit**

```powershell
git add frontend/space/stellar-renderer.js frontend/space/stellar-renderer.test.mjs
git commit -m "Render the complete pilot system as stars"
```

---

### Task 3: Replace Permanent Tunnels With Gravitational Filaments

**Files:**
- Modify: `frontend/space/space.js`
- Modify: `backend/tests/test_challenge_frontend_api.py`

**Interfaces:**
- Produces: `createRapidTransitFilament(THREE, curve, color, qualityLevel)` returning the existing route visual contract `{group, line, layers, baseOpacity}`.
- Preserves: `route.rapid`, route control points, guided travel, opacity emphasis, and disposal.

- [ ] **Step 1: Write a failing source-contract test**

Assert `space.js` contains `createRapidTransitFilament`, uses it for rapid routes, and contains neither `new THREE.TubeGeometry` nor `new THREE.TorusGeometry`.

- [ ] **Step 2: Run the targeted contract and verify it fails**

Run: `python -m pytest backend/tests/test_challenge_frontend_api.py -q -k stellar_system`
Expected: FAIL because the permanent corridor is still tube-based.

- [ ] **Step 3: Implement the filament renderer**

Create a narrow dashed core plus three irregular line strands sampled from the route curve. At rest keep opacity below `0.12`; when focused reuse `setRouteOpacity` to brighten the core and strands. Do not create any cylindrical wall or repeated torus gate.

- [ ] **Step 4: Run route, static-contract, and syntax tests**

Run: `python -m pytest backend/tests/test_challenge_frontend_api.py -q`
Run: `node --test frontend/space/transit-route.test.mjs`
Run: `node --check frontend/space/space.js`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add frontend/space/space.js backend/tests/test_challenge_frontend_api.py
git commit -m "Replace permanent tunnels with gravity filaments"
```

---

### Task 4: Integrate, Frame, And Visually Verify The System

**Files:**
- Modify: `frontend/space/index.html`
- Test: all files above

**Interfaces:**
- The default `/trainer/space/` entrance opens on the complete system overview, not a single focused node.

- [ ] **Step 1: Bump the module cache keys**

Update the `space.js`, `cosmos-graph.js`, and `stellar-renderer.js` query versions to `20260714-stellar-system-1`.

- [ ] **Step 2: Run complete relevant verification**

Run: `python -m pytest backend/tests/test_challenge_frontend_api.py -q`
Run: `node --test frontend/space/cosmos-graph.test.mjs frontend/space/transit-route.test.mjs frontend/space/stellar-renderer.test.mjs`
Run syntax checks for all modified JavaScript modules.
Expected: zero failures.

- [ ] **Step 3: Capture real WebGL evidence**

Capture system overview, medium boss approach, and encounter framing. Reject if fewer than six stars are visible, the nodes form a lane, more than one boss is visible, a thick tube remains, or the boss remains a small remote icon.

- [ ] **Step 4: Commit and push**

```powershell
git add frontend/space/index.html
git commit -m "Expose the stellar system pilot"
git push
```
