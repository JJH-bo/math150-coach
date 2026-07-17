# Chapter Feedback Optimization Dry-Run Report

Status: Implemented by Codex
Date: 2026-07-04

## 1. Why this block was necessary

The content production pipeline could already generate, quality-check, correct, and publish-preview a chapter package. The remaining final-version gap was feedback optimization: once learners actually train on the package, the system must detect where the generated content is not working.

This phase adds the first authoring-side feedback analysis layer. It does not mutate the chapter package. It converts training attempts into revision signals and regeneration targets.

## 2. Major block upgraded

This upgrades the chapter package lifecycle:

```text
candidate package
-> question package
-> live training attempts
-> feedback optimization dry-run
-> correction dry-run
-> regenerated package
-> publish plan dry-run
```

## 3. Files changed

- `backend/app/challenge/chapter_feedback_optimizer.py`
  - New feedback optimization analyzer.
  - Aggregates attempt records by question.
  - Loads real safe JSONL session logs from a configured session root.
  - Detects false-pass excess, pass-rate anomalies, diagnosis instability, rubric evidence gaps, CompareGuard weakness, transfer weakness, Boss feedback gaps, hidden-ability support gaps, and ineffective repair paths.
  - Produces regeneration targets and correction operation templates.

- `backend/app/api/challenge/v1/schemas.py`
  - Adds `ChapterFeedbackOptimizationDryRunRequest`.
  - Adds `ChapterFeedbackOptimizationFromSessionsDryRunRequest`.

- `backend/app/api/challenge/v1/router.py`
  - Adds `POST /api/challenge/v1/authoring/chapter-package/feedback-optimization-dry-run`.
  - Adds `POST /api/challenge/v1/authoring/chapter-package/feedback-optimization-from-sessions-dry-run`.

- `backend/tests/test_chapter_feedback_optimizer.py`
  - Verifies feedback signals from synthetic training attempts over a generated chapter package.
  - Verifies real session log ingestion through `append_attempt` JSONL files.
  - Verifies API dry-run behavior.

- `docs/chapter_import_and_atlas_spec.md`
  - Documents feedback optimization inputs, outputs, and boundaries.

- `docs/explan.md`
  - Updates the project state and remaining gaps.

- `docs/ai_coordination/DISCUSSION_LOG.md`
  - Records the new Codex block for ChatGPT/Codex coordination.

## 4. Feedback signals

The analyzer can currently detect:

- `question_pass_rate_anomaly`;
- `false_pass_excess`;
- `diagnosis_instability`;
- `rubric_evidence_insufficient`;
- `compare_guard_not_blocking_confusion`;
- `migration_variant_weak`;
- `boss_feedback_gap`;
- `repair_path_ineffective`;
- `hidden_ability_unsupported`.

Each signal includes:

- severity;
- question id;
- node id;
- question kind;
- attempt count;
- observed pass states;
- observed root causes;
- affected assets.

## 5. Boundaries preserved

This implementation does not add:

- automatic package mutation;
- database-backed feedback history;
- LLM-based revision writing;
- frontend review UI.

It is a dry-run authoring layer. Corrections still go through the correction regeneration endpoint, and runtime writes still go through publish plan and controlled publish.

The session-log endpoint does not accept an arbitrary filesystem path from request JSON. It reads from the existing configured challenge session root, using `CHALLENGE_SESSION_ROOT` or the default local training session directory.

## 6. Known next steps

The next high-value blocks are:

1. Convert feedback signals into concrete correction drafts for questions, rubrics, and repair maps.
2. Add front-end review UI for feedback signals and regeneration plans.
3. Persist feedback snapshots with authoring version history.
4. Use feedback optimizer output to prioritize real-attempt calibration fixes.
5. Connect real-attempt lab mismatch reports as a first-class feedback source.

## 7. Verification

Local verification completed by Codex:

- Focused feedback optimizer tests: `4 passed`.
- Related authoring tests: `12 passed`.
- Full backend tests: `591 passed`.
- Golden evals: scoring `30/30`, diagnosis `25/25`, movement `12/12`.
- Synthetic diagnosis lab: `16/16`.
- Strict real-attempt lab remains release-blocked: root `5/8`, repair `6/8`, exact `4/8`, grade `fail`.
