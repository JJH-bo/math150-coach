# Logic Knowledge Graph Spec

This document defines the long-term logic graph architecture for Math150 Coach.
The graph must stay rigorous enough for diagnosis while keeping the learner map
small enough to feel like a game, not a task checklist.

## Core Principle

The knowledge graph has two layers:

- Visible training layer: nodes a learner can see, unlock, practice, or clear.
- Hidden ability layer: atomic evidence and causal structure used by diagnosis.

Hidden abilities may explain why a learner is stuck, but they do not create
progress nodes by themselves. Pass/fail, rollback, and forward movement remain
owned by the existing engines.

## Visible Node Roles

- `MacroNode`: a large knowledge area.
- `MicroNode`: a visible trainable ability under a macro node.
- `MacroChallenge`: a boss-style integrated acceptance task for one macro node.
- `CompareGuard`: a visible comparison point for easily confused methods.
- `TransferNode`: a graph-semantic node for variants and migration. It does not
  automatically become a training task.
- `SynthesisNode`: a graph-semantic node for decomposition of compound work. It
  does not automatically become a training task.

The UI map should display only nodes that are useful for learning flow. It must
not expose every hidden atomic criterion.

## Hidden Ability Roles

`LogicAbility.kind` says what is being checked. `LogicAbility.role` says why the
ability exists in the network.

- `atomic`: a minimal hidden ability behind one visible micro node.
- `prerequisite`: a hidden ability that must be stable before another ability is meaningful.
- `confusion_guard`: a guard against confusing neighboring nodes.
- `transfer` / `transfer_node`: a bridge to variants or migration.
- `synthesis` / `synthesis_node`: a decomposition or integrated solving route.
- `expression`: final mathematical writing and conclusion quality.
- `condition`: initial values, domains, nonzero restrictions, and condition tracking.
- `boss_criterion`: a hidden criterion checked by a macro challenge.

## Hidden Ability Kinds

- `concept_criterion`: concept object, definition, or theorem condition.
- `trigger_pattern`: problem features that should trigger a node or method.
- `method_step`: method selection and local method justification.
- `transformation_rule`: standard form, substitution, equivalence, or condition conversion.
- `calculation_skill`: execution such as integration, algebra, constants, and simplification.
- `expression_rule`: final answer form, constants, variables, and conclusion writing.
- `condition_rule`: initial values, domains, nonzero restrictions, and special solutions.
- `misconception_guard`: distinction between neighboring knowledge points.
- `synthesis_path`: decomposition route for integrated tasks.

## Required Hidden Ability Fields

Every hidden ability should explain its graph role:

- `why_exists`: why this ability belongs in the graph.
- `evidence_sources`: which evidence channels can support or refute it.
- `failure_modes`: what errors usually appear when it is unstable.
- `repair_target_node_id`: the visible training node to repair when it fails.
- `visibility_policy`: `hidden`, `diagnosis_only`, or `map_visible`.

These fields are for authoring, diagnosis, and quality validation. They should
not inflate the learner-facing map.

## Edge Types

Edges must be semantic. A valid edge explains why two abilities or nodes are
connected; it is not just a layout line.

- `requires`: source must be present before target is meaningful.
- `supports`: source strengthens target.
- `derives_to`: one ability causally derives or unlocks the next ability.
- `transforms_to`: a condition, equation, or method converts into another form.
- `contrasts_with`: two abilities must be compared.
- `commonly_confused_with`: nearby abilities are often mixed up.
- `checks`: a task or ability checks another ability.
- `repairs`: source points to the visible repair target or repair ability.
- `transfers_to`: source supports a variant or migration ability.
- `blocks`: an unstable source blocks target progress.
- `boss_checks`: a boss criterion checks hidden abilities.

Compatibility rule: legacy YAML value `remediates` is accepted and normalized to
`repairs` at load time. New graph content should use `repairs`.

Every edge should carry a `label` or `reason`, and a positive `weight`. Self
loops are invalid. Zero-weight edges are invalid.

## Diagnosis Use

Logic graph diagnosis is advisory. Current ownership remains:

- `CompositeScoringEngine`: scoring.
- `DiagnosisEngine`: root cause, error roles, evidence, and recommended action.
- `RollbackEngine`: rollback nodes and rollback level.
- `ForwardEngine`: forward nodes and forward level.
- API/UI: presentation only.

The logic graph may add hidden ability evidence, repair hints, and graph edge
semantics to diagnosis. It must not override movement decisions.

## Evidence Flow

```text
attempt
  -> CompositeScoringEngine
  -> DiagnosisEngine evidence bundle
  -> hidden ability evidence
  -> learner-safe diagnosis and repair guidance
```

The diagnosis layer may use:

- score vector dimensions;
- rubric required/optional misses;
- math validator flags;
- rule scorer weak signals;
- response steps and self explanation;
- hidden ability evidence;
- node policy;
- graph edge semantics.

Ability evidence status can be `demonstrated`, `weak`, `missing`,
`contradicted`, or `unknown`.

## Quality Gate

`KnowledgeGraphQualityValidator` is an authoring/runtime quality gate. It reports
quality issues only; it does not change learner behavior.

It checks:

- missing logic graph;
- macro nodes missing required visible micro types;
- trainable micro nodes without hidden ability coverage;
- hidden ability dimension mismatch with visible micro nodes;
- hidden repair targets outside visible trainable nodes;
- repair targets that are too broad, such as macro-only repair targets;
- every core root cause mapping to at least one hidden ability and one micro repair target;
- orphan hidden abilities;
- hidden abilities missing `why_exists` or `evidence_sources`;
- meaningless logic edges: self loops, missing label/reason, or zero weight;
- cycles across `requires`, `blocks`, and `derives_to`;
- visible micro node explosion under one macro node;
- CompareGuard nodes that do not actually connect at least two confused nodes;
- CompareGuard nodes without `misconception_guard` hidden ability coverage;
- MacroChallenge coverage of contained MicroNodes;
- MacroChallenge hidden coverage through `boss_checks` or synthesis-like edges.

Visible node budget:

- more than 8 visible micro nodes under one macro is a warning;
- more than 12 visible micro nodes under one macro is an error.

## Repair Precision

Every root cause should resolve through:

```text
error_ability_map -> hidden ability -> repair_target_node_id
```

The repair target should normally be a visible MicroNode. Macro-level repair is
allowed only as a warning-level fallback and should be avoided in final chapter
content.

MacroChallenge failure may use a more precise hidden ability repair target when
the target belongs to the same training region. Multiple hidden ability failures
should not open a pile of visible tasks at once.

## Current ODE Slice

The current sample slice is `ode_network_mvp`.

It demonstrates the final architecture on a small first-order ODE area:

- separable equations;
- first-order linear equations;
- first-order homogeneous equations;
- comparison guards for nearby methods;
- transfer and synthesis abilities for method selection and boss checks;
- hidden concept, trigger, method, transformation, calculation, expression, and condition chains.

This is not a full ODE chapter and not full Mathematics I. The purpose is to
prove the extensible architecture on a narrow slice.
