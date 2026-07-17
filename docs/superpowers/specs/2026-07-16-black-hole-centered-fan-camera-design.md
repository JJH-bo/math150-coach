# Black-Hole-Centered Fan Camera Design

## Goal

Replace the screen-centered affine viewer with a bounded three-dimensional observer that moves around the Boss black hole. The Boss, all systems, planets, and routes remain fixed in world space; accepted materials are unchanged.

## Camera contract

- `BOSS_WORLD` is the orbit pivot and the camera always looks back toward it.
- Drag changes spherical azimuth and elevation around the Boss, not any object transform.
- Wheel changes only the camera-to-Boss orbit radius.
- Hard bounds form the fan-shaped air wall: azimuth `-30deg..+30deg`, elevation `-15deg..+17deg`, radius `9.4..18.0`.
- A fixed projection offset keeps the Boss slightly right of screen center so the learning systems remain visible to its left. The offset never changes with input.
- Perspective and parallax are expected screen effects. World anchors never change.

## Layer synchronization

- Planets, routes, system envelopes, Boss anchor, and lens center use the same perspective projection.
- The Boss ray-traced observer receives azimuth, inclination, and radius derived from the shared orbit camera.
- The cosmos receives the same camera orientation; the obsolete affine sky transform remains neutral.
- Boss sampling quality and all accepted shaders remain unchanged.

## Acceptance

1. The camera position stays on a bounded spherical shell centered on the Boss.
2. Drag visibly reveals different safe Boss and system angles while the Boss remains at one stable composition anchor.
3. Wheel changes orbit radius and produces natural depth-dependent scaling.
4. World coordinates of every planet and system remain identical at every camera pose.
5. No screen-space object compensation, per-system camera following, or 2D scene translation remains.

