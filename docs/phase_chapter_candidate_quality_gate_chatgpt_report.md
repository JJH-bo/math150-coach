# Chapter Candidate Quality Gate Implementation Report

Status: Implemented by ChatGPT, pending Codex local verification
Date: 2026-07-03

## 1. Why this was the next block

The final Math150 Coach still lacks several major blocks:

- chapter import must evolve from draft preview into a safe controlled publish pipeline;
- logic knowledge network must prove runtime quality, not only parse YAML/Markdown;
- diagnosis must be calibrated on real learner attempts;
- repair, transfer, synthesis, and review scheduling need explicit routing logic;
- the cosmic map must visualize real learning state instead of only looking impressive.

Given the current repository state, the highest-leverage next move is not a new UI or broad content expansion. It is strengthening chapter import into a quality-control spine.

The previous step created candidate dry-run and content hashing. This step adds a candidate quality gate so generated candidates are scored and blocked before any future publish path.

## 2. Major block upgraded

This upgrades:

- chapter import;
- candidate build;
- runtime graph quality control;
- future controlled publish boundary.

## 3. Files changed

- `backend/app/challenge/chapter_candidate_quality.py`
  - New candidate quality evaluator.
  - Scores candidate content across seven dimensions.
  - Produces deterministic pass/warn/fail grade and blocking codes.
  - Keeps formal publish locked.

- `backend/app/challenge/chapter_candidate_builder.py`
  - Integrates `candidate_quality` into candidate dry-run responses.
  - Blocked candidates now also return a quality failure explanation.

- `backend/tests/test_chapter_candidate_quality.py`
  - Adds unit tests for strong candidate pass, invalid repair target failure, and trusted-field leak failure.

## 4. Quality algorithm

The quality gate scores seven dimensions:

1. `runtime_shape` — candidate must validate against runtime graph shape.
2. `visible_topology` — MacroNodes, MicroNodes, Boss coverage, and contains map must be coherent.
3. `repair_system` — root causes must map to existing MicroNodes and avoid repair overfunneling.
4. `logic_depth` — candidate should include hidden ability support and semantic logic connections.
5. `transfer_synthesis` — chapter should expose transfer and synthesis routes, not only isolated nodes.
6. `hash_integrity` — candidate hash must be a deterministic sha256 digest with or without `sha256:` prefix.
7. `learner_safety` — candidate preview must not leak trusted/internal answer fields and must keep formal publish locked.

## 5. Gate behavior

The gate returns:

- `grade`: `pass`, `warn`, or `fail`;
- `score` and `max_score`;
- per-dimension issues;
- `candidate_publish_gate.candidate_quality_passed`;
- `candidate_publish_gate.formal_publish_allowed: false`;
- `blocking_codes` for hard failures.

Important: even when candidate quality passes, formal publish remains locked. This is a candidate-quality gate, not a publish implementation.

## 6. Verification commands for Codex

ChatGPT did not run local commands. Codex should run:

```bash
python -m pytest backend/tests/test_chapter_candidate_quality.py -q
python -m pytest backend/tests/test_chapter_candidate_builder.py -q
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py -q
python -m pytest -q
```

Codex should also POST to:

```text
/api/challenge/v1/authoring/chapter-draft/candidate-dry-run
/api/challenge/v1/authoring/chapter-draft/candidate-build-dry-run
```

and verify that responses include `candidate_quality`.

## 7. Boundaries preserved

This step does not add:

- database;
- auth;
- real LLM;
- formal publish;
- runtime catalog writes;
- learner progress mutation;
- broad Mathematics I content expansion.

## 8. Known integration risks

- The existing candidate builder was modified by Codex after ChatGPT's first implementation, including `sha256:` hash prefix and trusted-field filtering. This quality gate was adjusted to accept `sha256:` prefixes.
- Codex should verify import order, route startup, and whether existing candidate dry-run tests still pass.
- If the quality grade is `warn` for sparse authoring samples, that is acceptable evidence: the gate is identifying that the candidate is not yet full-strength for final-system publishing.
