# Directional Learning System And Collapsing-Abyss Boss Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver one directional six-star learning system and one colossal collapsing-space Boss matching the approved Boss inspection frame.

**Architecture:** Keep the existing isolated `black-hole-renderer.js` boundary, but replace its spherical event horizon with a layered planar abyss and expand its outer storm into independent sheets, filaments and cloud particles. `cosmos-graph.js` owns the one-sector topology and exact route projection; `stellar-renderer.js` centers local dust on the learning cluster and adds one non-interactive gravity stream to the Boss. `space.js` keeps existing navigation and animation contracts.

**Tech Stack:** Browser-native ES modules, Three.js r162, GLSL shaders, Node test runner, FastAPI/TestClient contracts, headless Chrome DevTools capture.

## Global Constraints

- Exactly six pilot learning stars and exactly one Boss.
- Five internal learning links and only `expression -> macro_challenge` may enter the Boss.
- All six learning nodes occupy one compact directional sector; none surrounds the Boss perimeter.
- Boss abyss radius is at least `220`; Boss interaction radius is at least `620`.
- Boss source contains no `SphereGeometry`, ordinary portal throat or ordinary portal aperture.
- High and balanced quality both include abyss, storm sheets, shear filaments and storm-cloud particles.
- Manual camera rotation remains unrestricted and the Boss never follows screen space.
- Preserve backend learning ids, progression, scoring, selection and navigation semantics.

---

### Task 1: Replace The Black Sphere With A Layered Collapsing-Abyss Boss

**Files:**
- Modify: `frontend/space/black-hole-renderer.test.mjs`
- Modify: `frontend/space/black-hole-renderer.js`

**Interfaces:**
- Consumes: `createBossBlackHole(THREE, definition, qualityLevel)` and `updateBossBlackHole(node, elapsed, delta, isFocused)`.
- Produces: `createCollapsingAbyss`, `createStormSheets`, `createShearFilaments`, `createStormCloudField`, plus the unchanged public node contract.

- [ ] **Step 1: Write failing renderer structure and profile tests**

Require the approved layer families and reject the current spherical body:

```js
assert.match(source, /createCollapsingAbyss/);
assert.match(source, /createStormSheets/);
assert.match(source, /createShearFilaments/);
assert.match(source, /createStormCloudField/);
assert.doesNotMatch(source, /SphereGeometry/);
assert.doesNotMatch(source, /createPortalThroat|createPortalAperture/);

assert.ok(high.abyssRadius >= 220);
assert.ok(high.stormLayers >= 5);
assert.ok(high.filamentCount >= 18);
assert.ok(high.stormCloudCount > balanced.stormCloudCount);
assert.equal(high.abyssRadius, balanced.abyssRadius);
```

Also require source evidence for an offset core, depth-layer uniforms, torn continuous-noise storm masks and independent filament/cloud rotors.

- [ ] **Step 2: Run the focused test and confirm red**

Run:

```powershell
node --test frontend/space/black-hole-renderer.test.mjs
```

Expected: failure because the renderer still creates `SphereGeometry` and lacks the new layer builders/profile fields.

- [ ] **Step 3: Implement the collapsing abyss**

Replace `createEventHorizon` with `createCollapsingAbyss`. Use a `PlaneGeometry` and a dedicated fragment shader that:

```glsl
vec2 ellipsePoint = vec2(point.x, point.y / 0.74);
float boundaryNoise = fbm(ellipsePoint * 4.6 + vec2(time * 0.018, phase));
float aperture = 1.0 - smoothstep(0.79 + boundaryNoise * 0.045, 0.86, length(ellipsePoint));
vec2 offsetCore = ellipsePoint - vec2(0.16, -0.025);
float core = 1.0 - smoothstep(0.18, 0.34, length(offsetCore));
if (aperture < 0.01) discard;
```

Create three offset depth planes sharing physical aperture scale but using different `depthLayer` and `phase` uniforms. The deepest plane writes opaque black only inside the offset core; outer aperture regions remain red-black gas and fractured depth contours. Store `abyssLayers`, `abyssMaterials` and `abyssCore` in `node.userData`.

- [ ] **Step 4: Implement volumetric outer storm families**

Rename the current storm builder to `createStormSheets` and replace clean radial sine bands with value-noise/fBm torn masks. Create at least five high-quality low-alpha sheets with different tilt, scale and rotation direction.

