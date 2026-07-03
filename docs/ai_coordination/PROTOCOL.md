# AI Coordination Protocol

Status: Active
Owner: ChatGPT
Last updated: 2026-07-03

## Core Principle

This workspace exists to make ChatGPT and Codex cooperate through GitHub as a shared fact source.

The goal is not to create bureaucracy. The goal is to increase development speed, reduce ambiguity, preserve project direction, and push Math150 Coach toward its highest final version.

## Default Workflow

1. ChatGPT reads the current GitHub state.
2. ChatGPT decides the best next phase or task.
3. ChatGPT writes or updates the handoff in `WORK_HANDOFF.md`.
4. Codex implements from the handoff, runs local checks, and reports results using `CODEX_REPORT_TEMPLATE.md`.
5. ChatGPT reviews the result using `CHATGPT_REVIEW_TEMPLATE.md`.
6. The user makes final decisions for major direction changes.
7. Important decisions are recorded in `DECISION_LOG.md`.

## Work Handoff Requirements

A Codex task should usually include:

- Goal
- Background
- Files likely involved
- Required behavior
- Non-goals
- Verification commands
- Acceptance criteria
- Known risks
- Expected report format

## Communication Rules

- Do not paste raw chat logs unless they are essential.
- Record only decisions, task intent, implementation reports, reviews, and unresolved questions.
- Keep entries concise but specific.
- Codex should not treat broad ideas as permission to expand scope.
- ChatGPT should not remain at vague planning level when it can provide concrete specs, data, tests, or code guidance.

## High-Level Boundaries

These boundaries protect the engine while still allowing ambitious development:

- Scoring ownership remains in the scoring engine.
- Diagnosis ownership remains in the diagnosis engine.
- Rollback/forward ownership remains in their dedicated engines.
- API and UI should not secretly become new decision engines.
- Trusted fields must not leak to learner-facing surfaces.
- Large content expansion should not hide weak diagnosis or graph logic.
- Major additions such as database, auth, real LLM, formal publish workflow, or full Mathematics I graph require explicit user approval.

## Bias Toward Action

ChatGPT should act as a core builder, not merely a commentator. When feasible, ChatGPT should create or update project files directly, including specs, templates, test plans, data designs, and small/medium implementation pieces.
