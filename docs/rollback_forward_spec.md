# Rollback and Forward Spec

The engine decides movement from score evidence, weighted errors, node policy, and graph relation. Final answer correctness never controls movement by itself.

## Rollback Levels

### R1: r1_internal

Rollback stays inside the current node.

Use for:

- ordinary calculation errors;
- expression weakness;
- local trigger drills;
- process repair within the current method.

### R2: r2_prerequisite

Rollback targets one or a few direct prerequisite nodes.

Use for:

- clear concept gap in an immediate prerequisite;
- method confusion caused by missing direct foundation;
- transformation error caused by a prerequisite form.

### R3: r3_cross_chapter

Rollback targets a cross-chapter foundation.

Use for:

- calculus operation weakness;
- algebraic transformation weakness;
- formula memory weakness outside the ODE chapter.

Phase 0 may represent these as policy placeholders because the full graph is not built.

### R4: r4_chapter_framework

Rollback targets chapter-level structure.

Use for:

- synthesis failure;
- severe knowledge confusion across multiple ODE families;
- inability to classify the problem category.

## Forward Levels

### P0: p0_none

No forward movement.

Use when primary errors remain, required dimensions are low, or false-pass evidence appears.

### P1: p1_partial

Partial forward movement or limited successor exposure.

Use when the node is mostly stable but one non-critical dimension needs review.

### P2: p2_normal

Normal movement to the next planned successor.

Use when required dimensions meet thresholds and no primary error blocks progression.

### P3: p3_strong

Strong movement to multiple successors or challenge variants.

Use only after very strong multi-dimensional evidence. A correct final answer alone cannot trigger P3.

## False Pass Rule

If `final_answer` is high but `trigger` or `method` is low, the result should be classified as `false_pass` or `partial_pass`. The engine must not strong-forward this attempt.

## Precise Rollback Rule

Rollback selects the smallest useful set of target nodes. Ordinary calculation errors must not return all prerequisites. If no better target exists, use the current node as the local rollback target.

## Phase 2.2-lite Movement Linkage

Phase 2.2-lite treats rollback, forward, and next-action output as a contract that must stay stable before API exposure.

Ownership rules:

- RollbackEngine owns `rollback_level` and `rollback_nodes`.
- ForwardEngine owns `forward_level` and `forward_nodes`.
- DiagnosisEngine owns recommended training actions, but does not replace rollback or forward decisions.
- `next_action_hint` must aggregate authoritative outputs and must not become a separate movement decision engine.

Next-action priority:

- `fail` and `false_pass` prioritize rollback, local repair, or `need_more_evidence`.
- rule-only and no-signal cases prioritize `need_more_evidence`.
- `calculation_error` prioritizes local `calculation_repair` and R1 current-node work.
- only `pass` may unlock P2/P3 movement.
- `partial_pass` allows only P1 local review or same-node variants.
- derived errors, including downstream final-answer failure, cannot upgrade rollback or forward movement over the root cause.

Phase 2.2-lite does not add node-status suggestions, mastery updates, attempt history, review scheduling, API fields, database persistence, or frontend behavior.
