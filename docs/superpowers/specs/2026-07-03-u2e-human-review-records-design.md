# U2E Human Review Records Design

Date: 2026-07-03

Status: approved for autonomous execution

## 1. Decision

U2E adds a human review record layer to the chapter draft authoring workflow.
The record is authoring-only and non-persistent. It lets a reviewer turn a
validated draft preview into an auditable decision without writing to the formal
runtime catalog.

The authoring pipeline becomes:

```text
Structured Draft
  -> Draft Preview
  -> Graph Quality Gate
  -> Human Review Record
  -> Candidate Build Dry-Run (future U2F)
  -> Formal Publish (still locked)
```

## 2. Scope

U2E adds:

- a `human_review` packet to draft validation output.
- a new authoring endpoint that records one review decision for a Markdown draft.
- a frontend review panel with reviewer, checklist, notes, and decision controls.
- tests proving validation failures cannot be approved for candidate build.

U2E does not add persistence, content hashes, candidate build generation,
formal publishing, chapter content, auth, database storage, or LLM integration.

## 3. Backend Contract

Validation response includes:

```json
{
  "human_review": {
    "required": true,
    "status": "pending",
    "candidate_build_allowed": false,
    "formal_publish_allowed": false,
    "required_checklist": [
      {"code": "math_scope_checked", "label": "..."},
      {"code": "macro_micro_structure_checked", "label": "..."}
    ],
    "issue_snapshot": []
  }
}
```

When validation has blocking errors, `human_review.status` is
`blocked_by_validation`.

The review endpoint accepts:

- `markdown`: the draft under review.
- `reviewer`: non-empty reviewer name.
- `decision`: `request_changes` or `approve_for_candidate`.
- `checklist`: map of checklist code to boolean.
- `notes`: optional short text.

It returns:

```json
{
  "mode": "chapter_draft_human_review",
  "workflow_stage": "human_review",
  "publish_state": "draft_only",
  "candidate_build_allowed": false,
  "formal_publish_allowed": false,
  "review_record": {
    "record_id": "...",
    "chapter_id": "...",
    "reviewer": "...",
    "decision": "...",
    "status": "...",
    "checklist": [...],
    "issue_snapshot": [...]
  }
}
```

Candidate build is allowed only when:

- validation passed.
- decision is `approve_for_candidate`.
- every required checklist item is true.

Formal publish remains unavailable in every response.

## 4. Frontend Contract

The import report must render a human review panel after validation:

- reviewer input.
- required checklist checkboxes.
- notes field.
- request changes button.
- approve for candidate button.
- result area showing review status and candidate-build gate.

The panel is an authoring tool. It must not appear in the learner training flow.
It must not claim that a draft is formally published.

## 5. Review Checklist

Required checklist codes:

- `math_scope_checked`
- `macro_micro_structure_checked`
- `repair_targets_checked`
- `hidden_abilities_checked`
- `semantic_edges_checked`
- `boss_coverage_checked`
- `learner_surface_safe`

## 6. Non-Goals

U2E does not persist records, generate content hashes, build candidates, publish
content, expose trusted answer data, add login, or connect to an LLM.
