# Math150 Coach Project Vision Handoff

Last updated: 2026-07-02

This document is the first file a new assistant or new thread should read before making product, engine, UI, or content decisions for this project.

## One-Sentence Vision

Math150 Coach is a personal, game-like knowledge-network training system for exam math. It should feel like exploring a serious cosmic knowledge map, but underneath it must be a rigorous diagnostic engine that decides what the learner truly understands, where the evidence is weak, when to repair, and when to move forward.

It is not a normal question bank. It is not a checklist planner. It is not a flashcard app. It is a knowledge graph challenge system.

## User Intent

The user is building this for their own long-term exam preparation. They are highly self-driven and do not want the system to feel like a schedule, chore list, or externally imposed plan.

The system may give suggestions, but it should not over-plan the learner's life. The core design goal is to reflect the learner's current mastery state and make the knowledge structure visible, playable, and trustworthy.

The user values:

- Direct technical and product opinions, not empty praise.
- Creative system ideas when they make the project more mature.
- Aesthetic quality, especially iOS-like simplicity, smoothness, and visual polish.
- A knowledge map that feels alive, not a static tree or task list.
- Rigorous diagnosis: the system should understand why an answer is weak, not only whether the final answer is correct.

## What The User Does Not Want

These are product-direction boundaries, not only implementation details. Future threads should treat them as design constraints.

The user does not want:

- A normal question bank, brute-force practice app, flashcard app, or answer-checking tool.
- A rigid study planner, daily task manager, streak-pressure system, leaderboard, or anything that makes learning feel externally assigned.
- A giant visible checklist of tiny nodes. Hidden abilities can be detailed, but the visible map must stay playable, beautiful, and motivating.
- Content expansion that hides weak graph logic. Do not expand chapters just to make the map look bigger.
- Final-answer-only grading.
- A black-box AI judge. LLMs may assist later, but rules, rubrics, validators, and evidence chains must remain decisive.
- A generic dashboard, marketing landing page, rough admin UI, or ordinary web-app surface as the main experience.
- Social competition, productivity pressure, or gamification noise that distracts from mastery.
- Randomized progression or non-deterministic decisions.
- API, frontend, coach-output, or orchestration layers that secretly become new decision engines.
- Database, auth, long-term memory, mastery scheduler, or review-system complexity before explicit approval.
- A map that is beautiful but logically empty, or logically rigorous but visually exhausting.
- A system that over-plans the user's learning. It should reflect current mastery and suggest precise repairs, not command a schedule.

The preferred direction is:

```text
active learner control
rigorous hidden logic
precise diagnosis
beautiful cosmic map experience
deterministic engine behavior
```

## Current Product Shape

The current local product is a browser-based knowledge-network trainer.

Entry point:

```text
http://127.0.0.1:8000/trainer/
```

If port `8000` is occupied during local verification, use another port such as:

```text
http://127.0.0.1:8001/trainer/
```

Start command:

```bash
cd math150-coach
uvicorn app.main:app --app-dir backend --reload
```

The visible experience should eventually be:

1. The learner opens the trainer.
2. They enter a full-screen 2D knowledge map directly.
3. The map looks like a cosmic exploration interface: deep black / star-field / subtle nebula atmosphere, elegant nodes, smooth links, and high-end motion.
4. The learner clicks a node.
5. A training pod opens from the bottom, not a clunky right panel.
6. The learner answers with final answer, response steps, and self-explanation.
7. The system scores, diagnoses, updates node state, and gives a coach-like result.

## Latest Progress: 2026-07-02

The project now has a stronger expandable foundation for the final "logic knowledge network + diagnosis + UI" direction.

Completed in the latest implementation pass:

- Node-detail performance fix:
  - Clicking a map node no longer rebuilds the whole graph DOM/SVG.
  - Selection now updates only node classes, related edges, and the detail panel.
  - Opening the node sheet enters a motion-budget mode that pauses nonessential map, edge, and background animations.
  - Large real-time blur on the modal overlay was reduced to avoid the FPS drop seen when entering a node.

