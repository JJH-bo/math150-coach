# ChatGPT Review Template

Status: Active
Owner: ChatGPT
Last updated: 2026-07-03

ChatGPT should use this format when reviewing Codex work.

```md
# ChatGPT Review: <Task Title>

Status: Accepted / Needs Fixes / Rejected / Freeze Recommended
Date:
Reviewed commit / branch:

## 1. Verdict

Direct judgment.

## 2. What Was Actually Verified

List files read, behavior checked, and evidence inspected.

## 3. Alignment With Task

Does the implementation satisfy the handoff goal?

## 4. Boundary Audit

Check whether any frozen ownership or safety boundary was changed.

## 5. Test / Eval Evidence

Record available test evidence. If tests were not independently run by ChatGPT, say so clearly and inspect Codex's reported evidence.

## 6. Risks

List specific risks, not vague concerns.

## 7. Required Fixes

If needed, provide concrete required changes.

## 8. Next Step

Choose one:

- freeze this phase;
- request fixes;
- assign next Codex task;
- ask user for a direction decision.
```
