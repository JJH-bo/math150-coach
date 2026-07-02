# Catalog Spec

Status: Phase 4.3 authoring skeleton frozen by Phase 4.3.1 without changing the formal runtime catalog contract.

Phase 4.0-lite introduces a small server-side YAML question catalog. Its purpose is to stop learner clients from submitting trusted `Question` payloads.

## Layering

Catalog records are split into three Pydantic models:

- `CatalogManifestEntry`: immutable identity, node binding, status, audience, versions, tags, and optional content hash.
- `PublicQuestionView`: learner-visible title, stem, prompt, answer format, step mode, difficulty, public hints, and display assets.
- `TrustedQuestionSpec`: server-only expected answer, aliases, rubric, solution outline, validator config, internal notes, golden refs, and authoring metadata.

`CatalogQuestionRecord` combines those layers and can hydrate a trusted domain `Question` for engine use. Public routes return only `PublicQuestionView`.

## Question Ids

`question_id` is an immutable published artifact id. If prompt, answer key, rubric, or validator behavior changes in a way that affects scoring, publish a new `question_id`.

Phase 4.0-lite accepts only:

- lowercase ASCII letters;
- digits;
- dot, underscore, and hyphen;
- length 8 to 120.

Slash, backslash, colon, question mark, hash, percent, spaces, control characters, uppercase letters, and Unicode confusables are rejected or hidden as not found.

## Visibility

Learner-visible records must satisfy both:

- `status=published`;
- `audience=learner`.

Draft, retired, and internal-only records are invisible to learner routes and return `question_not_found`.

## Repository

`YamlQuestionCatalogRepository`:

- reads with `yaml.safe_load`;
- validates at first load or explicit `validate_catalog()`;
- requires unique `question_id`;
- requires each `node_id` to exist in the current ODE node catalog;
- rejects invalid status, audience, id, or path escape;
- keeps records in memory.

This is not a database and not an authoring workflow.

## Phase 4.3 Authoring Boundary

Phase 4.3 adds an authoring/import workflow skeleton outside the formal runtime catalog.

Authoring-only objects include:

- `AuthoringDraft`;
- `AuthoringStatus`;
- `SourceMetadata`;
- `HumanReviewChecklist`;
- `CatalogValidationReport`.

These objects do not change `CatalogStatus`, `CatalogQuestionRecord`, `YamlQuestionCatalogRepository`, or learner API routing.

The authoring workflow can build an in-memory publish candidate after validation and human review, but it does not write `backend/catalog_data/manifest.yaml`, does not create formal question YAML, and does not register anything with learner routes.

Source metadata is internal-only and must not appear in `PublicQuestionView` or learner responses.

Phase 4.3.1 freezes this boundary: authoring metadata, source metadata, validation reports, and review checklists are not learner API fields and are not runtime catalog service inputs.

The formal catalog remains the only learner runtime source.

Phase 4.4 adds a dry-run import CLI outside the runtime catalog. It can read authoring drafts and produce reports/previews, but it does not write the formal manifest, formal question YAML, or repository default root.

Phase 4.4.1 freezes this boundary. Reports, previews, import manifests, and dry-run candidates are not runtime catalog inputs. The formal catalog remains the only learner runtime source.

## Phase 4.2 Validator

Phase 4.2 adds a lightweight `CatalogValidator`. The repository loads YAML and builds the in-memory index; the validator owns catalog quality rules.

Validation is fail-fast at runtime through `CatalogValidationError`. A fuller `CatalogValidationReport` is deferred to a future authoring/import workflow.

Implemented validation groups:

- identity and manifest consistency;
- public presentation rules;
- trusted scoring rules;
- rubric rules;
- dimension and node consistency;
- public/trusted leak boundary checks;
- version formatting;
- `content_hash` format checks.

Error codes include:

- `catalog_identity_error`
- `catalog_public_layer_error`
- `catalog_trusted_layer_error`
- `catalog_rubric_error`
- `catalog_dimension_error`
- `catalog_leak_error`
- `catalog_version_error`
- `catalog_hash_error`

Phase 4.2.1 freezes this validation contract. Future validation rule changes require tests and documentation updates.

