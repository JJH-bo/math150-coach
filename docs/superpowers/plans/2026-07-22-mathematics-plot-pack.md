# Mathematics and Plot Pack Implementation Plan

**Goal:** Extend `studio_tools_v1` with verified numerical mathematics, independent expression verification, graph algorithms, and publication-grade interactive/static plotting without changing the Custom GPT Action workflow.

**Architecture:** Register four strict adapters behind the existing durable job runtime. Inputs remain structured JSON and never accept arbitrary Python. Numerical and graph outputs are deterministic JSON artifacts. Plot outputs include a canonical Plotly figure specification, interactive HTML, alt text, validation report, and static PNG/SVG artifacts rendered through Kaleido and the configured Chrome/Chromium runtime.

**Tech Stack:** NumPy 2.4.4, SciPy 1.17.1, NetworkX 3.6.1, Plotly 6.9.0, Kaleido 1.3.0, SymPy 1.14.0, FastAPI, Pydantic v2, pytest.

## Global quality gates

- Every adapter is `verified`, schema-bounded, deterministic for the same arguments, and confined to its job work directory.
- Inputs contain data, operations, methods, tolerances, domains, and presentation intent; they never contain executable Python.
- NaN, infinity, non-convergence, empty plots, missing alt text, blank images, clipped dimensions, and malformed graph references fail with repairable structured errors.
- Numeric results include convergence/method metadata and precision-aware values.
- Plot jobs always emit machine-readable figure JSON, accessible alt text, interactive HTML, a validation report, PNG, and SVG.
- Production registry discovery exposes all five verified math/plot tools through the existing six Action operations.

## Task 1: Dependency and shared data contracts

- Pin NumPy, SciPy, NetworkX, Plotly, and Kaleido in `requirements.txt`.
- Add shared finite-number, bounded-array, serialization, and deterministic artifact helpers.
- Prove rejection of non-finite values, oversized arrays, and path-bearing inputs.
- Commit independently after focused tests pass.

## Task 2: `math.numeric@1.0.0`

- Support structured operations for descriptive statistics, linear systems/eigenvalues, quadrature, scalar root finding, bounded scalar minimization, interpolation, ODE initial-value problems, FFT, and named probability distributions.
- Represent functions with a safe expression plus explicit variables/parameters; reuse the symbolic parser allowlist and never evaluate code.
- Include reference cases, convergence failures, tolerance bounds, dimension validation, and deterministic JSON/CSV artifacts.
- Register only after reference tests pass.

## Task 3: `math.verify@1.0.0`

- Compare two declared expressions through exact symbolic equivalence first and deterministic domain-aware numeric samples second.
- Return assumptions, excluded points, maximum error, sample evidence, and a counterexample when found.
- Distinguish `equivalent`, `not_equivalent`, and `inconclusive`; never convert an inconclusive check into a positive claim.
- Add adversarial domain and tolerance tests.

## Task 4: `math.graph@1.0.0`

- Accept bounded node/edge records and directed/weighted flags.
- Support summary, shortest path, connectivity/components, cycle detection/topological order, centrality, and deterministic spring/circular/shell layout data.
- Return ordered node/edge data and JSON/CSV artifacts; reject duplicate nodes, unknown edge endpoints, invalid weights, and impossible algorithm/graph combinations.

## Task 5: `visualization.plot@1.0.0`

- Accept bounded traces for line, scatter, bar, area, histogram, heatmap, contour, and surface plots plus explicit title, labels, units, alt text, theme, and dimensions.
- Build a canonical Plotly figure without arbitrary template/code injection.
- Validate non-empty visible marks, finite coordinates, trace compatibility, readable dimensions, and alt text.
- Emit `figure.json`, `figure.html`, `figure.png`, `figure.svg`, `alt.txt`, and `validation.json`; inspect static image dimensions and pixel variance before success.
- Use the configured Chrome/Chromium executable for Kaleido when available and return a dependency repair hint if static rendering is unavailable.

## Task 6: Registry, Action, evidence, and regression

- Register all adapters in the default Studio tool service and assert searchable discovery through the Action schema.
- Extend runtime evidence with representative numeric, verification, graph, and plot jobs; download and inspect every artifact.
- Run focused tests, the complete Python suite, frontend/model tests, dependency checks, and `git diff --check`.
- Commit in cohesive scopes and push the feature branch before starting the Authoring and Asset Pack.
