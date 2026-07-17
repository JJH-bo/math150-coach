# ChatGPT Parallel Push: Real Attempt Calibration Loop

Status: Ready for future implementation
Owner: ChatGPT
Created: 2026-07-03

## Why this matters

The current U2 line is building the authoring quality spine. That is necessary, but the final Math150 Coach system cannot be judged only by clean chapter drafts.

The final system must prove that it can diagnose real learner attempts.

This parallel push defines the next high-value learner-side slice: a real-attempt calibration loop for the current ODE network.

## Target

Create a small local lab that feeds real or realistic learner attempts into the existing scoring and diagnosis flow, then compares the engine output with an expected coaching judgment.

This is not a large new product layer. It is a calibration tool for the project brain.

## Minimum useful implementation

1. Add a seed case file for ODE learner attempts.
2. Each case should include:
   - node id;
   - question intent;
   - learner answer;
   - learner self explanation;
   - expected primary error;
   - expected repair target;
   - short human coaching note.
3. Add a local runner that loads the cases and calls the existing scoring/diagnosis path.
4. Produce a concise mismatch report:
   - expected vs actual root cause;
   - expected vs actual repair target;
   - score dimension weak points;
   - coaching explanation check.
5. Add focused tests around the runner and schema.

## Suggested file targets

- `backend/challenge_data/ode_network_mvp/real_attempt_lab_seed.yaml`
- `tools/run_real_attempt_lab.py`
- `backend/tests/test_real_attempt_lab.py`
- `docs/phase_real_attempt_lab_alpha_report.md`

## Initial seed case types

Use ODE because the current graph is strongest there.

Recommended first 8 cases:

1. separable equation recognized correctly but variables are not separated cleanly;
2. separable equation solved with missing integration constant;
3. first-order linear equation treated as separable;
4. first-order linear equation uses integrating factor but forgets standard form normalization;
5. homogeneous first-order equation recognized but uses wrong substitution direction;
6. homogeneous first-order equation confused with second-order constant-coefficient equation;
7. correct final answer but weak explanation of method trigger;
8. wrong final answer caused by calculation, while concept and method are acceptable.

## Acceptance signal

This slice is useful only if it tells us more than pass/fail.

A successful alpha should reveal whether the engine can distinguish:

- concept gap;
- trigger failure;
- method error;
- transformation error;
- calculation error;
- expression weakness;
- final answer mismatch;
- repair target selection.

## Boundary

Keep this as a local calibration lab. No database, account system, scheduling system, or broad content expansion is needed for this slice.

## Product judgment

This is a direct step toward the final version because it tests the core promise of Math150 Coach: not that it can display a knowledge graph, but that it can read a learner's attempt, find the real weakness, and point to the correct repair target.
