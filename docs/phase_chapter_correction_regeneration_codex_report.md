# Chapter Correction Regeneration Dry-Run Report

Status: Implemented by Codex
Date: 2026-07-04

## 1. Why this block was necessary

ChatGPT's accepted chapter-import chain already created:

- candidate dry-run;
- candidate quality gate;
- publish plan dry-run;
- controlled publish executor;
- deterministic question package generation.

The next missing final-version block was not another publish step. The gap was iteration: after generated material-aware candidates are reviewed by a teacher, user, ChatGPT, or Codex, the system needs a safe way to apply corrections, regenerate affected package assets, and show what changed before any publish plan is built.

## 2. Major block upgraded

This upgrades the chapter authoring pipeline:

```text
material upload
-> intelligent draft
-> candidate package
-> material-aware question package
-> correction dry-run
-> regenerated question package
-> publish plan dry-run
-> controlled publish
```

It is still preview-only. It does not write runtime files.

## 3. Files changed

- `backend/app/challenge/chapter_correction_regeneration.py`
  - New correction dry-run module.
  - Applies allowed correction operations to a candidate package.
  - Recomputes candidate content hash.
  - Reruns runtime validation and candidate quality.
  - Regenerates the training question package.
  - Produces changed paths, changed question ids, affected node ids, and regeneration scope.

- `backend/app/api/challenge/v1/schemas.py`
  - Adds `ChapterCorrectionOperation`.
  - Adds `ChapterCorrectionDryRunRequest`.

- `backend/app/api/challenge/v1/router.py`
  - Adds `POST /api/challenge/v1/authoring/chapter-package/correction-dry-run`.

- `backend/tests/test_chapter_correction_regeneration.py`
  - Verifies material-evidence and MicroNode corrections.
  - Verifies regenerated questions carry corrected material and node title.
  - Verifies the API returns a preview-only payload.

- `docs/chapter_import_and_atlas_spec.md`
  - Documents correction operation shape and response boundaries.

- `docs/explan.md`
  - Updates project status and remaining gaps.

## 4. Supported correction scope

The first implementation supports `replace` operations for:

- chapter fields;
- material evidence;
- MicroNodes;
- MacroNodes;
- MacroChallenges;
- AtomNodes;
- CompareNodes;
- GuideNodes;
- typed edges;
- error repair mappings.

Each dry run returns:

- correction record;
- before and after candidate hashes;
- corrected candidate preview;
- runtime validation;
- candidate quality;
- regenerated question package;
- changed question ids;
- affected node ids;
- regeneration scope.

## 5. Boundaries preserved

This implementation does not add:

- database writes;
- formal publish bypass;
- learner progress mutation;
- front-end diff editor;
- automatic training-feedback proposals;
- real LLM authoring.

Formal publish remains locked. Runtime file creation still belongs to the publish plan and controlled publish chain.

## 6. Known next steps

The next high-value blocks are:

1. Authoring diff UI for candidate, material evidence, and generated questions.
2. Persisted authoring version history and rollback metadata.
3. Training-attempt feedback analysis that proposes targeted corrections.
4. Worked-example parsing and symbolic normalization for formulas and solution chains.
5. Cross-chapter dependency checks before controlled publish.

## 7. Verification

Local verification completed by Codex:

- Focused correction regeneration tests: `2 passed`.
- Related chapter import/material/question/publish-plan tests: `10 passed`.
- Full backend tests: `587 passed`.
- Golden evals: scoring `30/30`, diagnosis `25/25`, movement `12/12`.
- Synthetic diagnosis lab: `16/16`.
- Strict real-attempt lab remains release-blocked: root `5/8`, repair `6/8`, exact `4/8`, grade `fail`.