## Public Presentation Rules

Public presentation fields must satisfy:

- `title`, `stem`, and `prompt_markdown` are nonblank after trimming;
- `answer_format` is one of `expression`, `equation`, `free_text`, or `expression_with_reasoning`;
- `response_step_mode` is one of `none`, `optional`, or `required`;
- `difficulty` is one of `basic`, `standard`, or `comprehensive`;
- public prompt and public hints must not leak the exact expected answer when the answer is long enough or has mathematical structure;
- `display_assets` remains `list[dict]`, but it must not contain trusted field names.

## Trusted Scoring Rules

For `published + learner` questions:

- `expected_answer` is required and nonblank;
- `answer_aliases` may be empty, but values must be nonblank and nonduplicate;
- `solution_outline` is required and nonblank;
- `rubric` is required;
- `rubric.items` must include at least one item;
- each item needs a nonblank id, nonblank description, at least one target dimension, positive weight, and nonblank hit/miss evidence;
- rubric item ids must be unique;
- at least one item must be required;
- required items must include `required_keywords` or `expected_patterns`.

Rubric target dimensions must be valid `ScoreDimension` values. They should belong to the node's `core_dimensions`, with limited allowed extensions:

- `calculation`
- `final_answer`
- `expression`

Published learner questions must cover at least one node core dimension.

## Validator Config Boundary

`TrustedQuestionSpec.validator_config` is server-side scoring configuration. It can provide safe validator flags such as `requires_constant: true`.

It must not contain reserved metadata, answer, rubric, override, debug, trace, or raw movement keys, including:

- `catalog_question_id`;
- `question_id`;
- `node_id`;
- `question_version`;
- `rubric_version`;
- `answer_key_version`;
- `expected_answer_aliases`;
- `expected_answer`;
- `answer_aliases`;
- `rubric`;
- `solution_outline`;
- `score_overrides`;
- `evidence_overrides`;
- `manual_override`;
- `scenario`;
- `include_debug`;
- `debug`;
- `scorer_results`;
- `diagnosis_trace`;
- `evidence_sources`;
- `raw_rollback_level`;
- `raw_forward_level`.

This is catalog validation, not learner request logic. It prevents trusted YAML data from overriding reserved domain `Question.metadata` during server-side hydration.

Phase 4.2 also enforces a whitelist. Allowed validator config keys:

- `requires_constant: bool`
- `requires_initial_condition: bool`
- `answer_equivalence_mode: "exact" | "normalized" | "symbolic"`

Unknown keys fail fast.

## Version And Immutability

Version fields must be nonblank and semver-like:

- `1`
- `1.0`
- `1.0.0`

If prompt, expected answer, rubric, or validator config changes in a way that can affect scoring, publish a new `question_id`.

## Content Hash

`content_hash` is still not strongly enforced in Phase 4.2.

If present, it must match:

```text
sha256:<64 lowercase hex chars>
```

Runtime validation does not calculate, compare, or auto-generate hashes.

Phase 4.3 adds an authoring-side utility that can deterministically generate a runtime content hash for a publish candidate. This utility is not called by learner API and does not change the runtime validator's format-only contract.

## Learner Submit Flow

The learner submit flow is fixed:

1. parse `LearnerAttemptRequest`;
2. recursively reject sensitive fields;
3. load a learner-visible published catalog record by `question_id`;
4. load the current node by the record's `node_id`;
5. hydrate trusted domain `Question` server-side;
6. assemble a safe domain `Attempt`;
7. call `LearningOrchestrator.process(question, attempt, node)`;
8. project the result to the learner-safe response.

The learner router does not score, diagnose, roll back, forward, or choose movement by itself.

## Non-Goals

Phase 4.0-lite does not implement:

- database persistence;
- catalog management UI;
- persistent catalog authoring workflow;
- formal catalog import CLI;
- runtime content-hash enforcement;
- user accounts or permissions;
- mastery model;
- review scheduler;
- automatic question generation;
- next-question recommendation.

APP_PROFILE route gating is implemented in Phase 4.1 at the app registration layer. It does not change catalog model behavior.
