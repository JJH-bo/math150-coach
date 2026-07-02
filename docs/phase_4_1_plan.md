# Phase 4.1 APP_PROFILE Route Gating

Status: implementation complete and frozen by Phase 4.1.1.

Phase 4.1 implements route registration and OpenAPI separation by deployment profile. It adds no new scoring, diagnosis, movement, catalog authoring, user, permission, database, frontend, LLM, mastery, or review feature.

## Profiles

Supported `APP_PROFILE` values:

- `learner`: expose only `/api/learner/v1/*`;
- `internal`: expose only `/api/v1/*`;
- `mixed`: expose both surfaces for local development and tests.

If `APP_PROFILE` is unset, the app defaults to `mixed` to preserve current local behavior and existing tests.

For learner-facing deployment, set:

```text
APP_PROFILE=learner
```

Invalid profile values fail fast with an explicit `Invalid APP_PROFILE` configuration error. Values are normalized with `strip().lower()`.

## App Factory

`backend/app/main.py` exposes:

```python
create_app(profile=None)
app = create_app()
```

`from app.main import app` remains supported. Tests can construct isolated apps with `create_app(profile="learner")`, `create_app(profile="internal")`, or `create_app(profile="mixed")` without mutating global environment state.

## Registration Rules

`mixed`:

- `/api/v1/*`;
- `/api/learner/v1/*`.

`learner`:

- `/api/learner/v1/*` only.

`internal`:

- `/api/v1/*` only.

The API layer only registers or hides routers. Endpoint internals and engine decisions are unchanged.

## Root Health

Root `/health` is retained for all profiles as a minimal deployment health check. It does not represent an API surface and does not list route capabilities.

Profile-owned health routes remain gated:

- `/api/v1/health` exists only in `internal` and `mixed`;
- `/api/learner/v1/health` exists only in `learner` and `mixed`.

## OpenAPI Separation

Each `create_app(profile=...)` call creates a separate FastAPI app, so OpenAPI reflects only the routes registered for that profile.

Learner profile OpenAPI does not include `/api/v1/*`.

Internal profile OpenAPI does not include `/api/learner/v1/*`.

Mixed profile OpenAPI includes both.

## Verification

Phase 4.1 verification:

- pytest: `264 passed`;
- scoring eval: `30/30 passed`;
- diagnosis eval: `25/25 passed`;
- movement eval: `12/12 passed`.

## Phase 4.1.1 Freeze Status

Phase 4.1.1 adds no product feature. It records the profile-boundary final audit and freezes the route-gating contract.

Frozen points:

- learner profile exposes only learner routes;
- internal profile exposes only internal routes;
- mixed profile remains local/test only;
- root `/health` remains a minimal health check, not an API surface declaration;
- profile gating is not an authentication or authorization system;
- no endpoint, engine, catalog, learner response, or golden eval behavior changed.

See `docs/phase_4_1_freeze_report.md` for the freeze record.
