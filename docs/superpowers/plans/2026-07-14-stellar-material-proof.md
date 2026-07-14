# Stellar Material Proof Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace only `ode_separable.concept` with one shader-driven living-star proof inside the existing knowledge universe, then stop for visual approval before building the rest of the stellar system.

**Architecture:** Add an isolated `stellar-renderer.js` that returns the same node interface as the approved singularity renderer. `space.js` dispatches only the named ODE pilot node to this renderer; every other learning node, system assessment, and boss continues through `singularity-renderer.js`. Pure profile tests and backend source-contract tests protect deterministic variation, quality modes, renderer isolation, and the prohibition on conventional glossy star materials.

**Tech Stack:** Three.js ES modules, GLSL `ShaderMaterial`, Node test runner, FastAPI `TestClient`, pytest, existing browser/WebGL verification workflow.

## Global Constraints

- Preserve all existing spatial-entrance and boss artwork.
- Do not change scoring, diagnosis, mastery, rollback, unlock policy, node ids, or challenge API payloads.
- Pilot exactly one node: `ode_separable.concept`.
- Do not use `MeshStandardMaterial`, `MeshPhysicalMaterial`, `MeshPhongMaterial`, or `MeshLambertMaterial` for the stellar photosphere or atmosphere.
- Surface animation must move through procedural shader fields; it must not rotate a bitmap texture around a sphere.
- Balanced quality may reduce noise octaves, prominence count, corona layers, and particles, but may not fall back to a glossy textured sphere.
- Stop after near, medium, and far screenshots. Do not build the full system until the user approves the material proof.

---

## File Structure

- Create `frontend/space/stellar-renderer.js`: deterministic stellar profiles, photosphere/chromosphere/corona shaders, prominences, local illumination, compatible node interface, and animation metadata.
- Create `frontend/space/stellar-renderer.test.mjs`: pure Node tests for the pilot predicate, deterministic profiles, quality reductions, and prohibited material names.
- Modify `frontend/space/space.js`: import the stellar renderer and dispatch only the pilot node while leaving singularity dispatch unchanged for every other object.
- Modify `frontend/space/index.html`: bump the `space.js` cache key once the new module is wired.
- Modify `backend/tests/test_challenge_frontend_api.py`: verify the new module is served and the frontend contract preserves singularities while using the stellar proof for exactly one node.

---

### Task 1: Lock The Pilot Predicate And Deterministic Stellar Profile

**Files:**
- Create: `frontend/space/stellar-renderer.js`
- Create: `frontend/space/stellar-renderer.test.mjs`

**Interfaces:**
- Produces: `isStellarMaterialPilotNode(definition: object): boolean`
- Produces: `stellarProfileFor(definition: object, qualityLevel: "high" | "balanced"): StellarProfile`
- `StellarProfile` fields: `seed`, `radius`, `activity`, `noiseOctaves`, `surfaceDetail`, `granulationScale`, `flowSpeed`, `coronaLayers`, `prominenceCount`, `lightIntensity`, `coreColor`, `midColor`, `edgeColor`.

- [ ] **Step 1: Write the failing pure-module tests**

Create `frontend/space/stellar-renderer.test.mjs`:

```js
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const moduleUrl = new URL("./stellar-renderer.js", import.meta.url);

async function loadRenderer() {
  let source = null;
  try {
    source = await readFile(moduleUrl, "utf8");
  } catch {
    // The first TDD run intentionally reaches the assertion before the module exists.
  }
  assert.equal(typeof source, "string", "stellar-renderer.js must exist");
  const renderer = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
  return { renderer, source };
}

test("only the separable concept node enters the material proof", async () => {
  const { renderer } = await loadRenderer();
  assert.equal(renderer.isStellarMaterialPilotNode({ id: "ode_separable.concept", role: "training" }), true);
  assert.equal(renderer.isStellarMaterialPilotNode({ id: "ode_separable.method", role: "training" }), false);
  assert.equal(renderer.isStellarMaterialPilotNode({ id: "ode_separable.macro_challenge", role: "boss" }), false);
});

test("stellar profiles are deterministic and balanced mode reduces cost without changing identity", async () => {
  const { renderer } = await loadRenderer();
  const definition = { id: "ode_separable.concept", radius: 14, difficulty: 0.24 };
  const highA = renderer.stellarProfileFor(definition, "high");
  const highB = renderer.stellarProfileFor(definition, "high");
  const balanced = renderer.stellarProfileFor(definition, "balanced");

  assert.deepEqual(highA, highB);
  assert.equal(highA.radius, 23.8);
  assert.ok(highA.activity >= 0.55 && highA.activity <= 0.9);
  assert.equal(highA.noiseOctaves, 5);
  assert.equal(highA.surfaceDetail, 5);
  assert.equal(highA.coronaLayers, 3);
  assert.equal(highA.prominenceCount, 4);
  assert.equal(balanced.noiseOctaves, 3);
  assert.equal(balanced.surfaceDetail, 4);
  assert.equal(balanced.coronaLayers, 2);
  assert.equal(balanced.prominenceCount, 2);
  assert.equal(balanced.coreColor, highA.coreColor);
  assert.equal(balanced.midColor, highA.midColor);
  assert.equal(balanced.edgeColor, highA.edgeColor);
});

test("stellar renderer forbids conventional glossy or bitmap star materials", async () => {
  const { source } = await loadRenderer();
  assert.match(source, /ShaderMaterial/);
  assert.doesNotMatch(source, /MeshStandardMaterial|MeshPhysicalMaterial|MeshPhongMaterial|MeshLambertMaterial/);
  assert.doesNotMatch(source, /TextureLoader|CanvasTexture/);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend\space\stellar-renderer.test.mjs
```

Expected: FAIL with `stellar-renderer.js must exist`.

- [ ] **Step 3: Implement the predicate and pure profile functions**

Create the initial `frontend/space/stellar-renderer.js`:

```js
const MATERIAL_PILOT_NODE_ID = "ode_separable.concept";

export function isStellarMaterialPilotNode(definition = {}) {
  return definition.id === MATERIAL_PILOT_NODE_ID && definition.role === "training";
}

export function stellarProfileFor(definition = {}, qualityLevel = "high") {
  const seed = hashUnit(definition.id || MATERIAL_PILOT_NODE_ID);
  const difficulty = clamp(Number(definition.difficulty ?? 0.24), 0, 1);
  const highQuality = qualityLevel === "high";
  return {
    seed,
    radius: Number((Number(definition.radius || 14) * 1.7).toFixed(3)),
    activity: Number((0.55 + difficulty * 0.22 + seed * 0.08).toFixed(4)),
    noiseOctaves: highQuality ? 5 : 3,
    surfaceDetail: highQuality ? 5 : 4,
    granulationScale: Number((7.4 + seed * 2.1).toFixed(4)),
    flowSpeed: Number((0.035 + difficulty * 0.025).toFixed(4)),
    coronaLayers: highQuality ? 3 : 2,
    prominenceCount: highQuality ? 4 : 2,
    lightIntensity: highQuality ? 13 : 8,
    coreColor: 0xfff2cf,
    midColor: 0xffa24a,
    edgeColor: 0xd94820,
  };
}

function hashUnit(value) {
  let hash = 2166136261;
  for (const character of String(value)) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 4294967295;
}

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}
```

