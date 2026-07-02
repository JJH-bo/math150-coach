# Question Generation Spec

Phase 0 does not implement full question generation. It defines the rule boundary for later phases.

## Generation Sources

A question candidate may come from:

- a typed template;
- a parameter pool;
- a human-authored seed question;
- an AI-assisted draft.

AI-assisted drafts are candidates only and cannot enter the bank directly.

## Required Validation

Before a generated question can be stored, it must pass:

1. Template schema validation.
2. Parameter range validation.
3. Mathematical solvability validation.
4. Answer verification.
5. Metadata validation for node, dimensions, expected errors, and variant policy.
6. Duplicate or near-duplicate checks in later phases.

## ODE Variant Policy Examples

- Change coefficients while preserving separability.
- Change presentation form while preserving first-order linear structure.
- Add or remove an initial condition.
- Switch between distinct and repeated characteristic roots.
- Change nonhomogeneous forcing term while preserving method family.

## Storage Rule

A candidate becomes an official question only after validation. If validation fails, the question must be rejected or returned for repair with a clear reason.
