# Chapter Candidate Dry-Run Implementation Report

Status: Implemented by ChatGPT, pending Codex local verification
Date: 2026-07-03

## 1. Major block upgraded

This implementation upgrades the chapter import and authoring pipeline.

The previous pipeline could validate a structured chapter draft and record human review. This push adds the next major gate: a deterministic candidate dry-run builder with runtime-shaped challenge graph output and stable content hashing.

This is not formal publish. It is the safe candidate-preview layer before any future controlled publish workflow.

## 2. Files changed

- `backend/app/challenge/chapter_candidate_builder.py`
  - New core implementation.
  - Builds candidate dry-run payloads after validation and human review.
  - Produces runtime-shaped `ChallengeGraph` candidate content.
  - Produces logic graph candidate content.
  - Computes deterministic sha256 content hash from canonical candidate content.
  - Excludes reviewer identity, notes, timestamps, and UI state from the hash basis.
  - Blocks candidate creation when validation or human review is incomplete.

- `backend/app/api/challenge/v1/schemas.py`
  - Adds `ChapterDraftCandidateDryRunRequest`.

- `backend/app/api/challenge/v1/router.py`
  - Adds `POST /api/challenge/v1/authoring/chapter-draft/candidate-dry-run`.

- `backend/tests/test_chapter_candidate_builder.py`
  - Adds candidate dry-run tests for successful build, incomplete review blocking, hash stability, and API behavior.

## 3. Behavior implemented

The candidate builder now supports:

- validation gate;
- human review gate;
- runtime candidate graph construction;
- deterministic content hashing;
- candidate blocking when review is incomplete;
- formal publish lock;
- API response for candidate preview.

The response always includes:

- `dry_run_only: true`;
- `formal_publish_allowed: false`;
- candidate gate status;
- content schema version;
- content hash when allowed;
- runtime validation report.

## 4. Core algorithm

### Candidate gate

A candidate is allowed only when:

1. draft validation has zero blocking errors;
2. human review status is `approved_for_candidate`;
3. all required human review checklist items are complete.

Otherwise the response is blocked, has no candidate payload, and has no content hash.

### Runtime-shaped candidate build

The builder converts structured draft content into a runtime-shaped candidate:

- MacroNodes;
- MicroNodes with default scoring dimensions;
- MacroChallenges with target dimensions;
- contains map;
- unlock edges;
- atom nodes from HiddenAbilities;
- compare nodes from CompareGuards;
- guide nodes from TransferNodes and SynthesisNodes;
- typed edges mapped from authoring semantic edges;
- error-to-micro repair mapping.

The candidate is validated through `ChallengeGraph.model_validate` before being accepted.

### Content hash

The hash is:

```text
sha256:<64 lowercase hex chars>
```

The digest is computed from:

```text
json.dumps(canonical_candidate, sort_keys=True, separators=(",", ":"))
```

The canonical candidate recursively sorts dictionary keys and sorts ID-based lists by `id`. The hash deliberately excludes reviewer identity, review notes, timestamps, UI state, and trusted/internal fields such as `evidence_sources`.

## 5. Verification commands for Codex

ChatGPT did not run local commands. Codex should run:

```bash
python -m pytest backend/tests/test_chapter_candidate_builder.py -q
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py -q
python -m pytest -q
```

Codex should also manually POST to:

```text
/api/challenge/v1/authoring/chapter-draft/candidate-dry-run
```

and verify that:

- valid reviewed drafts produce a stable content hash;
- incomplete review blocks candidate creation;
- `formal_publish_allowed` remains false;
- runtime validation passes for valid candidate content.

## 6. Boundaries preserved

This implementation does not add:

- database;
- auth;
- real LLM;
- formal publish;
- learner progress mutation;
- runtime catalog writes;
- broad Mathematics I content expansion.

## 7. Known risk

This was written through GitHub without local execution. Codex should check:

- import order and typing;
- whether `ChallengeGraph.model_validate` accepts string keys for `error_to_micro_mapping` as intended;
- whether the endpoint import passes app startup;
- whether the router update and schema update are compatible with existing tests.

If local tests fail, Codex should fix integration and preserve the candidate dry-run algorithm and boundaries.

## 8. Codex verification and hardening addendum

Codex accepted this as a valid ChatGPT upstream implementation because it includes a major authoring-pipeline upgrade, concrete algorithm code, API wiring, tests, and a report.

Codex then hardened the implementation:

- content hashes now use the project-wide `sha256:<64 lowercase hex chars>` format;
- candidate payloads recursively remove trusted/internal fields before hashing or returning the candidate preview;
- `/authoring/chapter-draft/candidate-build-dry-run` is available as an alias for the original `/candidate-dry-run` endpoint;
- tests now assert the hash format, trusted-field boundary, and both endpoint paths.
