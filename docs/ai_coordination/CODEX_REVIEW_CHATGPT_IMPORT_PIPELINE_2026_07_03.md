# Codex Review: ChatGPT Chapter Import Pipeline Push

Status: Accepted with Codex hardening
Date: 2026-07-03
Reviewed remote head: `0e1d69d`

## 1. Hard-Gate Decision

ChatGPT's push satisfies the user's handoff acceptance gate.

Reasons:

- It directly upgrades a major final-version block: chapter import and controlled runtime publish pipeline.
- It includes concrete development results, not only instructions for Codex.
- It implements algorithm code for candidate quality, publish planning, and controlled publish execution.
- It includes tests and implementation reports.

## 2. Accepted Pipeline

The implemented chain is:

```text
structured Markdown
-> draft validation
-> human review
-> candidate dry-run
-> runtime-shaped graph
-> content hash
-> candidate quality gate
-> publish plan dry-run
-> controlled publish executor
```

## 3. Codex Hardening

Codex made two corrections before accepting the result as integrated:

- Candidate quality warnings now force overall `grade: "warn"` instead of allowing a high score to pass.
- HTTP controlled-publish writes are disabled by default and require `CHAPTER_CONTROLLED_PUBLISH_API_WRITES=1`.

Codex also added tests for:

- incomplete core repair mapping becoming `warn`;
- publish plan blocking non-pass quality;
- HTTP controlled publish defaulting to dry-run;
- HTTP write requests being rejected by default.

## 4. Verification

Focused verification:

```bash
python -m pytest backend/tests/test_chapter_publish_executor.py backend/tests/test_chapter_publish_plan.py backend/tests/test_chapter_candidate_quality.py backend/tests/test_chapter_candidate_builder.py backend/tests/test_ultimate_atlas_and_chapter_import.py -q
```

Result:

```text
28 passed
```

Full validation after hardening:

```bash
python -m pytest backend/tests -q
python evals/run_evals.py
python evals/run_synthetic_diagnosis_lab.py
python tools/run_real_attempt_lab.py --json
python tools/run_real_attempt_lab.py --strict
```

Results:

```text
573 backend tests passed
Scoring eval: 30/30 passed
Diagnosis eval: 25/25 passed
Movement eval: 12/12 passed
Synthetic diagnosis lab: 16/16 passed
Real Attempt Lab: root=5/8, repair=6/8, exact=4/8, grade=fail
```

The strict real-attempt lab exits non-zero by design while grade remains `fail`; this confirms the current real-attempt calibration is still blocked from release rather than silently passing.

## 5. Next Judgment

The chapter import pipeline is now functionally publish-capable but should still be treated as local/dev controlled publish until:

- a published chapter registry exists;
- runtime atlas loading of newly published chapters is verified;
- UI workflow exists for draft -> review -> candidate -> quality -> publish plan -> controlled publish;
- audit log and rollback metadata are designed.
