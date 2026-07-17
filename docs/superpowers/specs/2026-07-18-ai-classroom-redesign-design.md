# AI Classroom Route Two Redesign

> Date: 2026-07-18  
> Status: approved direction, implementation pending  
> Decision: build a new AI Classroom product spine inside the existing repository  
> Product priority: improve the learner's experience while learning new knowledge

## 1. Product Goal

Transform Math150 Coach from a diagnostic training product into an AI-generated interactive classroom.

The new product must improve on a linear chat window by letting the learner:

- see the structure of a chapter before and during learning;
- enter one complete core module without seeing a checklist of tiny tasks;
- keep formulas close to their explanations;
- follow long derivations without repeatedly scrolling to recover context;
- keep a mathematical or algorithmic model visible while the explanation advances;
- open one or more levels of detailed explanation in place;
- inspect examples, comparisons, code, diagrams, and model states together;
- return to the same classroom scene without reconstructing it manually.

The Custom GPT is the classroom author. The project is the authoring environment, model workshop, preview system, release system, and learner-facing runtime.

## 2. Explicitly Removed Product Scope

The new product does not include:

- error-cause diagnosis or learner error attribution;
- scoring, grading, mastery estimates, or ability profiles;
- review scheduling, forgetting curves, or retrospective review systems;
- question-bank training, variants, wrong-answer collections, or answer analytics;
- next-step recommendation based on learner performance;
- learning reports, progress analysis, ranking, points, or streaks;
- Boss assessment, challenge gates, or pass/fail progression;
- any system whose primary purpose is analyzing the learner after learning.

Existing code for these concerns may remain temporarily during migration, but it is not a dependency of the new architecture, must not shape the new domain model, and receives no feature expansion.

Versioning, diffs, audit records, publishing, and rollback exist only to make GPT classroom production reliable. They are not learner-analysis features.

## 3. Chosen Migration Route

The repository keeps infrastructure and visual assets that directly improve the classroom, while a separate product spine replaces the challenge runtime.

```text
Existing repository
├─ reusable infrastructure and cosmic rendering
├─ legacy challenge and diagnosis code, disconnected during migration
└─ new AI Classroom spine
   ├─ Classroom Studio API
   ├─ Classroom package domain
   ├─ Teaching model workshop and registry
   ├─ Preview and validation system
   ├─ Release and rollback system
   └─ Learner classroom runtime
```

The new runtime must not call the legacy `ChallengeEngine`, scoring engines, diagnosis engines, mastery state, question banks, or challenge progress store.

## 4. System Boundaries

### 4.1 Classroom Studio

The Studio is the high-authority surface used by the Custom GPT to:

- discover available capabilities and schemas;
- create and edit classroom content;
- upload and reuse assets;
- query and control registered teaching models;
- read, create, modify, test, and register teaching-model code;
- bind classroom content to model states and actions;
- render real previews;
- inspect visual, runtime, mathematical, and performance feedback;
- create versions and compare them;
- publish classroom packages;
- roll back published classroom packages.

The Studio does not make teaching decisions on behalf of GPT. It provides expressive objects, powerful tools, validation, and observable results.

Suggested API namespace:

```text
/api/studio/v1
```

### 4.2 Classroom Runtime

The Runtime is the learner-facing surface. It:

- lists published courses, chapters, and modules;
- loads one immutable published classroom package version;
- renders the chapter universe and core-module entry points;
- renders classroom content and teaching models;
- executes declared content-to-model bindings;
- saves only the minimal state needed to restore the classroom scene.

Suggested API namespace:

```text
/api/classroom/v1
```

The Runtime must not score, diagnose, rank, recommend, or infer mastery.

### 4.3 Teaching Model Workshop

The Workshop provides two equally supported paths:

1. configure and reuse an existing registered model through high-level teaching controls;
2. develop a new model when the registry cannot express the intended mechanism.

The user has explicitly authorized GPT to read, create, and modify model code and to register new models. The environment must therefore provide editing, testing, preview, diff, audit, and recovery tools strong enough to support that authority.

### 4.4 Preview and Quality Environment

Preview is a real runtime rendering, not a structural JSON projection.

