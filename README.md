# Math150 AI Classroom

Math150 AI Classroom turns chapter knowledge supplied by a custom GPT into a
coherent learning universe.

The GPT authors complete core modules. Each module can unfold at the learner's
pace through ordered content blocks, local detail branches, and persistent
teaching models. A module is a complete learning destination rather than a
fixed chain of small tasks.

## Product Surfaces

- **Studio API** — `/api/studio/v1` gives the custom GPT a broad, authenticated
  authoring environment for packages and teaching models.
- **Classroom Runtime API** — `/api/classroom/v1` exposes immutable published
  releases to the learner interface.
- **Learning universe** — `/classroom/` provides the chapter atlas, reading
  stage, in-place details, and model observatory.
- **Default entry** — `/` redirects to `/classroom/` in learner and mixed
  profiles.

The repository itself does not call an AI provider and does not need a provider
API key. The custom GPT is the author and calls Studio Actions using the
private `STUDIO_API_KEY`.

## Studio Tool Platform

`studio_tools_v1` gives the custom GPT one stable workflow for a growing set
of high-quality teaching tools. It can discover strict tool contracts, submit
idempotent durable jobs, poll terminal results, cancel obsolete work, and
download hash-verified artifacts. The current verified pack includes:

- `math.symbolic@1.0.0` for exact algebra, calculus, matrices, and LaTeX;
- `math.numeric@1.0.0` for statistics, linear algebra, quadrature, roots,
  optimization, interpolation, ODEs, FFT, and probability distributions;
- `math.verify@1.0.0` for exact checks, deterministic domain sampling, and
  counterexample evidence;
- `math.graph@1.0.0` for paths, components, cycles, centrality, topological
  order, and deterministic layout data;
- `visualization.plot@1.0.0` for accessible Plotly HTML plus browser-rendered
  PNG/SVG artifacts with pixel-level nonblank validation.
- `export.pptx@1.0.0` for editable native PowerPoint text and shapes, SVG
  mathematics, speaker notes, and OOXML/render validation;
- `export.reveal@1.0.0` for self-contained browser presentations, print PDF,
  slide PNGs, and DOM quality gates;
- `export.pdf@1.0.0` for fixed-layout distribution with deterministic metadata,
  extractable text, and page evidence;
- `export.html@1.0.0` for one-file offline browser lessons with a zero-external-
  resource audit;
- `export.package@1.0.0` for deterministic path-safe ZIP transfer with a
  cryptographic file manifest.

The GPT selects formats by teaching intent: PPTX for editable presenting,
Reveal for browser presenting, PDF for fixed distribution, HTML for direct web
use, and package for archival transfer. Multiple formats are generated from one
`semantic_lesson_v1` source and must report the same content hash.

The production Studio credential is authorized for all seven teaching scopes:
read, compute, render, author, publish, rollback, and tool administration.
Those scopes do not expose the host shell, arbitrary server paths, deployment
secrets, or unrestricted networking. Tools run with strict JSON schemas,
bounded time and artifact limits, and job-local storage.

The generic Action workflow is:

```text
GET  /api/studio/v1/tools
GET  /api/studio/v1/tools/{tool_id}
POST /api/studio/v1/tool-jobs
GET  /api/studio/v1/tool-jobs/{job_id}
POST /api/studio/v1/tool-jobs/{job_id}/cancel
GET  /api/studio/v1/tool-jobs/{job_id}/artifacts/{artifact_name}
```

New math, plot, page, asset, presentation, document, and animation adapters
register behind this protocol without changing the Custom GPT's workflow.

## Learning Package

`classroom_package_v1` supports:

- any number of courses, chapters, and complete core modules;
- ordered semantic blocks for prose, headings, formulas with explanations,
  derivations, comparisons, worked examples, code, tables, media, groups,
  model references, and expandable details;
- recursively nested detail branches for “没学懂，再详细展开”;
- exact-version references to teaching models;
- typed content-to-model bindings with explicit return behavior;
- deterministic drafts, validation reports, immutable releases, activation,
  idempotent writes, and rollback to an earlier release.

The sample package is
`backend/classroom_data/seed/calculus-foundations.json`.

## Teaching Model Workshop

`teaching_model_v1` gives the GPT a controlled source-and-preview loop:

