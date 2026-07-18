# AI Classroom Product Cutover Design

## Purpose

Project D completes the Route Two conversion. The repository stops presenting
or maintaining a training universe and becomes one product: an AI-authored,
reading-first classroom with optional local detail and teaching models.

This is a product-boundary cutover, not a feature flag. Git history is the
archive for removed training code.

## Product Invariants

- `/` enters the classroom through the canonical `/classroom/` URL.
- Learner-facing code reads only `/api/classroom/v1`.
- Authoring uses only `/api/studio/v1`.
- There is no answer submission, scoring, diagnosis, mastery, review
  scheduling, recommendation, challenge progression, or Boss experience.
- A core module is a complete learning destination, not a task chain.
- Detail branches and teaching-model bindings support comprehension without
  producing learner-analysis records.

## Retained Product Spine

The following components remain active:

- `backend/app/classroom`: package, release, model, validation, preview, and
  runtime domain.
- `backend/app/api/studio/v1`: authenticated GPT authoring tools.
- `backend/app/api/classroom/v1`: read-only learner projection.
- `frontend/classroom`: learner atlas and reading stage.
- `frontend/model-runtime`: controlled teaching-model host and preview shell.
- classroom seed data, model seeds, bootstrap tools, evidence tools, and their
  focused tests.
- deployment profiles: `internal` exposes Studio, `learner` exposes Classroom,
  and `mixed` exposes both.

The generic API error response helper moves to `app.api.errors`; no retained
module may import a legacy API namespace.

## Removed Product Spine

The following are deleted rather than hidden:

- internal scoring/diagnosis/movement API `/api/v1`;
- learner question/attempt API `/api/learner/v1`;
- challenge API `/api/challenge/v1` and `/trainer`;
- scoring, diagnosis, mastery, rollback/forward, logic-evidence, local-trainer,
  question-catalog, challenge graph, progress, and Boss implementation;
- challenge/question/authoring data and evaluation cases used only by those
  systems;
- old trainer and legacy space frontends;
- tests, tools, reports, and specifications whose only subject is the removed
  training product.

The old material stays recoverable from Git history. Keeping it in an
`archive/` directory would preserve misleading maintenance surface and is
therefore rejected.

## Routing and Profiles

Routes are registered before static mounts.

- `internal`: `/api/studio/v1`, `/health`; `/` and classroom routes are absent.
- `learner`: `/api/classroom/v1`, `/classroom/`, `/classroom-runtime/`,
  `/health`, and `/` redirects to `/classroom/`.
- `mixed`: the union of internal and learner routes.

The canonical classroom mount remains `/classroom` so relative static assets,
browser evidence, and existing GPT/runtime documentation have one stable URL.

## Deletion Safety

Cutover tests are written first and assert:

- the root entry resolves to the classroom;
- the old routes return 404 and do not appear in OpenAPI;
- new profiles expose only their intended surfaces;
- retained Python and browser modules do not import or request legacy systems;
- repository product text does not advertise the removed experience.

Deletion happens in reversible commits: route/error extraction, implementation
and data removal, documentation/test cleanup, then final audit.

## Completion Gate

Project D is complete only when:

- every retained Python and Node test passes;
- a real browser reaches the classroom from `/` and completes the Project C
  flow without legacy requests;
- scans find no active legacy imports, routes, entry points, data roots, or
  product documentation;
- README describes only the AI Classroom;
- `git diff --check` is clean and the branch is pushed.
