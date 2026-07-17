# Galactic Knowledge System Redesign

## Goal

Make the knowledge graph read as a large astronomical system rather than a cluster of glowing diagram nodes. Preserve all challenge interactions and node identifiers.

## Visual Hierarchy

- Macro chapter nodes are dominant planets with radii between 38 and 56 world units.
- Micro ability nodes are moons and minor bodies on multiple orbital shells between 120 and 210 units from their chapter planet.
- Chapter systems are separated at roughly twice the current distance and remain visible as distant destinations.
- Boss nodes remain gates, but scale with the larger planetary systems.

## Materials

- Generate deterministic 1024x512 macro textures from layered terrain noise, ridges, basins, polar variation, and sparse emissive details.
- Generate lighter 512x256 moon textures for micro nodes.
- Use restrained PBR settings: high roughness, low metalness, subtle bump, and low-opacity atmospheric scattering.
- Keep training state colors on navigation markers and route accents rather than tinting planetary surfaces.
- Give rings only to selected macro planets and render them as broad translucent physical bands.

## Routes

- Replace TubeGeometry route meshes and additive halos with thin Line or LineDashedMaterial paths.
- Local routes resemble orbital arcs; cross-chapter routes use long, sparse dashed trajectories.
- Lower route opacity so planets remain primary and the graph does not become a neon web.

## Camera And Scale

- Increase camera far plane and reduce fog density for the expanded galaxy.
- Frame focused nodes according to their physical radius so large planets occupy the viewport without clipping.
- Keep interaction radii proportional to object scale and preserve the existing pointer-lock flight controls.

## Verification

- Add frontend source assertions for hierarchy, PBR texture resolution, dashed routes, and removal of TubeGeometry routes.
- Run the complete test and evaluation suites.
- Verify desktop and mobile WebGL screenshots, nonblank canvas pixels, no fallback state, and no incoherent UI overlap.
