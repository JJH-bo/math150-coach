# Chapter Runtime Registry Codex Report

Status: Implemented by Codex
Date: 2026-07-03

## 1. Why this block matters

The chapter import pipeline could already build a candidate, quality-check it, create a publish plan, and run a controlled local/dev publish. However, the published output could still be graph-only:

```text
challenge_graph.yaml
logic_graph.yaml
publish_manifest.json
```

That is not yet a runnable Math150 training package because the training cabin also requires `questions.yaml` with full MicroNode and Boss question coverage.

This phase adds a runtime registry boundary so the system does not confuse "chapter files exist" with "chapter package can be trained".

## 2. Implemented block

New runtime registry:

- `backend/app/challenge/chapter_registry.py`

The registry scans `backend/challenge_data` and classifies each chapter as:

- `trainable`: valid graph, valid question bank, complete question coverage;
- `content_pending`: graph exists but questions or coverage are incomplete;
- `invalid`: graph cannot be loaded.

The runtime contract requires:

- valid `challenge_graph.yaml`;
- valid `publish_manifest.json` with `candidate_quality_grade: pass` when a publish manifest exists;
- valid `questions.yaml`;
- question bank `chapter_id` matches graph `chapter_id`;
- every `MicroNode` has at least one `micro_node` question;
- every `MacroChallenge` / Boss has at least one `macro_challenge` question;
- question `owner_id` and `node_id` point to known runtime graph nodes.

## 3. Runtime integration

Atlas now reads this registry before exposing chapter regions.

For each region, Atlas includes:

- `runtime.can_start`;
- `runtime.runtime_status`;
- `runtime.source`;
- `runtime.files`;
- `runtime.blocking_reasons`.

If `can_start` is false:

- Atlas marks the region as non-available;
- `detail.start_endpoint` is `null`;
- the frontend disables the region button;
- direct `start/status/submit/reset` calls are blocked by `ChallengeEngine`.

This prevents a controlled-publish graph-only output from entering the training cabin prematurely.

## 4. API

New read-only endpoint:

```text
GET /api/challenge/v1/chapters/registry
```

It exposes runtime readiness only. It does not expose trusted fields, answer keys, rubrics, or full question data.

## 5. Current limitation

Superseded addendum, 2026-07-03:

The next block described here has now been implemented by `chapter_training_question_builder.py`. Controlled publish can generate `questions.yaml`, and the runtime registry can start generated packages only when graph, manifest, question bank, and coverage all pass.

The remaining final-version limitation is deeper material-specific authoring: generated stems, answer keys, examples, variants, and repair evidence should be shaped by formulas, theorem wording, worked examples, and uploaded wrong-answer material rather than only the generated ability graph.

## 6. Verification

Focused verification:

```bash
python -m pytest backend/tests/test_chapter_runtime_registry.py backend/tests/test_ultimate_atlas_and_chapter_import.py backend/tests/test_ultimate_frontend_contract.py backend/tests/test_chapter_publish_executor.py -q --basetemp .pytest_tmp
```

Result:

```text
32 passed
```

The first run failed only because the sandbox denied pytest's default temp directory under `AppData\\Local\\Temp`. Re-running with `--basetemp .pytest_tmp` passed.
