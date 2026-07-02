# Scoring Spec

Each attempt is scored on the dimensions that the question actually tests. A dimension not tested by a question is represented as `None`.

Each scored dimension has:

- `score`: integer or float from 0 to 100;
- `evidence`: optional explanation of observed evidence;
- `notes`: optional grader notes.

`overall_score` is the weighted or unweighted average of available dimensions. It is a summary signal only and must never decide node passing by itself.

## Dimensions

### concept

- Definition: understanding of definitions, objects, theorem conditions, and conceptual boundaries.
- Range: 0-100.
- Scoring object: conceptual statements and use of definitions.
- High score: clearly identifies the mathematical object and necessary conditions.
- Low score: confuses definitions, omits required conditions, or uses concepts outside their scope.

### trigger

- Definition: recognition of the problem signal that points to a node, method, or transformation.
- Range: 0-100.
- Scoring object: explanation of why a method or node is relevant.
- High score: names the key condition and connects it to the correct node.
- Low score: guesses a method, cannot explain the trigger, or follows surface features only.

### method

- Definition: selection of a suitable solving method.
- Range: 0-100.
- Scoring object: chosen method and route.
- High score: selects a valid method with awareness of assumptions.
- Low score: chooses an incompatible method or switches randomly.

### transformation

- Definition: conversion of the original condition into a usable mathematical form.
- Range: 0-100.
- Scoring object: substitutions, rearrangements, standard forms, and equivalent transformations.
- High score: transforms conditions correctly and preserves equivalence.
- Low score: loses conditions, makes non-equivalent transformations, or fails to reach standard form.

### process

- Definition: logical completeness of the solution process.
- Range: 0-100.
- Scoring object: step order, justification, and continuity.
- High score: solution is coherent and every major transition is justified.
- Low score: skips key steps, contains logical breaks, or jumps to results without support.

### calculation

- Definition: execution of algebra, calculus, simplification, and arithmetic.
- Range: 0-100.
- Scoring object: computations after the method is chosen.
- High score: calculations are accurate and controlled.
- Low score: signs, constants, derivatives, integrals, or simplifications are wrong.

### final_answer

- Definition: correctness and completeness of the final result.
- Range: 0-100.
- Scoring object: final expression, constants, domain, and required form.
- High score: final answer matches the required result and includes needed constants or restrictions.
- Low score: answer is missing, incompatible, incomplete, or numerically/symbolically wrong.

### expression

- Definition: rigor and clarity of written mathematical expression.
- Range: 0-100.
- Scoring object: notation, statements, condition handling, and final presentation.
- High score: notation is consistent and conditions are stated clearly.
- Low score: expression is ambiguous, notation changes meaning, or conclusions are not stated rigorously.

### migration

- Definition: ability to transfer the method to variants and nearby problem forms.
- Range: 0-100.
- Scoring object: variant explanation, generalization, and adaptation.
- High score: explains how the method changes under variants.
- Low score: can only reproduce the exact pattern and fails when conditions shift.

## Pass Rule Boundary

Node passing must consider:

- required dimensions;
- minimum dimension thresholds;
- weighted errors;
- primary error count;
- false-pass signals;
- mastery history in later phases.

`overall_score` alone is never enough.

## Phase 1 Scoring Architecture

Default scoring uses `CompositeScoringEngine.evaluate_detailed()` and merges scorer outputs per dimension.

Default scorer order:

1. `ManualOverrideScorer`
2. `RubricScorer`
3. `MathValidatorScorer`
4. `RuleScorer`
5. `LLMScorerStub`

`ManualOverrideScorer` is active only when `attempt.metadata.score_overrides` is present. Its evidence must identify the score as imported/manual override.

`RubricScorer` is the Phase 1 primary scorer. It reads `Question.rubric`, `expected_key_points`, and `expected_patterns`; it does not read `expected_scores`.

### Rubric Required / Optional Rules

Each rubric item can be required or optional.

- Required item hit: contributes its configured weight to all target dimensions.
- Required item miss: strongly lowers the weighted score for its target dimensions and must appear in evidence as `required_missed`.
- Optional item hit: contributes its configured weight as additional support.
- Optional item miss: is recorded as `optional_missed`, but should be configured with low weight so it does not penalize like a required miss.

When a rubric item defines both `required_keywords` and `expected_patterns`, the Phase 1 rule is strict: all required keywords and all expected patterns must match for that item to count as hit. This prevents a copied keyword or a single surface phrase from satisfying a multi-part rubric item.

Rubric evidence must record `matched_items`, `missed_items`, `required_missed`, and `optional_missed` so downstream diagnosis can explain which scoring requirements were or were not met.

`MathValidatorScorer` is a lightweight string validator for final-answer and calculation signals. It checks simple normalized answer matches, equivalent aliases, missing arbitrary constants, and initial-value answers that stop at a general solution.

### MathValidator Phase 1 Boundary

`MathValidatorScorer` can affect only `final_answer` and `calculation` in Phase 1. It supports:

- normalized string containment or direct answer match;
- expected answer aliases for simple equivalent final forms;
- missing arbitrary-constant checks for general-solution questions;
- constant forms such as `C`, `c`, `C1`, `c1`, `C_1`, `任意常数`, and `常数项`;
- initial-value checks that distinguish an unresolved general solution from a resolved special solution such as `C=2` or a final answer with no arbitrary constant.

It does not perform full algebraic equivalence, symbolic ODE substitution, or complete SymPy verification. A high `final_answer` score from this scorer must not repair low `trigger`, `method`, `transformation`, or `process` evidence.

`RuleScorer` is weak evidence only. It recognizes surface signals such as separable, first-order linear, integrating factor, `y=vx`, `p=y'`, and resonance. Its confidence is capped at 0.55 and it cannot independently prove mastery.

### RuleScorer Weak-Signal Boundary

`RuleScorer` is intentionally limited to weak `trigger` and `method` hints. It can notice surface phrases such as "separable", "first-order linear", "integrating factor", `y=vx`, `p=y'`, and "resonance", but it cannot infer a complete solution route from keywords alone.

Rule-only scoring must not:

- create `full_pass`;
- unlock P2 or P3 forward progress;
- fill unobserved `process`, `calculation`, or `final_answer` dimensions;
- override rubric misses or math-validator failures.

This protects against answers that copy the prompt keywords or name a method while solving by an incompatible route.

`LLMScorerStub` is inactive and does not call any external API.

The old scenario/default-score behavior is isolated in `LegacyScenarioScorer` and the compatibility `ScoringEngine` class. It is not part of the default CompositeScoringEngine path.

## False Pass Boundary

A `false_pass` is triggered when the answer appears correct or near-correct on `final_answer`, but the explanation lacks the core evidence needed for mastery. Typical patterns:

- `final_answer` is high while `trigger` or `method` is low or missing;
- `final_answer` is high while `process` is blank or unsupported;
- the answer names a correct-looking method but cannot explain the triggering condition;
- the result matches an alias, but the attempt gives no evidence of transformation or calculation control.

`false_pass` must block strong forward progress. It can allow local review or variants, but it must not unlock comprehensive migration nodes.
