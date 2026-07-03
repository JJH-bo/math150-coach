# Phase Real Attempt Lab Alpha Report

Status: Implemented by ChatGPT, pending local verification
Date: 2026-07-03

## 1. Major block improved

This phase improves the diagnosis calibration block.

The project already has an authoring pipeline and an ODE knowledge graph. This phase adds a learner-attempt calibration path so the engine can be checked against realistic wrong answers, not only against synthetic golden cases.

## 2. Files changed

- `backend/app/challenge/real_attempt_lab.py`
  - Adds the reusable real-attempt calibration engine.
  - Loads lab cases, validates node and error references, runs attempts through the existing ChallengeEngine and LearningOrchestrator path, compares expected root cause and repair target with actual output, and produces a calibration report.

- `tools/run_real_attempt_lab.py`
  - Converts the earlier script into a thin CLI wrapper around the real-attempt lab engine.
  - Supports normal output, JSON output, and strict non-zero exit when calibration does not pass.

- `backend/challenge_data/ode_network_mvp/real_attempt_lab_seed.yaml`
  - Provides the first 8 ODE real-attempt seed cases.

- `backend/tests/test_real_attempt_lab_seed.py`
  - Checks seed references against the current ODE graph and known error types.

- `backend/tests/test_real_attempt_lab_engine.py`
  - Tests lab spec validation and the calibration summary algorithm.

## 3. Behavior added

The project can now run a local calibration lab:

```bash
python tools/run_real_attempt_lab.py
python tools/run_real_attempt_lab.py --json
python tools/run_real_attempt_lab.py --strict
```

The lab returns:

- case count;
- root-cause match count;
- repair-target match count;
- exact match count;
- warning count;
- failure count;
- overall calibration grade;
- per-case mismatch reasons.

## 4. Algorithm implemented

The calibration algorithm checks two levels:

1. Root cause match
   - expected primary error vs actual diagnosis root cause.
2. Repair target match
   - expected repair node vs actual repair target.

Severity rule:

- `pass`: root cause and repair target both match.
- `warn`: repair target matches but root cause differs.
- `fail`: repair target differs.

Lab grade rule:

- `fail`: any case has repair-target failure, or there are zero cases.
- `warn`: no repair-target failure, but at least one root-cause warning.
- `pass`: every case exactly matches.

This makes repair-target correctness the hard gate because the final product must guide the learner to the right repair node.

## 5. Verification to run locally

ChatGPT created code and tests through GitHub, but did not run local commands. Codex should run:

```bash
python -m pytest backend/tests/test_real_attempt_lab_seed.py backend/tests/test_real_attempt_lab_engine.py -q
python tools/run_real_attempt_lab.py --json
python tools/run_real_attempt_lab.py --strict
```

Expected first outcome is not necessarily full calibration pass. If strict mode fails, that is useful evidence: it shows which real-attempt patterns the current diagnosis engine misses.

## 6. Boundaries

This phase does not add:

- database persistence;
- account system;
- learner scheduling;
- new chapter content beyond ODE seed calibration cases;
- changes to scoring, diagnosis, rollback, forward, or ChallengeEngine ownership.

## 7. Remaining work for Codex

Codex should verify, fix imports or runtime errors if any, and decide whether the lab reveals real diagnosis mismatches. If mismatches appear, the next step should be targeted diagnosis or evidence-rule improvement, not hiding the mismatch.