- Ultimate UI direction landed in the real frontend:
  - The UI now uses a darker cosmic exploration style with dynamic star-field atmosphere.
  - The start page, chapter knowledge map, node detail sheet, training pod, coach output, import modal, and atlas view share the same visual language.
  - Semantic graph lines remain visually distinct, but inactive lines are dimmed to reduce clutter.
  - HiddenAbility, CompareGuard, TransferNode, SynthesisNode, and Boss-related logic nodes have clearer visual roles.

- Macro atlas layer added:
  - New course-level atlas endpoint: `GET /api/challenge/v1/atlas`.
  - The atlas shows chapter-level galaxy regions and summary counts only.
  - It does not embed full chapter detail graphs, logic overlays, rubrics, current questions, or trusted fields.
  - Clicking a chapter region starts that chapter through the existing challenge flow.
  - This is the intended direction for future large-scale expansion: macro map first, lazy-load detailed chapter networks only when entered.

- Structured chapter import added:
  - New draft-only endpoint: `POST /api/challenge/v1/authoring/chapter-draft/validate`.
  - The user can paste structured Markdown for MacroNodes, MicroNodes, MacroChallenges, HiddenAbilities, CompareGuards, TransferNodes, SynthesisNodes, semantic edges, and ErrorRepairMap.
  - The importer returns a draft graph, draft logic graph, preview counts, errors, and warnings.
  - It never publishes directly into formal runtime training data.
  - It checks missing repair targets, hidden ability evidence, invalid edge types, unknown references, self-loop edges, node explosion, missing root-cause repair maps, and weak CompareGuard definitions.

- Documentation added:
  - `docs/chapter_import_and_atlas_spec.md` describes the structured Markdown import format, validation gates, runtime boundaries, and atlas layer behavior.

Latest verification:

```bash
python -m pytest -q
# 533 passed

python evals/run_evals.py
# Scoring 30/30 passed
# Diagnosis 25/25 passed
# Movement 12/12 passed

python evals/run_synthetic_diagnosis_lab.py
# Synthetic diagnosis lab 16/16 passed
```

Browser verification completed:

- Trainer page loads.
- Atlas view opens and shows chapter regions.
- Chapter graph loads with the ODE network.
- Node detail panel opens normally.
- Chapter import modal opens normally.
- A 30-node click smoke check kept map node count stable, confirming no DOM growth or graph rebuild leak during node selection.

Known current limits:

- The atlas is structurally ready, but only current small ODE chapter data exists.
- The chapter importer produces draft/preview/validation output, not a formal publish workflow.
- No real LLM is connected.
- No database/history layer is connected.
- Figma has not been used to write a design file yet because a target Figma file URL or plan key is still needed.
- Full Mathematics I and 408 content are not expanded yet.

## Latest Progress Addendum: 2026-07-03

The chapter import pipeline now has a runtime chapter registry boundary.

Implemented:

- New registry module: `backend/app/challenge/chapter_registry.py`.
- New endpoint: `GET /api/challenge/v1/chapters/registry`.
- Atlas now marks whether each chapter region can actually start training through `runtime.can_start`.
- `ChallengeEngine` blocks `start/status/submit/reset` for chapters that are not registered as trainable.
- Frontend Atlas regions with `can_start=false` are disabled instead of launching the training cabin.

Important correction:

```text
chapter files exist != runnable chapter training package
```

A chapter is trainable only when it has:

- valid `challenge_graph.yaml`;
- valid `questions.yaml`;
- question coverage for every MicroNode;
- question coverage for every MacroChallenge / Boss.

Current remaining gap:

- The controlled publish pipeline can produce graph assets.
- It still does not automatically generate complete scoreable/diagnosable `questions.yaml`.
- Therefore the next major content-production block is deterministic training-question package generation with rubrics, error repair maps, variants, and Boss coverage.

## Core Knowledge Graph Design

Important correction:

```text
KnowledgeNode is not MacroChallenge.
KnowledgeNode = MacroNode / BigNode / large knowledge node.
MacroChallenge = a comprehensive validation task bound to a MacroNode.
```

Core graph relationship:

```text
MacroNode contains MicroNodes
MicroNodes mastered -> MacroNode available
MacroChallenge pass -> MacroNode lit/mastered and unlock next nodes
MacroChallenge fail -> root cause maps to one target MicroNode
MicroNode fail -> stay on the same MicroNode, no rollback
```

