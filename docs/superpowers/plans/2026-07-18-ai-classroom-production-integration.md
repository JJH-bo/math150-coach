# AI Classroom Production Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with review checkpoints.

**Goal:** Deploy the completed AI Classroom as a durable HTTPS service and connect the user's Custom GPT to its authenticated Studio API.

**Architecture:** Package the existing mixed-profile FastAPI application, Node preview worker, Playwright dependency, and Chromium in one Docker service. Mount one persistent data root, expose a filtered production-origin Action schema and public privacy policy, then configure and test the Custom GPT against the deployed service.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, Node.js, Playwright, Chromium, Docker, Railway config-as-code, pytest.

## Global Constraints

- Do not commit or expose `STUDIO_API_KEY`.
- Keep Studio operations Bearer-authenticated.
- Keep learner reads and learner assets free of Studio credentials.
- Do not add diagnosis, review, scoring, mastery, challenge, or training logic.
- Run only one service instance while the repository uses filesystem writes.
- Bootstrap an empty persistent root without overwriting existing production data.
- The accepted design is `docs/superpowers/specs/2026-07-18-ai-classroom-production-integration-design.md`.

---

### Task 1: Production-facing Action Contract

**Files:**
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_production_integration.py`

- [ ] Write failing tests for the filtered Action schema, Bearer security,
  request-origin server URL, profile visibility, unique operation IDs, privacy
  page, and secret non-disclosure.
- [ ] Run the focused tests and confirm RED.
- [ ] Implement `/api/studio/v1/action-schema.json` for internal/mixed profiles
  and `/privacy` for all profiles.
- [ ] Run the focused tests and confirm GREEN.

### Task 2: Reproducible Production Image

**Files:**
- Create: `package.json`
- Create: `package-lock.json`
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `railway.json`
- Delete: `render.yaml`
- Modify: `backend/tests/test_production_integration.py`

- [ ] Add failing static contract tests for the Docker runtime, preview
  environment, mixed profile, persistent data root, health check, Docker
  builder, and restart policy.
- [ ] Run the focused tests and confirm RED.
- [ ] Pin the Node Playwright dependency and generate its lockfile.
- [ ] Add a Python/Node/Chromium Dockerfile and Railway config-as-code.
- [ ] Run the focused tests and confirm GREEN.

### Task 3: Regression and Runtime Verification

- [ ] Run the complete Python test suite.
- [ ] Run all Node tests.
- [ ] Run the classroom bootstrap against a temporary data root.
- [ ] Launch the application locally with production-like environment values.
- [ ] Verify health, privacy, schema, Studio authorization, learner reads, and a
  real-browser preview.
- [ ] Run `git diff --check`.

### Task 4: Repository Delivery

- [ ] Commit the design and implementation in intentional scopes.
- [ ] Push `feature/ai-classroom-foundation` to origin.
- [ ] Confirm the remote branch points to the tested commit.

### Task 5: Railway Deployment

- [ ] Open Railway and create a project from
  `JJH-bo/math150-coach`, branch `feature/ai-classroom-foundation`.
- [ ] Add a volume mounted at `/var/data`.
- [ ] Configure `APP_PROFILE=mixed`, `CLASSROOM_DATA_ROOT=/var/data`,
  `MODEL_PREVIEW_NODE=/usr/bin/node`,
  `MODEL_PREVIEW_BROWSER=/usr/bin/chromium`, `NODE_PATH=/app/node_modules`,
  `PYTHON_EXECUTABLE=/usr/local/bin/python`, and a newly generated
  `STUDIO_API_KEY`.
- [ ] Generate a Railway public domain.
- [ ] Confirm or hand off only platform login, CAPTCHA, or paid-plan checkout.
- [ ] Wait for build and health checks.
- [ ] Verify the Studio secret remains private.
- [ ] Record the production HTTPS origin without storing the secret.
- [ ] Verify persistent content survives a redeploy.

### Task 6: Custom GPT Action

- [ ] Open the user's Custom GPT editor.
- [ ] Import `<production-origin>/api/studio/v1/action-schema.json`.
- [ ] Configure API Key authentication as HTTP Bearer using the generated
  production secret.
- [ ] Set `<production-origin>/privacy` as the privacy policy URL.
- [ ] Save the GPT and test capabilities in Preview.

### Task 7: Public End-to-end Test

- [ ] Use the Action to inspect capabilities and the active catalog.
- [ ] Create or update a draft with an idempotency key.
- [ ] Validate and publish the draft.
- [ ] Read the active release through the public classroom API.
- [ ] Open the learner classroom and verify the published module renders.
- [ ] Confirm the flow stores content only and introduces no learner-analysis
  behavior.
