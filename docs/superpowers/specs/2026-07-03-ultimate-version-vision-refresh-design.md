# Ultimate Version Vision Refresh Design

Date: 2026-07-03

Status: confirmed by user for execution

## 1. Decision

The project continues on this route:

```text
Multi-subject knowledge universe as the product architecture,
strict diagnostic engine as the non-negotiable core standard,
authoring workshop as the expansion safety layer.
```

The current `ode_network_mvp` remains the proof slice. The project should not
prove maturity by adding large amounts of chapter content first. It should prove
maturity by making future expansion safe, reviewable, and mostly data/graph
authoring work.

## 2. Product Target

The final product is a personal knowledge-network training system, not a normal
question bank, planner, checklist, dashboard, flashcard app, leaderboard, or
final-answer checker.

The learner-facing system should feel like:

```text
Subject Galaxy
  -> Chapter Nebula
    -> Knowledge Network
      -> Training Pod
        -> Diagnostic Result
          -> Repair Target
```

The implementation standard is:

```text
The learner sees a simple, playable, high-end knowledge universe.
The system underneath runs a strict, auditable, multi-evidence diagnostic engine.
```

## 3. Learner Universe

The visual language is part of the product and must map to real learning
semantics:

- `SubjectGalaxy`: top-level subject world.
- `ChapterNebula`: chapter region and summary state.
- `MacroNode`: major visible knowledge anchor.
- `MicroNode`: trainable ability node under a MacroNode.
- `MacroChallenge`: Boss validation bound to a MacroNode.
- `CompareGuard`: contrast or confusion beacon.
- `TransferNode`: migration or variant-transfer point.
- `SynthesisNode`: convergence path for integrated reasoning.
- `RepairTarget`: focused repair flare.
- `TrainingPod`: local answer and diagnosis dock.

Visual design must not create decision logic. The frontend presents state and
interaction context; it does not decide mastery, diagnosis, rollback, or forward
movement.

## 4. Diagnostic Core

The diagnostic core remains the main product differentiator.

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

The system must preserve these rules:

- Final answer alone cannot prove mastery.
- Weak signals cannot create strong diagnosis by themselves.
- Root cause is selected by causal precedence, evidence strength, graph
  semantics, and node policy, not by highest weight alone.
- Calculation error can cause final-answer failure, but must not erase stable
  concept, trigger, or method evidence.
- `condition_miss` must not be mislabeled as pure calculation error.
- `expression_weakness` must not hide a real concept gap.
- `knowledge_confusion` should require graph support from CompareGuard or
  confusion edges.
- `synthesis_failure` should require synthesis or Boss context.

Diagnosis should distinguish:

- `root_cause`
- `primary_errors`
- `secondary_errors`
- `derived_errors`
- `downstream_result`
- `weak_signal`
- `evidence_gap`
- `ability_state`

## 5. Graph Quality Standard

Future chapter expansion must pass graph quality checks before it can become
runtime content.

The graph quality system should detect:

- MacroNode and MacroChallenge confusion.
- visible MicroNode explosion.
- orphan visible nodes.
- orphan hidden abilities.
- missing HiddenAbility evidence sources.
- missing `why_exists`.
- invalid or meaningless semantic edges.
- root causes without repair targets.
- repair targets pointing to unrelated nodes.
- CompareGuard nodes without real contrast.
- TransferNode nodes that do not validate migration.
- SynthesisNode nodes that do not support Boss decomposition.
- Boss challenges without MicroNode coverage.
- content that looks large but has weak diagnostic structure.

## 6. Authoring Workshop

The authoring workshop is the next major maturity layer. It is separate from the
learner training flow.

Target pipeline:

```text
Structured Draft
  -> Draft Preview
  -> Graph Quality Gate
  -> Human Review
  -> Candidate Build
  -> Formal Publish
```

Current implementation already has:

- structured Markdown draft validation.
- draft-only `workflow_stage`.
- readiness gates.
- draft preview graph.

Next maturity steps:

1. U2C: Link quality gates and report issues to draft preview graph highlights.
2. U2D: Add structured quality issue codes, severities, targets, and suggested fixes.
3. U2E: Add human review records.
4. U2F: Add candidate build dry-run with content hashes.
5. U3: Expand real Mathematics I chapters only after the workshop is reliable.

## 7. Expansion Policy

Content expansion should not be the immediate proof of progress.

The correct order is:

1. Prove the architecture on the ODE slice.
2. Mature the authoring workflow.
3. Add Mathematics I chapters through structured drafts and quality gates.
4. Add 408 as a separate subject galaxy when the subject model is ready.
5. Add LLM assistance, database history, auth, and deployment only after explicit
   approval.

## 8. Current Implemented Baseline

As of this refresh:

- GitHub remote is connected.
- `ultimate-ode-proof-slice` is pushed to `origin/ultimate-ode-proof-slice`.
- U1 delivered cosmic atlas visual grammar, runtime quality HUD, and diagnostic
  verdict display.
- U2A delivered draft readiness projection.
- U2B delivered draft preview graph.
- Recent verification observed full pytest, golden evals, synthetic diagnosis
  lab, JavaScript syntax check, and browser verification passing.

## 9. Non-Goals

This design does not approve:

- adding concrete chapter content immediately.
- formal publish from drafts.
- database persistence.
- auth.
- real LLM integration.
- frontend/API ownership of scoring, diagnosis, rollback, or forward movement.
- planner, streak, leaderboard, or social competition features.
- learner exposure of trusted answer fields, rubrics, solution outlines, or debug
  traces.

## 10. Final Test

The ultimate version is on track only if the answer stays yes:

```text
Can the system become much more rigorous and expandable underneath
while staying simple, playable, and visually coherent for the learner?
```