Add `createShearFilaments`: deterministic partial `CatmullRomCurve3`/`TubeGeometry` strands distributed between `abyssRadius * 1.12` and `stormOuterRadius`, with alternating tilt and rotation groups.

Add `createStormCloudField`: deterministic buffer particles with orbit phase, radial band, vertical scatter and point size attributes. Its shader renders soft gas/ember sprites and slowly shears their orbital angle; high quality has more particles but identical envelope scale.

- [ ] **Step 5: Integrate motion and remove spherical assumptions**

Add the abyss layers, storm sheets, filaments and cloud points in explicit render order around the existing back/front accretion fragments and infall field. `updateBossBlackHole` must:

```js
node.userData.abyssLayers.forEach((layer, index) => {
  layer.position.x = node.userData.abyssOffsets[index] * (1 + Math.sin(elapsed * 0.09 + index) * 0.08);
});
node.userData.shearFilaments.forEach((filament, index) => {
  filament.rotation.z += delta * (0.0018 + index % 3 * 0.0007) * (index % 2 ? -1 : 1);
});
```

No update path may scale or rotate a black sphere because no spherical body remains.

- [ ] **Step 6: Run renderer tests and syntax checks**

```powershell
node --test frontend/space/black-hole-renderer.test.mjs
node --check frontend/space/black-hole-renderer.js
```

Expected: all tests pass and both commands exit `0`.

- [ ] **Step 7: Commit the Boss renderer**

```powershell
git add frontend/space/black-hole-renderer.js frontend/space/black-hole-renderer.test.mjs
git commit -m "Build the collapsing abyss boss"
```

---

### Task 2: Project One Directional Knowledge System And One Terminal Route

**Files:**
- Modify: `frontend/space/cosmos-graph.test.mjs`
- Modify: `frontend/space/cosmos-graph.js`
- Modify: `frontend/space/stellar-renderer.test.mjs`
- Modify: `frontend/space/stellar-renderer.js`

**Interfaces:**
- Consumes: `buildCosmosGraph(challenge)` and `createStellarSystemEnvironment(THREE, definitions, qualityLevel)`.
- Produces: deterministic one-sector positions, exact pilot progression pairs, local system dust lanes and `createSystemGravityStream`.

- [ ] **Step 1: Write failing topology and environment tests**

Assert exact pilot route pairs:

```js
const expectedPairs = [
  ["ode_separable.concept", "ode_separable.trigger"],
  ["ode_separable.trigger", "ode_separable.method"],
  ["ode_separable.method", "ode_separable.transformation"],
  ["ode_separable.transformation", "ode_separable.calculation"],
  ["ode_separable.calculation", "ode_separable.expression"],
  ["ode_separable.expression", "ode_separable.macro_challenge"],
];
assert.deepEqual(graph.edges.map(edge => [edge.sourceId, edge.targetId]), expectedPairs);
```

Require all learning nodes to remain on the entry side:

```js
assert.ok(Math.max(...learningNodes.map(node => node.position[0])) < boss.position[0] - boss.radius * 1.5);
assert.ok(clusterDiameter(learningNodes) <= 620);
assert.ok(boss.radius >= 220);
assert.ok(boss.interactionRadius >= 620);
```

Update the environment source test to require `learningCenter`, `createSystemGravityStream` and local lane radii, and reject `const center = boss?.position`.

- [ ] **Step 2: Run graph and stellar tests and confirm red**

```powershell
node --test frontend/space/cosmos-graph.test.mjs frontend/space/stellar-renderer.test.mjs
```

Expected: failure because current layout allows nodes around the Boss, uses Boss radius `196`, and centers both dust lanes on the Boss.

- [ ] **Step 3: Implement deterministic directional positions and edge projection**

Use a compact left-sector cluster similar to:

```js
const STELLAR_SYSTEM_POSITIONS = new Map([
  ["ode_separable.concept", [-540, 160, -720]],
  ["ode_separable.trigger", [-470, -150, -790]],
  ["ode_separable.method", [-350, 205, -820]],
  ["ode_separable.transformation", [-260, -35, -770]],
  ["ode_separable.calculation", [-330, -225, -910]],
  ["ode_separable.expression", [-470, 5, -990]],
  [STELLAR_PILOT_BOSS_ID, [390, 20, -880]],
]);
```