- [ ] **Step 4: Run the tests and verify they pass**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend\space\stellar-renderer.test.mjs
```

Expected: `3` tests pass, `0` fail.

- [ ] **Step 5: Commit the deterministic profile contract**

```powershell
$git='C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
& $git add frontend/space/stellar-renderer.js frontend/space/stellar-renderer.test.mjs
& $git commit -m 'Add deterministic stellar material profile'
```

---

### Task 2: Build The Shader-Driven Living Star

**Files:**
- Modify: `frontend/space/stellar-renderer.js`
- Test: `frontend/space/stellar-renderer.test.mjs`

**Interfaces:**
- Consumes: `stellarProfileFor(definition, qualityLevel)` from Task 1.
- Produces: `createKnowledgeStar(THREE, definition, qualityLevel): CelestialNode`.
- `CelestialNode` must expose `id`, `title`, `description`, `role`, `kind`, `status`, `radius`, `interactionRadius`, `difficulty`, `group`, and `userData`.
- `userData` must expose `beacon`, `shaderMaterials`, `rotors`, `coronas`, and `stellar` so existing status, animation, and disposal paths remain compatible.

- [ ] **Step 1: Extend the failing source contract**

Append to `frontend/space/stellar-renderer.test.mjs`:

```js
test("living star contains independent photosphere, chromosphere, corona, prominences, and local light", async () => {
  const { source } = await loadRenderer();
  assert.match(source, /createKnowledgeStar/);
  assert.match(source, /createPhotosphere/);
  assert.match(source, /createChromosphere/);
  assert.match(source, /createCoronaLayers/);
  assert.match(source, /createProminences/);
  assert.match(source, /PointLight/);
  assert.match(source, /limb/);
  assert.match(source, /granulation/);
  assert.match(source, /convection/);
  assert.match(source, /userData\.stellar = true/);
});
```

- [ ] **Step 2: Run the source contract and verify it fails**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend\space\stellar-renderer.test.mjs
```

Expected: the new test FAILS because `createKnowledgeStar` and the shader layers do not exist.

- [ ] **Step 3: Add complete procedural shader foundations**

Add these shader constants below the profile helpers in `stellar-renderer.js`. The implementation may format them differently, but it must preserve the named inputs and the independent time-driven field:

```js
const PHOTOSPHERE_VERTEX_SHADER = `
  varying vec3 vObjectNormal;
  varying vec3 vViewNormal;
  varying vec3 vViewDirection;
  void main() {
    vObjectNormal = normalize(normal);
    vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
    vViewNormal = normalize(normalMatrix * normal);
    vViewDirection = normalize(-viewPosition.xyz);
    gl_Position = projectionMatrix * viewPosition;
  }
`;

const PHOTOSPHERE_FRAGMENT_SHADER = `
  uniform float time;
  uniform float seed;
  uniform float activity;
  uniform float noiseOctaves;
  uniform float granulationScale;
  uniform float flowSpeed;
  uniform vec3 coreColor;
  uniform vec3 midColor;
  uniform vec3 edgeColor;
  varying vec3 vObjectNormal;
  varying vec3 vViewNormal;
  varying vec3 vViewDirection;

  float hash31(vec3 p) {
    p = fract(p * 0.1031);
    p += dot(p, p.yzx + 33.33 + seed * 7.0);
    return fract((p.x + p.y) * p.z);
  }

  float valueNoise(vec3 p) {
    vec3 cell = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float n000 = hash31(cell + vec3(0.0, 0.0, 0.0));
    float n100 = hash31(cell + vec3(1.0, 0.0, 0.0));
    float n010 = hash31(cell + vec3(0.0, 1.0, 0.0));
    float n110 = hash31(cell + vec3(1.0, 1.0, 0.0));
    float n001 = hash31(cell + vec3(0.0, 0.0, 1.0));
    float n101 = hash31(cell + vec3(1.0, 0.0, 1.0));
    float n011 = hash31(cell + vec3(0.0, 1.0, 1.0));
    float n111 = hash31(cell + vec3(1.0, 1.0, 1.0));
    float nx00 = mix(n000, n100, f.x);
    float nx10 = mix(n010, n110, f.x);
    float nx01 = mix(n001, n101, f.x);
    float nx11 = mix(n011, n111, f.x);
    return mix(mix(nx00, nx10, f.y), mix(nx01, nx11, f.y), f.z);
  }

  float convection(vec3 p) {
    vec3 flow = vec3(
      sin(p.y * 2.7 + time * flowSpeed * 13.0),
      cos(p.z * 2.3 - time * flowSpeed * 9.0),
      sin(p.x * 2.1 + time * flowSpeed * 7.0)
    ) * (0.23 + activity * 0.08);
    float sum = 0.0;
    float amplitude = 0.58;
    float frequency = 1.0;
    for (int octave = 0; octave < 5; octave++) {
      float enabled = step(float(octave) + 0.5, noiseOctaves);
      sum += valueNoise((p + flow) * frequency) * amplitude * enabled;
      frequency *= 2.07;
      amplitude *= 0.48;
    }
    return sum;
  }

  void main() {
    vec3 p = normalize(vObjectNormal) * granulationScale;
    float field = convection(p);
    float cells = valueNoise(p * 2.9 + field * 1.7);
    float granulation = smoothstep(0.28, 0.78, cells + field * 0.34);
    float darkLane = 1.0 - smoothstep(0.05, 0.2, abs(cells - 0.47));
    float limb = clamp(dot(normalize(vViewNormal), normalize(vViewDirection)), 0.0, 1.0);
    vec3 color = mix(edgeColor, midColor, pow(limb, 0.55));
    color = mix(color, coreColor, granulation * 0.72);
    color *= 0.72 + field * 0.42 - darkLane * 0.16;
    color += coreColor * pow(1.0 - limb, 3.4) * activity * 0.12;
    gl_FragColor = vec4(color, 1.0);
  }
