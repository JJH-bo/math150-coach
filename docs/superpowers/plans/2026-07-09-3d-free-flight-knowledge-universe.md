# 3D Free Flight Knowledge Universe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first `/trainer/space/` free-flight 3D ODE universe that keeps existing training decisions in the backend.

**Architecture:** Add a separate static Three.js frontend under `frontend/space/`. It consumes the existing challenge API and projects current ODE network state into planets, satellites, gates, proximity hints, and an encounter pod without changing scoring, diagnosis, rollback, or forward ownership.

**Tech Stack:** FastAPI static mount, existing `/api/challenge/v1`, native HTML/CSS/JavaScript, Three.js module from a pinned CDN URL, pytest/FastAPI TestClient for static-entry coverage.

## Global Constraints

- Do not modify the existing `/trainer/` 2D trainer for the first slice.
- Do not add a database, auth, real LLM API, game economy, streaks, or social competition.
- Do not let frontend decide score, diagnosis, rollback, forward movement, or challenge transition.
- Use the existing ODE runtime slice only.
- Keep the answer experience in a readable overlay rather than inside a 3D mesh.

---

### Task 1: Static 3D Entry Contract

**Files:**
- Modify: `backend/tests/test_challenge_frontend_api.py`
- Create: `frontend/space/index.html`
- Create: `frontend/space/space.css`
- Create: `frontend/space/space.js`

**Interfaces:**
- Consumes: FastAPI static mount at `/trainer`.
- Produces: `/trainer/space/` HTML, `/trainer/space/space.css`, `/trainer/space/space.js`.

- [ ] **Step 1: Write the failing test**

```python
def test_space_trainer_static_page_and_assets_are_served_from_mixed_profile() -> None:
    client = TestClient(create_app("mixed"))

    page = client.get("/trainer/space/")
    script = client.get("/trainer/space/space.js")
    styles = client.get("/trainer/space/space.css")

    assert page.status_code == 200
    assert "3D Free Flight Knowledge Universe" in page.text
    assert 'type="module" src="/trainer/space/space.js"' in page.text
    assert script.status_code == 200
    assert "createKnowledgeUniverse" in script.text
    assert styles.status_code == 200
    assert ".space-hud" in styles.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_challenge_frontend_api.py::test_space_trainer_static_page_and_assets_are_served_from_mixed_profile -q`

Expected: FAIL because `/trainer/space/` is not present yet.

- [ ] **Step 3: Implement the static files**

Create the three frontend files with a pinned Three.js import, HUD shell, overlay shell, free-flight scene, ODE objects, and API calls.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_challenge_frontend_api.py::test_space_trainer_static_page_and_assets_are_served_from_mixed_profile -q`

Expected: PASS.

### Task 2: Browser Verification

**Files:**
- No code files required unless defects are found.

**Interfaces:**
- Consumes: local app server, `/trainer/space/`.
- Produces: verification evidence that the 3D scene renders and remains interactive.

- [ ] **Step 1: Start the local app**

Run: `python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`

Expected: server starts. If port 8000 is occupied, use 8001.

- [ ] **Step 2: Open `/trainer/space/` in the browser**

Expected: HUD appears, star field renders, and the canvas is nonblank.

- [ ] **Step 3: Verify desktop interaction**

Use keyboard/mouse to confirm camera movement, nearest-object detection, and encounter pod opening.

- [ ] **Step 4: Verify mobile viewport**

Confirm the page remains readable and the overlay does not cover all controls permanently.