The system must not treat every concept as just another visible training node. A rigorous knowledge network should have multiple node and edge roles:

- MacroNode / BigNode: visible large knowledge point.
- MicroNode: visible trainable ability branch under a MacroNode.
- MacroChallenge / Boss: comprehensive validation bound to a MacroNode.
- Hidden ability / AtomNode: non-visible or low-visibility fine-grained evidence unit used for diagnosis.
- Guide / comparison node: helps distinguish nearby concepts without becoming a heavy training burden.
- Boss / synthesis node: validates integration, transfer, and multi-step reasoning.
- Edges: must carry meaning, not only visual connection.

The project should avoid becoming a giant list of tiny tasks. The hidden ability layer and semantic edges are how the graph becomes rigorous without overwhelming the learner.

## Current Node Philosophy

The visible map should stay playable:

- Too many visible nodes makes learning feel exhausting.
- Hidden atomic abilities can support diagnosis without crowding the map.
- Repair should target the most useful visible MicroNode or small repair focus, not explode into many tasks.
- Boss / MacroChallenge nodes should test whether the learner can integrate the micro-abilities.

Default MicroNode types:

- concept
- trigger
- method
- transformation
- calculation
- expression

Additional system-level node roles are allowed when they improve logic:

- comparison / guard nodes
- hidden ability nodes
- synthesis / boss nodes
- transfer / migration nodes
- condition-check nodes

But do not add visible node types just for decoration. Every type must improve diagnosis, movement, or learning clarity.

## Scoring Requirements

The system must never judge mastery by final answer alone.

Scoring dimensions:

- concept
- trigger
- method
- transformation
- process
- calculation
- final_answer
- expression
- migration

Every non-null dimension score should have evidence.

Dimensions may be `None` when not tested. This is important: an untested dimension is not the same as a learner omission.

`overall_score()` may exist as a helper, but it must never decide pass state alone.

Current scoring engine structure:

- `CompositeScoringEngine`
- `ManualOverrideScorer`
- `RubricScorer`
- `MathValidatorScorer`
- `RuleScorer`
- `LLMScorerStub`

Key boundaries:

- Manual overrides are only for tests, evals, or imported human grading.
- RuleScorer is weak evidence only.
- MathValidatorScorer is lightweight and does not perform full symbolic ODE verification.
- No real LLM API is currently integrated.
- Scenario-based deterministic scoring must not be used as the default real scoring path.

## Diagnosis Requirements

Diagnosis must answer:

- What is the root cause?
- Which errors are primary?
- Which errors are secondary?
- Which errors are downstream or derived?
- What evidence supports the diagnosis?
- What is the next repair action?
- Why is this not just a calculation mistake or answer mistake?

Current diagnosis output includes:

- root_cause
- primary_errors
- secondary_errors
- derived_errors
- error_chain
- confidence
- evidence_sources
- recommended_actions
- diagnosis_trace
- learner_explanation
- debug explanation

Core diagnosis principle:

```text
Root cause is not simply the highest-weight error.
Root cause is selected by causal precedence and evidence.
```

Examples:

- trigger_failure can cause method_error, transformation_error, and process_gap.
- method_error can cause process_gap, calculation_error, and final answer failure.
- transformation_error can cause process_gap and final answer failure.
- calculation_error can cause final answer failure.
- condition_miss can make an answer incomplete but should not be mislabeled as calculation_error.
- expression_weakness should not become concept_gap when the concept is basically understood.
- rule-only or weak-only evidence must not create a strong root cause.

The learner explanation must be Chinese, coach-like, and not a debug string. It should explain:

- root-cause judgment
- why it is not another common error
- whether the learner can move forward
- next training action

## Movement Requirements

The responsibility boundaries are frozen and must not be blurred:

```text
DiagnosisEngine = diagnosis, evidence, root cause, recommended actions
RollbackEngine = final rollback owner
ForwardEngine = final forward owner
API / UI / trainer = orchestration and display only
```

The API or frontend must not become a fourth decision engine.

Movement principles:

- false_pass must not allow strong forward movement.
- rule-only and no-signal cases must prefer need_more_evidence.
- calculation_error should usually stay local, not rollback to concepts or methods.
- derived errors must not upgrade movement.
- knowledge_confusion and synthesis_failure may suggest broader review, but R4-style behavior must pass rollback safety rules.
- MicroNode failure means stay on that MicroNode; it does not trigger graph rollback.
- MacroChallenge failure maps the root cause to one target MicroNode.

## Ultimate Version Requirements

This section describes the target capability for the "ultimate" logic knowledge network and diagnosis system. It is a product and engine target, not a request to expand the question bank immediately.

The immediate strategy is:

```text
Build ultimate engine capability on the current small ODE slice first.
Do not prove maturity by adding lots of content.
After the engine is stable, future chapters should mainly require graph/data authoring, not core redesign.
```

### Ultimate Knowledge Network

The final knowledge network must be a rigorous ability graph, not a simple tree and not a visible task checklist.

The system must separate:

- visible learning nodes: what the learner sees and plays;
- hidden ability nodes: what the diagnostic engine uses to reason;
- challenge nodes: what validates integrated mastery;
- comparison/guard nodes: what prevents nearby knowledge confusion;
- semantic edges: why one ability supports, blocks, checks, or repairs another.

Required node roles:

- `MacroNode`: a visible large knowledge point, such as separable equations or first-order linear equations.
- `MicroNode`: a visible trainable ability branch under a MacroNode.
- `MacroChallenge`: a Boss-style integrated validation task bound to a MacroNode. It is not the MacroNode itself.
- `HiddenAbility` / `AtomNode`: a fine-grained, usually non-visible ability used for evidence and diagnosis.
- `CompareGuard`: a comparison node for concepts that are often confused.
- `TransferNode`: a variant/migration target that checks whether a method transfers.
- `SynthesisNode`: a compound reasoning or modeling node that checks decomposition path, not just formula memory.

Required edge semantics:

- `requires`: the target ability depends on the source.
- `supports`: the source makes the target more stable but may not be a strict prerequisite.
- `derives_to`: one idea or form is derived from another.
- `transforms_to`: a condition or expression must be transformed into a standard form.
- `contrasts_with`: two nodes should be compared to clarify boundaries.
- `commonly_confused_with`: errors often come from mixing these nodes.
- `checks`: one ability checks conditions, domains, constants, initial values, or final-form requirements.
- `repairs`: an error target maps back to this repair ability.
- `transfers_to`: mastery should migrate from one form or scenario to another.
- `blocks`: missing the source ability should block or weaken downstream confidence.

The graph must be able to explain:

- why a node exists;
- whether it should be visible or hidden;
- which abilities it depends on;
- which downstream abilities it supports;
- which nearby nodes it is confused with;
- which errors it repairs;
- which challenge or Boss task validates it;
- why a failure should target one repair node instead of many.

The visible map must stay playable. Do not put every atomic ability on the map. Hidden ability nodes should absorb most fine-grained logic so the learner sees a beautiful, meaningful map instead of a dense checklist.

### Ultimate Graph Quality Gate

The graph needs a quality validator before any serious expansion.

It should detect:

- orphan visible nodes;
- orphan hidden abilities;
- edges with missing or invalid semantic type;
- circular dependencies in strict prerequisite paths;
- visible-node explosion where too many small abilities are exposed;
- MacroChallenges that do not cover the core MicroNodes they claim to validate;
- root causes without a repair target;
- repair targets that point to unrelated nodes;
- CompareGuard nodes that do not actually connect confused concepts;
- HiddenAbility entries without scoring evidence, rubric cues, validator flags, or response cues;
- Boss/Synthesis nodes that test only calculation instead of integrated reasoning;
- graph branches that cannot be unlocked or cannot be completed deterministically.

A future chapter import should fail or warn before runtime if these graph-quality rules are violated.

### Ultimate Diagnosis System

The final diagnosis engine must behave like a strict math coach, not a label mapper.

It must not do this:

```text
low dimension score -> one error label -> crude rollback
```

It must do this:

```text
score evidence + rubric evidence + validator evidence + response evidence + hidden ability graph + node policy
-> root cause
-> primary/secondary/derived errors
-> confidence
-> repair target suggestion
-> learner-safe explanation
```

