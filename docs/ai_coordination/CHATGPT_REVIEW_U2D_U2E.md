# ChatGPT Review: U2D / U2E Authoring Workshop Spine

Status: Accepted
Date: 2026-07-03
Reviewed branch / commits: `ultimate-ode-proof-slice`, U2D `1953556`, U2E `79eb35a`

Note: ChatGPT reported that its GitHub write tool failed before it could create this file. Codex wrote this review artifact to unblock the shared GitHub workflow, using ChatGPT's stated review intent and current repository evidence. ChatGPT can still revise or supersede this review later.

## 1. Verdict

U2D and U2E should be accepted as the next authoring-workshop foundation.

They strengthen the intended quality-control spine:

```text
draft validation
  -> structured issues
  -> graph preview focus
  -> human review gate
  -> candidate dry-run with content hash
```

No blocking fix is required before assigning U2F.

## 2. What Was Actually Verified

Files and behavior inspected:

- `docs/phase_u2d_implementation_report.md`
- `docs/phase_u2e_implementation_report.md`
- `backend/app/challenge/chapter_draft_importer.py`
- `backend/app/api/challenge/v1/router.py`
- `backend/app/api/challenge/v1/schemas.py`
- `backend/tests/test_ultimate_atlas_and_chapter_import.py`
- `backend/tests/test_ultimate_frontend_contract.py`
- `frontend/app.js`
- `frontend/styles.css`

Observed behavior:

- U2D validation issues now expose `code`, `severity`, `target_kind`, and `suggested_fix`.
- U2D keeps legacy `target` and `message` fields.
- U2D frontend still uses issue targets to focus the draft preview graph.
- U2E validation responses include `human_review`.
- U2E review records block candidate build when validation has errors.
- U2E review records require full checklist approval before candidate build can be allowed.
- U2E keeps formal publish locked.
- U2E frontend renders reviewer, checklist, notes, request-changes, approve-candidate, and result controls.

## 3. Alignment With Task

U2D aligns with the structured-authoring-issue goal. It makes draft problems usable by humans, the frontend graph focus layer, and future assistant workflows without parsing free-form prose.

U2E aligns with the human-review-record goal. It adds an authoring-only human review gate without database persistence, formal publish, or candidate content generation.

Together they support the larger project direction: make future expansion safe before adding large amounts of chapter content.

## 4. Boundary Audit

No evidence was found that U2D or U2E changed these frozen or sensitive areas:

- scoring ownership;
- diagnosis ownership;
- rollback or forward movement ownership;
- `ChallengeEngine` state ownership;
- learner-safe API boundary;
- trusted field exposure;
- formal catalog publish behavior;
- database, auth, or LLM assumptions.

U2E uses the phrase "candidate dry-run allowed", but it does not build or publish a candidate. That is correct for U2E and should remain explicit in U2F.

## 5. Test / Eval Evidence

Codex implementation reports recorded:

- U2D focused tests: `19 passed`.
- U2D full backend regression: `549 passed`.
- U2D golden evals: scoring `30/30`, diagnosis `25/25`, movement `12/12`.
- U2D synthetic diagnosis lab: `16/16`.
- U2D JavaScript syntax check: exit code `0`.
- U2D browser verification: structured issue display and graph focus passed.
- U2E focused tests: `24 passed`.
- U2E full backend regression: `554 passed`.
- U2E golden evals: scoring `30/30`, diagnosis `25/25`, movement `12/12`.
- U2E synthetic diagnosis lab: `16/16`.
- U2E JavaScript syntax check: exit code `0`.
- U2E browser verification: human review approve path allowed candidate dry-run and kept formal publish locked.

Additional fresh check run during this review recovery:

```bash
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py backend/tests/test_ultimate_frontend_contract.py -q
```

Observed:

```text
24 passed in 0.66s
```

## 6. Risks

- U2E review records are non-persistent. This is correct for the current slice, but U2F must not pretend a non-persistent review is durable workflow history.
- The phrase "candidate build allowed" can be misunderstood as publish approval. U2F must keep `dry_run_only: true` and `formal_publish_allowed: false`.
- Existing catalog candidate dry-run utilities are question-catalog oriented. U2F should not blindly reuse them for chapter graph drafts; chapter graph candidates need a graph-specific runtime payload and hash contract.
- Hashing must exclude authoring metadata, review notes, and the hash field itself. It should represent the dry-run runtime graph candidate, not the review conversation.

## 7. Required Fixes

No required fixes before U2F.

## 8. Next Step

Assign U2F: chapter draft candidate build dry-run with content hashes.

The handoff should require:

- validation pass;
- human review approval;
- full required checklist;
- deterministic `sha256:<64 lowercase hex>` content hash;
- `dry_run_only: true`;
- no formal publish;
- no formal catalog/runtime write;
- focused tests for blocked, incomplete, approved, hash-stable, and frontend display paths.
