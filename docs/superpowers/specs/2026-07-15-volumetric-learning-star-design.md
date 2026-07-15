# Volumetric Learning Star Visual Design

## Goal

Replace the current ordinary learning-star material with one isolated, high-end visual proof. The proof exists only to judge the celestial material: it does not change knowledge data, node layout, routes, the approved Boss, or gameplay.

The ordinary learning node remains a living star, matching the previously approved stellar-system direction. It is not redesigned as a rocky planet and it must never read as a glossy painted sphere.

## Route Decision

Three routes were considered:

1. Improve the existing Three.js sphere and transparent shells. This is cheapest, but the mesh silhouette, layered shells, and tube prominences remain visible at close range. Its quality ceiling is below the approved Boss.
2. Use high-resolution solar textures on a PBR sphere. This can provide good still detail, but introduces UV/pole artifacts, finite texture resolution, and a familiar mapped-ball appearance during animation.
3. Render an implicit star with a full-screen WebGL2 light-field shader. This is the selected route. It removes the conventional mesh surface from the final image and continuously generates the photosphere, chromosphere, corona, and prominences in shader space.

## Scope

- Add an independent `/trainer/space/stellar-lab/` visual laboratory.
- Display exactly one ordinary learning star.
- Provide standard, close, and limb-emphasis views.
- Keep the background restrained and non-interactive.
- Do not modify `stellar-renderer.js` or integrate the material into the knowledge scene until the proof is approved.
- Do not run project tests for this visual-only approval pass.

## Rendering Architecture

### Implicit body

A full-screen fragment shader analytically intersects the camera ray with a sphere. The star is therefore resolution-independent and has no UV seam, polygon silhouette, normal-map sheen, or environment reflection.

The photosphere uses animated three-dimensional procedural fields:

- cellular granulation for bright convective cells and dark intergranular lanes;
- multi-octave noise for large convection regions;
- domain warping and differential rotation so the pattern evolves as plasma rather than sliding like a bitmap;
- sparse dark active regions with surrounding bright faculae;
- physically motivated center-to-limb darkening.

### Atmospheric volume

The shader integrates a thin emissive shell outside the photosphere instead of stacking transparent geometry. Density varies with height, direction, and animated turbulence. This creates a continuous red-orange chromosphere and an irregular corona without visible shell boundaries.

The corona contains broad asymmetric streamers, fine radial fibers, and dark gaps. Its silhouette is deliberately uneven so the star does not read as a circle with a blur filter.

### Prominences

Several animated signed-distance arcs rise from the limb. Their bases remain visually attached to active regions, their thickness tapers, and their interiors break into filamentary strands. They are shader fields, not tube meshes.

### HDR finish

The star renders into a floating-point target. A compact bloom chain extracts only the hottest emission, blurs it at reduced resolution, and recombines it before ACES-style tone mapping. Bloom supports the material but does not erase surface granulation.

## Art Direction

- Core light: near-white amber, restricted to hot granule centers and active faculae.
- Main photosphere: layered gold, orange, and deep ember lanes.
- Chromosphere: thin saturated red-orange rim.
- Corona: restrained dark red and amber with a few bright streamers.
- Sunspots: dark maroon rather than pure black, with bright fractured edges.
- Background: near-black with very faint, sparse depth specks only.

The standard view keeps the entire corona visible. The close view makes the surface occupy most of the frame so texture quality can be judged. The limb view emphasizes chromosphere thickness, prominence attachment, and corona breakup.

## Motion

- Granules boil locally instead of rotating as one texture layer.
- Large convection regions drift more slowly than fine detail.
- Active regions evolve gently without appearing or disappearing abruptly.
- Corona streamers breathe and shear at different speeds.
- Prominences move slowly enough to preserve their magnetic-loop character.

Motion remains continuous and restrained; there is no uniform pulsing sphere effect.

## Acceptance Standard

The proof passes only if:

- the body reads immediately as luminous plasma rather than plastic or stone;
- close view reveals stable granulation, dark lanes, active regions, and depth;
- the limb has a real chromosphere transition instead of a hard sphere edge;
- the corona is asymmetric, turbulent, and attached to the body;
- prominences look filamentary and physically rooted, not like decorative rings;
- the star remains legible at both standard and close scales;
- the visual quality is compatible with the approved relativistic Boss.

Automated tests are intentionally outside this approval pass. The user judges the isolated rendered result directly.
