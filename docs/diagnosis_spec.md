# Diagnosis Spec

This document defines the long-term diagnosis architecture for Math150 Coach.
Diagnosis should behave like a math coach: it explains the likely cause, the
evidence, the uncertainty, and the next repair action. It must not become a
simple low-score-to-error-label table.

## Engine Boundary

`DiagnosisEngine` owns:

- root cause analysis;
- primary, secondary, derived, downstream, weak, and evidence-gap attribution;
- evidence collection and learner-safe explanation;
- recommended repair action type.

It does not own movement:

- `RollbackEngine` remains the only rollback decision maker.
- `ForwardEngine` remains the only forward decision maker.
- API/UI only call and present the result.

## Error Vector

An `ErrorVector` contains weighted `ErrorItem` entries:

- `error_type`
- `weight`: 0-1
- `related_dimensions`
- `evidence`
- `is_primary`
- `suggested_rollback_level`

Default bands:

- primary error: `weight >= 0.7`
- secondary error: `0.4 <= weight < 0.7`
- weak signal: `weight < 0.4`

These bands are not enough to choose root cause. Root cause is selected by
causal policy, evidence strength, and graph semantics.

## Error Types

- `concept_gap`: concept object, definition, or condition is unstable.
- `trigger_failure`: the learner cannot identify the problem feature that points
  to the method.
- `method_error`: method selection or method justification is wrong.
- `transformation_error`: standard form, substitution, or equivalence conversion fails.
- `process_gap`: solution chain has unsupported jumps or missing steps.
- `calculation_error`: execution error after the method route is valid.
- `condition_miss`: initial value, domain, nonzero condition, or other stated condition is missed.
- `formula_memory_error`: a remembered formula or standard form is wrong.
- `knowledge_confusion`: neighboring knowledge points are mixed up.
- `expression_weakness`: mathematical writing is imprecise but the idea is traceable.
- `migration_failure`: standard case works but variant transfer fails.
- `synthesis_failure`: compound problem is not decomposed into a solvable path.

## Diagnostic Roles

The final diagnosis has more roles than old primary/secondary/derived lists:

- `root_cause`: earliest supported cause in the solution path.
- `primary_errors`: high-weight current blockers.
- `secondary_errors`: meaningful non-root errors.
- `derived_errors`: errors causally downstream of the root.
- `downstream_result`: final-answer failure caused by an earlier root; it should
  not become root by itself.
- `weak_signal`: surface or low-strength signal that is not enough for strong diagnosis.
- `evidence_gap`: proof of mastery is missing, but no strong root can be asserted yet.

Compatibility: `derived_result` can still appear in the internal error chain for
older tests and consumers. New consumers should read `downstream_result_errors`.

## Evidence Bundle

`DiagnosisTrace.evidence_bundle` organizes multi-source evidence. It may include:

- `active_scorers`
- `score_vector`
- `dimension_sources`
- `rubric_required_missed`
- `rubric_optional_missed`
- `math_validator_flags`
- `weak_rule_signal`
- `response_steps`
- `self_explanation`
- `hidden_ability_evidence`
- `graph_edge_semantics`

Related trace fields:

- `response_evidence`: whether response steps or self explanation are present.
- `graph_edge_semantics`: typed graph edges relevant to the current node.
- `evidence_gaps`: missing proof signals such as surface keywords without structure.
- `logic_ability_signals`, `logic_contradictions`, and `logic_weak_signals`:
  hidden graph evidence used by the diagnosis policy.

The bundle is evidence organization. It is not a movement decision.

## Causal Policy

Root cause is selected by causal priority plus evidence gates:

- trigger failure can derive method, transformation, and process errors;
- method error can derive process, calculation, and final answer errors;
- transformation error can derive calculation and final answer errors;
- calculation error should not roll back to concept or method when the earlier route is supported;
- missed constant `C` is completeness/calculation/final-answer evidence, not method error;
- missed initial value is `condition_miss`;
- imprecise but traceable expression is `expression_weakness`;
- keyword-only responses should become `need_more_evidence`, not strong root cause;
- optional-only misses must not create a strong root cause;
- RuleScorer-only evidence must stay weak;
- high final answer cannot hide missing trigger, method, transformation, or condition evidence;
- rubric/math-validator conflict cannot be erased by a final-answer score alone;
- knowledge confusion should be supported by comparison/guard context;
- synthesis failure should be supported by compound-node or boss/synthesis context.

## Boundary Cases

- Correct final answer without trigger/method/process explanation: `false_pass`.
- Correct process with local arithmetic/integration slip: `calculation_error`, no concept rollback.
- Concept mostly understood but imprecise: `partial_pass` / concept-imprecise state.
- Wrong trigger causing wrong method: root is `trigger_failure`.
- Wrong method causing wrong calculation: root is `method_error`.
- Wrong transformation causing wrong final answer: root is `transformation_error`.
- Missing `C`: do not call it `method_error`.
- Missing initial condition: `condition_miss`.
- Weak but traceable writing: `expression_weakness`.
- Only keywords, no structure: `need_more_evidence`.
- Multiple optional misses: weak evidence only.

## Learner Explanation

`explanation` is debug text. It may include enum values, policy hits, evidence
bundle keys, and error-chain internals.

`learner_explanation` is learner-facing Chinese coaching text. It must include:

- root-cause judgment;
- why the issue is not another common error;
- whether forward movement is allowed;
- the next repair action.

It must not be raw enum concatenation, debug text, or an English template.

## Current Boundaries

Still not implemented:

- real LLM diagnosis;
- complete symbolic ODE verification;
- full Mathematics I graph;
- database-backed longitudinal diagnosis history;
- frontend redesign;
- automatic authoring of new graph content.
