# Math150 Coach Engine

Math150 Coach Engine is a backend foundation for a knowledge-graph diagnostic training system targeting a 150-point goal in Graduate Entrance Exam Mathematics I.

This is not a simple question bank. The engine is designed around knowledge-node progression, multi-dimensional scoring, weighted error diagnosis, precise rollback/forward decisions, validated variant generation, and review scheduling.

## Project Vision Handoff

For a new thread or a new assistant, read [docs/explan.md](docs/explan.md) first. It captures the product vision, current engine boundaries, UI direction, knowledge-network philosophy, development requirements, and known-good verification baseline.

## Current Phase

Phase 0 / 0.5 / 0.6 are complete. They built the foundation:

- Python backend skeleton.
- Minimal FastAPI app.
- Pydantic domain models.
- Rule documents for scoring, diagnosis, rollback/forward, and question generation.
- A sample ODE knowledge graph.
- Rule-based diagnosis, rollback, and forward decision contracts.
- Golden cases and executable eval checks for the ODE sample chapter.

Phase 1 is complete. It added the default `CompositeScoringEngine` path with manual override, rubric scoring, lightweight math validation, weak rule signals, detailed scorer audit output, and an inactive LLM stub.

Phase 1.1 is scoring-boundary hardening. It adds red-team tests and fixes for keyword-only answers, rubric required/optional behavior, arbitrary-constant handling, initial-value answer checks, answer aliases, and rule-only forward-safety.

Phase 2 is complete. It strengthens diagnosis with root-cause analysis, primary/secondary/derived error roles, scorer evidence tracing, learner-facing explanations, recommended training actions, and separate diagnosis golden evals.

Phase 2.1 is complete. It adds diagnosis red-team hardening for mixed causes, rubric/math-validator conflicts, optional-only and rule-only weak evidence, condition-miss gates, and Chinese coach-style learner explanations.

Phase 2.2-lite is complete. It hardens the movement contract between rollback, forward, diagnosis recommendations, and next-action hints before any Phase 3 API is exposed.

Phase 3.1 is complete. It adds a minimal internal/dev API and a `LearningOrchestrator` that safely exposes the existing scoring, diagnosis, rollback, forward, and next-action outputs without changing engine logic.

Phase 3.2 is complete. It adds real FastAPI TestClient HTTP red-team tests for API response shape, debug gating, override rejection, malformed requests, and movement consistency.

Phase 3.3 is complete. It freezes the Phase 3 contract with a freeze report, dependency snapshot, final verification record, and explicit boundaries for future phases.

Phase 4.0-lite is complete. It adds a server-side YAML question catalog and a learner-safe public API under `/api/learner/v1`. Learner clients submit only `question_id`, `user_answer`, optional response steps, and optional self-explanation; trusted answer keys, rubrics, solution outlines, and validator config are loaded only from the server catalog.

Phase 4.0.1 is complete. It freezes the Phase 4.0-lite contract, adds a freeze report, and prevents catalog `validator_config` from overriding reserved domain metadata, override, debug, trace, or raw movement keys.

Phase 4.1 is complete. It adds `APP_PROFILE` route gating and OpenAPI separation for learner, internal, and mixed deployment profiles without changing endpoint behavior or engine logic.

Phase 4.1.1 is complete. It freezes the profile-gating contract and records the final profile boundary audit.

Phase 4.2 is complete. It adds server-side catalog validation hardening through a lightweight `CatalogValidator` without changing API behavior or engine logic.

Phase 4.2.1 is complete. It freezes the catalog validation contract and records the final validation boundary audit.

Phase 4.3 is complete. It adds an authoring/import workflow skeleton with authoring-only models, validation reports, deterministic content-hash generation for publish candidates, and a human review gate. It does not write the formal catalog, add endpoints, add a database, add UI, add auth, add LLM integration, or change scoring/diagnosis/movement behavior.