`;

const ATMOSPHERE_VERTEX_SHADER = PHOTOSPHERE_VERTEX_SHADER;

const ATMOSPHERE_FRAGMENT_SHADER = `
  uniform float time;
  uniform float seed;
  uniform float activity;
  uniform float layer;
  uniform vec3 edgeColor;
  varying vec3 vObjectNormal;
  varying vec3 vViewNormal;
  varying vec3 vViewDirection;
  void main() {
    float limb = 1.0 - clamp(dot(normalize(vViewNormal), normalize(vViewDirection)), 0.0, 1.0);
    float turbulence = 0.72 + 0.28 * sin(
      atan(vObjectNormal.y, vObjectNormal.x) * (11.0 + layer * 4.0)
      + vObjectNormal.z * 8.0
      + time * (0.11 + activity * 0.05)
      + seed * 19.0
    );
    float alpha = pow(limb, 2.2 + layer * 0.5) * turbulence * (0.2 + activity * 0.16) * (1.0 - layer * 0.24);
    gl_FragColor = vec4(edgeColor * (1.0 + activity * 0.2), alpha);
  }
`;
```

- [ ] **Step 4: Build the photosphere, atmosphere, corona, prominences, beacon, and compatible node object**

Add the following concrete functions to `stellar-renderer.js`. Keep helpers small; do not copy the singularity renderer or import its private helpers.

