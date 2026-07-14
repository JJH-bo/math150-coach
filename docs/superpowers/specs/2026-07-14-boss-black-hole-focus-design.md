# Boss Black Hole And Chapter Focus Design

## Goal

Upgrade the single-system ODE pilot so the chapter reads as a deliberately framed local galaxy instead of a small collection of objects floating in an unlimited sky. The single endpoint becomes a true black-hole boss rather than a larger version of the existing traversable portal.

This work must preserve all learning ids, progression, interaction, scoring, and navigation behavior. It changes presentation only.

## Diagnosis

The current boss fails for three related reasons:

1. Its center contains visible tunnel spirals and depth bands, so it reads as an illuminated entrance instead of an event horizon.
2. Its world-space radius is only about four times a learning star and it sits deeper than most stars, reducing the projected scale difference.
3. The system is distributed against a uniformly detailed sky. Even when all objects are visible, no local gravitational center owns the composition, so the background competes with the chapter.

The screenshot also exposes a renderer-dispatch defect: a failed or repair-state micro node falls back to the blue portal renderer. Every pilot learning micro node must remain a star regardless of training or repair state.

## Chosen Direction

Build an isolated black-hole renderer for the pilot boss and recompose the system around it. Do not keep extending the generic portal renderer: portals are traversable spatial entrances, while this boss needs a distinct physical and visual identity.

Rejected alternatives:

- Scaling the existing portal would amplify the wrong tunnel language.
- Merely darkening the portal center would improve contrast but retain the visible inward corridor and circular gateway silhouette.

## Boss Architecture

The boss is composed from independent layers, ordered from the black core outward:

1. **Event horizon:** a completely opaque, textureless black sphere/disc that remains darker than the sky and contains no visible spiral lines. Its silhouette is stable and readable at overview distance.
2. **Photon ring:** a narrow, irregular ring immediately outside the horizon. It uses asymmetric intensity and a hotter approaching side so it does not resemble a uniform neon torus.
3. **Accretion disc:** a broad, tilted elliptical disc with turbulent radial bands, broken opacity, and unequal brightness across the two sides. Separate back and front layers pass behind and in front of the horizon to sell three-dimensional occlusion.
4. **Infall field:** sparse particles orbit and accelerate as they approach the horizon. Their paths shorten and brighten near the inner disc rather than moving at one constant rate.
5. **Outer gravitational storm:** reuse the accepted red gas-envelope language at lower opacity and larger scale. It frames the black hole but cannot cover the event-horizon silhouette.
6. **Environmental light:** warm light affects nearby dust and filaments, while the horizon itself never emits light.

The black hole lives in a new `black-hole-renderer.js` module. It returns the same node contract used by the rest of the scene, so status, selection, navigation, disposal, and animation remain compatible without coupling the new shader code to ordinary portals.

## Scale And Composition

- Increase the pilot boss data radius from `118` to at least `188` world units.
- Keep learning-star photosphere radii in the existing `26–34` range, creating a physical core ratio of roughly `6:1`.
- Move the boss closer to the learning-star depth band instead of placing it at the deepest endpoint. Perspective must reinforce its size rather than cancel it.
- Place the boss at the center-right focal area, not against the viewport edge.
- Arrange the six learning stars across two asymmetric orbital bands around the boss. They remain a non-linear three-dimensional cluster and never overlap the event horizon in the initial frame.
- The initial desktop frame should devote roughly one third of its height to the event-horizon diameter and roughly one half to the full accretion/storm envelope. The complete system should use at least three quarters of the useful canvas width.
- Encounter framing intentionally crops the outer storm while retaining the event horizon and inner disc, making the boss feel larger than the viewport.

## Chapter Focus Environment

The environment becomes local and boss-centered:

- reshape the shared dust belt into two incomplete elliptical orbital lanes around the boss/system barycenter;
- concentrate warm dust density near the boss and learning-star paths instead of distributing it evenly;
- add a low-opacity boss-centered gravitational basin/haze that darkens toward the outer frame and lightly warms the system interior;
- bend the final relationship filament toward the black hole and increase its dust-flow acceleration near the endpoint;
- reduce decorative contrast outside the system focus region without removing the existing deep-space background.

Decorative particles remain non-interactive and must not resemble additional learning nodes.

## Learning-Star Consistency

All six pilot micro-node ids dispatch to the stellar renderer when their role is either `training` or `repair`. Repair state is expressed through status treatment, activity, or beacon color, never by replacing the star with a blue portal.

The single boss remains the only black hole in this pilot.

## Motion

- The photon ring drifts slowly and irregularly.
- Front and back accretion layers rotate at different speeds.
- Turbulence travels through the disc shader rather than rotating a static bitmap.
- Infall particles accelerate toward the center and reset outside the visible horizon.
- The outer storm moves more slowly than the inner disc, establishing scale through parallax.
- Reduced-motion preference retains subtle shader evolution but disables aggressive pulsing or camera shake.

No full-screen camera shake is required in this pass; scale, occlusion, contrast, and layered motion should produce the pressure.

## Verification Gates

Automated:

- the pilot graph exposes exactly six micro stars and one boss with boss radius at least `188`;
- all six pilot ids remain stars for both `training` and `repair` roles;
- the boss dispatches to `createBossBlackHole`, not `createBossCataclysm`;
- the new renderer contains separate event-horizon, photon-ring, accretion-disc, infall, and storm layers;
- the event horizon uses an opaque black material and the black-hole module does not call portal-throat or portal-aperture helpers;
- existing graph, route, API, and backend test suites remain green;
- JavaScript syntax and WebGL shader compilation checks pass.

Visual:

- overview shows six stars and one unmistakably larger black hole with a fully black center;
- no pilot learning node appears as a blue portal, including a repair-state node;
- the boss is the dominant focal object before approach;
- the system fills the useful frame without relying on uniform global particle density;
- encounter view crops the outer storm and disc while preserving the readable event horizon;
- no runtime, console, WebGL, or shader errors occur in the captured browser session.

## Non-Goals

- simulating physically exact gravitational lensing of the background framebuffer;
- adding multiple medium assessment black holes;
- changing backend learning semantics or challenge content;
- completing the remaining chapter systems;
- replacing ordinary spatial entrances;
- adding decorative planets or clickable filler objects.

