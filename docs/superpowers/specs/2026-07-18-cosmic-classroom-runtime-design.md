# Cosmic Classroom Runtime Design

> Date: 2026-07-18
> Status: approved by the active Route Two goal
> Project: C
> Parent: `2026-07-18-ai-classroom-redesign-design.md`

## Outcome

Project C creates the learner-facing AI Classroom at `/classroom`. It replaces
the visible task chain with a learning universe whose primary destinations are
complete core modules. Entering a destination opens a readable classroom stage
where explanation, formula, example, detail branches, and a synchronized
teaching model remain connected.

The old `/trainer` is retained only until Project D cutover.

## Chosen Experience

The old Three.js flight scene is not adapted because its object roles, controls,
progress state, and observatory are coupled to Challenge semantics. A pure
linear document is also rejected because it loses chapter structure and model
continuity.

The selected experience has two modes:

1. a calm cosmic atlas for course, chapter, and complete-module navigation;
2. a reading-first classroom stage with a sticky model observatory.

Cosmic visuals establish place and relationship. They never compete with text,
look like hidden tasks, or imply pass/fail state.

## Universe Navigation

The learner sees:

```text
course universe -> chapter region -> core module destination
```

The catalog loads from `/api/classroom/v1/catalog`. Selecting a package loads
its immutable active version. Course and chapter controls change the visible
region. Every module appears once as a named destination; module relations are
subtle explanatory routes, not locks.

Decorative stars use lower contrast, no pointer cursor, and no accessible
button role. There is no Boss, challenge, mastery, score, progress percentage,
streak, recommendation, or next-task language.

## Classroom Stage

Desktop uses a reading column and a sticky model column. Mobile uses a single
reading flow with a collapsible sticky model dock.

The renderer supports every Project A block kind with a readable fallback.
Formula explanations use adjacent panels. Derivations and worked examples keep
step numbers and context visible. Comparisons, tables, matrices, code, images,
groups, and model references use dedicated semantic layouts.

Detail branches open directly beneath their parent content. Opening or closing
a branch does not navigate, reset scroll, or destroy model state. Recursive
branches are supported with a practical visual indentation limit.

The stage header always offers a return to the chapter region. Full-screen
model observation preserves reading scroll, open branches, and model state.

## Model Runtime and Bindings

The learner downloads only exact registered model versions through Classroom
Runtime. The generic Project B host mounts the pinned source and exposes
lifecycle, snapshot, and disposal behavior.

The binding engine maps:

- block visibility and activation;
- detail branch open and close;
- explicit controls;
- allowed parameter changes

to typed effects from the published package. Temporary effects push a snapshot
and restore it according to the binding contract.

Model errors show the instance fallback description without breaking reading.
Changing modules disposes the old model before mounting the next instance.
Full-screen and inline viewports share the same controller.

## Scene Continuity

`localStorage` stores one `classroom_scene_v1` snapshot:

- package ID and immutable release version;
- selected course, chapter, and module;
- reading block and scroll position;
- open detail branch IDs;
- active model instance and model snapshot;
- viewport mode;
- quality and reduced-motion preferences.

The snapshot rejects or ignores all analysis-shaped keys. It contains no
answer, score, mastery, diagnosis, review, recommendation, failure count, or
learner profile.

## Visual and Input Behavior

- Text contrast meets classroom readability before Bloom or glow.
- Background particles slow or stop inside the stage.
- Reduced motion is automatic from media preference and manually selectable.
- Model pointer input owns its viewport; atlas movement never intercepts it.
- Escape exits full-screen model view before leaving the stage.
- Keyboard focus follows actual navigation and detail controls.
- Mobile controls remain at least 44 CSS pixels.

## Files and Mounting

New frontend code lives under `frontend/classroom`. The reusable model host is
copied into that static tree at build-free development time or imported through
the mounted `/classroom/model-runtime` path.

Learner and mixed profiles mount the static application at `/classroom`.
Internal profile does not expose it. Project D later makes it the default root
and removes `/trainer`.

## Testing and Evidence

Node tests cover atlas projection, content projection, scene snapshot
allowlist, and binding state transitions. Python tests cover static mounting,
profile boundaries, runtime-only API calls, and forbidden product language.

Playwright verifies:

- desktop atlas and module entry;
- adjacent formula/explanation and persistent model;
- local detail opening and restoration;
- full-screen model entry and return;
- reload scene restoration;
- mobile single-column layout and model dock;
- no console errors, overflow, or legacy network calls.

Desktop and mobile screenshots plus structured browser reports are checked in
under `docs/preview-artifacts/project-c`.

## Completion Gate

1. The learner can navigate course, chapter, and complete core module without
   seeing training nodes.
2. The sample limit module renders all authored content and its pinned model.
3. Detail branches expand locally and preserve scroll/model context.
4. Content bindings replay declared model states and restore temporary state.
5. Full-screen model view returns to the same reading location.
6. Reload restores only allowlisted scene continuity.
7. Desktop and mobile browser evidence has no console error or horizontal
   overflow.
8. New frontend code contains no challenge, answer, scoring, diagnosis,
   mastery, review, recommendation, or Boss product behavior.