```js
export function createKnowledgeStar(THREE, definition, qualityLevel = "high") {
  const profile = stellarProfileFor(definition, qualityLevel);
  const group = new THREE.Group();
  group.position.set(...definition.position);
  group.userData.id = definition.id;

  const photosphere = createPhotosphere(THREE, profile);
  const chromosphere = createChromosphere(THREE, profile);
  const corona = createCoronaLayers(THREE, profile);
  const prominences = createProminences(THREE, profile);
  const beacon = createStellarBeacon(THREE, profile.radius, new THREE.Color(profile.midColor));
  const light = new THREE.PointLight(profile.midColor, profile.lightIntensity, profile.radius * 18, 1.65);
  light.position.z = profile.radius * 0.35;

  group.add(photosphere.mesh, chromosphere.mesh, ...corona.meshes, ...prominences.meshes, beacon, light);

  const node = {
    id: definition.id,
    title: definition.title,
    description: definition.description,
    role: definition.role,
    kind: definition.kind,
    status: definition.status,
    radius: profile.radius,
    interactionRadius: Math.max(definition.interactionRadius || 0, profile.radius * 4.4),
    difficulty: definition.difficulty,
    trainable: definition.trainable,
    color: definition.color,
    group,
    userData: {
      beacon,
      shaderMaterials: [photosphere.material, chromosphere.material, ...corona.materials, ...prominences.materials],
      rotors: [],
      coronas: [],
      stellar: true,
      stellarProfile: profile,
    },
  };
  node.userData.stellar = true;
  return node;
}

function sharedUniforms(THREE, profile) {
  return {
    time: { value: 0 },
    seed: { value: profile.seed },
    activity: { value: profile.activity },
    noiseOctaves: { value: profile.noiseOctaves },
    layer: { value: 0 },
    granulationScale: { value: profile.granulationScale },
    flowSpeed: { value: profile.flowSpeed },
    coreColor: { value: new THREE.Color(profile.coreColor) },
    midColor: { value: new THREE.Color(profile.midColor) },
    edgeColor: { value: new THREE.Color(profile.edgeColor) },
  };
}

function createPhotosphere(THREE, profile) {
  const material = new THREE.ShaderMaterial({
    uniforms: sharedUniforms(THREE, profile),
    vertexShader: PHOTOSPHERE_VERTEX_SHADER,
    fragmentShader: PHOTOSPHERE_FRAGMENT_SHADER,
    depthWrite: true,
    transparent: false,
    toneMapped: true,
  });
  return { mesh: new THREE.Mesh(new THREE.IcosahedronGeometry(profile.radius, profile.surfaceDetail), material), material };
}

function createChromosphere(THREE, profile) {
  const material = new THREE.ShaderMaterial({
    uniforms: sharedUniforms(THREE, profile),
    vertexShader: ATMOSPHERE_VERTEX_SHADER,
    fragmentShader: ATMOSPHERE_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.BackSide,
    toneMapped: false,
  });
  const mesh = new THREE.Mesh(new THREE.IcosahedronGeometry(profile.radius * 1.08, Math.max(3, profile.surfaceDetail - 1)), material);
  return { mesh, material };
}

function createCoronaLayers(THREE, profile) {
  const meshes = [];
  const materials = [];
  for (let index = 0; index < profile.coronaLayers; index += 1) {
    const material = new THREE.ShaderMaterial({
      uniforms: {
        ...sharedUniforms(THREE, profile),
        layer: { value: index / Math.max(1, profile.coronaLayers - 1) },
      },
      vertexShader: ATMOSPHERE_VERTEX_SHADER,
      fragmentShader: ATMOSPHERE_FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      toneMapped: false,
    });
    const scale = 1.18 + index * 0.16;
    const mesh = new THREE.Mesh(new THREE.IcosahedronGeometry(profile.radius * scale, Math.max(3, profile.surfaceDetail - 2)), material);
    mesh.rotation.set(index * 0.37, index * -0.29, index * 0.21);
    meshes.push(mesh);
    materials.push(material);
  }
  return { meshes, materials };
}

function createProminences(THREE, profile) {
  const meshes = [];
  const materials = [];
  for (let index = 0; index < profile.prominenceCount; index += 1) {
    const angle = profile.seed * Math.PI * 2 + index * 2.399963;
    const radial = new THREE.Vector3(Math.cos(angle), Math.sin(angle), (index % 2 - 0.5) * 0.34).normalize();
    const tangent = new THREE.Vector3(-radial.y, radial.x, 0).normalize();
    const base = radial.clone().multiplyScalar(profile.radius * 0.98);
    const points = [
      base.clone(),
      base.clone().addScaledVector(radial, profile.radius * 0.42).addScaledVector(tangent, profile.radius * 0.18),
      base.clone().addScaledVector(radial, profile.radius * 0.62).addScaledVector(tangent, profile.radius * 0.38),
      base.clone().addScaledVector(radial, profile.radius * 0.08).addScaledVector(tangent, profile.radius * 0.52),
    ];
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal", 0.42);
    const material = new THREE.ShaderMaterial({
      uniforms: sharedUniforms(THREE, profile),
      vertexShader: PHOTOSPHERE_VERTEX_SHADER,
      fragmentShader: ATMOSPHERE_FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    meshes.push(new THREE.Mesh(new THREE.TubeGeometry(curve, 28, profile.radius * 0.018, 5, false), material));
    materials.push(material);
  }
  return { meshes, materials };
}

function createStellarBeacon(THREE, radius, color) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute([
    radius * 1.18, radius * 0.84, radius * 0.08,
    radius * 1.3, radius * 0.66, radius * 0.06,
    radius * 1.39, radius * 0.46, radius * 0.04,
  ], 3));
  return new THREE.Points(geometry, new THREE.PointsMaterial({
    color,
    size: Math.max(0.55, radius * 0.07),
    transparent: true,
    opacity: 0.22,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  }));
}
```

