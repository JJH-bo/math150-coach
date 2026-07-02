# Math150 Coach Ultimate Knowledge Universe Design

Date: 2026-07-02

Status: draft for user review

## 1. Design Decision

The ultimate version should follow route 2:

```text
Multi-subject knowledge universe as the product architecture,
with route 1's strict diagnostic engine as the core standard.
```

This means Math150 Coach is not only a Mathematics I app. It is a long-term
knowledge-network training system where Mathematics I is the first subject
galaxy and the current ODE slice is the first proof slice.

The highest priorities are:

1. Strict diagnosis.
2. Long-term extensibility.
3. High-end cosmic learning experience in service of the first two priorities.

The product must not become a normal question bank, a rigid planner, a dashboard,
a final-answer checker, or a beautiful but logically empty map.

## 2. Product Architecture

The outer product architecture is:

```text
Subject Galaxy
  -> Chapter Region
    -> Knowledge Network
      -> Training Pod
        -> Diagnostic Result
          -> Repair Target
```

### Subject Galaxy

A subject galaxy is a top-level subject world, such as:

- Mathematics I.
- 408 Computer Science.
- English, if its knowledge structure later proves suitable.
- Politics, if its knowledge structure later proves suitable.

Subject galaxies may have distinct visual identities, but they must share the
same core interaction and diagnostic grammar.

### Chapter Region

A chapter region is a chapter-level nebula. At the macro atlas level, it should
show only summary data and entry state. It must lazy-load detailed chapter
networks only after the learner enters that chapter.

The chapter atlas must not embed:

- full chapter detail graphs;
- logic overlays;
- current questions;
- trusted answer fields;
- rubrics;
- solution outlines;
- debug traces.

### Knowledge Network

A knowledge network is the detailed chapter-level map. It contains visible
learning nodes, bridge/semantic nodes, and hidden diagnostic abilities.

### Training Pod

The training pod is the learner's local interaction surface for:

- current task;
- final answer;
- response steps;
- self explanation;
- coach feedback;
- root-cause summary;
- evidence gaps;
- repair target.

The training pod is not a new decision engine.

## 3. Knowledge Graph Layer Model

The graph has three layers.

### Learner-Visible Layer

This is what the learner sees and plays.

- `SubjectGalaxy`: top-level subject world.
- `ChapterRegion`: chapter nebula, shown in the course atlas.
- `MacroNode`: large visible knowledge point.
- `MicroNode`: visible trainable ability branch under a MacroNode.
- `MacroChallenge`: Boss-style integrated validation bound to a MacroNode.

Important boundary:

```text
MacroNode is not MacroChallenge.
MacroChallenge validates a MacroNode.
```

Default MicroNode types remain:

- concept
- trigger
- method
- transformation
- calculation
- expression

The visible map must stay playable. The default target is around six trainable
MicroNodes per MacroNode. More than eight visible MicroNodes should be treated
as a warning. More than twelve should block serious publication unless there is
explicit approval and a strong reason.

### Bridge Semantic Layer

This layer clarifies transitions, confusion, transfer, and synthesis without
always creating extra training tasks.

- `CompareGuard`: distinguishes easily confused nearby knowledge points.
- `TransferNode`: checks whether mastery transfers to variants.
- `SynthesisNode`: represents integrated decomposition paths.
- `GuideNode`: navigation, warning, bridge, or gateway marker.

These nodes may be visible when they improve learning clarity, but they should
not inflate the training workload by default.

### Hidden Diagnostic Layer

This layer carries the fine-grained diagnostic structure.

- `HiddenAbility` / `AtomNode`: atomic evidence and ability units.
- `EvidenceRequirement`: what can prove the ability.
- `FailureMode`: what errors appear when the ability is unstable.
- `RepairCue`: learner-safe repair hint.
- `repair_target_node_id`: the visible MicroNode to repair.

Hidden abilities absorb complexity that would otherwise make the visible map a
giant checklist.

### Semantic Edge Types

Edges must explain why nodes are connected. They are not layout lines.

Required edge semantics:

- `requires`
- `supports`
- `derives_to`
- `transforms_to`
- `contrasts_with`
- `commonly_confused_with`
- `checks`
- `repairs`
- `transfers_to`
- `blocks`
- `boss_checks`
- `assesses`

