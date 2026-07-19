# Autonomous GPT Authoring Design

> Date: 2026-07-19
> Status: approved by the user's standing instruction to proceed without
> repeated confirmation
> Project: Custom GPT autonomous classroom authoring

## 1. Outcome

When the user supplies lecture material and says to make, import, or start the
classroom, the Custom GPT completes the authoring workflow immediately. It
does not ask the user for a classroom URL, `draft_id`, `package_id`, model ID,
or a routine publish confirmation.

The autonomous workflow covers:

1. inspect the Studio workspace;
2. match the material to an existing classroom or create a stable new target;
3. structure the chapter into complete core modules with progressive and
   detailed expansion;
4. reuse or author teaching models when they materially improve learning;
5. create or update a draft;
6. validate and repair the draft;
7. publish the valid classroom;
8. report the resulting learner URL and a concise summary.

This work does not add learner diagnosis, scoring, review scheduling, mastery
tracking, challenge gates, or training logic.

## 2. Root Cause

The existing Studio exposes get-by-ID and write operations but no discovery
operation for classroom drafts or active packages. The GPT therefore has no
reliable way to learn existing identifiers. Guessing plausible names produces
404 responses and forces the GPT to ask the user for internal IDs.

The previous GPT instructions also contained human confirmation checkpoints.
Those checkpoints contradict the user's intended authoring mode and turn
routine execution into a conversation about execution.

## 3. Selected Tool Shape

Add one authenticated read operation:

```text
GET /api/studio/v1/workspace
operationId: getStudioWorkspace
```

The response is a compact authoring bootstrap containing:

- the public learner origin;
- active classroom packages, including IDs, titles, versions, courses,
  chapters, and core module summaries;
- classroom drafts, including IDs, revisions, hashes, titles, and structure
  summaries;
- registered teaching models and their manifests;
- explicit autonomy and safety policy fields that tell the GPT which normal
  operations it may complete without a human checkpoint.

One bootstrap operation is preferred over several disconnected list endpoints
because it reduces Action round trips and gives the GPT a consistent snapshot
for target selection. Existing detailed get operations remain available after
the GPT chooses a target. The response uses bounded, deterministic
`offset`/`limit` pagination with per-collection counts and continuation
offsets, so persistent history cannot silently grow one Action response
without limit.

When several drafts share a `package_id`, the server marks exactly one
`recommended_for_update` target using persisted update time, then revision and
stable ID as legacy fallbacks. It also reports the candidate count and whether
each draft matches the active release. When several model versions share a
`model_id`, the latest registered version is marked
`recommended_for_use`. These are server-owned selection rules; the GPT does
not infer recency from hash-like version names.

## 4. Repository and Service Changes

`ClassroomRepository` gains a deterministic `list_drafts()` method. The
authoring service gains `workspace()` and composes draft summaries, active
release summaries, registered model summaries, and the configured public
origin.

The workspace response includes bounded summaries rather than complete package
bodies to keep Action payloads manageable. The GPT follows `next_offset` until
the relevant collections are complete, then retrieves one full draft with
`getClassroomDraft` only after selecting it.

The endpoint remains protected by the existing Studio bearer credential and
is included in the filtered Custom GPT Action schema.

## 5. GPT Operating Policy

The Custom GPT instructions will make the following rules explicit:

- supplied source material plus an imperative such as `做`, `开始`, `制作`,
  or `导入` is complete authorization for the routine authoring and publish
  workflow;
- call `getStudioWorkspace` before choosing identifiers;
- never guess an existing ID and never ask the user to provide an internal ID
  or project address;
- select a clear semantic match, otherwise create a stable new package and
  draft;
- recover from 404 and 409 responses by refreshing workspace state, reading
  the current draft, and retrying safely;
- validation failures are repair instructions, not reasons to ask the user for
  approval;
- publish automatically after validation succeeds;
- do not create learner analysis, diagnosis, review, scoring, or Boss
  assessment systems;
- do not roll back or overwrite an unrelated classroom;
- use rollback only when the user explicitly requests it or the GPT has just
  published a release that fails an objective post-publish verification.

## 6. Confirmation Boundary

GPT-authored conversational confirmations are removed. OpenAI may still show a
platform-controlled Action approval prompt depending on account, workspace,
and action settings. The project must not mislabel consequential write
operations in the OpenAPI schema merely to suppress platform controls.

## 7. Verification

The change is accepted when:

1. an authenticated workspace call lists the seeded active classroom and any
   existing classroom drafts;
2. the Action schema contains `getStudioWorkspace`;
3. missing, invalid, and unsafe credentials remain rejected;
4. all Python and Node tests pass;
5. the production endpoint returns the real workspace without exposing the
   Studio secret;
6. the Custom GPT receives a lecture-and-`做` prompt and proceeds without
   requesting a URL, draft ID, package ID, or routine confirmation.
