# Chapter Controlled Publish Implementation Report

Status: Implemented by ChatGPT, pending Codex local verification
Date: 2026-07-03

## 1. Why this was the next step toward the chapter-import final version

The chapter import pipeline had reached:

```text
structured Markdown
→ draft validation
→ human review
→ candidate dry-run
→ runtime-shaped graph
→ content hash
→ candidate quality gate
→ publish plan dry-run
```

The missing next block was a controlled publish executor: the layer that can take a ready publish plan and turn it into real runtime catalog files, while still being gated, auditable, hash-pinned, and safe from accidental writes.

This step implements that controlled execution layer.

## 2. Major block upgraded

This upgrades:

- chapter import;
- controlled publish boundary;
- runtime catalog expansion pipeline;
- publish safety and auditability.

## 3. Files changed

- `backend/app/challenge/chapter_publish_executor.py`
  - New controlled publish executor.
  - Default behavior is non-writing dry run.
  - Write behavior requires explicit `allow_write`, an approval phrase, and matching publish plan hash.
  - Refuses path traversal and absolute paths.
  - Uses create-only semantics and refuses to overwrite existing files.
  - Produces an execution manifest with deterministic hash.

- `backend/app/api/challenge/v1/schemas.py`
  - Adds `ChapterControlledPublishRequest`.

- `backend/app/api/challenge/v1/router.py`
  - Adds `POST /api/challenge/v1/authoring/chapter-draft/controlled-publish`.

- `backend/tests/test_chapter_publish_executor.py`
  - Adds tests for dry-run behavior, write blocking without approval phrase, and successful controlled file creation under `tmp_path`.

## 4. Controlled publish algorithm

The executor performs these gates:

1. Build a publish plan dry-run from the submitted Markdown and review data.
2. Require `publish_plan_grade == ready`.
3. If caller provides `expected_publish_plan_hash`, require it to match.
4. Validate every planned file path:
   - must be relative;
   - must not contain `..`;
   - must stay inside `target_root`;
   - must not already exist.
5. If `allow_write` is false, return `dry_run_ready` and do not create files.
6. If `allow_write` is true, require:
   - `approval_phrase == I_APPROVE_CHAPTER_CONTROLLED_PUBLISH`;
   - `expected_publish_plan_hash == publish_plan_hash`.
7. Create planned files with create-only semantics.
8. If write fails midway, attempt rollback of already-created files.

## 5. Why this matters for the final version

This turns chapter import from an authoring preview system into a real publish-capable pipeline while preserving strict safeguards.

It allows future full Mathematics I expansion to follow a controlled path:

```text
chapter draft
→ validation
→ human review
→ candidate
→ quality gate
→ publish plan
→ controlled publish
→ runtime graph available to trainer
```

This is a real final-version capability, not a placeholder.

## 6. Verification commands for Codex

ChatGPT did not run local commands. Codex should run:

```bash
python -m pytest backend/tests/test_chapter_publish_executor.py -q
python -m pytest backend/tests/test_chapter_publish_plan.py -q
python -m pytest backend/tests/test_chapter_candidate_quality.py -q
python -m pytest backend/tests/test_chapter_candidate_builder.py -q
python -m pytest -q
```

Codex should also manually check the API endpoint:

```text
POST /api/challenge/v1/authoring/chapter-draft/controlled-publish
```

and verify:

- with default `allow_write: false`, it does not write files;
- with `allow_write: true` but missing approval phrase, it blocks;
- with matching plan hash and approval phrase, it writes only planned files;
- it refuses to overwrite existing files.

## 7. Boundaries and risks

This is the first write-capable publish layer. It is intentionally gated and should remain local/dev only until Codex verifies it thoroughly.

Risks for Codex to inspect:

- Whether exposing the write-capable endpoint is acceptable under current app profile.
- Whether target root should be configurable only through environment variables in production.
- Whether file writes should include a separate audit log file in the future.
- Whether rollback behavior should become stronger for multi-file writes.

## 8. Next final-version blocks after this

After Codex verifies controlled publish, the remaining chapter-import final-version blocks are:

1. Published chapter registry / manifest index.
2. Runtime loading of newly published chapters into atlas.
3. Authoring version history and rollback metadata.
4. Cross-chapter dependency validation.
5. UI workflow for draft → review → candidate → quality → publish plan → controlled publish.