Every serious edge should have a label or reason and a positive semantic weight.
Strict prerequisite-like edges must be checked for cycles.

## 4. Strict Diagnostic Core

The diagnostic core is a multi-source evidence pipeline, not a score-to-label
lookup table.

Runtime evidence flow:

```text
Question + Attempt
  -> CompositeScoringEngine
  -> evidence bundle
  -> DiagnosisEngine
  -> hidden ability evidence
  -> root cause and error roles
  -> one repair target
  -> learner-safe explanation
```

### Evidence Inputs

The diagnostic core may use:

- `ScoreVector`;
- active scorer results;
- rubric required hits and misses;
- rubric optional hits and misses;
- math validator flags;
- weak rule signals;
- final answer evidence;
- response steps;
- self explanation;
- hidden ability evidence;
- graph edge semantics;
- node policy.

### Weak Signal Rules

Weak evidence cannot produce strong diagnosis by itself.

The following must remain weak or evidence-gap cases unless other strong
evidence supports them:

- keyword-only response;
- rule-only evidence;
- optional-only rubric misses;
- no response steps when steps are needed;
- no self explanation when explanation is needed;
- final answer only with no process evidence.

### Causal Policy

Root cause must be selected by causal precedence, evidence strength, graph
semantics, and node policy. It must not be selected by highest weight alone.

Required causal behavior:

- `trigger_failure` can derive method, transformation, and process errors.
- `method_error` can derive process, calculation, and final-answer errors.
- `transformation_error` can derive calculation and final-answer errors.
- `calculation_error` can derive final-answer failure, but must not erase stable
  trigger, concept, or method evidence.
- `condition_miss` must not be mislabeled as pure calculation error.
- `expression_weakness` must not hide a true concept gap.
- `concept_gap` must not be over-triggered when the learner mostly understands
  but is imprecise.
- `knowledge_confusion` should require graph support from CompareGuard or
  related confusion edges.
- `synthesis_failure` should require synthesis or Boss context.

### Diagnostic Output Roles

The final diagnosis should distinguish:

- `root_cause`: earliest supported cause.
- `primary_errors`: high-impact current blockers.
- `secondary_errors`: meaningful but non-root issues.
- `derived_errors`: caused by the root.
- `downstream_result`: final answer failure caused downstream.
- `weak_signal`: surface evidence that is not enough.
- `evidence_gap`: missing proof of mastery.
- `ability_state`: learner-friendly state.

Possible `ability_state` values include:

- understands-but-imprecise;
- answer-without-evidence;
- calculation-slip;
- neighbor-knowledge-confused;
- synthesis-path-broken;
- needs-more-evidence.

### Repair Target Projection

Diagnosis may see multiple weak hidden abilities, but the training flow should
activate one primary repair target:

```text
root_cause -> HiddenAbility -> repair_target_node_id -> one MicroNode
```

MacroChallenge failure should map to one target MicroNode inside the relevant
training region whenever possible. Derived errors must not expand rollback.

### Engine Ownership

Ownership boundaries are frozen:

- `CompositeScoringEngine`: scoring owner.
- `DiagnosisEngine`: diagnosis, evidence, root cause, explanation, repair hints.
- `RollbackEngine`: rollback owner.
- `ForwardEngine`: forward owner.
- `ChallengeEngine`: local challenge state transition owner.
- API/UI/trainer: orchestration and presentation only.

API, frontend, training pod, coach-output projection, and any future LLM must
not become new decision engines.

## 5. Ultimate UI And Cosmic Visual Language

The ultimate UI should feel like a serious knowledge universe, not a dashboard.
The cosmic feeling must be a reusable visual language, not a starry skin.

### Four Experience States

1. Exploration state:
   - opens directly into the knowledge universe;
   - subject galaxies and chapter nebulae are the first signal;
   - detailed chapter maps lazy-load after entry.

2. Training state:
   - selecting the current node opens the bottom training pod;
   - the map remains visible but enters a noise-reduced focus mode;
   - current node, relevant semantic edges, and repair context are highlighted.

