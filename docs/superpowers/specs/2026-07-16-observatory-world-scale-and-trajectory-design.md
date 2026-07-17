# Observatory World Scale and Trajectory Design

## Goal

Correct the remaining false camera-following impression in the upper and lower-right learning systems, and enlarge the real chapter-scale observation envelope. The lower-left system is the accepted motion reference: every system must remain fixed in world space while observer motion produces visible curved screen trajectories, depth-dependent scale, internal parallax, and changing occlusion.

The closest view must retain the accepted Boss pressure and material quality. The farthest view must become a complete chapter overview containing all three systems and the complete Boss, while the Boss still occupies approximately 35% to 45% of the viewport height.

This specification supersedes the fixed system positions and previous maximum camera distance in `2026-07-15-unified-world-camera-design.md`. Its shared-world-camera and accepted-material constraints remain in force.

## Scope

- Keep the accepted Boss model, ray-traced appearance, accretion-disc treatment, planet material, routes, and cosmos appearance unchanged.
- Change only fixed world layout data, system-local depth/orientation, the fixed observation target, and the camera distance envelope needed to present that layout.
- Preserve the lower-left system as the visual reference for correct world-space motion.
- Do not add planet interaction, training UI, new systems, new materials, or camera-state-dependent object placement.

## Selected Approach: Real World-Scale Reconstruction

Use one fixed world scene and one perspective camera. Increase the physical spacing and depth of the scene rather than separating objects with screen-space offsets.

Two alternatives are explicitly rejected:

1. Coupling field of view to dolly distance would preserve composition artificially and recreate the unnatural zoom response already rejected.
2. Compensating each system's projected screen position from camera state would make systems follow the camera and violate the fixed-world requirement.

## World Layout

The three system centers and the Boss remain immutable world anchors for the lifetime of a scene. Camera input may never modify or compensate those anchors.

- Retain the lower-left system's current motion character as the reference baseline.
- Move the upper and lower-right system centers farther from the camera sightline and introduce separation along all three world axes. No two system centers may share both a near-identical camera depth (within 5% of scene depth) and a near-identical view-axis offset.
- Expand the chapter's world-space span so that, at the default view, no system appears to sit on the Boss accretion disc. The visible gap between every system envelope and the Boss footprint must be at least one large projected planet diameter.
- Keep the three systems in a fan-shaped chapter composition rather than distributing them evenly around the Boss.
- Recompute one fixed observation target from the enlarged chapter bounds. It must not track the camera or any individual system during interaction.

## System Volume and Trajectory

The upper and lower-right systems currently behave visually like thin cards. Their local planet layouts must gain enough depth and plane rotation to expose real perspective changes over the approved yaw and pitch envelope.

- Give every four-planet system a local depth range of at least 25% of its local left-to-right span instead of keeping all planets near one plane.
- Preserve each system's recognizable four-node topology and all route endpoints.
- Use distinct fixed plane orientations so that no two systems collapse into the same apparent motion.
- Between the left and right yaw limits, every system must change its projected internal width by at least 12%. At one or both limits, at least one planet pair within that system must differ in apparent radius by at least 8% because of camera depth.
- System centers may move naturally across the screen as the observer moves, but their paths must be curved perspective projections rather than camera-matched rigid translation.
- Internal routes and terminal routes are regenerated from the same fixed three-dimensional planet anchors, so they cannot detach or lag behind.

## Camera and Dolly Envelope

Keep the current fixed field of view and true orbital dolly model.

- Preserve the accepted near-distance composition and Boss pressure by retaining the current `8.6` minimum distance and `10.0` default distance unless a rendering safety issue requires moving either farther away.
- Increase the maximum distance substantially. Select the smallest distance that satisfies the complete-scene far-view fit after the world layout is enlarged; do not obtain extra range by changing object scale or field of view.
- At the farthest default-angle view, all three complete systems and the complete Boss must fit inside the viewport with at least a 3% viewport margin on every edge.
- At that far bound, the Boss must occupy 35% to 45% of viewport height. It must remain the dominant object, not become a background icon.
- Dolly changes only camera distance. It must not change field of view, object world positions, independent object scales, or per-system screen offsets.
- Retain the existing yaw and pitch limits. Enlarge or reposition the fixed world layout and choose the far bound so those accepted angular limits remain safe; do not reduce them to hide trajectory problems.

## Boss and Material Protection

- Do not edit the Boss shader, ray-traced source, event horizon, photon ring, accretion disc, lensing style, or approved color treatment.
- Continue deriving the Boss observer angle and projected footprint from the shared world camera.
- Do not enlarge a low-resolution Boss cache to satisfy the near view; retain the current accepted high-quality sampling path.
- Planet and route materials remain unchanged. This task adjusts their fixed placement and projection only.

## Interaction Contract

- Drag moves only the observer around the fixed observation target.
- Wheel moves only the observer nearer or farther along the bounded orbit radius.
- Double click restores the approved default pose.
- No scene object receives a transform derived from drag delta, wheel delta, or projected screen position.
- All foreground and background layers consume the same camera state in the same animation frame.

## Acceptance Criteria

1. The lower-left system retains its accepted fixed-world motion character.
2. The upper and lower-right systems no longer look attached to the camera; they exhibit curved motion, at least 12% projected-width change across the yaw range, and camera-depth radius differences of at least 8% within each system.
3. At rest and throughout the allowed observation envelope, the three systems are visibly separated from the Boss rather than appearing pasted onto its accretion disc.
4. The closest view retains the currently accepted Boss scale, pressure, appearance, and material quality.
5. The farthest default-angle view contains all three complete systems and the complete Boss with at least 3% edge margin, while the Boss occupies 35% to 45% of viewport height.
6. Dolly is continuous and physical: no planet freezes in screen space, no system moves with the camera, and no field-of-view compensation creates a vertigo effect.
7. Planets, internal routes, terminal routes, Boss projection, lensing, and cosmos remain synchronized at every allowed camera pose.
8. No allowed pose exposes route detachment, object clipping, white patches, missing Boss surfaces, degraded materials, or near-plane failures.

## Focused Verification

- Check that system centers and planet world anchors are identical before and after drag or dolly input.
- Compare projected system centers and local planet spans at the left, center, and right yaw limits; every system must show non-rigid perspective change.
- Check near, default, and far distance bounds at the default angle and yaw extremes.
- Measure the far-view Boss height ratio and verify complete-scene fit plus the required visual gap between systems and Boss.
- Perform focused browser inspection of those boundary poses only. Do not run unrelated full-project validation for this visual correction.
