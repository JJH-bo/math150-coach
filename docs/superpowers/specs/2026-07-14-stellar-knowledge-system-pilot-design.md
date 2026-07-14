# Stellar Knowledge System Pilot Design

## Goal

Build a deliberately small visual pilot from the existing ordinary differential equations chapter that proves three things before the full knowledge galaxy is expanded:

1. Learning nodes can read as high-quality living stars rather than textured plastic spheres.
2. A compact group of learning stars can read as one dense, coherent knowledge system rather than isolated objects in empty space.
3. The existing singularity language can remain intact for the system assessment and can escalate into a genuinely oppressive boss encounter.

The pilot is a visual-quality gate, not a content-completeness milestone. Missing chapter coverage is acceptable. The existing ODE identifiers, interactions, scoring, diagnosis, rollback, and progression behavior remain authoritative.

## Approved Long-Term Structure

- One major chapter contains three to five core knowledge systems.
- Each system contains several stellar learning nodes.
- Each system ends at one medium singularity entrance used for system assessment.
- After all systems are completed, the learner reaches a final chapter boss.
- Existing singularity and space-entrance artwork is preserved. It must not be replaced with a planet or simplified into a generic sphere.

The pilot implements only one representative system and one boss-scale endpoint. It does not attempt to build all three to five systems.

## Pilot Content Slice

Use the existing `ode_network_mvp` data without requiring new mathematics content. The separable-equations module is the preferred sample because it already has a complete progression chain and an existing macro challenge.

The pilot presentation may use up to five of these existing learning nodes:

- `ode_separable.concept`
- `ode_separable.trigger`
- `ode_separable.method`
- `ode_separable.transformation`
- `ode_separable.calculation`

`ode_separable.macro_challenge` is the pilot endpoint and boss-scale stand-in. This is a visual pilot mapping only; it must not silently redefine the backend meaning of the macro challenge or invent trusted learning state. The expression node and auxiliary logic nodes may remain available but are not required to occupy primary visual positions in the first pilot.

## Visual Architecture

### Stellar learning nodes

A learning star is not a `SphereGeometry` with a conventional material and a rotating bitmap. It is a layered emissive phenomenon with independently animated surface and atmospheric structures.

Each star contains:

- a procedural photosphere shader with multi-scale convection cells, granular breakup, darker lanes, and deterministic variation;
- animated surface advection that moves through the shader field rather than rotating as a painted globe;
- limb darkening and an irregular chromosphere so the silhouette never reads as a hard plastic edge;
- a restrained volumetric corona whose brightness and scale vary around the circumference;
- sparse prominences or magnetic plasma arcs that emerge from selected regions rather than forming a uniform decorative ring;
- a local light contribution that illuminates nearby dust, routes, and environmental particles;
- a separate status beacon or navigation accent so learning state does not recolor the whole star into a traffic-light object.

Conventional metallic highlights, glossy PBR reflections, obvious texture seams, and uniform halo sprites are disallowed. A star that reads as a smooth ball with bloom fails the pilot.

Stars use deterministic seeds derived from node ids. Different nodes may vary in temperature, activity, granulation scale, and prominence shape, but those differences remain within one restrained stellar family rather than becoming a rainbow collection of unrelated effects.

### System composition

The five learning stars form one compact three-dimensional system rather than a straight progression lane. Their positions use two or three depth shells with meaningful overlap in the initial camera frame. The system should occupy roughly two thirds of the initial view, while still leaving a clear direction toward the assessment endpoint.

The apparent density comes from multiple scales:

- primary learning stars;
- small non-interactive stellar fragments and knowledge particles near their owners;
- one or two dust belts crossing the system;
- localized nebular haze shaped around the system rather than spread evenly across the entire scene;
- distant star clusters that establish depth but remain much dimmer than learning nodes;
- gravitational filaments that connect related stars.

Decorative objects must not resemble clickable nodes. Density must come from composition and depth, not from indiscriminately increasing the global star-particle count.

### Routes

The current permanent translucent tube is not the target visual language for the pilot.

- At rest, a relation appears as a narrow gravitational filament with a faint dust flow and no visible cylindrical wall.
- When selected, the filament gains a brighter core, directional particles, and a broader but still irregular energy wake.
- During guided travel, the wake temporarily expands into a traversable corridor. It decays after arrival instead of remaining as a plastic tunnel in the scene.
- Route width responds to endpoint scale and camera distance; it is not one fixed world-space radius for every relationship.
- Unrelated routes fade strongly so the system does not become a neon web.

The existing guided-transit behavior and progression path semantics remain unchanged even if the route renderer changes.

### Assessment singularity and boss pressure

