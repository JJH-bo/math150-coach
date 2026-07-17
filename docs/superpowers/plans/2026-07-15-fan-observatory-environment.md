# Fan Observatory Environment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bounded three-dimensional fan observatory containing three four-planet systems and four physically motivated black-hole environment dynamics while preserving the approved visual materials.

**Architecture:** A pure camera/layout module owns world coordinates and projection. `galaxy-lab` projects three system groups and the Boss into the existing high-dynamic-range compositor; `cosmos-lab` consumes the same Boss projection for lensing; `boss-lab` adds stable differentially rotating hot spots inside the existing ray-traced accretion material.

**Tech Stack:** Native JavaScript ES modules, WebGL2, GLSL ES 3.00, Canvas 2D Boss compositor

## Global Constraints

- Exactly 3 core systems for this proof, with exactly 4 planets per system.
- Preserve the approved planet surface language, Boss event horizon, Boss palette, and cold deep-space sky.
- Camera limits: yaw `±12°`, pitch `-7°–9°`, distance `0.86–1.18` of the calibrated default.
- No node clicking, training UI, pointer lock, WASD flight, jets, shockwaves, or screen shake.
- Do not create another WebGL context.
- Per user instruction, do not run the full project test suite; reserve the final visual judgment for the user.

---

### Task 1: Shared Observatory Camera and Fan Layout

**Files:**
- Create: `frontend/space/galaxy-lab/observatory-camera.mjs`
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Produces: `createObservatoryCamera()` with `drag(dx, dy)`, `dolly(delta)`, `reset()`, `update(dt)`, and `snapshot(aspect)`.
- Produces: `createSceneFrame(camera, aspect)` returning projected `systems`, `boss`, and `lens` values.

- [ ] **Step 1: Add bounded camera state**

```js
export const LIMITS = Object.freeze({
  yaw: [-12 * Math.PI / 180, 12 * Math.PI / 180],
  pitch: [-7 * Math.PI / 180, 9 * Math.PI / 180],
  distance: [8.6, 11.8],
});

export function createObservatoryCamera() {
  const current = { yaw: 0, pitch: 0, distance: 10 };
  const target = { ...current };
  return {
    current,
    target,
    drag(dx, dy) {
      target.yaw = clamp(target.yaw - dx * 0.0022, ...LIMITS.yaw);
      target.pitch = clamp(target.pitch - dy * 0.0018, ...LIMITS.pitch);
    },
    dolly(delta) {
      target.distance = clamp(target.distance * Math.exp(delta * 0.0007), ...LIMITS.distance);
    },
    reset() { Object.assign(target, { yaw: 0, pitch: 0, distance: 10 }); },
    update(dt) {
      const k = 1 - Math.exp(-dt * 8.5);
      for (const key of ['yaw', 'pitch', 'distance']) current[key] += (target[key] - current[key]) * k;
    },
  };
}
```

- [ ] **Step 2: Define the three-system world layout**

```js
export const SYSTEM_LAYOUT = [
  { center: [-3.8, -0.9, 1.2], scale: 1.0, energy: 1.0, seed: 1.3 },
  { center: [-1.5, 1.9, -1.5], scale: 1.0, energy: 0.74, seed: 5.7 },
  { center: [0.4, -1.7, -3.2], scale: 1.0, energy: 0.56, seed: 9.1 },
];
export const BOSS_WORLD = [5.15, 0.0, 0.0];
```

Each system projects the same four local planet positions `[-0.82,0,0]`, `[0,0.72,-0.12]`, `[0,-0.72,0.12]`, `[0.86,0,0.18]`. Perspective controls apparent size; the material resolution remains full.

- [ ] **Step 3: Replace free-flight inputs with observatory inputs**

Use pointer drag for `camera.drag()`, wheel for `camera.dolly()`, and double-click for `camera.reset()`. Remove WASD state and the old `x/y/zoom` translation.

- [ ] **Step 4: Commit the camera/layout slice**

```powershell
git add frontend/space/galaxy-lab/observatory-camera.mjs frontend/space/galaxy-lab/index.html
git commit -m "Build the bounded fan observatory camera"
```

### Task 2: Three-System HDR Projection and Gravity-Responsive Routes

**Files:**
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Consumes: projected planet centers/radii and projected Boss center/scale from `createSceneFrame()`.
- Produces: three four-planet systems, internal plasma links, and one terminal gravity route per system.

- [ ] **Step 1: Replace single-system uniforms**

```glsl
uniform vec4 planetData[12];   // x, y, radius, energy
uniform vec4 systemData[3];    // center x, center y, bound radius, depth fade
uniform vec4 bossData;         // x, y, optical scale, lens strength
```