1. Create or update a model draft containing a strict manifest and one browser
   ES module.
2. Validate the lifecycle contract and declared parameters, commands, events,
   and snapshots.
3. Request a real-browser preview and inspect its durable report/screenshots.
4. Register only the exact draft revision whose preview completed without
   uncaught errors or retained resources.
5. Pin the resulting immutable `m-<hash>` version in a classroom package.

Model source executes only inside a browser context. The reusable host owns
mount, update, snapshot, restore, command dispatch, animation frames, event
listeners, and disposal.

Checked-in reference models:

- `limit-neighborhood-2d`
- `binary-search-array`

## Custom GPT Authoring Flow

The GPT should begin every authoring run by discovering the current workspace:

```text
GET /api/studio/v1/workspace
Authorization: Bearer <STUDIO_API_KEY>
```

The workspace response gives it the public learner URL, existing active
packages, classroom drafts with current revisions, registered teaching
models, and the autonomous authoring policy. This prevents the GPT from
guessing identifiers or asking the user for project addresses, `draft_id`
values, or `package_id` values.

The workspace response is bounded with `offset` and `limit` query parameters
and reports totals, returned counts, and `next_offset` for packages, drafts,
and models. When several drafts share a package or several versions share a
model ID, the server marks exactly one recommended target and explains the
selection basis. The GPT follows these signals rather than inventing its own
recency rule.

`GET /api/studio/v1/capabilities` separately declares the accepted block
vocabulary and teaching model contract. After the user supplies lecture
material and says to make, start, or import it, the GPT is expected to select
or create the target, validate, repair, and publish without a routine
confirmation checkpoint. The normal write flow is:

```text
POST /api/studio/v1/model-drafts
PUT  /api/studio/v1/model-drafts/{draft_id}
POST /api/studio/v1/model-drafts/{draft_id}/validate
POST /api/studio/v1/model-drafts/{draft_id}/previews
GET  /api/studio/v1/previews/{job_id}
POST /api/studio/v1/model-drafts/{draft_id}/register

POST /api/studio/v1/drafts
PUT  /api/studio/v1/drafts/{draft_id}
POST /api/studio/v1/drafts/{draft_id}/validate
POST /api/studio/v1/drafts/{draft_id}/publish
```

Every mutable request requires an `Idempotency-Key`. Updates and publication
also require the expected revision, so retries are safe and concurrent edits
cannot silently overwrite one another.

Validation and revision conflicts are self-recovery inputs for the GPT. It
refreshes the workspace or current draft and retries safely rather than
delegating internal recovery to the user. Rollback is limited to an explicit
user request or an objectively failed release that the GPT has just published.
The workspace and Studio intentionally expose no diagnosis, scoring, review,
mastery, Boss, or learner-training system.

The ready-to-paste GPT operating instructions live in
[`docs/custom-gpt-instructions.md`](docs/custom-gpt-instructions.md). They
separate two behaviors:

- the published classroom owns the fixed baseline route and reveals one
  already-authored step at a time;
- when the learner says “这里没懂”, the GPT discovers the most recent active
  learning session, reads the exact active content target, and calls
  `patchLearningSessionScene` to insert a newly designed explanation in place.

The session patch may be nested when the first redesign is still too abstract.
`returnLearningSessionExpansion` and the learner-side return control reconnect
the learner to the parent explanation without mutating or republishing the
baseline classroom.

The GPT-ready, Studio-only OpenAPI document is available at
`/api/studio/v1/action-schema.json` in `internal` and `mixed` profiles. It
declares the current deployment origin and Bearer authentication without
exposing the credential. `/openapi.json` remains the general developer schema.

## Quick Start

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Bootstrap the sample package and registered reference models:

```powershell
$env:PYTHONPATH = "backend"
python tools/bootstrap_ai_classroom.py `
  --data-root backend/classroom_data/local
```

Run the combined local profile:

```powershell
$env:APP_PROFILE = "mixed"
$env:STUDIO_API_KEY = "replace-with-a-private-local-secret"
$env:CLASSROOM_DATA_ROOT = "$PWD\backend\classroom_data\local"
uvicorn app.main:app --app-dir backend --reload
```

Open `http://127.0.0.1:8000/`.

## Deployment Profiles