Phase 4.3.1 is complete. It freezes the authoring/import workflow skeleton and records the final dry-run, draft isolation, human review gate, content-hash, source metadata, and known-limit audit.

Phase 4.4 is complete. It adds a minimal authoring-side import CLI and dry-run batch workflow with `validate-draft`, `validate-batch`, and `build-candidate-dry-run`. The CLI only reads authoring drafts, emits reports/previews, and never writes the formal catalog or registers learner API data.

Phase 4.4.1 is complete. It freezes the CLI dry-run boundary, including stdout JSON, path safety, strict/non-strict batch behavior, human review gate, source/copyright isolation, and learner API isolation.

Phase 4.5 P0 is complete. It adds a minimal local trainer CLI over the learner-safe API for listing public questions, showing a public question, submitting a learner answer, and appending a lightweight local JSONL session log. It does not add endpoints, database persistence, frontend UI, next-question selection, mastery/review behavior, formal catalog writes, or new engine logic.

Phase 4.5.1 is complete. It freezes the Local Trainer boundary, including command contract, stdout JSON, debug boundary, session log contract, path-safety contract, trusted-field denylist, and unchanged API/engine/catalog boundaries.

Phase 4.6 trial execution is complete. It verified that the frozen Local Trainer can run `list` / `show` / `submit`, generate JSONL session logs, and avoid trusted field leaks. The main issue found was learner-facing output clarity.

Phase 4.7 P0 is complete. It adds deterministic Local Trainer coach-output projection fields such as `coach_summary`, `status_label`, `progression_advice`, `evidence_gaps`, `friendly_score_summary`, and `next_step_plan`. It does not change engines, APIs, learner projector behavior, catalog, or real decisions.

Phase 4.7.1 is complete. It freezes the coach-output boundary, records the final audit checklist, and confirms that Phase 4.7 P0 remains a deterministic Local Trainer projection layer rather than a new decision engine.

Phase 4.7.2 audit is complete. It confirmed that `response_steps` and `self_explanation` are transported correctly, but current scorers do not consume those fields.

Phase 4.7.3 is complete. It adds display-only response-evidence integration for Local Trainer coach output through `response_evidence_present` and `unscored_dimensions`, so unscored dimensions are not mislabeled as learner omissions when steps/explanation were submitted. It does not change scoring, diagnosis, rollback, forward, API behavior, catalog, or eval cases.

Phase 4.8 is complete. It adds 8 authoring-only ODE catalog expansion drafts, one authoring batch manifest, validation reports, and dry-run candidate previews under the authoring workspace only. It does not modify the formal catalog, manifest, formal question YAML, engines, APIs, Local Trainer, coach output, or golden evals.

Phase 4.8.1 is complete. It freezes the authoring draft boundary and confirms that the Phase 4.8 candidates remain authoring-only, dry-run previews are not published questions, content hashes do not imply formal publish, the learner API still exposes only `ode-sep-001`, and no candidate selection or formal publish was performed.

Phase 4.8.2 is complete. It defines the human review and candidate selection plan for the 8 authoring-only ODE candidates, including a weighted review rubric, hard-fail rules, candidate review template, selection target of 3-5 candidates, and Phase 4.8.3 execution guidance. It does not perform actual candidate selection, formal publish, catalog writes, code changes, scoring integration, or feature expansion.

Phase 4.8.3A is complete. It exports a trusted-only human review packet for the 8 authoring-only ODE candidates, including public fields, trusted answers, rubrics, validator config, source metadata, validation report paths, dry-run preview paths, content hashes, and blank review templates. It does not perform scoring, candidate recommendation, candidate selection, formal publish, catalog writes, code changes, scoring integration, or feature expansion.

Phase 4.8.3B is complete. It records human reviewer hard-fail and 100-point review results for the 8 authoring-only ODE candidates, including per-candidate review records and a human reviewer recommendation summary. It does not modify candidates, publish, import, write formal catalog files, change code, or perform scoring integration.

