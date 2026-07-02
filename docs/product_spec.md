# Product Spec

## Product Goal

Math150 Coach Engine is a diagnostic training backend for students aiming at 150 points in Mathematics I. The system trains by knowledge nodes, not by undifferentiated question volume.

The core loop is:

1. Select a knowledge node.
2. Present a diagnostic or practice question.
3. Score the attempt across tested dimensions.
4. Diagnose weighted error causes.
5. Decide precise rollback, review, or forward movement.
6. Generate or schedule targeted variant practice after validation.

## Phase 0 Scope

Phase 0 delivers the contracts and sample data needed for the later product loop:

- Project skeleton.
- Rule documents.
- Core Pydantic models.
- Basic service interfaces.
- Sample ODE nodes.
- Golden scoring cases.
- Pytest coverage for key invariants.

## Out of Scope

- Frontend.
- Database.
- Real LLM API integration.
- Full symbolic solver.
- Full Mathematics I graph.
- Production deployment.

## Target User

The primary user is a serious exam candidate who needs to know exactly why a node is weak and what to review next. The system must be strict enough to prevent false confidence and specific enough to avoid wasting time on irrelevant rollback.