The existing spatial-entrance and boss renderer is the quality reference. Its core visual identity is preserved.

For the pilot, the assessment endpoint must demonstrate boss pressure through environmental influence rather than scale alone:

- it remains visible from the system but does not begin as a tiny remote icon;
- its projected size grows continuously during approach;
- surrounding dust and route particles bend and accelerate toward it;
- nearby routes visibly curve into its gravity field;
- its halo affects a substantial portion of the frame without washing out the stars;
- local light, haze, and contrast change as the learner approaches;
- at the encounter distance, the singularity interrupts the composition through occlusion and edge cropping, creating a sense that it exceeds the viewport.

The full product will distinguish medium system-assessment singularities from the final chapter boss. The pilot is allowed to render its single endpoint at boss scale to validate the upper visual ceiling, but must keep this presentation-only choice isolated from backend learning semantics.

## Camera And Scale

- Initial framing shows the complete pilot system and the direction of progression without placing most content in a small central island.
- Free-flight collision and interaction radii remain proportional to visible stellar envelopes, not only to the photosphere radius.
- Focus framing accounts for the corona so the camera does not clip a star unintentionally.
- Guided travel never passes through a stellar photosphere or boss core.
- Boss approach uses staged framing: system view, gravitational approach, and encounter distance.
- The far plane and fog must preserve distant destinations without flattening depth.

Exact world-unit values are implementation details and should be tuned from screenshots rather than copied from the previous planetary layout.

## Rendering And Performance Boundaries

The stellar renderer should be isolated from the existing singularity renderer so a failed experiment can be removed without destabilizing the approved portals.

Recommended ownership:

- `stellar-renderer.js`: stellar shaders, corona, prominences, stellar animation, and quality-level variants;
- `singularity-renderer.js`: existing entrances, repair singularities, and boss cataclysm, modified only where shared environmental influence is required;
- `cosmos-graph.js`: pilot system grouping and spatial placement while preserving ids and runtime state;
- `space.js`: renderer dispatch, route presentation states, animation updates, camera framing, and environment orchestration.

High and balanced quality levels must both remain supported. Balanced mode may reduce shader octaves, prominence count, corona layers, and environmental particle density, but it may not fall back to a glossy textured sphere.

## Implementation Gates

### Gate 1: single-star material proof

Render one separable-equations learning star in the existing space background at near, medium, and far distances. Do not build the full pilot system until this proof passes visual review.

The proof fails if:

- the silhouette is a smooth hard circle with bloom;
- surface motion resembles a rotating texture;
- a conventional specular highlight makes the object look plastic;
- the corona is a uniform sprite or ring;
- the star does not illuminate nearby environmental material;
- it clashes with the current singularity renderer in contrast, detail density, or atmospheric depth.

### Gate 2: one-system composition

After the star material passes, place the selected ODE learning stars into one compact system with dust, depth shells, and gravitational filaments. Confirm that useful content dominates the frame and that decorative density cannot be confused with learning nodes.

### Gate 3: boss approach

Add the pilot endpoint using the preserved singularity language. Validate system view, mid-approach, and encounter framing. The boss must create pressure before the final close-up and must become compositionally overwhelming at encounter distance.

## Verification

Automated checks:

- JavaScript syntax checks for all modified frontend modules;
- existing graph, route, API contract, and frontend contract tests remain green;
- targeted source-contract tests protect the new stellar renderer dispatch, quality-level variants, preservation of the singularity renderer, and absence of a conventional glossy star material;
- route tests preserve guided-transit control points and arrival behavior.

Browser checks:

- desktop screenshots for single-star near, medium, and far views;
- desktop screenshots for system overview, selected route, travel corridor, boss approach, and boss encounter;
- balanced-quality and mobile screenshots with no blank canvas, fallback state, clipped controls, or unintended horizontal overflow;
- no console errors or WebGL shader compilation failures;
- stable interaction and flight behavior in both free and guided modes.

Visual approval is mandatory. Automated tests cannot declare the stellar material acceptable.

## Non-Goals

- completing the full ODE chapter galaxy;
- authoring missing mathematics content;
- changing scoring, diagnosis, mastery, rollback, or unlock policy;
- replacing or redesigning the approved spatial entrances;
- creating all three to five knowledge systems;
- finalizing the medium-assessment versus chapter-boss data model;
- adding decorative density that has no compositional purpose.

## Approval Criterion

The pilot succeeds only when the user confirms that the learning stars no longer resemble plastic balls, the system reads as a dense and intentional astronomical structure, the existing singularity quality has been preserved, and the boss produces sustained pressure rather than appearing merely as a large object in the distance.