Phase 4.8.4 is complete. It plans how the human-review-recommended Top 3 candidates should move toward a later publish workflow, including required authoring revisions, rubric and alias review, validation/dry-run flow, learner-safe boundaries, and go/no-go criteria. It does not modify drafts, publish, import, write formal catalog files, change code, or perform scoring integration.

Phase 4.8.5 is complete. It revises only the Top 3 authoring-only drafts, generates Phase 4.8.5 validation reports and dry-run previews, and confirms the formal catalog and learner API remain unchanged. It does not publish, import, modify formal catalog files or manifest, change code, add endpoints, or perform scoring integration.

Knowledge Network Challenge MVP is implemented. It treats existing `KnowledgeNode` entries as MacroNodes / BigNodes, adds independent MicroNodes and MacroChallenge tasks in `backend/challenge_data`, and stores local challenge progress in JSON. The original CLI-only `ode_mvp` slice is still present for regression tests.

Minimal Browser Challenge Trainer is implemented for local use. It adds a thin `/api/challenge/v1` wrapper around the existing `ChallengeEngine`, mounts a static trainer at `/trainer`, and adds a three-MacroNode ODE runtime slice under `backend/challenge_data/ode_network_mvp`. It does not write the formal catalog, add a database, change scoring/diagnosis/movement engines, or expose challenge questions through the learner API.

Logic Knowledge Graph slice is implemented for `ode_network_mvp`. It adds non-trainable guide nodes, a hidden ability layer in `logic_graph.yaml`, cue-based ability evidence states, and a `LogicEvidenceEngine` that maps existing scoring/diagnosis evidence to precise hidden abilities and learner-safe repair focus. This does not become a new decision engine: scoring, diagnosis, rollback, and forward ownership remain unchanged.

Ultimate Knowledge Graph / Diagnosis Core P1 is implemented on the current ODE network slice. It adds hidden ability roles, richer typed-edge semantics, a `KnowledgeGraphQualityValidator`, hidden-logic contradiction signals inside `DiagnosisTrace`, surface-keyword-only low-confidence handling, partial concept understanding handling, and MacroChallenge repair-target precision from hidden ability evidence. This is an engine-capability upgrade, not a题库 or chapter expansion.

No database, user accounts, real LLM API, complete symbolic ODE validation, or full Mathematics I graph is included.

The frozen `/api/v1` API remains an internal/dev API. The `/api/learner/v1` API is the learner-safe public surface. `APP_PROFILE=mixed` remains the local default; production learner deployments should set `APP_PROFILE=learner`.

## Install

```bash
cd math150-coach
pip install -r requirements.txt
```

If you prefer installing manually:

```bash
pip install fastapi uvicorn pydantic pytest pyyaml
pip install httpx2
```

## Run Tests

```bash
cd math150-coach
pytest
```

## Run Golden Evals

```bash
cd math150-coach
python evals/run_evals.py
```

## Run the Minimal Local Trainer

The local trainer uses the existing learner-safe API in-process. It does not expose trusted catalog fields.

```bash
cd math150-coach/backend
python -m app.training.local_trainer list
python -m app.training.local_trainer show ode-sep-001
python -m app.training.local_trainer submit ode-sep-001 --answer "This is separable; separate variables; dy/y = 2x dx; integrate; ln|y|=x^2+C."
```

Submit appends a lightweight JSONL row under the current directory's `training_sessions/` by default. This is not a database or formal attempt persistence.

## Run the Local Knowledge Challenge MVP

The challenge MVP is local-only. It uses independent challenge YAML under `backend/challenge_data/ode_mvp`, not the formal learner catalog.

```bash
cd math150-coach/backend
python -m app.training.local_trainer challenge-start ode_mvp --session-id ode-run-001
python -m app.training.local_trainer challenge-status --session-id ode-run-001
python -m app.training.local_trainer challenge-submit --session-id ode-run-001 --answer "A separable equation lets variables be separated, with y terms on one side and x terms on the other."
python -m app.training.local_trainer challenge-reset --session-id ode-run-001 --all
```