Upload the arrays every frame from the camera projection. Continue using the approved `starField()` material function for every planet.

- [ ] **Step 2: Render bounded internal routes**

For each system, evaluate its four diamond links only when the fragment lies within `systemData[i].z`. Reuse the existing turbulent plasma SDF and vary only the seed and depth energy.

- [ ] **Step 3: Render terminal gravity routes**

```glsl
float gravity = 1.0 - smoothstep(0.34, 1.16, bossDistance);
samplePoint = boss + rotate2(-gravity * 0.34 / (bossDistance + 0.30)) * (samplePoint - boss);
float acceleration = mix(0.55, 2.8, gravity);
float packet = pow(0.5 + 0.5 * sin(t * 54.0 - time * 3.8 * acceleration), 8.0);
vec3 routeColor = mix(vec3(1.35, 0.54, 0.12), vec3(0.42, 0.008, 0.002), gravity);
```

Use one route from each system's merge planet to the Boss influence boundary. Fade before the event horizon instead of drawing over it.

- [ ] **Step 4: Commit the projected systems slice**

```powershell
git add frontend/space/galaxy-lab/index.html
git commit -m "Project three remastered systems into the fan"
```

### Task 3: Black-Hole Environment Dynamics

**Files:**
- Modify: `frontend/space/cosmos-lab/index.html`
- Modify: `frontend/space/boss-lab/index.html`
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Produces: `window.cosmosCamera.setGravityLens({ center, radius, strength })`.
- Consumes: projected Boss position and optical scale from the shared scene frame.

- [ ] **Step 1: Add background gravitational lensing**

```glsl
vec2 lensDelta = (screenPoint - gravityLens.xy) * vec2(aspect, 1.0);
float lensR = length(lensDelta);
float lensMask = smoothstep(gravityLens.z * 2.8, gravityLens.z * 0.72, lensR);
float deflection = gravityLens.w * lensMask / (lensR * lensR + gravityLens.z * gravityLens.z * 0.42);
screenPoint -= lensDelta / vec2(aspect, 1.0) * deflection;
```

Apply the warp before the sky ray direction is built. Keep the foreground planet layer unlensed.

- [ ] **Step 2: Add differentially rotating hot spots**

```glsl
float hotPhaseA = p_phi - art_time * (0.18 / pow(max(p_r, 3.0), 1.5));
float hotPhaseB = p_phi + 1.7 - art_time * (0.11 / pow(max(p_r, 3.0), 1.5));
float hotA = pow(max(cos(hotPhaseA * 3.0), 0.0), 18.0) * exp(-pow((p_r - 5.0) * 0.42, 2.0));
float hotB = pow(max(cos(hotPhaseB * 2.0), 0.0), 24.0) * exp(-pow((p_r - 7.2) * 0.34, 2.0));
float hotSpots = hotA + hotB * 0.62;
```

Blend hot spots into density and white-hot palette before the existing illegal-radiance guard.

- [ ] **Step 3: Add sparse spiral infall**

In the system fragment, derive polar coordinates around `bossData.xy`. Generate stable hashed cells along logarithmic spirals, stretch them tangentially, accelerate phase near the Boss, and fade color from amber to deep red before disappearance. Cap the visible particle coverage below `0.22`.

- [ ] **Step 4: Share Boss projection with the sky and compositor**

Every animation frame, send `frame.lens` to `cosmosCamera.setGravityLens()` and place the Boss composite using the projected Boss anchor. Clamp Boss optical scale to `0.92–1.12` of the approved baseline.

- [ ] **Step 5: Commit the environment slice**

```powershell
git add frontend/space/cosmos-lab/index.html frontend/space/boss-lab/index.html frontend/space/galaxy-lab/index.html
git commit -m "Animate the black hole environment"
```

### Task 4: User Visual Handoff

**Files:**
- Verify only: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Produces: `http://127.0.0.1:4173/space/galaxy-lab/?view=overview`

- [ ] **Step 1: Produce one final overview frame**

Open the page at `1920×860`, allow the shaders to settle, and capture one overview image. Do not run the full project suite.

- [ ] **Step 2: Push the completed branch**

```powershell
git push origin stellar-material-proof
```

## Self-Review

- Spec coverage: camera bounds, three systems, four planets per system, four environment dynamics, preserved Boss/planet/sky materials, and no click interaction each have a concrete task.
- Placeholder scan: no deferred implementation markers or undefined interfaces remain.
- Interface consistency: Task 1 produces `createSceneFrame()` and Task 2/3 consume its `systems`, `boss`, and `lens` fields.