- [ ] **Step 5: Run the renderer source tests**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend\space\stellar-renderer.test.mjs
```

Expected: `4` tests pass, `0` fail.

- [ ] **Step 6: Check module syntax**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check frontend\space\stellar-renderer.js
```

Expected: exit code `0` with no output.

- [ ] **Step 7: Commit the isolated living-star renderer**

```powershell
$git='C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
& $git add frontend/space/stellar-renderer.js frontend/space/stellar-renderer.test.mjs
& $git commit -m 'Build shader driven knowledge star'
```

---

### Task 3: Dispatch Exactly One ODE Node To The Stellar Renderer

**Files:**
- Modify: `frontend/space/space.js`
- Modify: `frontend/space/index.html`
- Modify: `backend/tests/test_challenge_frontend_api.py`
- Test: `frontend/space/stellar-renderer.test.mjs`

**Interfaces:**
- Consumes: `isStellarMaterialPilotNode` and `createKnowledgeStar` from Task 2.
- Preserves: `createCelestialNode`, `createBossCataclysm`, `applyCelestialStatus`, and `updateCelestialObject` from `singularity-renderer.js`.
- Produces: `createRenderedKnowledgeObject(definition)` inside `space.js`, returning the compatible `CelestialNode` from the correct renderer.

- [ ] **Step 1: Write the failing static frontend contract**

Append to `backend/tests/test_challenge_frontend_api.py`:

```python
def test_space_trainer_exposes_one_isolated_stellar_material_proof() -> None:
    client = TestClient(create_app("mixed"))

    page = client.get("/trainer/space/")
    script = client.get("/trainer/space/space.js")
    star = client.get("/trainer/space/stellar-renderer.js")
    singularity = client.get("/trainer/space/singularity-renderer.js")

    assert page.status_code == 200
    assert script.status_code == 200
    assert star.status_code == 200
    assert singularity.status_code == 200
    assert 'from "./stellar-renderer.js?v=' in script.text
    assert "createRenderedKnowledgeObject" in script.text
    assert "isStellarMaterialPilotNode(definition)" in script.text
    assert "createKnowledgeStar" in script.text
    assert 'MATERIAL_PILOT_NODE_ID = "ode_separable.concept"' in star.text
    assert "ShaderMaterial" in star.text
    assert "createKnowledgeSingularity" in singularity.text
    assert "createBossCataclysm" in singularity.text
    assert "MeshStandardMaterial" not in star.text
    assert "MeshPhysicalMaterial" not in star.text
    assert "MeshPhongMaterial" not in star.text
    assert "MeshLambertMaterial" not in star.text
    assert "TextureLoader" not in star.text
```

- [ ] **Step 2: Run the contract and verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_challenge_frontend_api.py -q -k stellar_material_proof
```

Expected: FAIL because `/trainer/space/stellar-renderer.js` is not yet exposed through the space page and `space.js` does not import it.

- [ ] **Step 3: Import and dispatch the pilot renderer in `space.js`**

Add the import beside the singularity imports:

```js
import {
  createKnowledgeStar,
  isStellarMaterialPilotNode,
} from "./stellar-renderer.js?v=20260714-stellar-material-proof-1";
```

Replace the direct renderer call inside `rebuildKnowledgeUniverse`:

```js
state.graph.objects.forEach((definition) => {
  const node = createRenderedKnowledgeObject(definition);
  state.scene.add(node.group);
  state.objects.push(node);
  state.objectById.set(node.id, node);
  applyCelestialStatus(state.THREE, node, definition.status, definition.id === state.currentTaskId);
});
```

Add this focused dispatch helper immediately before `rebuildKnowledgeUniverse`:

```js
function createRenderedKnowledgeObject(definition) {
  if (isStellarMaterialPilotNode(definition)) {
    return createKnowledgeStar(state.THREE, definition, state.qualityLevel);
  }
  return createCelestialNode(state.THREE, definition, state.qualityLevel);
}
```

- [ ] **Step 4: Bump the page cache key**

In `frontend/space/index.html`, change only the `space.js` query value to:

```html
<script type="module" src="./space.js?v=20260714-stellar-material-proof-1"></script>
```

- [ ] **Step 5: Run targeted tests and syntax checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_challenge_frontend_api.py -q -k "stellar_material_proof or knowledge_singularities"
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend\space\stellar-renderer.test.mjs
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check frontend\space\stellar-renderer.js
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check frontend\space\space.js
```

