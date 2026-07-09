# 3D Free Flight Knowledge Universe Design

Date: 2026-07-09

Status: approved for first implementation

## Decision

The learner experience moves toward a real three-dimensional, free-flight knowledge universe.
The goal is no longer to make the existing strict trainer look three-dimensional. The goal is to
make exploration the primary experience and let math review happen through encounters inside that
space.

The first implementation should prove immersion, movement, discovery, and learning-event entry.
It must not attempt to become a full game, expand all Mathematics I content, add accounts, add a
database, or make the frontend decide mastery.

## Product Shape

The first version opens directly into space:

```text
Enter universe
  -> free flight
  -> discover the ODE sector
  -> approach a knowledge object
  -> enter an encounter pod
  -> answer or reflect
  -> receive diagnostic feedback
  -> see the universe state react
```

The ODE network remains the only runtime content slice.

## Interaction Model

- Mouse controls view direction after pointer lock.
- `W`, `A`, `S`, `D` move horizontally through space.
- `Space` and `Ctrl` move up and down.
- `Shift` accelerates.
- Approaching a knowledge object reveals its role and interaction hint.
- `E` opens the encounter pod for the nearest usable object.
- `Esc` exits pointer lock or closes the active overlay.

This is intentionally closer to exploration than to a dashboard.

## Spatial Grammar

- MacroNode: large knowledge planet or station.
- MicroNode: orbiting satellite or ability core.
- MacroChallenge/Boss: star gate.
- CompareGuard: twin warning beacon.
- GuideNode: navigation buoy.
- RepairTarget: unstable or damaged ability core.
- Semantic edge: light route, orbit path, warning arc, or repair beam.

The visual objects represent existing learning semantics. They do not create new progression logic.

## Learning Boundary

The frontend can present objects, proximity, prompts, and effects. It must not decide:

- score;
- diagnosis;
- rollback;
- forward movement;
- challenge state transition.

Those remain owned by the existing backend engines.

The encounter pod can call the existing challenge API. It may display learner-safe feedback and
convert repair targets into visual highlights.

## First Implementation Scope

Create a separate static entry at:

```text
/trainer/space/
```

The first slice includes:

- independent `space/index.html`, `space/space.css`, and `space/space.js`;
- Three.js scene with a star field, nebula fog, free camera, and flight controls;
- an ODE sector with 3 macro planets, 18 micro satellites, and 3 boss gates;
- proximity detection and nearest-object HUD;
- encounter pod overlay with answer and explanation fields;
- calls to existing `/api/challenge/v1/start`, `/status`, `/submit`, and `/reset`;
- visual state updates from the challenge payload;
- a clear fallback if WebGL or remote Three.js loading fails.

## Non-Goals

- No full Mathematics I universe.
- No new content generation system.
- No real game economy, levels, inventory, coins, streaks, or social systems.
- No database or account layer.
- No migration of the existing 2D trainer.
- No attempt to make long-form answer entry happen directly inside a 3D mesh.

## Acceptance Criteria

- `/trainer/space/` serves the new experience in mixed profile.
- Existing `/trainer/` remains available.
- The 3D scene renders nonblank in a browser.
- Desktop free flight works with keyboard and mouse.
- The encounter pod can start/reset/submit through existing challenge APIs.
- The page remains usable on mobile with a visible non-pointer-lock fallback.
- Backend tests still pass for the touched API/static surface.
