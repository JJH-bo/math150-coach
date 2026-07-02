# Usability Trial Protocol

Status: Phase 4.6 planning artifact.

This protocol is a manual trial script for the frozen Local Trainer. It should be followed before deciding the next product phase.

## 1. Preparation

Start from the backend module root:

```text
cd math150-coach/backend
```

Use the current frozen Local Trainer only:

```text
python -m app.training.local_trainer ...
```

Do not change code, catalog data, engines, APIs, or Local Trainer commands during the trial.

## 2. List Questions

Run:

```text
python -m app.training.local_trainer list
```

Record:

- success or fail;
- question count;
- available `question_id` values;
- whether output is clear;
- whether stdout is JSON;
- whether any trusted field appears.

Trusted field leak check:

- no `expected_answer`;
- no `answer_aliases`;
- no `rubric`;
- no `solution_outline`;
- no `validator_config`;
- no `trusted_scoring`;
- no `scorer_results`;
- no `diagnosis_trace`;
- no `evidence_sources`;
- no raw movement levels.

## 3. Show One Question

Run:

```text
python -m app.training.local_trainer show <question_id>
```

Record:

- whether the stem is clear;
- whether `prompt_markdown` is enough;
- whether public hints are appropriate;
- whether formatting is readable in the terminal;
- whether output needs a better layout;
- whether answer, explanation, or rubric leaks.

## 4. Submit Near-correct Answer

Run:

```text
python -m app.training.local_trainer submit <question_id> --answer "..."
```

Use a correct or near-correct answer.

Record:

- `pass_state`;
- `score_vector_summary`;
- `learner_explanation`;
- `recommended_actions`;
- `rollback_required`;
- `forward_allowed`;
- `next_action_hint`;
- whether `session_log_written` is true;
- whether the response is useful for real training.

## 5. Submit Incomplete Answer

Run another submit command with an incomplete answer.

Record whether the system recognizes:

- correct trigger but incomplete process;
- correct method but weak expression;
- missing steps;
- need for more evidence;
- false-pass risk.

Also record whether the feedback explains what to improve next.

## 6. Submit Wrong or Low-signal Answer

Run a third submit command with a clearly wrong or low-signal answer.

Record whether the system recognizes:

- method error;
- trigger failure;
- no signal;
- false pass avoidance;
- rollback or no-forward behavior.

## 7. Inspect Session Log

Inspect:

```text
training_sessions/
```

Record:

- whether JSONL was generated;
- whether each row is readable;
- whether the log is useful for review;
- whether a `history` command feels necessary;
- whether better summary fields are needed;
- whether any trusted field leaked.

Do not treat this file as formal attempt persistence. It is only a lightweight local learner log.

## 8. Trial Summary

Fill in:

- What was the biggest blocker?
- What is the most wanted next feature?
- Was the diagnosis output good enough for training?
- Was the local record useful enough?
- Did anything leak or feel unsafe?
- Which next phase should be recommended?

Use `docs/usability_trial_report_template.md` for the final report.

## 9. Stop Rule

Stop the trial and record the issue if:

- a trusted field appears in list/show/submit output;
- the command cannot produce parseable JSON;
- submit cannot write a session log;
- the local log writes into a protected project area;
- any command requires code changes to complete the trial.

Do not patch code during the trial. File a next-phase recommendation instead.

