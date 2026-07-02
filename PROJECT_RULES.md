# Project Rules

These rules are non-negotiable for Math150 Coach Engine.

## 1. Never Judge Mastery by Final Answer Alone

A correct final answer can hide weak trigger recognition, copied methods, fragile transformations, or lucky calculation. A wrong final answer can still contain strong concept, method, and process evidence.

## 2. Multi-Dimensional Scoring Is the Core

Every meaningful attempt must be evaluated across the scoring dimensions that the question actually tests:

- concept
- trigger
- method
- transformation
- process
- calculation
- final_answer
- expression
- migration

Missing dimensions are allowed when a question does not test them. They must be represented explicitly as `None`, not silently scored as zero.

## 3. Error Diagnosis Must Be Multi-Label and Weighted

An attempt may contain several causes at once. The engine must support multiple error entries, each with a 0-1 weight, related dimensions, evidence, primary/secondary status, and suggested rollback level.

Primary error threshold: `weight >= 0.7`.

Secondary error threshold: `0.4 <= weight < 0.7`.

## 4. Rollback Must Be Precise

The engine must not roll back to all prerequisites just because an answer is wrong.

Rollback must be selected from the dominant error evidence, the current node, the node rollback policy, and the graph relation. Ordinary calculation errors should usually trigger local review or calculation-focused practice, not full prerequisite rollback.

## 5. Forward Movement Requires Accumulated Evidence

The engine must not unlock all successor nodes because one answer is correct.

Forward movement must depend on multi-dimensional score evidence, severe error count, node pass criteria, and later mastery history. `overall_score` is useful evidence, but it is never sufficient by itself.

## 6. Question Generation Must Be Validated

AI-generated or template-generated questions are candidates only. A question can enter the system only after it passes template constraints, parameter-pool constraints, mathematical verification, answer verification, and metadata checks.

## 7. All Diagnosis Results Must Be Explainable

A diagnosis result must explain:

- why points were deducted;
- which errors were selected;
- why rollback was selected;
- why forward movement was blocked or allowed;
- what the student should do next.

## 8. ODE Is the Phase 0 Sample Chapter

Phase 0 uses ordinary differential equations as the sample chapter. It must not attempt to build the full Mathematics I graph.
