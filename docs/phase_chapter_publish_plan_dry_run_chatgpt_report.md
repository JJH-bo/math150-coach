# Chapter Publish Plan Dry-Run Implementation Report

Status: Implemented by ChatGPT, pending Codex local verification
Date: 2026-07-03

## 1. Why this was the next development step

After candidate dry-run, content hash, and candidate quality gate, the chapter import pipeline still lacked one critical final-version bridge: a publish plan that shows exactly what would be written if a future controlled publish phase is approved.

Without this layer, the system can say a candidate is good, but cannot yet produce a deterministic, inspectable file manifest for the future runtime catalog. That gap blocks safe expansion from one ODE slice toward a full Mathematics I graph.

## 2. Major block upgraded

This upgrades the chapter import / authoring pipeline into a stronger quality-control spine:

```text
structured Markdown
→ draft validation
→ human review
→ candidate dry-run
→ runtime-shaped graph
→ content hash
→ candidate quality gate
→ publish plan dry-run
→ future controlled publish
```

This is still not formal publish. It is the dry-run manifest layer before a separate publish implementation exists.

## 3. Files changed

- `backend/app/challenge/chapter_publish_plan.py`
  - New publish plan dry-run builder.
  - Calls candidate dry-run and candidate quality gate.
  - Blocks when candidate build or candidate quality fails.
  - Produces deterministic planned file list when ready.
  - Produces content hashes for planned files and the full publish plan.
  - Keeps `formal_publish_allowed: false`.

- `backend/app/api/challenge/v1/router.py`
  - Adds `POST /api/challenge/v1/authoring/chapter-draft/publish-plan-dry-run`.

- `backend/tests/test_chapter_publish_plan.py`
  - Adds tests for ready publish plan dry-run, quality-blocked publish plan, and API response.

## 4. Algorithm implemented

The publish plan builder does this:

1. Run `build_chapter_candidate_dry_run`.
2. Inspect candidate build status, runtime validation, and candidate quality.
3. If anything fails or candidate quality is not `pass`, return a blocked publish plan with reasons.
4. If ready, build planned file manifests:
   - `backend/challenge_data/<chapter_id>/challenge_graph.yaml`
   - `backend/challenge_data/<chapter_id>/logic_graph.yaml`
   - `backend/challenge_data/<chapter_id>/publish_manifest.json`
5. Compute deterministic hashes for each planned file.
6. Compute a deterministic publish plan hash.
7. Return `dry_run_only: true` and `formal_publish_allowed: false`.

## 5. Why this matters for the final version

This makes future full Mathematics I expansion safer. A chapter will not jump directly from an authored draft into runtime data. It must first produce a deterministic plan that can be reviewed by ChatGPT, Codex, and the user before any controlled publish phase exists.

This directly reduces false maturity: large content expansion cannot hide weak graphs, weak repair mapping, or unsafe candidate content.

## 6. Verification commands for Codex

ChatGPT did not run local commands. Codex should run:

```bash
python -m pytest backend/tests/test_chapter_publish_plan.py -q
python -m pytest backend/tests/test_chapter_candidate_quality.py -q
python -m pytest backend/tests/test_chapter_candidate_builder.py -q
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py -q
python -m pytest -q
```

Codex should also POST to:

```text
/api/challenge/v1/authoring/chapter-draft/publish-plan-dry-run
```

and verify:

- ready candidate returns `publish_plan_grade: ready`;
- weak candidate returns `publish_plan_grade: blocked`;
- planned files are preview-only and not written;
- formal publish remains locked.

## 7. Boundaries preserved

This implementation does not add:

- runtime catalog writes;
- formal publish;
- database;
- auth;
- real LLM;
- learner progress mutation;
- broad Mathematics I content expansion.

## 8. Known risks for Codex to verify

- Whether candidate quality is too strict for early sparse chapters.
- Whether `yaml.safe_dump` output matches the project's expected YAML style.
- Whether `deterministic_content_hash` prefix format remains consistent across tests.
- Whether the new route imports cleanly after recent Codex modifications.
