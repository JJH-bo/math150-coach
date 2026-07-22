# Custom GPT Tool Platform Design

## Goal

Give the Math150 Custom GPT a stable, discoverable, high-authority Studio tool platform that can compute, render, author, preview, export, publish, and recover classroom artifacts without requiring a new OpenAI API integration.

The Custom GPT remains the planner and classroom author. The project owns execution, deterministic artifacts, validation, versioning, and the learner runtime.

## Current State

The repository already provides authenticated Custom GPT Actions for classroom drafts, teaching-model source authoring, semantic browser previews, immutable releases, rollback, live learning-session expansion, and workspace discovery. The missing layer is a general tool protocol: every new mathematical or rendering capability currently needs a bespoke API and cannot expose a uniform execution record or artifact contract.

## Architecture

```text
Custom GPT
  |
  | OpenAPI Action + Bearer STUDIO_API_KEY
  v
Studio Tool API
  |- discover tools and versions
  |- submit idempotent jobs
  |- inspect status and structured results
  |- download hash-addressed artifacts
  `- cancel queued/running work
        |
        v
Durable Tool Runtime
  |- permission and limit policy
  |- isolated job directory
  |- adapter registry
  |- execution trace
  `- artifact validator
        |
        +-- Symbolic mathematics worker
        +-- Numerical modeling worker
        +-- Plot and chart worker
        +-- Teaching-model/browser preview worker
        +-- Page and classroom authoring worker
        +-- Presentation/document export worker
        `-- Mathematical animation worker
