# Phase 4.1 Freeze Report

Phase 4.1 is frozen after the Phase 4.1.1 profile-boundary final audit.

## Status

Complete:

- `APP_PROFILE` route gating;
- OpenAPI separation;
- `learner`, `internal`, and `mixed` profiles;
- invalid `APP_PROFILE` fail-fast handling;
- `create_app(profile=...)` app factory;
- `app = create_app()` compatibility for `from app.main import app`.

## Verification Baseline

Final local verification for the freeze pack:

- pytest: `264 passed`;
- scoring eval: `30/30 passed`;
- diagnosis eval: `25/25 passed`;
- movement eval: `12/12 passed`.

## Frozen Profile Contract

`APP_PROFILE=learner`:

- registers only `/api/learner/v1/*`;
- does not register `/api/v1/*`;
- learner submit remains catalog-backed and learner-safe.

`APP_PROFILE=internal`:

- registers only `/api/v1/*`;
- does not register `/api/learner/v1/*`;
- Phase 3 internal/dev contract remains unchanged.

`APP_PROFILE=mixed`:

- registers both `/api/v1/*` and `/api/learner/v1/*`;
- exists only for local development and tests;
- must not be used as the learner-facing production profile.

Default behavior:

- unset `APP_PROFILE` defaults to `mixed`;
- explicit `create_app(profile=...)` takes precedence over the environment variable;
- invalid `APP_PROFILE` values fail fast.

## OpenAPI Contract

Frozen OpenAPI behavior:

- learner profile OpenAPI does not include `/api/v1/*`;
- internal profile OpenAPI does not include `/api/learner/v1/*`;
- mixed profile OpenAPI includes both route groups;
- OpenAPI route visibility matches actual HTTP 404 behavior for hidden profile routes.

## Root Health Contract

Root `/health`:

- is a minimal deployment health check;
- is not part of `/api/v1` or `/api/learner/v1`;
- does not list route capabilities;
- does not reveal whether profile-outside API routes are registered.

Profile-owned health routes remain gated:

- `/api/v1/health` exists only in `internal` and `mixed`;
- `/api/learner/v1/health` exists only in `learner` and `mixed`.

## Security Boundary

Production learner deployment must explicitly set:

```text
APP_PROFILE=learner
```

Phase 4.1 is not an authentication or authorization system. It is route registration and OpenAPI exposure separation. Future user or permission systems must not replace profile gating.

## Unchanged

Unchanged by Phase 4.1:

- scoring, diagnosis, rollback, and forward engines;
- `LearningOrchestrator` call order;
- Phase 3 `/api/v1` endpoint behavior;
- Phase 4.0 `/api/learner/v1` endpoint behavior;
- catalog model behavior;
- learner-safe response projector;
- scoring, diagnosis, and movement golden evals.

## Final Audit

Audit conclusions:

1. `create_app(profile="learner")` does not register `/api/v1/*`.
2. `create_app(profile="internal")` does not register `/api/learner/v1/*`.
3. `create_app(profile="mixed")` preserves both local API surfaces.
4. root `/health` does not list route capabilities.
5. `app = create_app()` defaults to mixed unless `APP_PROFILE` is explicitly set.
6. invalid `APP_PROFILE` fails fast.
7. learner profile learner submit works.
8. internal profile internal submit works.
9. learner-safe response does not expose trusted, debug, or internal fields.
10. OpenAPI and HTTP 404 behavior are consistent for profile-hidden routes.

These audit points are covered by `backend/tests/test_phase_4_1_app_profile_gating.py`.

## Known Limits

Still not implemented:

- profile gating is not authentication or authorization;
- YAML catalog remains in-memory and minimal;
- `content_hash` is not enforced;
- no user accounts;
- no database;
- no frontend;
- no mastery model;
- no review scheduler;
- no real LLM;
- no full Mathematics I graph.

## Recommended Next Phase

Do not jump directly into frontend, mastery, or LLM integration.

Recommended next step is a Phase 4.2 plan, not immediate implementation. Candidate directions:

- catalog validation hardening;
- catalog authoring or import workflow design;
- attempt persistence plan;
- mastery and review model research.

Any Phase 4.2 scope should wait for explicit user approval.

