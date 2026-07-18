# AI Classroom Production Integration Design

> Date: 2026-07-18
> Status: approved by the user's standing instruction to execute Route Two
> Project: production deployment and Custom GPT Action integration

## 1. Outcome

The AI Classroom becomes a public HTTPS service that a Custom GPT can use as
an authenticated Action and that the learner can open directly in a browser.
The first production release keeps Studio authoring, classroom runtime,
teaching-model preview, and durable content storage in one service so a
published release is immediately visible to the learner runtime.

This integration does not add diagnosis, scoring, review scheduling, mastery
tracking, challenge gates, or any other learner-analysis system.

## 2. Selected Deployment Shape

The selected production target is one Docker web service on Railway:

- `APP_PROFILE=mixed` exposes both authenticated Studio authoring and the
  read-only classroom runtime;
- a persistent disk mounted at `/var/data` is the single
  `CLASSROOM_DATA_ROOT`;
- one instance avoids concurrent writes to the current file repository;
- the Studio bearer secret is generated locally and entered only in Railway
  Variables rather than stored in Git;
- the image contains Python, Node.js, Playwright, Chromium, and suitable fonts;
- a startup bootstrap copies the checked-in seed into an empty persistent disk
  without overwriting later authored releases;
- `/health` is the platform health check;
- `/privacy` is the public policy URL needed by a shared Custom GPT Action;
- `/api/studio/v1/action-schema.json` is a public schema document describing
  only authenticated Studio operations.

Railway is selected because it detects the existing root `Dockerfile`, supports
GitHub branch deployments, service variables, public HTTPS domains, and a
persistent volume mounted at `/var/data`. Its trial does not require a credit
card, so the complete runtime can be validated before choosing an ongoing
plan. A serverless frontend deployment would require replacing the Python
runtime, filesystem repository, subprocess worker, and Chromium execution
path.

## 3. GPT Action Boundary

The Action schema endpoint is intentionally unauthenticated so the GPT editor
can import it. The imported operations themselves continue to require HTTP
Bearer authentication.

The generated schema:

- contains only paths under `/api/studio/v1`;
- omits the schema endpoint itself;
- preserves stable, unique `operationId` values;
- declares the actual request origin in `servers`;
- preserves the OpenAPI bearer security scheme;
- never contains the bearer secret or local filesystem paths.

The Custom GPT receives the generated production secret only through its
Action authentication configuration. Learner pages and runtime APIs never
receive it.

## 4. Persistence and Runtime

The persistent root stores:

```text
/var/data/
  packages/
  releases/
  model-drafts/
  models/
  preview-jobs/
  preview-artifacts/
  idempotency/
```

The startup command calls the existing classroom bootstrap tool before
starting Uvicorn. Bootstrap must be idempotent: a fresh disk gets a usable
sample classroom and registered teaching models, while an existing disk is
left intact.

Playwright uses the system Chromium executable. Node resolves the pinned
Playwright package from `/app/node_modules`. Authored model JavaScript remains
confined to the existing sandboxed preview page with network blocking and an
ephemeral browser context.

## 5. Security and Privacy

- Studio writes require `Authorization: Bearer <STUDIO_API_KEY>`.
- The secret is generated in the hosting platform and is never committed,
  logged, returned by health checks, or embedded in OpenAPI.
- Classroom reads, static learner assets, health, privacy, and the Action
  schema are public.
- Source content sent through the Action is stored on the service's persistent
  disk to publish the requested classroom material.
- The product does not infer learner ability, diagnose errors, score answers,
  or schedule review.
- Model preview runs with browser networking blocked.

## 6. Deployment and Integration Flow

1. Commit and push the Docker, Railway config-as-code, schema, privacy, and
   tests.
2. Create a Railway project from the GitHub repository and select the
   `feature/ai-classroom-foundation` branch.
3. Set `APP_PROFILE=mixed`, `CLASSROOM_DATA_ROOT=/var/data`, preview runtime
   paths, and a newly generated `STUDIO_API_KEY` in Railway Variables.
4. Attach one volume to `/var/data` and generate a Railway public domain.
5. Wait for the Docker build and health check to pass.
6. Verify the public classroom, privacy page, Action schema, Studio bearer
   protection, and real-browser preview prerequisites.
7. Import the schema URL into the user's Custom GPT.
8. Configure Bearer authentication with the generated secret.
9. Set the GPT Action privacy URL to the deployed `/privacy` endpoint.
10. Exercise capabilities, draft, validation, publish, and learner reads through
   the public service.

Platform login, CAPTCHA, and paid-plan confirmation remain user-controlled
actions. They do not change the architecture or repository implementation.

## 7. Alternatives Rejected

### Separate Studio and learner services

Rejected for the first release. The current repository is atomic and durable
on one filesystem, but independent services cannot mount one Railway volume
concurrently.
Splitting them would require a database or object-storage migration before the
GPT-published release could become visible to the learner.

### Render Blueprint

Rejected after the first deployment attempt because account creation required
an hCaptcha flow and the user elected to change providers. Render-specific
configuration is removed rather than retained as an ambiguous second
production target.

### Fly.io

Rejected for the first release. It can run the Docker image and mount a volume,
but new organizations require a credit card. Railway allows the runtime to be
validated on its trial before a billing decision.

### Rewrite for a serverless site platform

Rejected. It would replace rather than deploy the completed FastAPI,
subprocess, filesystem, Node, and Chromium architecture and would delay the
Custom GPT integration.

### In-memory or ephemeral production storage

Rejected. Deploys and restarts would erase GPT-authored drafts, releases,
registered model versions, and preview evidence.

## 8. Completion Gate

Production integration is complete when:

1. The repository contains a reproducible production image and hosting
   config-as-code file with a persistent data root documented for the service.
2. All tests prove profile visibility, Action schema filtering and security,
   privacy availability, secret non-disclosure, and deployment file contracts.
3. The pushed service is healthy over HTTPS and survives a deploy with its
   published content intact.
4. The Custom GPT imports only Studio operations and authenticates with Bearer.
5. A public end-to-end run publishes or updates classroom content and the
   learner runtime reads the resulting active release.
6. No diagnosis, review, scoring, mastery, or training system is introduced.