Expected: all targeted pytest cases pass, `4` Node tests pass, and both syntax checks exit `0`.

- [ ] **Step 6: Commit the one-node integration**

```powershell
$git='C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
& $git add frontend/space/space.js frontend/space/index.html backend/tests/test_challenge_frontend_api.py
& $git commit -m 'Integrate one stellar material proof node'
```

---

### Task 4: Verify The Material Proof And Stop For Visual Approval

**Files:**
- Test: `backend/tests/test_challenge_frontend_api.py`
- Test: `frontend/space/stellar-renderer.test.mjs`
- Inspect: `frontend/space/stellar-renderer.js`
- Inspect: `frontend/space/space.js`

**Interfaces:**
- Consumes: the integrated pilot node from Task 3.
- Produces: near, medium, and far visual evidence for user approval; no additional feature code.

- [ ] **Step 1: Run the complete relevant automated verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_challenge_frontend_api.py -q
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend\space\cosmos-graph.test.mjs frontend\space\transit-route.test.mjs frontend\space\stellar-renderer.test.mjs
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check frontend\space\stellar-renderer.js
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check frontend\space\space.js
```

Expected: pytest reports `0` failures, Node reports all tests passing, and syntax checks exit `0`.

- [ ] **Step 2: Start the local app and open the pilot node**

Run:

```powershell
Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory (Get-Location) -WindowStyle Hidden
```

Open:

```text
http://127.0.0.1:8000/trainer/space/?focus=ode_separable.concept
```

Expected: the focused object is the new stellar proof; nearby non-pilot objects remain the existing spatial entrances.

- [ ] **Step 3: Capture the three mandatory distances**

Capture:

1. Far: complete pilot star plus neighboring existing portals in one frame.
2. Medium: photosphere, chromosphere, and irregular corona are all distinguishable.
3. Near: convection cells, dark lanes, and prominence attachment points remain coherent without a texture seam or glossy highlight.

Expected visual evidence:

- surface motion changes internally while the object silhouette remains stable;
- no rotating-map seam is visible;
- corona brightness varies around the limb;
- prominences emerge from localized regions rather than forming a uniform ring;
- nearby dust or objects receive local illumination;
- existing singularity portals still render unchanged;
- no blank canvas, fallback state, console error, or WebGL shader compile error.

- [ ] **Step 4: Compare against the explicit failure list**

Reject the proof and iterate Task 2 if any of these are visible:

- smooth plastic sphere with bloom;
- hard circular edge with a single uniform halo;
- conventional specular highlight;
- rotating bitmap or texture seam;
- flat surface without multi-scale convection;
- star visibly lower in detail or atmospheric depth than the existing portals.

- [ ] **Step 5: Push the verified checkpoint**

Only after the automated verification is green and screenshots contain no runtime failure:

```powershell
$git='C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
& $git status --short
& $git push
```

Expected: the current branch pushes successfully. Do not start system layout, routes, or boss work.

- [ ] **Step 6: Present the three screenshots and wait**

Show the far, medium, and near evidence to the user and ask for one binary decision:

```text
恒星材质样板是否通过？通过后我才开始“一个知识系统＋Boss”的下一阶段；不通过则只迭代恒星，不扩大场景。
```

Expected: execution stops until the user explicitly approves or rejects the material proof.