Required diagnosis categories:

- `root_cause`: the causal source of the failure.
- `primary_errors`: major current errors.
- `secondary_errors`: relevant but non-dominant errors.
- `derived_errors`: downstream errors caused by the root.
- `downstream_result`: final answer failure that should not become root by itself.
- `weak_signal`: surface evidence that is not enough for strong diagnosis.
- `evidence_gap`: missing proof of mastery.
- `ability_state`: a learner-friendly state such as understands-but-imprecise, answer-without-evidence, calculation-slip, or neighbor-knowledge-confused.

The root cause must be selected by causal precedence, not by maximum weight alone.

Required causal behavior:

- `trigger_failure` can derive `method_error`, `transformation_error`, and `process_gap`.
- `method_error` can derive `process_gap`, `calculation_error`, and final answer failure.
- `transformation_error` can derive `process_gap`, `calculation_error`, and final answer failure.
- `calculation_error` can derive final answer failure but should not erase stable trigger/method evidence.
- `condition_miss` can make an answer incomplete but should not be mislabeled as pure calculation error.
- `expression_weakness` must not hide a true `concept_gap`.
- `concept_gap` must not be over-triggered when the learner is basically right but imprecise.
- `knowledge_confusion` should require node/graph support, not just a random low trigger score.
- `synthesis_failure` should require application/synthesis context, not just one missed formula.
- rule-only, weak-only, or optional-only evidence must not produce a strong root cause.

Required boundary cases:

- Correct final answer but weak trigger/method/process evidence -> `false_pass`.
- Process correct but final answer wrong -> likely `calculation_error`, not concept rollback.
- Concept answer broadly correct but not precise -> partial understanding, not total failure.
- Trigger wrong causing method wrong -> root is `trigger_failure`.
- Method wrong causing calculation wrong -> root is `method_error`.
- Transformation wrong causing final answer wrong -> root is `transformation_error`.
- Missing arbitrary constant `C` -> answer/calculation completeness, not method error.
- Missing initial value or condition -> `condition_miss`.
- Expression weak but reasoning traceable -> `expression_weakness`, usually partial repair.
- Keyword-only answer -> `need_more_evidence`.
- Multiple optional rubric misses -> weak signal only, not root cause.
- Rubric required miss plus high final answer -> do not let final answer hide missing reasoning.
- Knowledge confusion -> should point to comparison/guard ability.
- Synthesis failure -> should point to decomposition path, not a single formula.

Required evidence sources:

- `ScoreVector`
- scorer results from `CompositeScoringEngine`
- `RubricScorer` matched/missed/required/optional evidence
- `MathValidatorScorer` flags
- `RuleScorer` weak signals
- `response_steps`
- `self_explanation`
- hidden ability evidence
- node policy
- edge semantics from the logic graph

The diagnosis must produce a Chinese learner explanation that includes:

- root-cause judgment;
- why it is not another common error;
- whether forward movement is allowed;
- next repair/training action.

It must not expose debug strings, enum dumps, scorer internals, or raw trace language to the learner.

### Ultimate Movement Contract

Even in the ultimate version, diagnosis does not own movement.

Frozen ownership:

```text
CompositeScoringEngine = scoring owner
DiagnosisEngine = diagnosis and evidence owner
RollbackEngine = rollback owner
ForwardEngine = forward owner
ChallengeEngine = local challenge state transition owner
API / UI = orchestration and projection only
```

Ultimate behavior must preserve these movement rules:

- MicroNode fail -> stay on the same MicroNode.
- MicroNode pass -> light that MicroNode.
- All required MicroNodes mastered -> MacroNode becomes available.
- MacroChallenge pass -> MacroNode mastered/lit and unlocks successors.
- MacroChallenge fail -> root cause maps to one target MicroNode.
- Multiple candidate repair nodes -> choose one primary target, do not activate many at once.
- derived errors must not expand rollback.
- final_answer as downstream result must not trigger broad rollback.
- false_pass must block strong forward movement.
- rule-only/no-signal must prefer evidence collection.

### Ultimate UI/Experience Target

