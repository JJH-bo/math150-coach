# Codex Handoff Acceptance Standard

Status: Active
Owner: User + Codex
Last updated: 2026-07-03

This standard is binding for future ChatGPT-to-Codex handoffs.

## Core Rule

Codex must not accept a handoff merely because ChatGPT wrote a task. A handoff is actionable only when ChatGPT has already produced concrete upstream development results and the task clearly upgrades a major final-version project block.

If a handoff fails the gates below, Codex should reject it in the coordination log and ask ChatGPT to do the missing upstream work first.

## Gate 1: Final-Version Block Upgrade

The handoff must directly advance the final version by upgrading a major project block to a higher maturity level.

Acceptable major blocks include:

- chapter draft import and authoring quality control;
- logic knowledge network structure;
- diagnostic algorithm and root-cause reasoning;
- scoring and evidence calibration;
- rollback / forward movement policy;
- active-output verification;
- variant transfer and repair training loops;
- review scheduling;
- cosmic map UI as a learning-state and knowledge-network interface;
- runtime graph quality and publish safety.

Reject the handoff if it is only a small label change, shallow doc reminder, cosmetic-only tweak, generic cleanup, or isolated micro-task that does not clearly raise one major block.

## Gate 2: ChatGPT Must Deliver Concrete Development Results

Codex must reject handoffs where ChatGPT only asks Codex to do the work.

Before Codex accepts the task, ChatGPT should provide concrete results such as:

- committed code changes;
- committed tests;
- committed data/spec files;
- committed docs that define exact contracts, schemas, or acceptance criteria;
- a precise patch or implementation artifact when GitHub tooling is unavailable.

The handoff must include file paths, changed behavior, and enough implementation detail for Codex to review, integrate, optimize, or harden.

## Gate 3: Algorithm Code Must Be Implemented Upstream

When the handoff involves algorithmic behavior, ChatGPT must implement the algorithm code itself before handing it to Codex.

Algorithmic areas include:

- graph validation;
- diagnostic classification;
- scoring rules;
- candidate build logic;
- hash/canonicalization;
- repair target mapping;
- calibration logic;
- scheduling policy;
- transfer/synthesis routing;
- UI state derivation when it affects learning behavior.

Codex's role after that is to optimize, debug, integrate, test, and strengthen the algorithm. Codex should not accept a handoff that says, in effect, "Codex, please design and implement the whole algorithm from scratch."

## Minimum Handoff Package

A valid ChatGPT handoff should contain:

- the major block being upgraded;
- why this is a final-version maturity step;
- ChatGPT's concrete development result;
- exact files changed or proposed;
- algorithm code location if algorithmic behavior is involved;
- tests added or expected;
- verification evidence or a clear reason verification could not be run;
- what Codex should specifically optimize, fix, integrate, or verify;
- known risks and non-goals.

## Codex Response Policy

If the package is valid, Codex can proceed with critical review, edits, tests, browser verification, report, commit, and push.

If the package is invalid, Codex should not implement the task. Codex should instead write a short rejection with the missing gates and the exact upstream work ChatGPT must complete before the handoff can return.

