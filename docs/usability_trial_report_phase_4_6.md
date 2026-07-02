# Phase 4.6 Usability Trial Report

Trial date: 2026-06-29 Asia/Shanghai

Environment: Windows PowerShell, `math150-coach/backend`, frozen Phase 4.5 Local Trainer.

Command set used:

```text
python -m app.training.local_trainer list
python -m app.training.local_trainer show ode-sep-001
python -m app.training.local_trainer submit ode-sep-001 --session-id phase-4-6-trial-20260629 --answer "..."
```

Questions tested:

- `ode-sep-001`

Answers submitted:

1. Near-correct answer:
   `This is a separable differential equation. Separate variables as dy/y = 2x dx, then integrate to get ln|y| = x^2 + C, so y = C e^{x^2}.`
2. Incomplete answer:
   `It is separable. I separate variables and integrate.`
3. Wrong / low-signal answer:
   `Use the characteristic equation and solve for roots.`

## 1. List Experience

Success/fail: success.

Question count: 1.

Available `question_id` values:

- `ode-sep-001`

Friction:

- The JSON is parseable and compact.
- The command is easy to run.
- The current catalog has only one learner-visible question, so the trainer cannot yet support sustained practice.

Missing info:

- No section/chapter display beyond `node_id`.
- No short Chinese display title yet; the current title is English.
- No all-node learner-facing catalog overview, only question summary.

Leak check:

- No `expected_answer`, `answer_aliases`, `rubric`, `solution_outline`, `validator_config`, `trusted_scoring`, `scorer_results`, `diagnosis_trace`, `evidence_sources`, `raw_rollback_level`, or `raw_forward_level` field keys appeared.

## 2. Show Experience

Prompt clarity:

- The question is clear enough for the ODE separable-equation trial.
- `prompt_markdown` tells the learner to state the separable trigger, separate variables, integrate, and give the general solution.

Formatting:

- JSON is readable for technical review, but it is not comfortable as a student-facing study surface.
- The terminal output does not format math beautifully.

Hints usefulness:

- `hints_public` is appropriate and does not reveal the answer.
- The hint points to the separable-variable trigger.

Missing info:

- A learner may want a cleaner display mode, but this is not a P0 blocker.

Leak check:

- No answer, solution outline, rubric, expected answer, or trusted scoring block appeared.

## 3. Submit Experience

### Submit 1: Near-correct Answer

Pass state: `false_pass`.

Score vector usefulness:

- High useful dimensions:
  - `trigger`: 86.25
  - `method`: 86.25
  - `transformation`: 100.0
  - `calculation`: 92.29
  - `final_answer`: 95.0
- Missing dimensions:
  - `concept`
  - `expression`
  - `migration`
  - `process`

Learner explanation usefulness:

- The explanation says evidence is insufficient and asks the learner to write the trigger, method basis, and key process.
- This is directionally useful, but it feels too conservative for a near-correct answer that already includes method, separated form, integration, and final answer.

Recommended actions usefulness:

- Recommended action: `need_more_evidence`.
- This is reasonable if the system needs process evidence, but the learner-facing output should explain more concretely which process evidence was missing.

Rollback/forward clarity:

- `rollback_required`: false.
- `forward_allowed`: true.
- `forward_nodes`: `ode_homogeneous_first_order`.
- Friction: `pass_state=false_pass` and `forward_allowed=true` may confuse a learner. Internally this may mean limited forward with review retained, but the learner-facing boolean loses that nuance.

Next action usefulness:

- The next action asks for another same-node diagnostic question with trigger, method basis, and key process.
- This is useful, but it conflicts somewhat with the displayed `forward_allowed=true`.

### Submit 2: Incomplete Answer

Pass state: `fail`.

Score vector usefulness:

- `trigger`: 86.25
- `method`: 86.25
- `transformation`: 0.0
- `final_answer`: 35.0
- `calculation`: 79.43

Learner explanation usefulness:

- Stronger and clearer than the first response.
- It identifies transformation / standard-form handling as the main issue.

Recommended actions usefulness:

- Recommended action: `transformation_drill`.
- This is concrete and appropriate.

Rollback/forward clarity:

- `rollback_required`: true.
- `rollback_nodes`: `ode_separable`.
- `forward_allowed`: false.
- This is understandable.

Next action usefulness:

- The next action asks the learner to practice converting the original equation step by step into standard form and explaining equivalence.
- This is actionable.

### Submit 3: Wrong / Low-signal Answer

Pass state: `fail`.

Score vector usefulness:

- `trigger`: 0.0
- `method`: 0.0
- `transformation`: 0.0
- `calculation`: 30.86
- `final_answer`: 35.0

