# Boss Black Hole Focus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the pilot endpoint's portal interior with a dominant true black-hole boss and reframe the six learning stars as one boss-centered local galaxy.

**Architecture:** Add a focused `black-hole-renderer.js` whose node contract matches the existing celestial renderers, while leaving ordinary spatial entrances unchanged. `cosmos-graph.js` owns boss scale and boss-centered placement, `stellar-renderer.js` owns the local focus environment and repair-state star consistency, and `space.js` dispatches and animates the black hole.

**Tech Stack:** Browser-native ES modules, Three.js r162, GLSL shaders, Node test runner, FastAPI/TestClient contract tests, headless Chrome DevTools Protocol screenshots.

## Global Constraints

- Preserve all backend learning ids, progression, interaction, scoring, and navigation semantics.
- Keep exactly six pilot learning micro nodes and exactly one boss.
- Pilot boss radius must be at least `188`; pilot learning-star photospheres remain within `26–34` world units.
- Every pilot micro node uses the star renderer in both `training` and `repair` roles.
- The boss event horizon is opaque black and contains no portal-throat or portal-aperture rendering.
- Ordinary spatial entrances and repair singularities remain unchanged outside the pilot.
- High and balanced quality modes must both work.

---

### Task 1: Lock The Six-Star And Boss-Scale Graph Contract

**Files:**
- Modify: `frontend/space/cosmos-graph.test.mjs`
- Modify: `frontend/space/stellar-renderer.test.mjs`
- Modify: `frontend/space/cosmos-graph.js`
- Modify: `frontend/space/stellar-renderer.js`

**Interfaces:**
- Consumes: `buildCosmosGraph(challenge)` and `isStellarMaterialPilotNode(definition)`.
- Produces: one pilot graph with boss radius `>= 188`, boss-centered positions, and stellar dispatch for both `training` and `repair` micro roles.

- [ ] **Step 1: Write failing graph and renderer tests**

Add assertions equivalent to:

```js
assert.ok(bosses[0].radius >= 188);
assert.ok(bosses[0].position[2] >= -980);
assert.ok(Math.abs(bosses[0].position[0]) <= 360);

assert.equal(renderer.isStellarMaterialPilotNode({
  id: "ode_separable.concept",
  kind: "micro",
  role: "repair",
}), true);
```

Also assert that all six learning positions remain outside `boss.radius * 1.18` in three-dimensional distance so no photosphere overlaps the event horizon in the initial layout.

- [ ] **Step 2: Run the focused tests and confirm red**

Run:

```powershell
node --test frontend/space/cosmos-graph.test.mjs frontend/space/stellar-renderer.test.mjs
```

Expected: failure because boss radius is `118`, boss depth is `-1100`, and repair nodes are rejected by the stellar predicate.

- [ ] **Step 3: Implement the graph and predicate changes**

Set the pilot boss to radius `196`, move it to a center-right depth near `-900`, and recompose the six learning positions in two asymmetric three-dimensional orbital bands. Change the predicate to accept both pilot roles:

```js
export function isStellarMaterialPilotNode(definition = {}) {
  return STELLAR_PILOT_NODE_IDS.has(definition.id)
    && definition.kind === "micro"
    && (definition.role === "training" || definition.role === "repair");
}
```

Tune `frontFrame.camera` and `frontFrame.lookAt` so the boss is inside the center-right focal area while all six learning stars remain visible.

- [ ] **Step 4: Run focused tests and confirm green**

Run the command from Step 2. Expected: all graph and stellar tests pass.

- [ ] **Step 5: Commit the graph contract**

```powershell
git add frontend/space/cosmos-graph.js frontend/space/cosmos-graph.test.mjs frontend/space/stellar-renderer.js frontend/space/stellar-renderer.test.mjs
git commit -m "Reframe the pilot around a colossal boss"
```

---

### Task 2: Build The Isolated True Black-Hole Renderer

**Files:**
- Create: `frontend/space/black-hole-renderer.js`
- Create: `frontend/space/black-hole-renderer.test.mjs`

**Interfaces:**
- Produces: `createBossBlackHole(THREE, definition, qualityLevel)` returning the standard node object and `updateBossBlackHole(node, elapsed, delta, isFocused)` for per-frame motion.
- Node contract: `{ ...definition, group, materials, baseScale: 1, userData: { blackHole, boss, shaderMaterials, rotors, coronas, beacon } }`.

- [ ] **Step 1: Write failing source and profile tests**

The new test loads the module source through a data URL and asserts:

```js
assert.match(source, /createEventHorizon/);
assert.match(source, /createPhotonRing/);
assert.match(source, /createAccretionDisc/);
assert.match(source, /createInfallField/);
assert.match(source, /createGravitationalStorm/);
assert.doesNotMatch(source, /createPortalThroat|createPortalAperture/);
assert.match(source, /color:\s*0x000000/);
assert.match(source, /depthWrite:\s*true/);
```

Import and test a pure `blackHoleProfileFor(definition, qualityLevel)` function so high mode has more particles/layers than balanced mode while both preserve identical event-horizon scale.

- [ ] **Step 2: Run the new test and confirm red**

```powershell
node --test frontend/space/black-hole-renderer.test.mjs
```

Expected: failure because `black-hole-renderer.js` does not exist.

- [ ] **Step 3: Implement event horizon and photon ring**

Create an opaque `SphereGeometry` event horizon using a black `MeshBasicMaterial` with `depthWrite: true`, then add a shader-driven photon-ring plane immediately outside the silhouette. The ring fragment shader must use a narrow radial band, angular irregularity, and side-dependent beaming:

```glsl
float ring = 1.0 - smoothstep(width, width * 3.4, abs(length(p) - ringRadius));
float beaming = 0.42 + 0.58 * smoothstep(-0.85, 0.72, p.x);
float fracture = 0.72 + 0.28 * sin(angle * 11.0 - time * 0.38);
gl_FragColor = vec4(mix(ember, whiteHeat, beaming), ring * beaming * fracture);
```

- [ ] **Step 4: Implement the tilted accretion disc and storm**

Use two separately animated shader planes tilted around the local X and Z axes. Both discard fragments outside an annulus; the horizon's depth buffer occludes their center. The disc shader combines turbulent radial bands, sparse broken opacity, and Doppler asymmetry. Add two slower, larger storm planes behind the event horizon with low alpha and red/blood-cloud colors.

- [ ] **Step 5: Implement infall particles and update function**

Create deterministic particles from the boss id. Store particle data in buffer attributes and use a shader uniform `time` to accelerate angular travel as normalized radius decreases. `updateBossBlackHole` updates all time uniforms, rotates front/back disc layers at different rates, and only applies a restrained focus pulse to outer storm layers; it never scales the opaque horizon independently.

- [ ] **Step 6: Run renderer tests and JavaScript syntax check**

```powershell
node --test frontend/space/black-hole-renderer.test.mjs
node --check frontend/space/black-hole-renderer.js
```

Expected: all tests pass and syntax exits `0`.

- [ ] **Step 7: Commit the renderer**

```powershell
git add frontend/space/black-hole-renderer.js frontend/space/black-hole-renderer.test.mjs
git commit -m "Render the boss as a true black hole"
```

---

### Task 3: Integrate Boss Dispatch, Animation, And Local Focus Environment

**Files:**
- Modify: `frontend/space/space.js`
- Modify: `frontend/space/stellar-renderer.js`
- Modify: `frontend/space/stellar-renderer.test.mjs`
- Modify: `backend/tests/test_challenge_frontend_api.py`
- Modify: `frontend/space/index.html`

**Interfaces:**
- Consumes: `createBossBlackHole` and `updateBossBlackHole` from Task 2.
- Produces: boss-only renderer dispatch, boss-centered dust/focus environment, and cache key `20260714-black-hole-focus-1`.

- [ ] **Step 1: Write failing integration contracts**

Assert the served source imports and dispatches the black-hole renderer:

```python
assert 'from "./black-hole-renderer.js?v=20260714-black-hole-focus-1"' in script.text
assert "createBossBlackHole" in script.text
assert "updateBossBlackHole" in script.text
assert "createBossCataclysm" not in script.text
assert "bendFilamentTowardBlackHole" in script.text
assert "SYSTEM_FOCUS_FRAGMENT_SHADER" in stellar.text
```

Extend the stellar environment test to require two incomplete dust lanes and a focus-plane material using normal alpha blending rather than additive-only haze.

- [ ] **Step 2: Run targeted integration tests and confirm red**

```powershell
python -m pytest backend/tests/test_challenge_frontend_api.py -k "stellar or boss" -q
node --test frontend/space/stellar-renderer.test.mjs
```

Expected: failure because the new module is not imported or dispatched and the focus environment is absent.

- [ ] **Step 3: Dispatch and animate the black hole**

In `createRenderedKnowledgeObject`, dispatch boss first, then pilot stars, then ordinary celestial nodes:

```js
if (definition.role === "boss") {
  return createBossBlackHole(state.THREE, definition, state.qualityLevel);
}
if (isStellarMaterialPilotNode(definition)) {
  return createKnowledgeStar(state.THREE, definition, state.qualityLevel);
}
return createCelestialNode(state.THREE, definition, state.qualityLevel);
```