```

The public Action schema stays small and stable even as the registry grows. High-value classroom operations remain explicit Actions; the general tool job protocol serves the larger, extensible toolbox.

## Authority Model

The Studio bearer credential receives these project-level scopes:

- `studio.read`: inspect workspace, tools, jobs, drafts, models, releases, and artifacts;
- `studio.compute`: run symbolic, numerical, graph, optimization, and validation tools;
- `studio.render`: create plot, diagram, model-preview, slide, document, image, and animation artifacts;
- `studio.author`: create and modify classroom, model, template, asset, and export drafts;
- `studio.publish`: publish validated immutable classroom and model releases;
- `studio.rollback`: reactivate a previous immutable release;
- `studio.admin_tools`: install or enable a server-approved adapter version and change tool defaults.

The production Studio key receives every scope. Scope metadata remains explicit so a future shared deployment can issue narrower credentials without redesigning tools.

Authority does not expose raw host shell, arbitrary host paths, deployment secrets, or unrestricted outbound network access. Those are not teaching capabilities. Code-producing tools execute only inside per-job workspaces with declared inputs, time limits, output limits, and artifact allowlists.

## Stable Tool Contract

Every tool definition contains:

- stable `tool_id` and semantic `version`;
- title, description, category, and quality tier;
- required scope;
- JSON Schema for arguments and structured result;
- synchronous or asynchronous execution mode;
- timeout, artifact-count, and artifact-byte limits;
- deterministic flag and cache policy;
- supported output media types;
- quality gates and failure codes;
- official upstream project and license metadata.

The first Action surface is:

- `GET /api/studio/v1/tools` — searchable registry;
- `GET /api/studio/v1/tools/{tool_id}` — complete definition;
- `POST /api/studio/v1/tool-jobs` — idempotent job submission;
- `GET /api/studio/v1/tool-jobs/{job_id}` — durable status, result, trace, and artifacts;
- `POST /api/studio/v1/tool-jobs/{job_id}/cancel` — cooperative cancellation;
- `GET /api/studio/v1/tool-jobs/{job_id}/artifacts/{artifact_name}` — artifact download.

Every mutation requires `Idempotency-Key`. Reusing a key with different arguments is a conflict. A job records tool/version, canonical argument hash, creation/start/finish times, state, result, warnings, error, execution metrics, and artifact descriptors.

## Quality Tiers

- `verified`: deterministic reference cases, schema validation, artifact inspection, and runtime tests all pass;
- `previewed`: output passes automated visual or document preview but has no domain reference suite yet;
- `experimental`: discoverable only when explicitly requested and never selected automatically for publish-critical output.

Custom GPT instructions require `verified` tools by default. Experimental adapters cannot produce a publish-eligible classroom artifact.

## Core Tool Packs

### Mathematics pack

1. `math.symbolic` — SymPy 1.14 series for simplify, factor, expand, solve, differentiate, integrate, limits, series, matrices, equation equivalence, and LaTeX output.
2. `math.numeric` — NumPy/SciPy for linear algebra, quadrature, root finding, optimization, interpolation, ODE initial-value problems, FFT, probability distributions, and descriptive statistics.
3. `math.verify` — independent symbolic/numeric cross-checks, domain/assumption reporting, counterexample search over deterministic samples, and tolerance-aware comparison.
4. `math.graph` — NetworkX algorithms for dependency graphs, paths, connectivity, cycles, centrality, and layout data.
5. `math.optimize` — SciPy optimization initially; OR-Tools becomes a separate worker for CP-SAT and routing workloads.

Structured operations are exposed instead of arbitrary Python expressions. Symbols, assumptions, domains, methods, tolerances, and output formats are explicit arguments.

### Visualization pack

1. `visualization.plot` — Plotly 6 series for validated interactive figure JSON/HTML and Kaleido/Chromium PNG, SVG, and PDF exports.
2. `visualization.diagram` — Mermaid and Graphviz adapters for dependency, flow, state, and graph diagrams.
3. `visualization.geometry2d` — a browser-native geometry adapter using SVG/Canvas primitives and the teaching-model runtime.
4. `visualization.scene3d` — Three.js teaching-model scaffolds, preview, interaction evidence, and versioned registration.
5. `visualization.animation` — Manim Community Edition in an isolated render worker for MP4/WebM/GIF and poster-frame artifacts.

Every visual tool must provide alt text, a machine-readable scene/figure specification, and a browser or pixel validation report. Blank, pure-background, clipped, or interaction-no-op output fails.

### Authoring and page pack

1. `classroom.compose` — create a complete classroom package from validated blocks, models, bindings, and coverage evidence.
2. `classroom.patch` — apply typed JSON Patch-like operations with revision checks and dry-run diff.
3. `page.preview` — render a module, detail branch, viewport, and quality profile through the real learner runtime.
4. `template.list` and `template.instantiate` — select layouts by learning intent rather than fixed subject.
5. `asset.ingest` — chunked upload or URL import into a content-addressed asset store with media inspection.

The page vocabulary remains compositional. GPT may choose continuous classroom, slide deck, visual lab, worked-example notebook, concept map, narrated animation, or a mixed output without changing the underlying knowledge coverage contract.

### Export pack

1. `export.pptx` — PptxGenJS with native editable text, shapes, formulas as SVG, speaker notes, and rendered slide QA.
2. `export.reveal` — Reveal.js HTML slides with browser and PDF export.
3. `export.pdf` — Typst source plus PDF, with font, formula, link, page-overflow, and PDF-standard checks.
4. `export.html` — self-contained or project-hosted interactive lesson bundle.
5. `export.package` — immutable classroom package, dependency manifest, assets, and verification report.

Exports derive from one semantic lesson document so PPT, PDF, HTML, and classroom output do not silently contradict each other.

## Runtime Isolation and Limits

Each job uses `<CLASSROOM_DATA_ROOT>/tool-jobs/<job_id>/work` and may write only inside that directory. Artifacts are promoted atomically into an immutable artifact directory after validation. Adapters receive no Studio key or environment dump.

Default limits:

- synchronous metadata calls: 10 seconds;
- core math jobs: 30 seconds;
- plot and document jobs: 90 seconds;
- model and browser preview: 120 seconds;
- animation worker: 600 seconds;
- 64 artifacts per job;
- 256 MiB combined artifacts for core workers;
- 1 GiB combined artifacts for animation workers;
- cancellation checked between adapter phases;
- stdout/stderr stored with secret redaction and bounded to 1 MiB each.

## Error Contract

Errors are structured as `code`, `message`, `path`, `retryable`, and `repair_hint`. Stable families include:

- `tool_not_found`, `tool_version_unavailable`;
- `tool_scope_denied`;
- `tool_argument_invalid`;
- `tool_timeout`, `tool_cancelled`;
- `tool_dependency_unavailable`;
- `tool_execution_failed`;
- `artifact_missing`, `artifact_invalid`, `artifact_limit_exceeded`;
- domain codes such as `symbolic_domain_ambiguous`, `numeric_nonconvergence`, `plot_empty`, and `document_overflow`.

## Delivery Decomposition

1. Tool Platform Core: registry, permissions, durable jobs, artifacts, API, and Custom GPT instructions.
2. Mathematics and Plot Pack: symbolic, numerical, verification, graph, and Plotly adapters.
3. Authoring and Asset Pack: typed classroom patching, template registry, chunked assets, and real page preview.
4. Presentation and Document Pack: PPTX, Reveal, Typst/PDF, and HTML exports with render QA.
5. Animation and Advanced Modeling Pack: Manim, optimization worker, richer geometry, and long-running job infrastructure.
6. Production Cutover: deploy, update the Custom GPT Action schema/instructions, and run real material-to-classroom and material-to-PPT smoke tests.

Each project produces independently usable software; none is considered evidence for a later pack until its own runtime and artifact gates pass.

## Completion Evidence

The full objective is complete only when:

- the production Custom GPT can discover every verified tool without being told internal IDs;
- it can submit, poll, cancel, and retrieve artifacts through the Action;
- representative symbolic, numerical, plot, 3D model, page, PPTX, PDF, HTML, and animation jobs pass their reference suites;
- one uploaded mathematics chapter is independently transformed into at least three appropriate output formats chosen by GPT;
- every output passes mathematical, structural, visual, and artifact validation;
- the Custom GPT can preview, repair, publish, and roll back without a developer editing the repository;
- production secrets are not present in schemas, traces, artifacts, or client code;
- the public branch, deployment, Action schema, and Custom GPT instructions all reference the same tool protocol version.