Every preview artifact must identify:

- classroom package and version;
- chapter and module;
- content segment or block;
- model definition, code version, preset, and state;
- viewport and quality profile;
- source revision used to generate the artifact.

## 5. Classroom Content Model

The new top-level artifact is `ClassroomPackage`.

```text
ClassroomPackage
├─ package metadata
├─ courses
│  └─ chapters
│     ├─ core modules
│     ├─ module relations
│     └─ chapter synthesis content, optional
├─ model definitions and presets
├─ assets and source anchors
└─ release metadata
```

### 5.1 CoreModule

A `CoreModule` is one complete knowledge object and one primary visible destination in the learning universe.

It is not required to contain a fixed number of stages. It does not become mastered, passed, failed, locked by performance, or broken into visible MicroNodes.

It may contain:

- uninterrupted explanation;
- a small or large ordered learning sequence;
- formulas and derivations;
- examples and comparisons;
- code and algorithm state;
- local or full-screen teaching models;
- recursive detailed explanations;
- optional chapter-level relationships.

### 5.2 LearningSegment

A `LearningSegment` is an authoring and layout unit inside a module. It is not a task or progression node.

GPT may use zero, one, or many segments. Segments may be reordered, nested only where the selected presentation requires it, or omitted in favor of continuous content.

### 5.3 ContentBlock

Content blocks are composable presentation primitives. The first stable set must support:

- prose;
- heading;
- callout or core conclusion;
- inline and display mathematics;
- formula with adjacent explanation;
- step-by-step derivation;
- concept comparison;
- worked example;
- step-by-step solution;
- code with synchronized line explanation;
- table and matrix;
- image or annotated figure;
- interactive two-dimensional model;
- interactive three-dimensional model;
- algorithm and data-structure model;
- local detailed expansion trigger;
- full-screen model observation;
- flexible grouped layout.

Blocks carry stable IDs so GPT, previews, bindings, validation errors, and visual inspection can refer to the same object.

### 5.4 DetailBranch

A `DetailBranch` is an optional recursive expansion attached to a segment, block, derivation step, formula symbol, code line, or model object.

Opening a detail branch must not navigate away from the current learning context. Closing it restores the previous content and model state.

There is no fixed depth, but the renderer may use practical depth and payload limits to preserve readability and performance. Those limits must be discoverable by GPT.

### 5.5 ModuleRelation

Relations exist to explain the knowledge structure and support navigation, not to enforce performance gates.

Initial relation semantics:

- prerequisite context;
- conceptual dependency;
- contrast;
- analogy;
- derivation;
- application;
- shared model;
- chapter synthesis.

Relations may influence map layout and explanatory links. They never create pass/fail locks.

### 5.6 SourceAnchor

Important blocks may reference:

- source asset ID;
- filename;
- page or slide;
- chapter or section;
- quoted or hashed source span;
- authoring note.

Source anchors are selective. The system does not require a citation on every sentence.

## 6. Teaching Model Environment

### 6.1 Model Registry

Every registered teaching model exposes self-describing metadata:

- stable model ID and version;
- teaching purpose and supported domains;
- parameters, types, ranges, and defaults;
- named high-level states;
- supported actions and transitions;
- bindable symbols and visual objects;
- supported interactions;
- supported viewport modes;
- expected assets;
- quality and device constraints;
- lifecycle hooks;
- test and preview scenarios;
- compatibility information.

High-level teaching controls are the default. Examples:

- show the seventh Fourier partial sum;
- highlight `b_3`;
- zoom to a discontinuity;
- expose the tangent construction;
- advance one algorithm step;
- focus one matrix cell update.

GPT may use lower-level code development when the registered vocabulary cannot express a new teaching model.

### 6.2 Model Instances and Presets

A classroom package references model definitions by immutable version and creates configured instances.

An instance includes:

- instance ID;
- model definition and version;
- initial preset;
- parameter overrides;
- initial state;
- viewport placement;
- allowed learner interactions;
- quality profile;
- fallback presentation.

Presets are reusable and versioned independently from classroom content.

### 6.3 Model Lifecycle

The runtime provides explicit lifecycle behavior:

```text
create -> mount -> update -> pause/resume -> reset -> unmount -> dispose
```

The environment must detect:

- leaked animation loops;
- undisposed geometries, materials, textures, and event listeners;
- duplicate mounts;
- stale model instances after module changes;
- WebGL context failures;
- conflicts between model input, classroom scrolling, and universe flight controls.

### 6.4 New Model Development

GPT receives a controlled model-development workspace with:

- relevant source-tree discovery and file reading;
- file creation and modification;
- model scaffold and registry manifest generation;
- mathematical logic tests;
- interaction tests;
- lifecycle and disposal tests;
- syntax, type, and build checks where applicable;
- real preview generation;
- console, WebGL, asset, and performance feedback;
- source, behavior, and visual diffs;
- registration and release operations;
- rollback to a previous registered version.

Model registration requires the declared checks to pass, but GPT has authority to complete registration and release without a separate human publishing role.

## 7. Content-to-Model Binding

A binding connects a stable content target to a model target.

Supported triggers include:

- segment enters or leaves the active reading region;
- block becomes active;
- scroll progress crosses a declared range;
- formula or symbol is clicked, focused, or hovered;
- detail branch opens or closes;
- example step changes;
- code line changes;
- learner changes an allowed parameter;
- explicit classroom control is activated.

Supported effects include:

- set model state;
- animate between states;
- update parameters;
- highlight or dim symbols and objects;
- change camera target;
- play, pause, reset, or step;
- open local or full-screen viewport;
- save a state snapshot;
- restore the previous state.

Bindings must declare return behavior so temporary detail or highlight states never strand the model in an unrelated state.

The validator checks target existence, version compatibility, legal parameters, reachable states, missing return behavior, conflicting simultaneous bindings, and replay consistency.

## 8. Learner Experience

### 8.1 Navigation

The cosmic environment has three learner-facing levels:

```text
course universe -> chapter region -> core module destination
```

Only complete core modules are primary destinations. Decorative celestial objects must not look clickable.

The former Boss concept is removed. Existing singularity art may be reused only as a non-assessment spatial landmark, transition, or explanatory phenomenon when it improves learning.

### 8.2 Classroom Stage

Entering a core module opens a classroom stage rather than a question pod.

The stage must support:

- readable content as the primary layer;
- a persistent model viewport when a model is relevant;
- adjacent formula and explanation layouts;
- stable context during long derivations;
- local detail expansion without losing the current position;
- smooth transitions between model states;
- full-screen observation without destroying reading state;
- clear return to the chapter universe.

The cosmic background remains present but subordinate. During reading:

- nonessential background motion reduces;
- Bloom cannot damage text, curves, axes, or labels;
- contrast follows classroom readability requirements;
- model interaction temporarily owns conflicting inputs;
- reduced-motion and balanced-quality modes remain available.

### 8.3 Minimal Session Snapshot

The only learner state stored by the new runtime is scene continuity:

- selected course, chapter, and module;
- current content location;
- open detail branches;
- active model state and allowed parameter values;
- viewport mode and camera state where useful.

It must not contain mastery, scores, ability estimates, failure counts, recommendations, review dates, or inferred learner attributes.

## 9. Studio Capability Surface

The exact route names may change during implementation, but GPT must receive stable structured operations in these capability groups.

### 9.1 Discovery

- describe Studio capabilities and limits;
- fetch content schemas and examples;
- list content components;
- list registered models and versions;
- inspect model controls, states, bindings, assets, and compatibility;
- inspect validation and preview profiles.

### 9.2 Classroom Authoring

- create and read drafts;
- create, update, reorder, and delete courses, chapters, modules, segments, blocks, and detail branches;
- attach source anchors;
- upload, inspect, reuse, replace, and delete draft assets;
- create and modify model instances, presets, and bindings;
- save large classrooms in chunks;
- resume interrupted authoring;
- protect retries with idempotency keys;
- patch individual objects without resending the full package.

### 9.3 Model Development

- inspect relevant model code and manifests;
- create and modify model code;
- run targeted tests and build checks;
- generate real previews;
- inspect errors and performance;
- compare model source and rendered behavior;
- register, publish, and roll back model versions.