The ultimate knowledge network should feel like a cosmic exploration game with serious math underneath.

It should not feel like:

- a spreadsheet;
- a task manager;
- a generic dashboard;
- a dense prerequisite chart;
- a normal question-bank app.

It should feel like:

- a deep black knowledge universe;
- a living 2D map;
- visible nodes with meaningful light/state;
- smooth parallax and high-frame-rate motion;
- elegant semantic connections;
- bottom-sheet training pod;
- calm, high-end, iOS-like learning interface;
- coach feedback that feels personal and exact.

Visual beauty is part of the product, not decoration. But visual design must not create new decision logic.

### Ultimate Acceptance Criteria

Before calling the logic graph and diagnosis system "ultimate-ready", the project should satisfy:

- Existing pytest passes.
- scoring eval passes.
- diagnosis eval passes.
- movement eval passes.
- synthetic diagnosis lab passes.
- graph quality validator covers visible nodes, hidden abilities, edge semantics, challenge coverage, repair targets, and over-visibility.
- synthetic cases cover concept imprecision, false pass, calculation slip, trigger/method confusion, transformation failure, condition miss, expression weakness, knowledge confusion, synthesis failure, and weak evidence.
- current ODE slice demonstrates the full architecture without needing a large question bank.
- future chapter expansion mostly requires YAML/data authoring plus validation, not engine redesign.

The final test of the architecture:

```text
Can the system stay simple to use while becoming more logically rigorous underneath?
```

## Current Implemented System State

The project has already implemented:

- Multi-dimensional scoring.
- Root-cause diagnosis and evidence chain.
- Rollback / forward movement contracts.
- Learner-safe API surface.
- Internal/dev API surface.
- Local Trainer CLI.
- Browser-based challenge trainer.
- ODE challenge graph slice.
- Logic graph / hidden ability evidence layer.
- Synthetic diagnosis lab for offline red-team cases.
- Authoring-only catalog workflow and review packets.
- Local visual knowledge map with cosmic style and browser trainer UI.

Recent verified checks before this handoff:

```text
pytest: 521 passed
scoring eval: 30/30 passed
diagnosis eval: 25/25 passed
movement eval: 12/12 passed
synthetic diagnosis lab: 16/16 passed
```

The exact numbers may change after future work, but these are the known good baseline at this handoff.

## Current Important Files

Backend:

- `backend/app/main.py`
- `backend/app/services/composite_scoring_engine.py`
- `backend/app/services/diagnosis_engine.py`
- `backend/app/services/rollback_engine.py`
- `backend/app/services/forward_engine.py`
- `backend/app/logic_graph/evidence_engine.py`
- `backend/app/logic_graph/quality_validator.py`
- `backend/app/challenge/engine.py`
- `backend/app/api/challenge_v1/routes.py`
- `backend/app/training/local_trainer.py`

Challenge and graph data:

- `backend/challenge_data/ode_network_mvp/`
- `backend/challenge_data/ode_network_mvp/logic_graph.yaml`
- `backend/app/seed/ode_nodes.yaml`

Frontend trainer:

- `frontend/trainer/`

Evals:

- `evals/run_evals.py`
- `evals/run_synthetic_diagnosis_lab.py`
- `evals/golden_cases/`
- `evals/synthetic_cases/ode_diagnosis_synthetic_cases.yaml`

Core docs:

- `docs/scoring_spec.md`
- `docs/diagnosis_spec.md`
- `docs/movement_spec.md`
- `docs/logic_graph_spec.md`
- `docs/local_trainer_spec.md`
- `docs/api_spec.md`

## Current UI Direction

The desired UI is not a generic dashboard.

Target feel:

- iOS-like high-end minimalism.
- Deep cosmic black background.
- Star-field / nebula atmosphere, not noisy cartoon galaxy.
- Smooth continuous zoom and pan.
- Nodes and lines should feel elegant, luminous, and alive.
- Connections should be meaningful and visually refined.
- Training panel should be a bottom sheet / learning pod, not a rough side drawer.
- The training pod should be glass-like, calm, and uncluttered.
- Avoid visually noisy cards, heavy panels, grid clutter, and blocky nodes.

Interaction expectations:

