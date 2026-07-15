# Unified World Camera Design

## Goal

Replace the mixed screen-space composition with one bounded orbital camera. The observer moves; the planets, routes, Boss black hole, and background remain fixed in world space. Preserve the accepted materials and restrict this change to camera, projection, and Boss observer synchronization.

## Scope

- Keep the existing planet, route, Boss, and cosmos shaders and appearance presets.
- Keep the existing world positions and fan-shaped chapter layout.
- Replace drag and wheel behavior plus the projection/composition bridge.
- Do not add node-click interactions, new systems, new materials, or unrelated validation.

## Camera Model

The scene uses one fixed world-space observation target between the visible module group and the Boss. The camera orbits that target inside the existing bounded yaw and pitch envelope. Dragging changes only camera yaw and pitch. The fixed field of view is retained.

The wheel performs a true dolly by changing the camera's orbital distance to the fixed target. It does not change a separate Boss focus value and does not freeze the planets in screen space. Because every object remains fixed in world space, perspective naturally changes apparent size, separation, occlusion, and parallax.

World-space immobility does not mean pixel immobility: when the observer moves, projected screen positions must change according to depth.

## Shared Projection

Planets, routes, system envelopes, the Boss world anchor, and the gravity-lens center all use the same view basis and perspective projection.

The Boss screen center is the projection of its world anchor. Its composite size is derived from its fixed world radius and projected depth. Remove the Boss screen-position clamp, manually biased anchor, and independent optical scale. Camera limits and the fixed observation target preserve the intended composition instead of screen pinning.

The star field receives the same camera orientation and distance state so background motion agrees with foreground parallax.

## Boss Ray-Traced View

Derive the Boss renderer's observer direction directly from the vector between the shared camera position and the Boss world anchor:

- azimuth comes from the horizontal component of that vector;
- inclination comes from its vertical component;
- observer radius follows the camera-to-Boss distance inside a quality-safe bounded mapping.

This replaces the art-directed yaw-to-inclination coupling. Limited orbiting can therefore reveal the accretion disc's near/far sides, upper/lower surfaces, photon-ring response, and changing lensing, while respecting that the event horizon itself is approximately symmetric.

## Visual Quality Safeguards

- Do not alter accepted material or shading functions.
- Render the Boss source with enough overscan and pixel density for its largest allowed projected footprint; avoid enlarging a low-resolution cached frame.
- Keep the ray-traced observer parameters inside ranges already known to render without missing geometry or white artifacts.
- Derive the gravity-lens radius, route deflection envelope, and Boss composite footprint from the same projected world radius.
- Use eased camera interpolation only; never interpolate object world positions.
- Clamp camera distance before critical geometry crosses the near plane or exits the approved fan composition.

## Interaction Contract

- Drag: bounded orbit around the fixed scene target.
- Wheel: bounded physical dolly toward or away from the target.
- Double click: restore the approved initial camera pose.
- During drag and dolly, all scene layers must respond to the same camera state in the same animation frame.

## Acceptance Criteria

1. With no input, the accepted visual composition and material level remain intact.
2. Dragging changes only the camera pose; no object world anchor changes.
3. Planets, routes, Boss, lensing, and star field exhibit mutually consistent perspective and parallax.
4. The Boss is not screen-pinned and shows a real bounded ray-traced viewpoint change.
5. Dolly changes the apparent scale and separation of the whole fixed scene according to depth; it is not Boss-only scaling and does not freeze planets on screen.
6. At every allowed yaw, pitch, and distance boundary, the Boss and planets remain visible without crop seams, white patches, missing surfaces, or low-resolution enlargement.
7. The change does not modify the accepted material shaders or add unrelated functionality.

## Focused Verification

- Unit checks for fixed world anchors, true distance changes, projection/parallax direction, and Boss observer-vector mapping.
- Boundary checks at the minimum and maximum yaw, pitch, and distance combinations.
- Browser visual inspection at the default pose and each boundary pose, concentrating on crop seams, material stability, layer synchronization, and Boss ray-tracing artifacts.
- No unrelated full-project validation is required for this focused change.