### 9.4 Preview and Validation

- validate structure and references;
- validate LaTeX and math rendering;
- validate functions, domains, special points, and numerical results;
- detect `NaN`, `Infinity`, and inconsistent labels or model values;
- validate bindings and replay;
- render selected modules, blocks, branches, model states, and viewports;
- capture desktop and mobile screenshots;
- capture short interaction recordings for stateful behavior;
- report console, WebGL, resource, layout, contrast, FPS, memory, and disposal issues;
- map preview objects back to source objects;
- compare before and after structure, source, behavior, and visuals.

### 9.5 Release

- create immutable candidate versions;
- inspect package and model dependency diffs;
- validate a complete release;
- publish a classroom version;
- confirm the active published version;
- roll back to a previous complete version;
- confirm runtime recovery after rollback.

GPT is authorized to perform publish and rollback operations. Reliability is enforced through expected-version checks, immutable release artifacts, validation, atomic activation, and recoverable history rather than a mandatory human approval role.

### 9.6 Custom GPT Action Access

The Studio capability surface must be callable from the Custom GPT through an Action-compatible OpenAPI description.

The Action environment provides:

- one discoverable OpenAPI contract with stable operation IDs;
- concise capability descriptions and request examples;
- project-owned authentication for the Custom GPT;
- public HTTPS reachability for the configured Action;
- bounded, structured responses that do not depend on reading server logs;
- chunked content and asset operations for large classroom packages;
- resumable jobs for preview, build, test, publish, and rollback work that may exceed one request;
- job and artifact lookup after a timeout or interrupted conversation;
- idempotency and expected-revision fields on mutable operations;
- explicit receipts containing object IDs, versions, hashes, and next valid actions.

The project does not need an OpenAI API key to call the Custom GPT in this route. The Custom GPT calls the project's Studio API. Its Studio credential is separate from OpenAI credentials and carries the high-authority classroom, model-development, publish, and rollback permissions approved by the user.

## 10. Reliability and Error Handling

All mutable Studio operations use:

- stable object IDs;
- schema versions;
- expected revision or content hash;
- idempotency keys;
- structured field-level errors;
- atomic writes at the operation boundary;
- immutable release artifacts;
- explicit success receipts.

Long or expensive operations expose durable job status and artifacts so GPT can recover after a timeout without repeating completed work.

Error results identify:

- error code and severity;
- package version and object path;
- related model, asset, or binding;
- human-readable reason;
- machine-readable context;
- whether retry is safe;
- available logs or preview artifacts.

Automatic repair suggestions are optional. The environment must not silently rewrite classroom content, model logic, or visual design.

## 11. Reuse of Existing Repository Assets

### Reused directly or adapted

- FastAPI application and test infrastructure;
- static frontend mounting and local deployment flow;
- chapter Atlas concepts and chapter registry foundations;
- Three.js scene, camera, flight, particles, lighting, post-processing, and quality profiles;
- singularity and stellar visual assets where they serve navigation or explanation;
- content hashing, validation-report patterns, dry-run concepts, and controlled file writes;
- WebGL fallback and frontend contract-testing patterns.

### Replaced in the product path

- `ChallengeGraph` as the runtime content contract;
- `ChallengeEngine` as the primary orchestrator;
- question and attempt APIs;
- challenge progress and mastery state;
- score, diagnosis, rollback, and forward decisions;
- MacroChallenge and Boss gates;
- training pod UI and answer submission flow.

### Temporarily isolated

Legacy modules remain in source control until the new vertical slice and migration tests pass. They receive no new features and are removed from new routes, navigation, runtime dependencies, documentation, and product language.

Physical deletion happens after:

- the new runtime serves the accepted classroom slice;
- no new code imports legacy decision engines;
- migration tests prove the old path is not required;
- useful generic utilities have been extracted;
- the removal commit can remain separate and reversible.

## 12. Implementation Decomposition

The redesign is implemented as four independently verifiable projects.

### Project A: Classroom Foundation Vertical Slice

Deliver:

- new classroom domain models;
- draft storage and package validation;
- basic Studio discovery and authoring operations;
- basic Classroom read API;
- one authored sample core module;
- prose, math, derivation, comparison, example, detail branch, and model-reference blocks with readable fallback content;
- no dependency on legacy challenge engines.

Success condition: GPT can create and publish one structurally valid module, and the runtime can load it.

### Project B: Teaching Model and Preview Loop

Deliver:

- model registry and self-description;
- model instance lifecycle;
- content-to-model bindings;
- one high-quality two-dimensional teaching model;
- one representative three-dimensional or algorithmic model path;
- real preview artifacts;
- math, visual, runtime, and performance validation;
- model development and registration workflow.

Success condition: GPT can author, preview, debug, publish, and replay a synchronized content-and-model module.

### Project C: Cosmic Classroom Runtime

Deliver:

- chapter universe and core-module navigation using the new APIs;
- classroom stage;
- persistent and full-screen model viewports;
- local recursive detail expansion;
- minimal session snapshots;
- learning-mode visual and input behavior;
- removal of challenge language and controls from the learner path.

Success condition: the accepted sample module is materially clearer and more usable than the same lesson in a linear chat transcript.

### Project D: Cutover and Legacy Removal

Deliver:

- new classroom entry as the default product;
- old challenge routes and UI removed from product navigation;
- new project documentation and run commands;
- deletion or archival of unused training, scoring, diagnosis, review, and Boss code;
- regression checks for retained infrastructure;
- isolated removal commits.

Success condition: the production path contains no learner-analysis or challenge dependency and the repository describes itself as an AI Classroom.

## 13. Testing Strategy

### Domain and API tests

- schema validation and forward-compatible version handling;
- arbitrary module structure without fixed node counts;
- recursive detail branches;
- chunked authoring, idempotent retry, conflict detection, and recovery;
- model registry, version pinning, and preset validation;
- publish and rollback atomicity;
- learner API contains no authoring internals or legacy analysis fields.

### Mathematical tests

- LaTeX parsing and rendering smoke tests;
- deterministic reference cases for model calculations;
- domain and special-point checks;
- `NaN` and `Infinity` guards;
- agreement between text values, formula labels, and model state.

### Model runtime tests

- lifecycle creation and disposal;
- deterministic state replay;
- binding entry, exit, branch, and return behavior;
- input ownership between scrolling, models, and flight;
- WebGL failure and lower-quality fallbacks.

### Browser and visual tests

- real screenshots at accepted desktop and mobile sizes;
- formula readability and adjacent explanation;
- long derivation context retention;
- local detail expansion and restoration;
- persistent model visibility;
- full-screen model entry and return;
- contrast, overflow, console, WebGL, FPS, and resource checks;
- before-and-after review against a linear chat presentation.

Automated tests cannot alone approve classroom quality. The user must review the representative classroom in its real runtime.

## 14. Acceptance Criteria

The redesign is successful when:

1. GPT can independently create, modify, preview, validate, publish, and roll back a classroom package.
2. GPT can reuse registered models and develop a new teaching model when required.
3. One core module remains a coherent knowledge object rather than a task checklist.
4. Formula, explanation, derivation, example, and model states remain visibly connected.
5. Detailed explanation opens locally and restores the prior context.
6. Real preview feedback identifies exact content, model, state, viewport, and version context.
7. The learner runtime stores only the minimum scene-continuity state.
8. The new runtime has no scoring, diagnosis, mastery, review, recommendation, question-bank, or Boss-assessment dependency.
9. Learning clarity takes priority over cosmic visual effects.
10. The representative classroom is demonstrably more usable for learning new knowledge than a linear chat transcript.

## 15. Locked Decisions

- Route Two is selected: a new AI Classroom spine inside the existing repository.
- The product is a learning environment, not a diagnostic training system.
- GPT has model-code development, model registration, classroom publishing, and rollback authority.
- Core modules are complete visible knowledge objects with free internal composition.
- Content-to-model synchronization is a first-class capability.
- Real preview and observable feedback are mandatory.
- The cosmic environment is retained only where it improves learning.
- Legacy analysis and challenge systems do not shape the new product and are removed after safe cutover.
