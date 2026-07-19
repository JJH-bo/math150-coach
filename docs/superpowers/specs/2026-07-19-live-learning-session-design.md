# Live Learning Session and Classroom V2 Design

> Date: 2026-07-19  
> Status: approved direction, specification review pending  
> Product: Math150 AI Classroom  
> Primary outcome: make the classroom serve the learner's real learning process and improve learning efficiency

## 1. Product Decision

Math150 AI Classroom will use a stable, GPT-authored baseline classroom plus
session-specific, GPT-authored detailed expansions.

The learner flow is:

```text
lecture material
-> GPT compiles a stable chapter blueprint
-> the website publishes core modules and their baseline learning routes
-> the learner unfolds the baseline route at their own pace
-> the learner returns to the Custom GPT when one exact point is not understood
-> GPT reads the active learning session automatically
-> GPT inserts a newly designed detailed explanation at that exact point
-> the website updates without losing the surrounding model
-> the learner returns to the baseline route after the obstacle is resolved
```

The baseline classroom is fixed for one published blueprint version. Detailed
expansions are dynamic and belong to a learning session unless explicitly
promoted into a later blueprint version.

## 2. Learning Standard

The system is successful only when it supports the learner's actual learning
behavior:

- begin with a small number of high-value core questions or mechanisms;
- let the true structure determine module and step count;
- reveal only the current module and the next useful part of its causal chain;
- preserve already established context while one point is expanded;
- connect intuition, visual behavior, mechanism, formal expression, example,
  counterexample, and compressed model when those representations are useful;
- let the learner state their own model and point to an exact conflict;
- preserve correct parts of that model and repair the smallest broken relation;
- use a different representation when more words would not help;
- return every detailed expansion to the original complete model;
- keep mathematical notation and visual objects readable and synchronized.

The system must not turn these principles into a mandatory visible checklist.
GPT chooses the smallest set of representations needed for the current
knowledge object and obstacle.

## 3. Explicitly Excluded Scope

The V2 classroom does not add:

- diagnosis or error-cause classification;
- mastery, ability, confidence, or performance estimates;
- scoring, grading, pass/fail state, or Boss assessment;
- question-bank training or forced understanding checks;
- review scheduling, forgetting curves, or retrospective notes;
- automated next-module recommendations based on learner behavior;
- learner reports, rankings, points, streaks, or progress analysis.

The session may store only explicit, local learning context required to render
and continue the current scene. It must not infer durable learner attributes.

## 4. Fixed and Dynamic Boundaries

### 4.1 Fixed for a Published Blueprint Version

- course, chapter, and core-module identities;
- the primary question of each core module;
- the baseline causal learning route;
- baseline formulas, examples, counterexamples, and source anchors;
- reusable teaching models and their semantic targets;
- module relations used by the chapter atlas;
- baseline scene layouts and readable fallbacks.

### 4.2 Dynamic for a Learning Session

- selected module and current baseline step;
- which baseline content is currently revealed;
- current visual focus and model state;
- the learner's explicitly stated conflict or question;
- detailed expansion branches created for that conflict;
- nested expansion depth;
- the return path to the parent explanation and baseline route.

Dynamic session changes do not republish or mutate the active blueprint.

## 5. Product Surfaces

### 5.1 Custom GPT

The Custom GPT has two roles.

#### Chapter compiler

When the learner supplies lecture material and asks to create the classroom,
GPT:

1. discovers the Studio workspace;
2. creates or selects the correct chapter blueprint;
3. identifies the smallest set of complete core modules;
4. authors each baseline learning route;
5. creates or reuses meaningful teaching models;
6. validates content, mathematics, visuals, and runtime behavior;
7. publishes the valid blueprint without routine confirmation;
8. returns the learner entry URL.

#### Live learning director

When the learner says `展开` or `继续`, GPT advances only to the next published
baseline step. It does not generate a new explanation for routine progression.

When the learner says `这里没懂`, `我理解成...`, or points to a specific
conflict, GPT:

1. discovers the recommended active learning session;
2. reads its current scene and revision;
3. identifies the exact current knowledge relation;
4. preserves correct surrounding context;
5. designs a local detailed expansion using a better representation;
6. writes a typed scene patch with matching model commands;
7. verifies the resulting scene;
8. reports that the classroom has been updated.

GPT never asks the learner for a package ID, module ID, content ID, session ID,
or classroom URL when the Studio can discover it.

### 5.2 Classroom Website

The website provides:

