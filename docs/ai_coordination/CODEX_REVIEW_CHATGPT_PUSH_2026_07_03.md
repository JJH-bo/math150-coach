# Codex Review: ChatGPT Push 2026-07-03

Status: Reviewed and partially hardened by Codex
Date: 2026-07-03
Reviewed remote head: `626d2e8`

## 1. Hard-Gate Decision

The ChatGPT push satisfies the user's handoff acceptance gate.

Reasons:

- It upgrades major final-version blocks: real-attempt diagnosis calibration and chapter authoring candidate dry-run.
- It includes concrete development results, not only planning.
- It includes algorithm code, tests, and implementation reports.

## 2. Accepted Work

### Real Attempt Lab Alpha

Accepted as a valid major-block upgrade.

The lab runs real learner-style attempts through the existing challenge engine and reports root-cause / repair-target calibration quality. Current strict result is intentionally failing because the diagnosis engine misses several real-attempt expectations.

This is useful evidence, not a reason to hide the lab.

### Chapter Candidate Dry-Run Builder

Accepted as a valid upstream implementation, but Codex hardened the boundary before treating it as integrated project work.

Codex changes:

- use `sha256:<64 lowercase hex chars>` content hash format;
- recursively remove trusted/internal fields from candidate payloads;
- add `/candidate-build-dry-run` route alias;
- expand tests for hash format, trusted-field boundary, and endpoint compatibility.

## 3. Verification Evidence

Initial ChatGPT-focused checks:

```bash
python -m pytest backend/tests/test_chapter_candidate_builder.py backend/tests/test_real_attempt_lab_seed.py backend/tests/test_real_attempt_lab_engine.py -q
```

Result before Codex hardening:

```text
7 passed
```

Real attempt lab strict check:

```bash
python tools/run_real_attempt_lab.py --strict
```

Result:

```text
grade=fail
root=5/8, repair=6/8, exact=4/8
```

Interpretation: the lab is working and exposing real diagnosis misses.

## 4. Next Engineering Judgment

Do not discard the real-attempt lab because strict mode fails. Use the failure as the next diagnosis improvement target.

The two hard failures to investigate first:

- `ode.real_attempt.separable_constant_002`
- `ode.real_attempt.linear_standard_form_004`

