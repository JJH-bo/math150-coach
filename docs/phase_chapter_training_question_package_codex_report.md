# Chapter Training Question Package Codex Report

Status: Implemented by Codex
Date: 2026-07-03

## 1. Why this block matters

The content production system could generate a chapter ability graph and controlled-publish graph assets, but a graph alone cannot enter the Math150 training loop.

The missing runtime asset was:

```text
questions.yaml
```

Without it, the training cabin cannot select questions, score answers, diagnose root causes, repair nodes, or trigger Boss acceptance.

## 2. Implemented block

New deterministic generator:

- `backend/app/challenge/chapter_training_question_builder.py`

It turns a chapter candidate into:

- runtime `questions.yaml`;
- per-question rubric;
- per-question repair target;
- per-question error repair map;
- false-pass risk metadata;
- variant relation metadata;
- mastery criteria states;
- question package quality report.

## 3. Question coverage

The generator creates trainable questions for:

- concept judgement;
- trigger identification;
- method selection;
- condition transformation;
- calculation execution;
- expression standardization;
- confusion compare;
- transfer variant;
- synthesis decomposition;
- Boss acceptance.

Every MicroNode gets at least one `micro_node` question.

Every MacroChallenge / Boss gets at least one `macro_challenge` question.

If CompareGuard, TransferNode, or SynthesisNode assets exist, the generator adds corresponding diagnostic/advisory questions owned by the nearest runtime task owner.

## 4. Publish integration

`build_chapter_publish_plan_dry_run()` now generates the training question package after candidate quality passes.

The publish plan is blocked unless question package quality is exactly `pass`. Warnings do not pass the publish boundary because the runtime registry also requires a pass-grade manifest.

Planned files now include:

```text
backend/challenge_data/<chapter_id>/challenge_graph.yaml
backend/challenge_data/<chapter_id>/logic_graph.yaml
backend/challenge_data/<chapter_id>/questions.yaml
backend/challenge_data/<chapter_id>/publish_manifest.json
```

`publish_manifest.json` records:

- question package schema version;
- question bank content hash;
- question package quality grade;
- question package quality report;
- mastery criteria schema version.

`execute_chapter_controlled_publish()` writes `questions.yaml` through the existing create-only, hash-pinned controlled publish path.

## 5. Runtime integration

The runtime registry can now mark a controlled-published generated chapter as `trainable` immediately after controlled publish, because the publish plan includes complete question coverage.

If `questions.yaml` is removed or incomplete, the registry still blocks start with `content_pending`.

## 6. Intelligent Import Integration

`POST /api/challenge/v1/authoring/chapter-draft/intelligent-generate` now returns a public training question package summary:

- quality pass state;
- question count;
- generated question kinds;
- rubric dimensions;
- mastery states.

Trusted fields such as answers, rubrics, solution outlines, validator config, and evidence sources are still stripped from the public intelligent-generate payload.

## 7. Current limitation

This is deterministic package generation, not a full mathematical authoring brain.

It produces valid, trainable, scoreable, diagnosable skeleton questions from the generated ability graph. The next major block should make the question stems, answer keys, worked processes, and variants more material-specific by extracting formulas, theorem statements, typical examples, and user-provided wrong-answer material.

## 8. Verification

Focused verification:

```bash
python -m pytest backend/tests/test_chapter_training_question_builder.py backend/tests/test_chapter_intelligent_importer.py backend/tests/test_chapter_publish_plan.py backend/tests/test_chapter_publish_executor.py backend/tests/test_chapter_runtime_registry.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Result:

```text
16 passed
```

Full regression verification:

```text
backend/tests: 582 passed, 1 warning
golden evals: scoring 30/30, diagnosis 25/25, movement 12/12
synthetic diagnosis lab: 16/16
```

Strict real-attempt calibration remains release-blocked and is not hidden by this phase:

```text
root=5/8, repair=6/8, exact=4/8, grade=fail
```
