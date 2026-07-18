# AI Classroom Product Cutover Implementation Plan

**Goal:** Make AI Classroom the only active product and remove the complete
training-universe implementation, data, tests, and documentation.

**Accepted design:** `docs/superpowers/specs/2026-07-18-ai-classroom-cutover-design.md`

## Task 1: Freeze the New Product Boundary

- Add `backend/tests/test_ai_classroom_cutover.py`.
- Assert root/profile routing, canonical redirect, retained APIs, and 404 for
  every removed API/UI entry.
- Add a repository boundary test that rejects legacy imports and active product
  directories.
- Run the focused tests RED.

## Task 2: Detach Routing and Shared Errors

- Create `backend/app/api/errors.py`.
- Point Studio and Classroom routers/auth at the new helper.
- Remove legacy router imports and registrations from `backend/app/main.py`.
- Add the learner/mixed root redirect and update health/product metadata.
- Run routing, Studio, Classroom, and cutover tests GREEN.
- Commit `Cut over application routing to AI Classroom`.

## Task 3: Delete the Training Product

- Delete legacy API packages, engines, catalog, challenge, logic graph,
  training, seed, question/challenge data, legacy frontend, and eval tools.
- Delete their dedicated tests and generated reports/specifications.
- Preserve only classroom/model runtime code, data, tools, evidence, and
  relevant Route Two design history.
- Run retained tests and boundary scans.
- Commit `Remove legacy training universe`.

## Task 4: Rewrite Product Documentation

- Rewrite README around GPT authoring, package/model lifecycle, bootstrap,
  profiles, learner runtime, tests, evidence, and security boundaries.
- Remove every obsolete training-era document and command.
- Add a concise architecture/status document if needed for handoff.
- Run link/path and product-language scans.
- Commit `Document the AI Classroom product`.

## Task 5: Final Product Audit

- Run all Python tests with the real browser environment.
- Run all Node tests.
- Generate Project B and Project C browser evidence again.
- Open `/` in real Chrome and verify canonical classroom entry.
- Scan tracked files for removed routes, imports, directories, and training
  product terms; allow only explicit deny-list assertions and migration design
  history.
- Run `git diff --check`, inspect status/log, push, and record the final commit.
