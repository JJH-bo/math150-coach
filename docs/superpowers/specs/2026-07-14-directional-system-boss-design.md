# Directional Learning System And Collapsing-Abyss Boss Design

## Scope

This pilot renders one `ode_separable` learning system and one final Boss. It is the quality baseline for adding the remaining core systems later; it is not a miniature version of the final multi-system galaxy.

Visual acceptance is based on the approved target frame `boss-design-inspection-v2.png`: one compact six-node learning system occupies one directional sector, while a colossal red collapsing-space Boss dominates the opposite side of the frame.

## Non-Negotiable Topology

- Show exactly six learning stars and exactly one final Boss.
- The six stars form one compact local system on one side of the Boss. They must not be distributed around the Boss perimeter.
- The system owns five internal progression links:
  `concept -> trigger -> method -> transformation -> calculation -> expression`.
- Only one route leaves the local system for the Boss:
  `expression -> macro_challenge`.
- Decorative dust, gas and particles are non-interactive and must not resemble extra learning nodes.
- Future core systems may occupy the remaining directions. This pilot must leave those directions empty rather than implying that one system already surrounds the Boss.

## Boss Identity

The Boss is a dedicated collapsing-space black-hole entrance, not a conventional planet, not a black sphere and not a flat black disc.

### Internal Abyss

- Remove `SphereGeometry` from the Boss event horizon.
- Render the interior as a dedicated planar collapsing abyss with an irregular elliptical boundary.
- Use multiple offset depth layers. Each deeper layer is smaller, darker and slightly displaced toward an off-center black core, creating parallax rather than a painted spiral.
- The core is only the deepest part of the entrance; it must not fill the whole Boss silhouette.
- Add translucent red-black gas curtains, fractured photon arcs and accelerating inward particles between depth layers.
- Outside the aperture, fragments are discarded so the renderer never produces a solid rectangular plane.
- The abyss keeps depth writing for correct occlusion while its outer edge fades irregularly into the storm.

### Outer Storm

- Preserve the accepted red spatial-entrance language and exceed the old portal's visible layer count.
- High quality uses at least five procedural storm sheets, eighteen three-dimensional shear filaments and a deterministic volumetric cloud/ember field. Balanced quality may reduce counts but not remove any layer family.
- Storm sheets use continuous noise and torn spiral masks; they cannot be clean concentric rings.
- Shear filaments are partial three-dimensional curves with different tilt, radius and rotation direction.
- Cloud and ember particles occupy the volume between the abyss rim and the outer storm envelope, with sparse fragments falling inward.
- The storm moves slower than the internal abyss and photon fragments so parallax communicates enormous scale.

## Scale And Default Composition

- Boss abyss radius is at least `220` world units.
- Learning-star visible photosphere radii remain in their existing approximately `26-34` range, giving an abyss-to-star ratio above `6:1` before the outer storm is counted.
- Boss interaction radius is at least `620` world units.
- The Boss center is placed to the right of the one-system cluster and closer to the pilot depth band, never at the end of a long centered line.
- In the initial `1600x1000` view, the Boss storm is intentionally cropped by the right, top or bottom frame edges. Its visible envelope uses at least half of the useful canvas width, while the internal abyss remains readable.
- The local six-star system uses the left directional sector and remains visually subordinate. Its node-to-node connections read as one coherent system before the single terminal route reaches the Boss.
- The initial camera shows all six stars and the Boss. Manual exploration remains unrestricted; the Boss is never attached to screen space and the camera is never forcibly re-centered.

## Local Environment

- Replace the Boss-centered pair of complete-looking dust lanes with incomplete local lanes centered on the six-star system.
- Add one broad gravity stream extending from the system's terminal side toward the Boss.
- Background dust and star distortion may indicate the Boss direction, but must not add artificial orbit rings around the full Boss.
- The warm red-black environmental gradient is directional: strongest toward the Boss, cooler around the learning-system entry side.

## Motion

- Depth layers drift at different angular and offset speeds.
- Fractured photon arcs rotate slowly and never form one perfect continuous ring.
- Shear filaments counter-rotate in small groups.
- Volumetric storm clouds evolve more slowly than inner particles.
- Infall particles accelerate as they cross the aperture and reset outside the storm volume.
- Reduced-motion mode retains subtle layer evolution but disables large pulses and rapid rotations.

## Automated Verification

- The pilot graph contains six micro stars, one Boss and the exact six progression pairs specified above.
- No learning node lies on the far side of the Boss or inside the abyss/storm exclusion zone.
- Boss radius is at least `220` and interaction radius at least `620`.
- `black-hole-renderer.js` contains dedicated abyss, storm-sheet, shear-filament and storm-cloud builders.
- Boss source contains no `SphereGeometry` and no ordinary portal-throat/aperture calls.
- High quality has more storm sheets, filaments and particles than balanced quality while both keep the same physical scale.
- Existing backend, graph, route and navigation tests remain green.
- Browser capture reports no JavaScript, WebGL, shader or context-loss errors.

## Visual Verification

- Overview shows one directional six-star system, not a ring of nodes around the Boss.
- Only the system's terminal route reaches the Boss.
- The Boss is the first visual focal point and is dramatically larger than every star.
- The outer envelope is volumetric, irregular and layered rather than a collection of clean wire rings.
- The interior reads as a deep collapsing entrance with an offset black core, never as a black ball.
- Close view crops the outer storm while retaining readable internal depth.
- The system fills the local chapter frame without relying on uniform global particle density.

## Non-Goals

- Adding the remaining three to five core systems.
- Replacing ordinary spatial entrances elsewhere in the project.
- Physically exact framebuffer gravitational lensing.
- Restricting free-camera rotation or attaching the Boss to the viewport.
- Changing learning content, scoring, progression or backend challenge semantics.
