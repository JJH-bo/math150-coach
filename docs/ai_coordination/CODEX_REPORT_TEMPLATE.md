# Codex Report Template

Status: Active
Owner: Codex
Last updated: 2026-07-03

Codex should use this format after completing a task from `WORK_HANDOFF.md`.

```md
# Codex Implementation Report: <Task Title>

Status: Implemented / Partially Implemented / Blocked
Date:
Branch / commit:

## 1. Summary

Briefly state what was implemented.

## 2. Changed Files

- `path/to/file`: what changed and why.

## 3. Behavior Added Or Changed

Explain actual behavior, not only file changes.

## 4. Verification Commands

List exact commands run, for example:

```bash
python -m pytest -q
python evals/run_evals.py
python evals/run_synthetic_diagnosis_lab.py
```

## 5. Verification Results

Paste concise result lines. Do not claim success without command evidence.

## 6. Boundary Check

Confirm whether the implementation changed any of these:

- scoring ownership;
- diagnosis ownership;
- rollback/forward ownership;
- ChallengeEngine state ownership;
- learner-safe API boundary;
- trusted field exposure;
- formal catalog publish behavior;
- database/auth/LLM assumptions.

## 7. Known Limits

List remaining limits or risks.

## 8. Recommended Next Step

Suggest the next concrete action.
```