Learner explanation usefulness:

- The explanation correctly identifies trigger failure.
- It explains why this is not mainly a calculation issue.

Recommended actions usefulness:

- Recommended action: `trigger_drill`.
- This is specific and appropriate.

Rollback/forward clarity:

- `rollback_required`: true.
- `rollback_nodes`: `ode_separable`.
- `forward_allowed`: false.
- This is clear.

Next action usefulness:

- The next action tells the learner to practice identifying why the problem points to this node.
- This is useful.

### General Submit Friction

- The stdout JSON is parseable.
- In this Windows/Codex terminal capture, Chinese text displayed as mojibake in stdout, while the JSONL file stored readable UTF-8 Chinese. This may be a terminal encoding issue rather than a Local Trainer data issue.
- `score_vector_summary.notes` includes scorer names such as `RubricScorer` and `MathValidatorScorer`. This does not leak rubric content or scorer results, but it feels more like internal implementation language than learner-facing feedback.

## 4. Session Log Review

Log created: yes.

Path:

```text
backend/training_sessions/phase-4-6-trial-20260629.jsonl
```

Rows appended: 3.

Log readable:

- Yes. The JSONL rows are valid JSON and readable as UTF-8.
- Each row includes the learner answer, pass state, score summary, explanation, recommended actions, rollback/forward data, and next action hint.

Useful for review:

- Enough for a technical after-action review.
- Useful to compare how different answer quality changes scoring and diagnosis.
- Not yet comfortable for a learner to browse without a `history` command or formatted summary.

Missing fields:

- No attempt label such as `near_correct`, `incomplete`, or `wrong`.
- No command invocation field.
- No compact score summary optimized for learner reading.
- No display ordering or session summary.

Need history command:

- Helpful soon, but not the first blocker from this trial.
- Manual JSONL inspection is workable for one trial, but would become painful after repeated practice.

Leak check:

- No trusted field keys found in JSONL:
  - `expected_answer`
  - `answer_aliases`
  - `rubric`
  - `solution_outline`
  - `validator_config`
  - `trusted_scoring`
  - `scorer_results`
  - `diagnosis_trace`
  - `evidence_sources`
  - `raw_rollback_level`
  - `raw_forward_level`

Audit note:

- Score notes include scorer labels like `RubricScorer`, which are not the same as leaked rubric data, but they are not ideal learner-facing language.

## 5. Training Value Judgment

Did this improve real math training?

- Partially yes. The system distinguishes near-correct, incomplete, and wrong answers in a meaningful way.
- It gives useful actions for incomplete and wrong answers.

Was the feedback actionable?

- For incomplete and wrong answers: yes.
- For near-correct answer: partially. It asks for more evidence but does not make it obvious why the existing answer still counted as `false_pass`.

Did it expose the weak point?

- Yes for transformation failure and trigger failure.
- Less clearly for near-correct answer because the problem appears to be missing process evidence, but the answer already includes several process-like elements.

Would I use this again tomorrow?

- For debugging the engine and trying a small number of questions: yes.
- For sustained learner practice: not yet. The output needs refinement and the catalog is too small.

## 6. Main Problems Found

P0 blocker:

- No hard blocker. The frozen Local Trainer can complete `list` / `show` / `submit` and writes JSONL.

P1 improvement:

- Learner-facing output needs refinement. In particular:
  - `false_pass` with `forward_allowed=true` is confusing.
  - near-correct answers need clearer explanation of what evidence was insufficient.
  - score notes expose internal scorer names rather than student-friendly evidence.
  - terminal display of Chinese may need encoding/display guidance.

P2 future polish:

- More learner-visible questions are needed for realistic repeated practice.
- A `history` command would make JSONL review easier.
- A lightweight UI may eventually improve math readability, but CLI is not the biggest blocker yet.

## 7. Next-phase Recommendation

Chosen recommendation:

```text
C. Learner Output / Coach Feedback Refinement
```

Reason:

- The trial succeeded technically, so micro-hardening is not the main need.
- The catalog is small, but the single-question trial already revealed a more fundamental issue: the feedback and movement display need to be more learner-comprehensible before scaling usage.
- The strongest evidence is the near-correct answer response: high dimensional scores, `false_pass`, `forward_allowed=true`, and `need_more_evidence` all appear together. This may be valid internally, but the learner-facing explanation does not fully resolve the apparent contradiction.
- Improving learner output would make future trials more informative before investing in history, frontend, persistence, or catalog expansion.

Secondary recommendation:

- After feedback refinement, consider `B. Minimal Catalog Expansion for Real Practice`, because one learner-visible question cannot support sustained training.

Do not implement the recommendation in Phase 4.6. This report is trial evidence only.