| `APP_PROFILE` | Studio | Classroom API/UI | Root entry |
| --- | --- | --- | --- |
| `internal` | yes | no | 404 |
| `learner` | no | yes | `/classroom/` |
| `mixed` | yes | yes | `/classroom/` |

`mixed` is the local default and the first production shape: Studio endpoints
remain private through Bearer authentication while learner endpoints are
public. Separate `internal` and `learner` services are supported only when
they share a future database or object repository; two independent filesystem
roots would not publish into the same classroom.

## Production Deployment

`railway.json` tells Railway to build the checked-in `Dockerfile`, wait for
`/health`, and restart only failed processes. The Railway service must use:

- `APP_PROFILE=mixed`;
- `AI_CLASSROOM_PUBLIC_ORIGIN=https://<generated-domain>` after generating
  the public domain;
- one persistent volume mounted at `/var/data`;
- `CLASSROOM_DATA_ROOT=/var/data`;
- a private, randomly generated `STUDIO_API_KEY`;
- `MODEL_PREVIEW_NODE=/usr/bin/node`;
- `MODEL_PREVIEW_BROWSER=/usr/bin/chromium`;
- `NODE_PATH=/app/node_modules`;
- `PYTHON_EXECUTABLE=/usr/local/bin/python`;
- one instance for safe filesystem writes;
- system Node.js and Chromium plus pinned Playwright `1.61.1`.

The container bootstraps checked-in models and the sample classroom only when
needed, then starts Uvicorn. Existing persistent content is not replaced.

Create a Railway project from `JJH-bo/math150-coach`, select the
`feature/ai-classroom-foundation` branch, add the variables above, and attach a
volume at `/var/data`. In Service Settings > Networking, choose
**Generate Domain**. After deployment:

1. Set `AI_CLASSROOM_PUBLIC_ORIGIN` to the generated HTTPS origin, without a
   trailing slash.
2. Open `/health`, `/`, and `/privacy`.
3. Import `/api/studio/v1/action-schema.json` in the Custom GPT Action editor.
4. Choose API Key authentication, select Bearer, and enter the generated
   `STUDIO_API_KEY` from Railway Variables.
5. Use the deployed `/privacy` URL as the Action privacy policy.
6. Test `getStudioWorkspace`, then the draft/validate/publish flow.

Do not copy the Studio secret into source files, GPT instructions, classroom
content, screenshots, or learner-side JavaScript.

## Runtime Continuity

The browser stores only `classroom_scene_v1` continuity:

- package and immutable release identity;
- course, chapter, module, and active content location;
- scroll position and open detail IDs;
- teaching-model snapshot;
- viewport quality and motion preference.

If a teaching model cannot load, lesson content remains readable and the model
dock shows a fallback. Reduced motion follows the system preference and can be
enabled in the atlas.

## Verification

Run the complete retained Python suite:

```powershell
$env:PYTHONPATH = "backend"
python -m pytest -q
```

Run browser-module tests with Node:

```powershell
node --test frontend/classroom/*.test.mjs frontend/model-runtime/*.test.mjs
```

Real preview and classroom evidence additionally require Playwright plus Chrome
or Edge:

```powershell
$env:MODEL_PREVIEW_NODE = "C:\path\to\node.exe"
$env:NODE_PATH = "C:\path\to\node_modules"
$env:MODEL_PREVIEW_BROWSER = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$env:PYTHONPATH = "backend"

python tools/generate_project_b_preview_evidence.py
python tools/generate_project_c_evidence.py
python tools/generate_tool_platform_evidence.py
```

Evidence is checked in under:

- `docs/preview-artifacts/project-b/`
- `docs/preview-artifacts/project-c/`
- `docs/preview-artifacts/tool-platform-core/`

## Repository Map

```text
backend/app/api/studio/v1/       GPT authoring API
backend/app/api/classroom/v1/    read-only learner API
backend/app/classroom/           package, release, model, preview domain
backend/app/tools/               tool contracts, registry, jobs, adapters
backend/classroom_data/          package and model seeds
frontend/classroom/              learner learning universe
frontend/model-runtime/          teaching-model host and preview shell
tools/                           bootstrap and browser evidence tools
docs/superpowers/                accepted Route Two designs and plans
```