The MVP graph uses:

```text
MacroNode contains MicroNodes
MicroNodes mastered -> MacroNode available
MacroChallenge pass -> MacroNode mastered
MacroChallenge fail -> root cause maps to one target MicroNode
MicroNode fail -> stay on the same MicroNode
```

## Run the Browser Challenge Trainer

The browser trainer is the easiest entry point for the knowledge-network challenge flow. It uses `ode_network_mvp`, which currently contains three ODE MacroNodes:

- `ode_separable`
- `ode_first_order_linear`
- `ode_homogeneous_first_order`

Start the local app:

```bash
cd math150-coach
uvicorn app.main:app --app-dir backend --reload
```

Then open:

```text
http://127.0.0.1:8000/trainer/
```

The page calls only `/api/challenge/v1/*`. That API is a thin wrapper around `ChallengeEngine`; scoring still comes from `CompositeScoringEngine`, diagnosis still comes from `DiagnosisEngine`, and movement still comes from the existing challenge state transition rules.

## Run the Minimal App

```bash
cd math150-coach
uvicorn app.main:app --app-dir backend --reload
```

Then open:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/api/learner/v1/health
```

`/health` is the legacy minimal health route. `/api/v1/health` is the frozen Phase 3 internal/dev API health route. `/api/learner/v1/health` is the Phase 4.0-lite learner-safe API health route.

`APP_PROFILE` controls which versioned API surface is registered:

- `learner`: only `/api/learner/v1/*`;
- `internal`: only `/api/v1/*`;
- `mixed`: both surfaces, local default.

Root `/health` is retained in every profile as a minimal deployment health check and does not list internal or learner route capabilities.

## Implemented Boundaries

Implemented:

- Stable enum strings for YAML, API, and tests.
- ScoreVector with per-dimension score, evidence, notes, optional missing dimensions, and an overall score helper.
- ErrorVector with weighted multi-error entries.
- DiagnosisResult with a full explanation chain.
- NodeAction with rollback, forward, review, node-status, and mastery update placeholders.
- ODE sample nodes and golden cases.
- Phase 1 CompositeScoringEngine with manual override, rubric, lightweight math validation, weak rule signals, and inactive LLM stub.
- Phase 1.1 red-team scoring tests for rule-only, rubric-missing, constant, initial-value, alias, and false-pass boundaries.
- Phase 2 DiagnosisEngine detailed path with root cause, error chain, evidence sources, diagnosis trace, and recommended actions.
- Phase 2.1 diagnosis red-team tests, 25 diagnosis golden cases, and Chinese learner explanations.
- Phase 2.2-lite movement red-team tests, movement golden cases, and clear RollbackEngine / ForwardEngine ownership boundaries.
- Phase 3.1 internal/dev API routes for health, nodes, score evaluation, diagnosis, next action, and attempt submission.
- Public API request validation that recursively rejects override/scenario injection fields.
- Learner/debug/internal response layering.
- Phase 3.2 real HTTP API red-team coverage with FastAPI TestClient.
- Phase 3.3 freeze report and dependency snapshot.
- Separate scoring, diagnosis, and movement golden evals.
- Phase 4.0-lite YAML question catalog with manifest, public presentation, and trusted scoring layers.
- Phase 4.0-lite learner-safe public routes for health, question lookup, node question listing, and attempt submission.
- Server-side trusted Question hydration before calling `LearningOrchestrator`.
- Recursive learner request rejection for answer keys, rubrics, solution outlines, validator config, debug fields, scenarios, and overrides.
- Learner-safe response projection with no answer key, rubric, solution outline, scorer trace, diagnosis trace, or raw movement level leakage.
- Phase 4.0.1 freeze report and catalog `validator_config` reserved-key protection.
- Phase 4.1 `APP_PROFILE` route gating and profile-specific OpenAPI separation.
- Phase 4.2 catalog validation hardening for identity, public/trusted layering, rubric, validator config, dimension consistency, leak checks, version format, and content-hash format.
- Phase 4.3 authoring/import skeleton with `AuthoringDraft`, `SourceMetadata`, `HumanReviewChecklist`, `CatalogValidationReport`, deterministic authoring-side content hash, and dry-run publish candidate creation.
- Phase 4.4 minimal import CLI with path-safe authoring IO, import manifest parsing, batch reports, dry-run candidate previews, stable exit codes, strict/non-strict batch behavior, and no formal catalog writes.
- Phase 4.5 P0 local trainer CLI with learner-safe list/show/submit commands, stdout JSON, local JSONL session logs, session path safety, and trusted-field denylist checks.
- Phase 4.5.1 freeze report and Local Trainer boundary audit.
- Phase 4.6 usability trial report for the frozen Local Trainer.
- Phase 4.7 P0 Local Trainer coach-output projection with learner-friendly submit fields and raw scorer-name cleanup.
- Phase 4.7.1 freeze report and coach-output boundary audit.
- Phase 4.7.2 response evidence integration audit.
- Phase 4.7.3 display-only response evidence fields for Local Trainer output and session logs.
- Phase 4.8 authoring-only minimal ODE catalog expansion drafts, validation reports, and dry-run previews.
- Phase 4.8.1 freeze report and authoring draft boundary audit.
- Phase 4.8.2 human review and candidate selection plan.
- Phase 4.8.3A trusted-only human review packet export.
- Phase 4.8.3B human reviewer review records and recommendation summary.
- Phase 4.8.4 formal publish planning for the human-review-recommended Top 3 candidates.
- Phase 4.8.5 authoring-only revisions for the human-review-recommended Top 3 candidates, with validation reports and dry-run previews.
- Local Knowledge Network Challenge MVP with one ODE MacroNode slice, six MicroNode types, one MacroChallenge, local JSON progress, deterministic task selection, and Local Trainer challenge commands.
- Minimal Browser Challenge Trainer with `/trainer`, `/api/challenge/v1`, and a three-MacroNode ODE challenge slice in `backend/challenge_data/ode_network_mvp`.
- Ultimate graph/diagnosis core P1 with logic graph quality validation, hidden ability roles, hidden-logic contradiction evidence, and precise MacroChallenge repair targets.

Not implemented yet:

- Persistent database.
- User accounts.
- Real LLM scoring.
- Full symbolic math validation.
- Full mastery accumulation algorithm.
- Full Mathematics I knowledge graph.
- Production-grade frontend experience.
- Persistent catalog authoring or catalog management UI.
- Strong runtime content-hash verification.
- Formal catalog import/write workflow.
- Formal catalog publish/export CLI.
- Full local trainer history browser.
- Next-question recommendation.
- Full knowledge-network graph beyond the current ODE first-order slice.
- Automatic chapter knowledge-point extraction from unstructured uploads.
- Database-backed challenge progress.

## Next Phase

Phase 3 is frozen. Phase 4.8 authoring-only catalog expansion is complete and frozen by Phase 4.8.1. Phase 4.8.2 is complete as a human review and candidate selection plan. Phase 4.8.3A is complete as a trusted-only review packet export. Phase 4.8.3B is complete as human review record export. Phase 4.8.4 is complete as formal publish planning only. Phase 4.8.5 is complete as authoring-only revision of the Top 3 candidates.

```text
Phase 4.8.5.1 Authoring Revision Boundary Freeze
```

The recommended next step is a freeze/audit of the Phase 4.8.5 authoring-only revisions. Do not directly perform formal publish. Do not directly edit the formal catalog or manifest. Do not add databases, frontend, user accounts, auth, mastery, review scheduling, attempt persistence, history, next-question recommendation, scoring integration, broad catalog expansion, or LLM integration before explicit approval.
