# Autonomous GPT Authoring Implementation Plan

> **For agentic workers:** execute task-by-task with test-first checkpoints.

**Goal:** Give the Custom GPT enough discoverability and operating authority
to turn supplied lecture material into a published AI Classroom without
asking the user for internal identifiers, addresses, or routine confirmation.

**Architecture:** Add one authenticated workspace bootstrap operation over
the existing filesystem repositories, expose it in the Action schema, deploy
it, and rewrite the GPT instructions around autonomous target selection,
repair, validation, and publishing.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pytest, Custom GPT Actions,
Railway.

## Global Constraints

- Do not expose or rotate `STUDIO_API_KEY` unnecessarily.
- Do not add diagnosis, review, scoring, mastery, challenge, Boss, or training
  systems.
- Preserve optimistic revisions, idempotency, immutable releases, and
  authenticated Studio writes.
- Do not claim platform-level Action approval prompts can always be disabled.
- The accepted design is
  `docs/superpowers/specs/2026-07-19-autonomous-gpt-authoring-design.md`.

### Task 1: Workspace Discovery Contract

**Files:**
- Modify: `backend/tests/test_classroom_repository.py`
- Modify: `backend/tests/test_studio_api.py`
- Modify: `backend/tests/test_production_integration.py`

- [ ] Write a failing repository test for deterministic draft listing.
- [ ] Write a failing Studio test for active package, draft, model, public
  origin, and autonomy policy summaries.
- [ ] Write failing tests for bounded pagination and authoritative selection
  among duplicate-package drafts and multiple model versions.
- [ ] Write a failing Action-schema test for `getStudioWorkspace`.
- [ ] Run focused tests and confirm RED.

### Task 2: Workspace Discovery Implementation

**Files:**
- Modify: `backend/app/classroom/repository.py`
- Modify: `backend/app/classroom/authoring.py`
- Modify: `backend/app/api/studio/v1/router.py`

- [ ] Implement deterministic classroom draft listing.
- [ ] Compose compact workspace summaries in the authoring service.
- [ ] Add bounded pagination, continuation metadata, and server-owned
  recommended-target signals.
- [ ] Add the authenticated `GET /api/studio/v1/workspace` operation.
- [ ] Run focused tests and confirm GREEN.

### Task 3: Documentation and Regression

**Files:**
- Modify: `README.md`

- [ ] Document workspace-first autonomous authoring.
- [ ] Run the complete Python suite.
- [ ] Run the complete Node suite.
- [ ] Run `git diff --check`.

### Task 4: Delivery and Deployment

- [ ] Commit the completed scope without secrets.
- [ ] Push `feature/ai-classroom-foundation`.
- [ ] Wait for the Railway deployment and verify health.
- [ ] Call the production workspace endpoint with authentication and verify
  real persisted state.
- [ ] Verify the public Action schema contains `getStudioWorkspace`.

### Task 5: Custom GPT Configuration

- [ ] Refresh the Action schema in the GPT editor without changing the bearer
  secret.
- [ ] Replace confirmation-oriented instructions with the autonomous policy.
- [ ] Save the GPT.
- [ ] Test a lecture-and-`做` prompt in Preview.
- [ ] Verify that the GPT calls the workspace operation and does not request a
  URL, internal ID, or routine confirmation.
