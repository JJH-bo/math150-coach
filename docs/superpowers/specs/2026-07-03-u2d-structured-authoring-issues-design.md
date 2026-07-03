# U2D Structured Authoring Issues Design

Date: 2026-07-03

Status: approved for autonomous execution

## 1. Decision

U2D upgrades chapter draft validation issues from plain text messages into a
stable authoring contract:

```text
target + message
  -> code + severity + target + target_kind + message + suggested_fix
```

The old `target` and `message` fields stay intact for compatibility. The new
fields make the same validation result useful to three consumers:

- human reviewers deciding what to fix first.
- the frontend draft preview graph deciding what to highlight.
- ChatGPT or other assistant workflows proposing repairs without guessing the
  issue category from prose.

## 2. Scope

This slice changes only draft authoring feedback. It does not add chapter
content, publish draft content, alter runtime scoring, alter diagnosis, change
student progression, add persistence, or add LLM integration.

## 3. Backend Contract

Every item in `report.errors` and `report.warnings` must include:

- `target`: existing focus identifier, usually a node id, edge id, collection
  name, or root cause.
- `message`: existing human-readable validation message.
- `code`: stable snake_case issue code.
- `severity`: `error` or `warning`.
- `target_kind`: coarse object family such as `chapter`, `macro_nodes`,
  `micro_nodes`, `logic_nodes`, `logic_edges`, or `error_repair_map`.
- `suggested_fix`: one short author action.

Issue codes should describe the validation rule rather than the exact prose.
Examples:

- `invalid_chapter_id`
- `missing_item_id`
- `duplicate_item_id`
- `invalid_micro_macro`
- `invalid_micro_type`
- `invalid_macro_challenge_macro`
- `invalid_macro_challenge_coverage`
- `invalid_compare_guard`
- `missing_compare_contrast`
- `invalid_logic_owner`
- `invalid_repair_target`
- `invalid_edge_type`
- `self_loop_edge`
- `invalid_edge_endpoint`
- `missing_edge_reason`
- `visible_node_budget_warning`
- `visible_node_budget_exceeded`
- `missing_why_exists`
- `missing_evidence_sources`
- `invalid_root_cause`
- `missing_repair_map`
- `orphan_logic_node`

The readiness projection may continue using the existing message and target
fields, but should prefer issue codes where that makes the rule clearer.

## 4. Frontend Contract

The import report must render the structured fields without becoming a dense
debug panel:

- show severity and code as compact metadata.
- keep the target as the focus button.
- show `target_kind` as context when available.
- show `suggested_fix` as a short next action.
- keep `.issue-focus` and `data-focus-targets` working with U2C graph focus.

The frontend must tolerate older issue objects that only contain `target` and
`message`.

## 5. Testing

Backend tests must prove:

- errors contain the full structured issue contract.
- warnings contain the same contract with `severity: warning`.
- at least one repair-target validation error has a stable specific code.

Frontend contract tests must prove:

- the report renders issue code, severity, kind, and suggested fix affordances.
- graph focus still uses the issue target button.

Existing full regression tests, golden evals, synthetic diagnosis lab, JavaScript
syntax checking, and browser validation remain required before completion.

## 6. Non-Goals

U2D does not introduce automatic fixing, formal publishing, human review storage,
candidate builds, content hashes, database history, auth, deployment, or new
chapter content.