3. Diagnosis state:
   - after submission, the system shows root cause, evidence summary,
     common-misdiagnosis exclusion, movement status, and one repair target;
   - hidden ability chains are expandable, not forced into the main view.

4. Authoring state:
   - chapter draft import, graph quality reports, human review, and candidate
     build live in a separate workshop;
   - authoring tools must not pollute the learning flow.

### Cosmic Visual Grammar

The final visual system should map product concepts to celestial roles:

- `SubjectGalaxy`: a subject-level galaxy with its own identity.
- `ChapterNebula`: chapter-level cloud/region with summary state.
- `MacroNode`: a major star or anchor.
- `MicroNode`: trainable satellite star.
- `MacroChallenge/Boss`: high-energy core or gate.
- `CompareGuard`: warning or contrast beacon.
- `TransferNode`: migration arc point.
- `SynthesisNode`: convergence or composite path node.
- `RepairTarget`: focused repair flare.
- `TrainingPod`: observation/diagnosis dock.

Edges should become a light language:

- `requires`: stable prerequisite light.
- `supports`: softer support glow.
- `repairs`: repair loop or red/orange corrective line.
- `contrasts_with` / `commonly_confused_with`: warning or double-sided contrast
  line.
- `transfers_to`: migration arc.
- `boss_checks`: convergence beam into Boss.
- `blocks`: muted barrier or blocked route.

Visual quality is part of the product, but it must not create decision logic.

### UI Constraints

- No generic dashboard as the main screen.
- No giant checklist of tiny nodes.
- No heavy planner, streak pressure, leaderboard, or social competition.
- No visible debug strings in learner-facing feedback.
- Motion must serve cognition: focus, zoom, context, edge highlighting, and
  training pod docking.
- When the pod is open, nonessential animation should pause or reduce.
- Map interaction must stay smooth on desktop and mobile.

## 6. Long-Term Authoring And Publish Flow

Future expansion should be bold in authoring and conservative in publication.

The pipeline is:

```text
Structured Draft
  -> Draft Preview
  -> Graph Quality Gate
  -> Human Review
  -> Candidate Build
  -> Formal Publish
```

### Structured Draft

A draft can describe:

- MacroNodes;
- MicroNodes;
- MacroChallenges;
- HiddenAbilities;
- CompareGuards;
- TransferNodes;
- SynthesisNodes;
- semantic edges;
- ErrorRepairMap;
- public questions;
- trusted scoring fields.

Drafts must not write formal runtime data.

### Draft Preview

Preview should show:

- graph counts;
- visible node budget;
- semantic edge summary;
- hidden ability coverage;
- Boss coverage;
- repair-target coverage;
- warnings and errors.

Preview must remain learner-safe and must not expose trusted scoring fields to
the learner runtime.

### Graph Quality Gate

The quality gate should detect:

- missing logic graph;
- orphan visible nodes;
- orphan hidden abilities;
- trainable MicroNodes without hidden ability coverage;
- hidden ability dimension mismatch;
- missing evidence sources;
- missing why_exists;
- bad repair targets;
- root causes without repair targets;
- semantic edges with missing meaning;
- self-loop edges;
- zero-weight edges;
- dependency cycles;
- visible node explosion;
- CompareGuard nodes without actual comparison;
- Boss challenges without MicroNode coverage;
- Boss/Synthesis nodes that only test calculation.

### Human Review

Human review must inspect:

- mathematical correctness;
- problem quality;
- rubric quality;
- answer aliases;
- public prompt safety;
- solution outline correctness;
- graph semantics;
- repair target relevance.

### Candidate Build

Candidate builds should generate dry-run previews and content hashes. They are
still not formal publication.

### Formal Publish

Formal publish must be an explicit future phase. It may write formal runtime
data only after approval and verification. It should preserve rollback records
or enough content-hash evidence to audit what changed.

## 7. Engineering Architecture

The engineering architecture should keep modules small and responsibilities
clear.

Runtime modules:

- `ChallengeRepository`: loads chapter graph, question bank, and logic graph.
- `CompositeScoringEngine`: merges scoring evidence.
- `DiagnosisEngine`: root cause and evidence roles.
- `LogicEvidenceEngine`: advisory hidden ability evidence.
- `RollbackEngine`: rollback decision.
- `ForwardEngine`: forward decision.
- `ChallengeEngine`: challenge progress and local state transition.
- Learner API: safe projection.
- Frontend trainer: map, training pod, diagnosis display.
- Authoring tools: draft validation, preview, report, candidate dry-run.

