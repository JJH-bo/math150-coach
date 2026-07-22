# Visual, Page, and Teaching-Model Tool Pack Plan

> Execution rule: implement each adapter test-first and do not register it as
> `verified` until its real artifact and interaction gates pass.

## Goal

Extend `studio_tools_v1` with high-quality diagram, geometry, 3D scene, page,
template, asset, and animation capabilities while preserving the existing
Custom GPT Action and seven-scope permission model.

## Task 1: Verified diagram rendering

- Add failing tests for a structured Mermaid diagram request, descriptive alt
  text, canonical source/specification, self-contained SVG/HTML, PNG rendering,
  node/edge counts, and blank/clipping/error rejection.
- Pin Mermaid and render through the configured real Chromium runtime.
- Implement `visualization.diagram@1.0.0` without accepting arbitrary scripts,
  filesystem paths, or remote resource URLs.
- Register the adapter and add end-to-end Studio API evidence.

## Task 2: Verified browser-native 2D geometry

- Define a bounded scene schema for points, segments, vectors, circles,
  polygons, labels, axes, and declared learner controls.
- Emit canonical scene JSON, accessible self-contained SVG/HTML, PNG, and a
  geometry/pixel validation report.
- Exercise every declared control and fail registration when interaction is a
  no-op or produces invalid coordinates.

## Task 3: Verified Three.js 3D scenes

- Pin Three.js and define a bounded scene schema for mathematical surfaces,
  curves, vectors, points, grids, camera, lights, and declared controls.
- Produce a self-contained browser scene, poster PNG, multiple interaction
  screenshots, and WebGL/console/resource/interaction reports.
- Reuse the teaching-model lifecycle contract when a scene becomes a reusable
  registered model; do not expose arbitrary host code execution.

## Task 4: Page preview, templates, and assets

- Expose `template.list` and `template.instantiate` using learning intent,
  output mode, density, and interaction needs rather than subject labels.
- Implement `page.preview` through the real learner runtime at desktop and
  mobile viewports with overflow, console, model, typography, and accessibility
  evidence.
- Implement content-addressed `asset.ingest` for explicit uploads and tightly
  validated imports, including MIME sniffing, dimensions/duration, hashes,
  duplicate detection, size limits, and safe filenames.

## Task 5: Mathematical animation

- Run Manim Community in an isolated production worker with a structured scene
  vocabulary; do not accept arbitrary Python from the GPT.
- Emit source specification, MP4/WebM/GIF as requested, poster frame,
  representative frame sheet, captions/alt text, and media validation report.
- Add Docker dependencies and a reference animation only after the actual
  container can render it; until then the tool must not be advertised as
  `verified`.

## Task 6: Production and GPT handoff

- Generate reference evidence through the public Studio job protocol.
- Verify discovery, submit, poll, cancellation, artifact download, secret
  absence, and tool-scope enforcement for every new adapter.
- Build the production image, deploy it with durable storage and a rotated
  `STUDIO_API_KEY`, update the Custom GPT Action schema/instructions, then run a
  production author-preview-repair-publish-rollback journey.

