# Phase 4.6 Plan: Usability Trial / Real Training Run Protocol

Status: planning only. Do not implement product features in this phase.

Phase 4.6 uses the frozen Phase 4.5 Local Trainer to run a real learner-flow trial. The goal is not to add features. The goal is to verify whether the current local training loop can actually support meaningful math practice.

Core question:

```text
Can the current frozen Local Trainer serve a real math training run?
```

## 1. Goals

Phase 4.6 should:

- use the frozen Local Trainer for a real training trial;
- observe current usability in real math practice;
- collect issues in output quality, command experience, diagnosis feedback, record format, and review value;
- decide the next phase based on trial evidence instead of guessing feature priority.

The trial should answer:

- Can a learner find a question?
- Can a learner understand the question display?
- Can a learner submit multiple answer qualities smoothly?
- Does the response feel like useful math-coach feedback?
- Does the JSONL session log support after-action review?
- What is the most painful missing capability?

## 2. Non-goals

Phase 4.6 does not implement:

- history command;
- frontend;
- database;
- formal attempt persistence;
- mastery/review scheduler;
- next-question recommendation;
- catalog expansion;
- formal publish/export;
- LLM integration;
- UI polishing;
- code refactor.

No code should be changed during this planning phase.

## 3. Trial Scope

Recommended trial scope:

- use current published learner questions only;
- run `list` at least once;
- run `show` at least once;
- submit at least 2-3 answers of different quality:
  - correct or near-correct answer;
  - incomplete answer;
  - clearly wrong or low-signal answer;
- check stdout JSON;
- inspect `training_sessions/*.jsonl`;
- record real friction and training value.

The trial should be small enough to complete manually but concrete enough to expose actual learner pain.

## 4. Trial Evaluation Dimensions

Evaluate:

- whether questions are easy to find;
- whether question display is clear;
- whether commands are easy to use;
- whether answer submission is smooth;
- whether diagnosis output feels like math coaching;
- whether `score_vector_summary` is useful for review;
- whether `learner_explanation` guides correction;
- whether `recommended_actions` are concrete;
- whether rollback/forward information is understandable;
- whether `next_action_hint` is helpful;
- whether JSONL session log is enough for review;
- whether history is needed;
- whether output format needs improvement;
- whether more questions are needed;
- whether a frontend is needed;
- whether formal persistence is needed;
- whether any trusted field leaks;
- whether there are path or record problems.

## 5. Decision Rule

After the trial, choose the next phase by the dominant problem:

```text
A. Biggest problem: cannot view prior attempts
   -> Phase 4.7 Plan: Local Trainer History P1

B. Biggest problem: too few questions
   -> Phase 4.7 Plan: Minimal Catalog Expansion for Real Practice

C. Biggest problem: feedback is not coach-like enough
   -> Phase 4.7 Plan: Learner Output / Coach Feedback Refinement

D. Biggest problem: CLI is uncomfortable
   -> Phase 4.7 Plan: Minimal Learner UI / Frontend Exploration

E. Biggest problem: records cannot support review
   -> Phase 4.7 Plan: Attempt Persistence / Review Scheduler Research

F. Biggest problem: path safety or session-root policy
   -> Phase 4.5.2 Micro-hardening
```

Do not proceed to frontend, database, persistence, mastery, review, or catalog expansion without the trial report naming that as the dominant problem.

## 6. Success Criteria

Phase 4.6 is successful when:

- a user can independently complete one `list` / `show` / `submit` loop;
- at least one JSONL session log row is created;
- scoring, diagnosis, rollback, forward, and next-action information can be read from the response;
- at least 3 real usability issues are listed;
- the next phase can be chosen from evidence;
- no code pollution is introduced;
- no product feature expansion is performed.

## 7. Required Artifacts

Phase 4.6 should produce:

- a completed usability trial report using `docs/usability_trial_report_template.md`;
- command outputs or summarized observations;
- at least one session log inspection note;
- a next-phase recommendation selected by the decision rule.

## 8. Boundary

Frozen boundaries remain in force:

- do not change Local Trainer commands;
- do not implement history;
- do not add endpoints;
- do not modify API contracts;
- do not modify scoring, diagnosis, rollback, forward, or orchestration logic;
- do not write formal catalog files;
- do not expand the question catalog;
- do not add database, frontend, auth, LLM, mastery, or review.