In `updateCosmicMotion`, call `updateBossBlackHole` for `object.userData.blackHole`; otherwise retain `updateCelestialObject`.

Before constructing the final Catmull-Rom curve, pass control points targeting the boss through a deterministic `bendFilamentTowardBlackHole` helper. Clone the points, derive a tangent from the penultimate point to the boss center, and offset that penultimate point by `target.radius * (0.16 + seed * 0.1)`. The endpoints remain unchanged, so guided travel continues to arrive at the same safe approach point while visibly curving into the gravity field.

- [ ] **Step 4: Rebuild the local focus environment**

Pass the boss definition into `createStellarSystemEnvironment`, use the boss position as the dominant barycenter, and generate two partial elliptical dust lanes with different tilt, radius, and density. Replace the additive uniform haze with `SYSTEM_FOCUS_FRAGMENT_SHADER`: low alpha near the system, progressively darker alpha near the plane edge, plus a restrained warm band inside the orbital region. Keep `depthWrite: false` and position the focus plane behind all interactive objects.

- [ ] **Step 5: Update cache keys and integration contracts**

Use `20260714-black-hole-focus-1` for `space.js`, `cosmos-graph.js`, `stellar-renderer.js`, and `black-hole-renderer.js` imports so a browser cannot reuse the previous portal Boss bundle.

- [ ] **Step 6: Run targeted tests and syntax checks**

```powershell
python -m pytest backend/tests/test_challenge_frontend_api.py -q
node --test frontend/space/cosmos-graph.test.mjs frontend/space/stellar-renderer.test.mjs frontend/space/black-hole-renderer.test.mjs frontend/space/transit-route.test.mjs
node --check frontend/space/space.js
node --check frontend/space/stellar-renderer.js
node --check frontend/space/black-hole-renderer.js
git diff --check
```

Expected: all commands exit `0`.

- [ ] **Step 7: Commit integration**

```powershell
git add frontend/space/space.js frontend/space/stellar-renderer.js frontend/space/stellar-renderer.test.mjs frontend/space/index.html backend/tests/test_challenge_frontend_api.py
git commit -m "Focus the chapter around its black hole"
```

---

### Task 4: Tune From Real WebGL Frames And Close Out

**Files:**
- Modify only if screenshots reveal a measurable violation: `frontend/space/cosmos-graph.js`, `frontend/space/black-hole-renderer.js`, `frontend/space/stellar-renderer.js`, and their matching tests.
- Capture outside the repository: Codex visualization output directory.

**Interfaces:**
- Consumes: the live trainer at `/trainer/space/` and boss focus query `?focus=ode_separable.macro_challenge`.
- Produces: overview, approach, and encounter screenshots with zero runtime or WebGL errors.

- [ ] **Step 1: Start or reuse the local FastAPI server**

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8014
```

Expected: `/trainer/space/` returns HTTP `200` and the new cache key is present.

- [ ] **Step 2: Capture fresh desktop WebGL frames**

Use headless Chrome at `1600x1000` to capture:

- system overview after loading finishes;
- boss-focused encounter;
- one backed-away boss approach frame.

Collect `Runtime.exceptionThrown`, console error entries, and Chrome stderr matching `WebGL`, `shader`, `GL_INVALID`, or `CONTEXT_LOST`.

- [ ] **Step 3: Enforce the visual gate**

Reject and tune the implementation unless all are true:

- exactly six learning stars and one boss are visible in overview;
- no learning micro node is a blue portal;
- the event horizon is fully black with no tunnel spiral;
- boss event-horizon diameter is visually at least five learning-star photospheres;
- the full boss envelope occupies about half the useful frame height in overview;
- the complete local system uses at least three quarters of useful canvas width;
- encounter crops the outer storm while retaining event horizon readability;
- runtime and Chrome/WebGL error lists are empty.

Any tuning change must be paired with the closest deterministic graph/profile/source assertion before recapturing.

- [ ] **Step 4: Run full verification**

```powershell
python -m pytest backend/tests -q
node --test frontend/space/cosmos-graph.test.mjs frontend/space/stellar-renderer.test.mjs frontend/space/black-hole-renderer.test.mjs frontend/space/transit-route.test.mjs
node --check frontend/space/cosmos-graph.js
node --check frontend/space/stellar-renderer.js
node --check frontend/space/black-hole-renderer.js
node --check frontend/space/space.js
git diff --check
```

Expected: all tests and checks pass with zero failures.

- [ ] **Step 5: Commit any screenshot-driven tuning and push**

```powershell
git add frontend/space backend/tests/test_challenge_frontend_api.py
git commit -m "Tune the black hole chapter composition"
git push -u origin stellar-material-proof
```

If no tuning files remain after Task 3, do not create an empty commit; push the existing commits.