Set the pilot Boss radius to `224` and interaction radius to `640`. Define `STELLAR_PILOT_ROUTE_PAIRS` from the six required pairs. When pilot presentation is active, project only matching visible runtime edges in that exact order; preserve their original metadata and do not synthesize backend progression.

Tune `frontFrame.camera` and `lookAt` so all six stars and the cropped right-side Boss are visible in the initial frame.

- [ ] **Step 4: Recenter the local environment on the system**

Always compute `learningCenter` from the six micro positions and set the environment group to it. Reduce dust-lane radii so both incomplete lanes wrap the module cluster, not the Boss.

Implement `createSystemGravityStream(THREE, bossOffset, seed, qualityLevel)` as a non-interactive points field following one bowed interpolation from local-system space toward `boss.position - learningCenter`. Add it to the group beside local dust and the focus field. Do not create a second full Boss orbit.

- [ ] **Step 5: Run focused tests and syntax checks**

```powershell
node --test frontend/space/cosmos-graph.test.mjs frontend/space/stellar-renderer.test.mjs
node --check frontend/space/cosmos-graph.js
node --check frontend/space/stellar-renderer.js
```

Expected: all tests pass and all commands exit `0`.

- [ ] **Step 6: Commit the directional system**

```powershell
git add frontend/space/cosmos-graph.js frontend/space/cosmos-graph.test.mjs frontend/space/stellar-renderer.js frontend/space/stellar-renderer.test.mjs
git commit -m "Build one directional learning system"
```

---

### Task 3: Integrate, Tune Against Real WebGL, And Deliver

**Files:**
- Modify: `frontend/space/space.js`
- Modify: `frontend/space/index.html`
- Modify: `backend/tests/test_challenge_frontend_api.py`
- Modify only when a captured violation has a matching test: renderer, graph or stellar files from Tasks 1-2.

**Interfaces:**
- Consumes: the unchanged public renderer and graph contracts from Tasks 1-2.
- Produces: cache key `20260714-directional-abyss-1`, fresh overview/outer/inner captures and a pushed branch.

- [ ] **Step 1: Write failing integration/cache contracts**

Update the backend static contract to require:

```python
assert "20260714-directional-abyss-1" in index.text
assert "20260714-directional-abyss-1" in script.text
assert "createBossBlackHole" in script.text
assert "updateBossBlackHole" in script.text
assert "SphereGeometry" not in black_hole.text
assert "createSystemGravityStream" in stellar.text
```

Retain the existing assertion that ordinary portal helpers are absent from the Boss renderer.

- [ ] **Step 2: Run the contract test and confirm red**

```powershell
python -m pytest backend/tests/test_challenge_frontend_api.py -k "stellar or boss" -q
```

Expected: failure because the cache key and new layer contracts are absent.

- [ ] **Step 3: Update integration and cache identity**

Keep `createBossBlackHole`/`updateBossBlackHole` dispatch unchanged unless the new layer contract requires a backward-compatible optional argument. Update `index.html` and all pilot ES-module imports to `20260714-directional-abyss-1` so the browser cannot reuse the rejected spherical Boss bundle.

- [ ] **Step 4: Capture and enforce the real-WebGL visual gate**

Use the existing local server at `http://127.0.0.1:8014/trainer/space/` and headless Chrome at `1600x1000`. Capture:

- initial one-system overview;
- Boss focus/outer-storm frame;
- closer internal-abyss frame.

Reject the result unless all are true:

- six stars form one left-side system and none appears around the far Boss perimeter;
- only one final visible route reaches the Boss;
- the Boss storm is cropped and uses at least half the useful canvas width;
- outer storm reads as torn gas, filament and cloud volume rather than clean wire rings;
- inner abyss has layered depth and an offset dark core with no black sphere silhouette;
- no micro node becomes a blue portal;
- runtime, console, WebGL, shader and context-loss error lists are empty.

Every screenshot-driven code adjustment must first add or tighten the closest deterministic profile, topology or source test.

- [ ] **Step 5: Run full verification**

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

- [ ] **Step 6: Commit screenshot-driven tuning and push**

```powershell
git add backend/tests/test_challenge_frontend_api.py frontend/space
git commit -m "Tune the directional abyss boss"
git push -u origin stellar-material-proof
```

If no files remain after the Task 1-2 commits and cache update, do not create an empty commit.