- the course and chapter atlas;
- one core-module destination per complete core module;
- the stable baseline learning route;
- learner-paced reveal of baseline steps;
- one active learning scene rather than a full static article dump;
- a persistent, synchronized visual workspace when useful;
- session-specific detailed expansions inserted at the exact parent point;
- nested expansion and return without losing context;
- automatic updates after GPT writes a scene patch;
- restoration after refresh or temporary disconnection.

The website does not call or embed the Custom GPT. The Custom GPT calls Studio
Actions. The page receives resulting session updates from the project backend.

### 5.3 Studio

Studio remains the private, high-authority API used by the Custom GPT. It gains
blueprint V2 authoring, session discovery, scene patching, session verification,
and model-scene binding capabilities.

## 6. Domain Model

### 6.1 ChapterBlueprintV2

```text
ChapterBlueprintV2
├─ identity and source metadata
├─ courses
│  └─ chapters
│     ├─ core modules
│     └─ module relations
├─ typed baseline learning scenes
├─ teaching model references
├─ assets and source anchors
└─ immutable release metadata
```

`ChapterBlueprintV2` replaces `classroom_package_v1` as the authoring and
published learning contract. V1 remains read-only during migration and is
removed from the product path after all active packages are migrated.

### 6.2 CoreModuleV2

A core module is one complete knowledge object organized around one primary
question or mechanism.

It contains:

- `id`;
- `title`;
- `primary_question`;
- `summary`;
- `baseline_route`;
- optional `visual_workspace`;
- source anchors.

It has no fixed number of steps and no performance state.

### 6.3 BaselineLearningStep

A baseline step is one meaningful movement in the module's causal explanation.
It is not a task, checkpoint, node, or planet.

```text
BaselineLearningStep
├─ id
├─ purpose
├─ scene nodes
├─ formula focus
├─ visual commands
├─ return model contribution
└─ optional next step
```

Steps are revealed at the learner's pace. The published content is stable.

### 6.4 Typed Scene Nodes

V2 removes arbitrary `ContentBlock.data`. Scene nodes use a discriminated union
with a schema for each kind.

Initial node kinds:

- `explanation`;
- `mechanism_step`;
- `core_conclusion`;
- `formula_with_meaning`;
- `derivation`;
- `worked_example`;
- `counterexample`;
- `comparison`;
- `code_walkthrough`;
- `table`;
- `matrix`;
- `annotated_figure`;
- `visual_focus`;
- `model_control`;
- `bridge_explanation`;
- `group`.

Each node has a stable ID and declares enough structure for deterministic
rendering. Node schemas describe presentation data, not a mandatory teaching
sequence.

### 6.5 LearningSession

```text
LearningSession
├─ session_id
├─ access token hash
├─ blueprint_id and immutable version
├─ course, chapter, and module identity
├─ revision
├─ current baseline step
├─ revealed baseline step IDs
├─ current scene
├─ expansion stack
├─ visual workspace state
├─ explicit local learning context
├─ created_at
└─ updated_at
```

`explicit_local_learning_context` may contain only the learner's current,
explicitly supplied statement or question and its scene target. It may not
contain inferred diagnosis, mastery, or ability fields.

### 6.6 Scene

```text
Scene
├─ central question
├─ active relation or mechanism
├─ stable context nodes
├─ active explanation nodes
├─ formula focus
├─ visual state
├─ parent scene reference
└─ return target
```

The scene is the complete renderable learning state for one moment. It keeps
the surrounding model visible while one relation is expanded.

### 6.7 DetailedExpansion

A detailed expansion is generated after a learner explicitly reports an
obstacle. It contains:

- parent scene and target node;
- the learner's explicit question or model conflict;
- correct context that must remain unchanged;
- the one relation being repaired;
- selected representation strategy;
- inserted typed scene nodes;
- visual/model state changes;
- return explanation that reconnects the branch to the parent model.

Detailed expansions are session-scoped by default. They are not pre-authored
recursive text branches.

### 6.8 ScenePatch

A scene patch is an ordered, typed set of local operations.

Initial operations:

- `set_focus`;
- `insert_before`;
- `insert_after`;
- `replace_node`;
- `show_node`;
- `hide_node`;
- `set_formula_focus`;
- `set_model_state`;
- `perform_model_action`;
- `push_expansion`;
- `return_to_parent`;
- `recompose_model`.

Every patch includes:

- `expected_revision`;
- `idempotency_key`;
- target session and scene;
- a concise pedagogical intent;
- typed operations;
- optional verification scenario.

The service applies the patch atomically or rejects it without partial changes.

## 7. Data Flow

### 7.1 Baseline Classroom Creation

```text
lecture
-> workspace discovery
-> blueprint draft
-> typed validation
-> math rendering verification
-> model preview and behavior verification
-> complete classroom preview
-> publish immutable blueprint
-> learner URL
```