### Runtime Data Flow

```text
Question + Attempt
  -> Score Evidence
  -> Diagnosis Evidence
  -> Movement Decision
  -> Challenge State
  -> Learner Projection
  -> Frontend Map And Pod
```

The frontend must not infer movement from display fields. It receives state and
renders it.

### Data Boundary

These data zones must stay separate:

- draft authoring data;
- dry-run candidate previews;
- formal catalog data;
- runtime challenge graph data;
- learner API projection;
- local session progress;
- session logs;
- debug/eval artifacts.

## 8. Error Handling

The system should handle errors without breaking trust.

Runtime learner-facing errors should be safe:

- missing chapter: show unavailable chapter, not stack trace;
- missing current task: show no active challenge;
- no signal response: ask for more evidence;
- bad request: show clear input error;
- logic overlay absent: continue without hidden overlay;
- graph quality warning: do not silently publish.

Authoring-facing errors can be more detailed but should still be structured:

- `target`;
- `severity`;
- `code`;
- `message`;
- optional suggested fix.

Trusted fields must never leak through learner API or frontend.

## 9. Testing And Acceptance

The ultimate-ready architecture should be considered credible only when these
checks pass:

- Python unit and contract tests pass.
- Scoring golden eval passes.
- Diagnosis golden eval passes.
- Movement golden eval passes.
- Synthetic diagnosis lab passes.
- Graph quality validator covers visible nodes, hidden abilities, semantic
  edges, Boss coverage, repair targets, and visible-node budget.
- Synthetic cases cover false pass, concept imprecision, calculation slip,
  trigger/method confusion, transformation failure, condition miss,
  expression weakness, knowledge confusion, synthesis failure, weak evidence,
  and answer-without-evidence.
- Browser verification confirms map loads, atlas loads, node selection does not
  rebuild the full graph, training pod opens smoothly, motion budget works, text
  does not overlap, and mobile view remains usable.
- Learner-facing responses contain no trusted answer keys, rubrics, solution
  outlines, debug traces, raw scorer internals, or hidden trusted catalog fields.

## 10. Phased Roadmap

### Phase U0: Ultimate Blueprint Freeze

Output:

- this design spec;
- implementation plan after user review;
- no chapter content expansion;
- no runtime behavior change.

### Phase U1: ODE Proof Slice

Goal:

Use the existing `ode_network_mvp` slice to prove the ultimate architecture and
experience.

Scope:

- improve cosmic atlas and chapter map visual language;
- improve training pod experience;
- improve diagnosis display and hidden ability chain explanation;
- improve graph quality report presentation;
- preserve current engine ownership;
- preserve current content scope;
- run existing tests and browser verification.

Non-goals:

- no full Mathematics I graph;
- no new real chapter content;
- no database;
- no auth;
- no real LLM API;
- no formal publish.

### Phase U2: Authoring Workshop Maturity

Goal:

Make future chapter expansion mostly authoring and validation work.

Scope:

- richer draft preview;
- structured quality report;
- human review records;
- candidate build dry-run;
- publish planning.

Formal publish remains explicit and separate.

### Phase U3+: Approved Expansion

Future capabilities that require explicit approval:

- more Mathematics I chapters;
- 408 subject galaxy;
- real practice sample calibration;
- LLM-assisted authoring;
- database-backed long-term history;
- formal publish workflow;
- production deployment.

## 11. Non-Goals For The Current Blueprint

This design does not approve:

- adding concrete chapter content now;
- publishing authoring drafts;
- writing formal catalog entries;
- adding database persistence;
- adding user accounts or auth;
- connecting a real LLM;
- making the frontend or API a decision engine;
- replacing multi-dimensional scoring with final-answer grading;
- turning the product into a planner or checklist;
- exposing trusted fields to the learner UI.

## 12. Final Architecture Test

The architecture is successful if it can answer yes to this question:

```text
Can the system stay simple, playable, and beautiful for the learner
while becoming more rigorous and expandable underneath?
```