- Smooth node hover.
- Smooth click transition.
- Smooth bottom-sheet opening.
- Smooth zoom, pan, and map movement.
- Background should move subtly with the map to create exploration depth.
- The visible map should feel like a living knowledge galaxy, not a dead tree.

## User's Long-Term Vision

The final system may become a multi-subject universe:

- Mathematics as one galaxy.
- 408 Computer Science as another galaxy.
- Possibly English and Politics if a good knowledge-network model fits.

Inside a subject:

- Chapters become star clusters.
- A chapter opens into its own rigorous knowledge network.
- Each branch represents a real conceptual direction, not arbitrary layout.
- Nodes are connected by strict prerequisite, support, contrast, transfer, and synthesis relationships.

The map should not become complicated just because the knowledge is rigorous. The graph engine should support rigor internally, while the learner sees a playable, meaningful, beautiful map.

## Near-Term Strategic Direction

Because the user is currently preparing for final exams and cannot provide many real practice samples, the best near-term direction is not massive content expansion.

Instead:

1. Keep improving the engine using synthetic diagnosis cases.
2. Build graph-quality validation tools that can catch bad knowledge relationships.
3. Strengthen hidden ability evidence and repair-target precision.
4. Improve the UI smoothness and aesthetic quality.
5. When the user has time to practice, collect real answer samples and compare them against synthetic assumptions.

Do not require the user to produce lots of samples right now.

## Development Requirements

Always preserve these boundaries unless the user explicitly approves changing them:

- Do not replace scoring with final-answer judging.
- Do not make API/frontend decide rollback or forward.
- Do not let DiagnosisEngine become the movement owner.
- Do not use LLM as final authority.
- Do not use random behavior in core training decisions.
- Do not write to formal catalog from authoring or challenge flows unless a formal publish phase explicitly says so.
- Do not expose trusted catalog fields to learner API or frontend.
- Do not let `response_steps` / `self_explanation` be mistaken as absent just because a dimension was unscored.
- Do not expand the full Mathematics I graph casually.
- Do not add many visible training nodes when hidden ability structure would solve the problem better.

Preferred implementation style:

- Deterministic first.
- Configurable rules.
- Small focused tests.
- Preserve frozen eval behavior.
- Add red-team tests when touching scoring, diagnosis, movement, or graph logic.
- Keep frontend changes visually polished and verified in browser.

## What Not To Do Without Explicit Approval

- Add database persistence.
- Add user accounts or auth.
- Add real LLM API.
- Add full symbolic ODE validation.
- Publish authoring candidates into the formal catalog.
- Build full Mathematics I content.
- Convert the product into a rigid study planner.
- Turn the map into a huge checklist.
- Add a new decision engine in frontend/API/orchestrator.

## Good Next Moves

Possible next moves, depending on what the user asks:

1. UI polish pass:
   - smoother training pod
   - better node layout
   - deeper parallax star-field
   - cleaner typography and spacing

2. Synthetic diagnosis lab expansion:
   - more concept-imprecision cases
   - more trigger/method confusion cases
   - expression-vs-concept boundary cases
   - answer-right-but-evidence-weak cases

3. Knowledge graph quality tooling:
   - detect bad edge direction
   - detect orphan abilities
   - detect over-visible node explosion
   - detect missing repair targets
   - detect MacroChallenge coverage gaps

4. Real practice sample mode later:
   - once the user is free from finals, collect real attempts
   - compare system diagnosis with user/human judgment
   - refine rubrics and hidden ability cues

5. Minimal content expansion only after engine confidence:
   - expand ODE carefully
   - keep authoring-only until reviewed
   - never dump a giant graph into runtime without validation

## How A New Thread Should Start

If a future assistant receives this project cold, it should:

1. Read this file.
2. Read `README.md` current phase.
3. Inspect `backend/challenge_data/ode_network_mvp/`.
4. Inspect `docs/logic_graph_spec.md` and `docs/diagnosis_spec.md`.
5. Run or at least know the baseline checks:

```bash
python -m pytest -q
python evals/run_evals.py
python evals/run_synthetic_diagnosis_lab.py
```

Then continue from the user's latest request without redesigning the already-frozen engine boundaries.