Publishing requires objective checks. It does not require routine learner
confirmation.

### 7.2 Starting Learning

1. GPT or the classroom creates a session pinned to an immutable blueprint.
2. The session begins at a selected module and its first baseline scene.
3. The website opens an opaque learner URL or session cookie.
4. The website loads the current snapshot and subscribes to session events.
5. The learner reveals baseline steps at their own pace.

### 7.3 Asking for Detailed Expansion

1. The learner returns to the same Custom GPT conversation and identifies the
   obstacle in natural language.
2. GPT calls session discovery and selects the recommended active session.
3. GPT reads the current scene, current baseline step, expansion stack, and
   visual state.
4. GPT designs the smallest useful replacement representation.
5. GPT submits one `ScenePatch`.
6. The backend validates and applies the patch in one transaction.
7. The backend emits `scene.updated`.
8. The website applies the new scene and preserves the learner's position.

The learner never supplies internal identifiers.

### 7.4 Returning to the Baseline Route

Closing or completing a detailed expansion restores its parent scene and model
state. The session remains at the same baseline step. The learner then reveals
the next baseline step when ready.

## 8. API Design

### 8.1 Studio Blueprint Operations

```text
GET   /api/studio/v2/capabilities
GET   /api/studio/v2/workspace
POST  /api/studio/v2/blueprint-drafts
GET   /api/studio/v2/blueprint-drafts/{draft_id}
PATCH /api/studio/v2/blueprint-drafts/{draft_id}
POST  /api/studio/v2/blueprint-drafts/{draft_id}/validate
POST  /api/studio/v2/blueprint-drafts/{draft_id}/previews
POST  /api/studio/v2/blueprint-drafts/{draft_id}/publish
```

V2 adds object-level patching so GPT does not resend a complete chapter for one
local repair.

### 8.2 Studio Session Operations

```text
GET   /api/studio/v2/learning-sessions
POST  /api/studio/v2/learning-sessions
GET   /api/studio/v2/learning-sessions/{session_id}
POST  /api/studio/v2/learning-sessions/{session_id}/reveal
PATCH /api/studio/v2/learning-sessions/{session_id}/scene
POST  /api/studio/v2/learning-sessions/{session_id}/model-commands
POST  /api/studio/v2/learning-sessions/{session_id}/return
POST  /api/studio/v2/learning-sessions/{session_id}/verify
```

Session discovery returns exactly one recommended active target when a clear
most-recent session exists. It explains the selection basis.

### 8.3 Learner Runtime Operations

```text
GET  /api/classroom/v2/catalog
GET  /api/classroom/v2/blueprints/{blueprint_id}
POST /api/classroom/v2/learning-sessions
GET  /api/classroom/v2/learning-sessions/{session_id}
POST /api/classroom/v2/learning-sessions/{session_id}/reveal
POST /api/classroom/v2/learning-sessions/{session_id}/interactions
GET  /api/classroom/v2/learning-sessions/{session_id}/events
```

The event endpoint uses Server-Sent Events. It supports replay after the last
received revision and periodic keepalive events.

## 9. Storage

Published blueprints and registered teaching models remain immutable artifacts.

Learning sessions and their event stream use SQLite in WAL mode for the first
production version:

- `learning_sessions` stores the current snapshot and revision;
- `learning_session_events` stores accepted patches and learner interactions;
- each patch is applied in one transaction;
- idempotency keys prevent duplicate writes;
- expected revision prevents lost updates;
- event retention is bounded but sufficient to reconnect active sessions;
- the Railway persistent volume stores the database.

This design supports the current single-instance deployment. A future
multi-instance deployment migrates session tables to PostgreSQL without
changing the API contracts.

## 10. Frontend Runtime

The current long-document `renderModule()` path is replaced by:

- `session-client` for snapshots, actions, and SSE;
- `scene-store-v2` for a safe local continuity cache;
- `scene-renderer` for typed scene nodes;
- `scene-patch-runtime` for deterministic local updates;
- `visual-workspace-controller` for synchronized model state;
- `math-renderer` using KaTeX or MathJax.

The classroom stage contains:

1. a compact module and central-question header;
2. the active causal explanation;
3. a persistent visual workspace when it improves understanding;
4. a compressed model showing how the current point fits the whole;
5. baseline reveal and expansion-return controls.

The cosmic background remains a navigation identity and must not reduce
content, formula, axis, label, or control readability.

## 11. Teaching Model V2 Contract

A model cannot be registered merely because it implements lifecycle methods.
Model verification must establish:

- the mounted root contains visible output;
- screenshots contain non-empty visual regions;
- declared state changes create observable visual changes;
- semantic targets can be focused or highlighted;
- labels, axes, formulas, and controls meet contrast and overflow rules;
- scene commands and model commands remain synchronized;
- reset and parent return restore the expected state;
- desktop and mobile viewports remain usable;
- there are no uncaught errors or retained runtime resources.

No-op teaching models fail verification.

## 12. Mathematics and Content Rendering

V2 uses a real mathematics renderer and removes the handwritten LaTeX parser.

Required support:

- inline and display mathematics;
- nested fractions and radicals;
- sums, products, limits, and integrals;
- matrices and piecewise functions;
- aligned multi-step derivations;
- Chinese text around and within formula explanations;
- symbol-level IDs and highlighting;
- graceful readable fallback if rendering fails.

Every scene-node kind has an end-to-end fixture produced through the same
schema used by GPT Actions.

## 13. Quality Gates

### 13.1 Blueprint Validation

Validation checks:

- typed node schemas;
- stable and unique IDs;
- valid module relations and source anchors;
- complete baseline route references;
- formula parsing and rendering;
- model version and semantic target references;
- scene/model command compatibility;
- absence of forbidden learner-analysis fields.

### 13.2 Full Classroom Preview

Preview renders the actual package in the actual classroom runtime, not an
isolated structural projection.

It records:

- desktop and mobile screenshots;
- empty, clipped, overlapping, or invisible regions;
- formula rendering errors;
- content-to-model state transitions;
- baseline reveal behavior;
- nested expansion and return behavior;
- refresh and reconnect restoration;
- console and runtime errors.

### 13.3 Learning-Flow Evaluation Fixtures

The project retains representative learning-flow fixtures based on real
learning patterns:

- Fourier coefficient frequency detection;
- geometric-series finite-sum derivation;
- strong connectivity versus complete graphs;
- critical-path non-connectable edge choices;
- Floyd staged matrix updates.

Fixtures test whether the system can preserve a correct partial model, repair
one relation using another representation, and return to the full model. They
do not grade the learner.

## 14. Reliability and Security

- Studio writes require the private Studio Bearer credential.
- Learner JavaScript never receives the Studio credential.
- Learner sessions use opaque random access tokens stored as hashes.
- Mutable operations require idempotency keys and expected revisions.
- Session patches are size- and depth-bounded.
- Unsupported patch operations fail before any state changes.
- SSE reconnect uses the last accepted event or revision.
- The most recent valid snapshot remains readable during a model or connection
  failure.
- Published blueprint releases remain immutable and rollback-capable.
- Session failure never mutates the active blueprint.

## 15. Migration

Migration proceeds without restoring legacy training systems.

1. Add V2 domain types and session infrastructure beside V1.
2. Add typed scene rendering and real mathematics rendering.
3. Add session APIs and SSE updates.
4. Add model V2 verification.
5. Convert the active Fourier classroom into a V2 blueprint.
6. Verify the complete baseline and dynamic expansion flow in production.
7. Convert remaining active classrooms.
8. Remove V1 from learner routing after migration evidence passes.
9. Retain V1 release artifacts only for rollback history until no longer needed.

The old Boss and node progression models are not migrated. Singularity or
stellar visual assets may be reused only when they serve navigation or a
specific explanation.

## 16. Acceptance Criteria

The change is accepted only when all of the following are true:

1. GPT can receive lecture material and publish a chapter with the correct
   number of complete core modules without asking for internal identifiers.
2. A learner can enter one module and reveal its fixed baseline learning route
   one useful step at a time.
3. The baseline route is stable across sessions for the same blueprint version.
4. The learner can return to GPT, say only `这里没懂` plus natural-language
   context, and GPT can discover the active session and exact current point.
5. GPT can insert a new detailed expansion at that point without republishing
   or rewriting the complete classroom.
6. The website receives the update without refresh and preserves the parent
   context, formula focus, visual state, and return path.
7. A second detailed expansion can be nested under the first.
8. Returning from an expansion restores the expected parent scene and then the
   baseline route.
9. Complex mathematics renders without raw LaTeX or mangled structure.
10. A registered teaching model cannot be empty and demonstrates meaningful
    state changes in preview.
11. Actual GPT-shaped production payloads render without blank components.
12. Desktop and mobile classroom screenshots are readable and free of
    structural blank regions.
13. No learner diagnosis, scoring, review, mastery, Boss, or training system is
    introduced.

Passing structural unit tests alone is not sufficient evidence. Acceptance
requires complete browser evidence for the real published classroom and one
real GPT-driven detailed expansion cycle.
