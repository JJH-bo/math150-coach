# Custom GPT Chapter Authoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete Custom GPT authoring path that creates a validated chapter knowledge-network draft, renders it through the existing high-fidelity galaxy scene, and lets the human reviewer publish the exact previewed revision with one click.

**Architecture:** Add a narrow `/api/gpt/v1` facade over the existing deterministic chapter importer and controlled publisher. Store immutable draft revisions on disk, keep GPT and human-review credentials separate, and serve both draft and published galaxy assets through one JSON contract. Generalize the existing infinite-series scene data loader without changing the approved shaders, models, camera physics, or training transition.

**Tech Stack:** Python 3, FastAPI, Pydantic, filesystem-backed JSON/Markdown storage, pytest, vanilla JavaScript ES modules, Node test runner, OpenAPI 3.1 YAML.

## Global Constraints

- GPT can create, update, validate, and read drafts; it cannot approve or formally publish.
- Human approval is a separate authenticated browser operation.
- Every published payload must match the exact preview revision and content hash.
- Keep every system at 3–5 training planets and retain one chapter Boss.
- GPT supplies semantic structure only; project code owns 3D positions, spacing, materials, shaders, Boss rendering, and camera limits.
- Preserve the currently approved planet, connection, Boss, cosmic-sky, and observatory visuals.
- Do not add a database or a full user-account system.
- Do not expose the project-wide FastAPI OpenAPI surface to the Custom GPT.
- Do not store real API keys in source, docs, tests, URLs, or browser-readable JavaScript.
- Preserve unrelated and pre-existing uncommitted changes; stage and commit only task-scoped files.

---

## File Structure

### Backend authoring domain

- Create `backend/app/challenge/chapter_galaxy_asset.py`
  - Canonical Markdown-to-galaxy-asset builder used by both CLI and HTTP flows.
- Create `backend/app/challenge/gpt_authoring_contract.py`
  - Versioned project contract and Action-facing template.
- Create `backend/app/challenge/gpt_draft_store.py`
  - Immutable filesystem draft revisions, idempotency records, and published lookup.
- Create `backend/app/challenge/gpt_authoring_service.py`
  - Validation/build/update orchestration and normalized response payloads.
- Modify `tools/chapter_galaxy_builder.py`
  - Keep CLI behavior but delegate canonical asset construction to the backend module.

### Backend HTTP surfaces

- Create `backend/app/api/gpt/v1/schemas.py`
  - Strict GPT Action request schemas.
- Create `backend/app/api/gpt/v1/auth.py`
  - Bearer authoring-key and signed human-review-session helpers.
- Create `backend/app/api/gpt/v1/router.py`
  - Contract and draft Action endpoints only.
- Create `backend/app/api/gpt/v1/__init__.py`
- Create `backend/app/api/gpt/__init__.py`
- Create `backend/app/api/chapter_review/v1/router.py`
  - Human session, preview asset, approve, and reject endpoints.
- Create `backend/app/api/chapter_review/v1/schemas.py`
- Create `backend/app/api/chapter_review/v1/__init__.py`
- Create `backend/app/api/chapter_review/__init__.py`
- Modify `backend/app/main.py`
  - Register the isolated routers only for the mixed profile.
- Modify `backend/app/config.py`
  - Centralize authoring environment resolution.
- Modify `backend/app/api/challenge/v1/router.py`
  - Add read-only published galaxy-asset endpoint.

### Frontend

- Create `frontend/space/galaxy-lab/chapter-data-loader.mjs`
  - Resolve `chapter`, `draft`, and `revision` URL parameters and fetch the appropriate asset.
- Modify `frontend/space/galaxy-lab/infinite-series-scene.mjs`
  - Generalize sector partitioning while preserving existing exports as compatibility aliases.
- Modify `frontend/space/galaxy-lab/index.html`
  - Replace the hard-coded chapter import with the async loader.
- Create `frontend/chapter-review/index.html`
  - Minimal authenticated preview/approve shell embedding the existing galaxy scene.
- Create `frontend/chapter-review/review.js`
- Create `frontend/chapter-review/review.css`

### Documentation and configuration

- Create `docs/custom-gpt/chapter-authoring-actions.openapi.yaml`
- Create `docs/custom-gpt/chapter-authoring-instructions.md`
- Create `docs/custom-gpt/setup.md`
- Create `docs/custom-gpt/example-conversation.md`
- Modify `.gitignore`
  - Ignore runtime draft and review-session artifacts.
- Create `.env.example`
  - Variable names and safe example values only.

### Tests

- Create `backend/tests/test_chapter_galaxy_asset.py`
- Create `backend/tests/test_gpt_draft_store.py`
- Create `backend/tests/test_gpt_authoring_api.py`
- Create `backend/tests/test_chapter_review_api.py`
- Create `frontend/space/galaxy-lab/chapter-data-loader.test.mjs`
- Modify `frontend/space/galaxy-lab/infinite-series-scene.test.mjs`
- Modify `backend/tests/test_challenge_frontend_api.py`

---

### Task 1: Promote the galaxy builder into the backend domain

**Files:**
- Create: `backend/app/challenge/chapter_galaxy_asset.py`
- Modify: `tools/chapter_galaxy_builder.py`
- Create: `backend/tests/test_chapter_galaxy_asset.py`
- Modify: `backend/tests/test_chapter_galaxy_builder.py`

**Interfaces:**
- Consumes: normalized chapter Markdown containing `GalaxyPlan`, `GalaxyBoss`, `MacroNodes`, `MicroNodes`, optional `Edges`, `TrainingAssets`, and `BossTrainingAsset`.
- Produces: `build_chapter_galaxy_asset(markdown: str) -> dict[str, Any]`.
- Produces: `write_galaxy_asset_module(asset: dict[str, Any], output: Path) -> None`.

- [ ] **Step 1: Write failing canonical-builder tests**

```python
from app.challenge.chapter_galaxy_asset import build_chapter_galaxy_asset


def test_canonical_galaxy_asset_contains_semantic_links(valid_galaxy_markdown: str) -> None:
    asset = build_chapter_galaxy_asset(valid_galaxy_markdown)

    assert asset["chapterId"] == "galaxy_demo"
    assert asset["metrics"] == {"systemCount": 1, "planetCount": 4, "bossCount": 1}
    assert asset["systems"][0]["links"] == [
        {
            "sourceId": "galaxy_demo.system.concept",
            "targetId": "galaxy_demo.system.trigger",
            "edgeType": "supports",
        },
        {
            "sourceId": "galaxy_demo.system.trigger",
            "targetId": "galaxy_demo.system.method",
            "edgeType": "supports",
        },
        {
            "sourceId": "galaxy_demo.system.method",
            "targetId": "galaxy_demo.system.expression",
            "edgeType": "supports",
        },
    ]


def test_canonical_galaxy_asset_rejects_disconnected_system(valid_galaxy_markdown: str) -> None:
    disconnected = valid_galaxy_markdown.replace(
        "| edge-3 | supports | galaxy_demo.system.method | galaxy_demo.system.expression |",
        "",
    )

    with pytest.raises(ValueError, match="missing visible supports edges"):
        build_chapter_galaxy_asset(disconnected)
```

- [ ] **Step 2: Run tests and verify the backend module is missing**

Run:

```powershell
python -m pytest backend/tests/test_chapter_galaxy_asset.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: collection fails with `ModuleNotFoundError: No module named 'app.challenge.chapter_galaxy_asset'`.

- [ ] **Step 3: Move the canonical implementation without changing behavior**

Create `backend/app/challenge/chapter_galaxy_asset.py` with the parser currently implemented in `tools/chapter_galaxy_builder.py`, preserving the existing semantic-link additions. Export:

```python
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

TABLE_SECTIONS = {"GalaxyPlan", "GalaxyBoss", "MacroNodes", "MicroNodes"}
MICRO_TYPES = {"concept", "trigger", "method", "transformation", "calculation", "expression"}


def build_chapter_galaxy_asset(markdown: str) -> dict[str, Any]:
    # Use the complete existing parser body from build_chapter_asset.
    # Preserve strict 3-5 planet counts, visible supports edges, training
    # payloads, Boss coverage, and metrics.
    return _build_asset(markdown)


def write_galaxy_asset_module(asset: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asset, ensure_ascii=False, indent=2, sort_keys=False)
    output.write_text(f"export default {payload};\n", encoding="utf-8", newline="\n")
```

Rename the original public function body to private `_build_asset` in the new module. Keep all parsing helpers in this module. Replace the tool’s implementation import with:

```python
from app.challenge.chapter_galaxy_asset import (
    build_chapter_galaxy_asset as build_chapter_asset,
    write_galaxy_asset_module as write_javascript_module,
)
```

The tool keeps its current argument parser and `main()` only.

- [ ] **Step 4: Run builder tests**

Run:

```powershell
python -m pytest backend/tests/test_chapter_galaxy_asset.py backend/tests/test_chapter_galaxy_builder.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit only the canonical-builder scope**

```powershell
git add backend/app/challenge/chapter_galaxy_asset.py backend/tests/test_chapter_galaxy_asset.py backend/tests/test_chapter_galaxy_builder.py tools/chapter_galaxy_builder.py
git commit -m "Add canonical chapter galaxy asset builder"
```

---

### Task 2: Add immutable draft persistence and orchestration

**Files:**
- Create: `backend/app/challenge/gpt_authoring_contract.py`
- Create: `backend/app/challenge/gpt_draft_store.py`
- Create: `backend/app/challenge/gpt_authoring_service.py`
- Create: `backend/tests/test_gpt_draft_store.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `build_chapter_galaxy_asset(markdown: str)`.
- Consumes: `validate_chapter_markdown(markdown: str)`.
- Produces: `ChapterDraftStore(root: Path)`.
- Produces: `create_or_get_draft(request: DraftSubmission) -> dict[str, Any]`.
- Produces: `revise_draft(draft_id: str, expected_revision: int, submission: DraftSubmission) -> dict[str, Any]`.
- Produces: `load_revision(draft_id: str, revision: int | None = None) -> dict[str, Any]`.
- Produces: `find_published_by_chapter(chapter_id: str) -> dict[str, Any] | None`.

- [ ] **Step 1: Write failing store tests**

```python
def test_idempotent_submission_returns_same_draft(tmp_path: Path) -> None:
    store = ChapterDraftStore(tmp_path)
    first = store.create_revision(
        chapter_id="galaxy_demo",
        title="Galaxy Demo",
        source_markdown=VALID_GALAXY_MARKDOWN,
        client_request_id="request-001",
        contract_version="chapter-galaxy-v1",
        validation_report={"report": {"error_count": 0}},
        galaxy_asset={"chapterId": "galaxy_demo"},
    )
    second = store.create_revision(
        chapter_id="galaxy_demo",
        title="Galaxy Demo",
        source_markdown=VALID_GALAXY_MARKDOWN,
        client_request_id="request-001",
        contract_version="chapter-galaxy-v1",
        validation_report={"report": {"error_count": 0}},
        galaxy_asset={"chapterId": "galaxy_demo"},
    )

    assert second["draft_id"] == first["draft_id"]
    assert second["revision"] == 1


def test_idempotency_key_cannot_change_content(tmp_path: Path) -> None:
    store = ChapterDraftStore(tmp_path)
    store.create_revision(
        chapter_id="galaxy_demo",
        title="Galaxy Demo",
        source_markdown=VALID_GALAXY_MARKDOWN,
        client_request_id="request-001",
        contract_version="chapter-galaxy-v1",
        validation_report={"report": {"error_count": 0}},
        galaxy_asset={"chapterId": "galaxy_demo"},
    )

    with pytest.raises(IdempotencyConflict):
        store.create_revision(
            chapter_id="galaxy_demo",
            title="Galaxy Demo",
            client_request_id="request-001",
            source_markdown=VALID_GALAXY_MARKDOWN + "\nchanged",
            contract_version="chapter-galaxy-v1",
            validation_report={"report": {"error_count": 0}},
            galaxy_asset={"chapterId": "galaxy_demo"},
        )


def test_revision_compare_and_swap_prevents_overwrite(tmp_path: Path) -> None:
    store = ChapterDraftStore(tmp_path)
    created = store.create_revision(
        chapter_id="galaxy_demo",
        title="Galaxy Demo",
        source_markdown=VALID_GALAXY_MARKDOWN,
        client_request_id="request-001",
        contract_version="chapter-galaxy-v1",
        validation_report={"report": {"error_count": 0}},
        galaxy_asset={"chapterId": "galaxy_demo"},
    )

    with pytest.raises(RevisionConflict):
        store.revise(
            created["draft_id"],
            expected_revision=0,
            source_markdown=VALID_GALAXY_MARKDOWN,
            validation_report={},
            galaxy_asset={},
        )
```

- [ ] **Step 2: Run the store tests and verify failure**

Run:

```powershell
python -m pytest backend/tests/test_gpt_draft_store.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: collection fails because `gpt_draft_store` does not exist.

- [ ] **Step 3: Implement atomic draft storage**

Use these exact public types:

```python
from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,79}$")


class DraftStoreError(ValueError):
    pass


class DraftNotFound(DraftStoreError):
    pass


class IdempotencyConflict(DraftStoreError):
    pass


class RevisionConflict(DraftStoreError):
    pass


class ChapterDraftStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create_revision(
        self,
        *,
        chapter_id: str,
        title: str,
        source_markdown: str,
        client_request_id: str,
        contract_version: str,
        validation_report: dict[str, Any],
        galaxy_asset: dict[str, Any] | None,
    ) -> dict[str, Any]:
        self._validate_id(chapter_id)
        digest = self._content_hash(source_markdown)
        idempotency = self._read_json(self.root / "idempotency.json", {})
        existing = idempotency.get(client_request_id)
        if existing:
            if existing["content_hash"] != digest:
                raise IdempotencyConflict(client_request_id)
            return self.load(existing["draft_id"], existing["revision"])

        draft_id = f"{chapter_id}-{digest.removeprefix('sha256:')[:16]}"
        if (self.root / draft_id / "manifest.json").exists():
            record = self.load(draft_id)
        else:
            record = {
                "draft_id": draft_id,
                "chapter_id": chapter_id,
                "title": title,
                "contract_version": contract_version,
                "status": "preview_ready" if galaxy_asset else "invalid",
                "revision": 1,
                "content_hash": digest,
                "created_at": self._now(),
                "updated_at": self._now(),
            }
            self._write_revision(record, source_markdown, validation_report, galaxy_asset)
        idempotency[client_request_id] = {
            "draft_id": draft_id,
            "revision": record["revision"],
            "content_hash": digest,
        }
        self._atomic_json(self.root / "idempotency.json", idempotency)
        return self.load(draft_id, record["revision"])

    def revise(
        self,
        draft_id: str,
        *,
        expected_revision: int,
        source_markdown: str,
        validation_report: dict[str, Any],
        galaxy_asset: dict[str, Any] | None,
    ) -> dict[str, Any]:
        manifest = self._manifest(draft_id)
        if manifest["revision"] != expected_revision:
            raise RevisionConflict(draft_id)
        revision = expected_revision + 1
        record = {
            **manifest,
            "status": "preview_ready" if galaxy_asset else "invalid",
            "revision": revision,
            "content_hash": self._content_hash(source_markdown),
            "updated_at": self._now(),
        }
        self._write_revision(record, source_markdown, validation_report, galaxy_asset)
        return self.load(draft_id, revision)

    def load(self, draft_id: str, revision: int | None = None) -> dict[str, Any]:
        manifest = self._manifest(draft_id)
        selected = revision or int(manifest["revision"])
        revision_root = self.root / draft_id / "revisions"
        prefix = f"{selected:04d}"
        markdown_path = revision_root / f"{prefix}.md"
        if not markdown_path.exists():
            raise DraftNotFound(f"{draft_id}:{selected}")
        asset_path = revision_root / f"{prefix}.asset.json"
        return {
            **manifest,
            "revision": selected,
            "source_markdown": markdown_path.read_text(encoding="utf-8"),
            "validation_report": self._read_json(
                revision_root / f"{prefix}.validation.json",
                {},
            ),
            "galaxy_asset": self._read_json(asset_path, None) if asset_path.exists() else None,
        }

    def mark_published(
        self,
        draft_id: str,
        *,
        revision: int,
        content_hash: str,
        publish_result: dict[str, Any],
    ) -> dict[str, Any]:
        record = self.load(draft_id, revision)
        if record["content_hash"] != content_hash:
            raise RevisionConflict(draft_id)
        manifest = self._manifest(draft_id)
        manifest.update({
            "status": "published",
            "published_revision": revision,
            "published_at": self._now(),
            "publish_result": publish_result,
        })
        self._atomic_json(self.root / draft_id / "manifest.json", manifest)
        return self.load(draft_id, revision)

    def find_published_by_chapter(self, chapter_id: str) -> dict[str, Any] | None:
        self._validate_id(chapter_id)
        matches = []
        for manifest_path in self.root.glob("*/manifest.json"):
            manifest = self._read_json(manifest_path, {})
            if manifest.get("chapter_id") == chapter_id and manifest.get("status") == "published":
                matches.append(manifest)
        if not matches:
            return None
        latest = max(matches, key=lambda item: item.get("published_at", ""))
        return self.load(latest["draft_id"], int(latest["published_revision"]))

    def _write_revision(
        self,
        record: dict[str, Any],
        markdown: str,
        validation: dict[str, Any],
        asset: dict[str, Any] | None,
    ) -> None:
        root = self.root / record["draft_id"]
        revisions = root / "revisions"
        revisions.mkdir(parents=True, exist_ok=True)
        prefix = f"{record['revision']:04d}"
        markdown_path = revisions / f"{prefix}.md"
        if markdown_path.exists():
            raise RevisionConflict(record["draft_id"])
        self._atomic_text(markdown_path, markdown)
        self._atomic_json(revisions / f"{prefix}.validation.json", validation)
        if asset is not None:
            self._atomic_json(revisions / f"{prefix}.asset.json", asset)
        self._atomic_json(root / "manifest.json", record)

    def _manifest(self, draft_id: str) -> dict[str, Any]:
        self._validate_id(draft_id)
        path = self.root / draft_id / "manifest.json"
        if not path.exists():
            raise DraftNotFound(draft_id)
        return self._read_json(path, {})

    @staticmethod
    def _validate_id(value: str) -> None:
        if not ID_PATTERN.fullmatch(value):
            raise DraftNotFound(value)

    @staticmethod
    def _content_hash(markdown: str) -> str:
        return f"sha256:{hashlib.sha256(markdown.encode('utf-8')).hexdigest()}"

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _atomic_text(path: Path, text: str) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(path)

    @classmethod
    def _atomic_json(cls, path: Path, payload: Any) -> None:
        cls._atomic_text(
            path,
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
```

Verify this implementation:

- validates IDs with `^[a-z0-9][a-z0-9_-]{1,79}$`;
- computes SHA-256 content hashes;
- derives stable draft IDs from chapter ID plus a 16-character hash prefix;
- writes JSON and Markdown to a sibling `.tmp` path before `Path.replace`;
- stores revisions under `revisions/0001.*`;
- never edits an existing revision file;
- keeps `idempotency.json` under the draft-store root;
- updates `manifest.json` atomically;
- never follows user-provided filesystem paths.

- [ ] **Step 4: Implement the project contract and service**

`gpt_authoring_contract.py` exports:

```python
CONTRACT_VERSION = "chapter-galaxy-v1"


def chapter_authoring_contract() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "workflow": [
            "read_contract",
            "submit_complete_draft",
            "repair_validation_issues",
            "return_preview_url",
        ],
        "constraints": {
            "planets_per_system": {"minimum": 3, "maximum": 5},
            "chapter_boss_count": 1,
            "allowed_micro_types": [
                "concept",
                "trigger",
                "method",
                "transformation",
                "calculation",
                "expression",
            ],
            "gpt_can_publish": False,
        },
        "required_sections": [
            "GalaxyPlan",
            "GalaxyBoss",
            "MacroNodes",
            "MicroNodes",
            "Edges",
            "TrainingAssets",
            "BossTrainingAsset",
        ],
    }
```

`gpt_authoring_service.py` exports:

```python
@dataclass(frozen=True)
class DraftSubmission:
    chapter_id: str
    title: str
    source_markdown: str
    client_request_id: str
    contract_version: str


class GptAuthoringService:
    def __init__(self, store: ChapterDraftStore, public_base_url: str = "") -> None:
        self.store = store
        self.public_base_url = public_base_url.rstrip("/")

    def create(self, submission: DraftSubmission) -> dict[str, Any]:
        return self._build_and_store(submission)

    def revise(
        self,
        draft_id: str,
        *,
        expected_revision: int,
        submission: DraftSubmission,
    ) -> dict[str, Any]:
        return self._build_and_store(submission, draft_id=draft_id, expected_revision=expected_revision)

    def response(self, record: dict[str, Any]) -> dict[str, Any]:
        asset = record.get("galaxy_asset") or {}
        report = record.get("validation_report", {}).get("report", {})
        query = f"draft={quote(record['draft_id'])}&revision={record['revision']}"
        return {
            "draft_id": record["draft_id"],
            "chapter_id": record["chapter_id"],
            "title": record["title"],
            "status": record["status"],
            "revision": record["revision"],
            "content_hash": record["content_hash"],
            "metrics": asset.get("metrics", {}),
            "issues": report.get("issues", []),
            "preview_url": f"{self.public_base_url}/trainer/chapter-review/?{query}",
        }
```

Implement `_build_and_store` by calling `validate_chapter_markdown` first, then
`build_chapter_galaxy_asset`. Catch galaxy-asset `ValueError`, retain the
validation report, and pass `galaxy_asset=None` so the store assigns `invalid`.
For creation call `store.create_revision`; for updates call `store.revise`.
Return `self.response(record)` in both branches. Add `get` and `validate`
methods that load the current immutable revision, expose only `response`, and
rerun deterministic validation without changing the stored revision.

- [ ] **Step 5: Run store and service tests**

Run:

```powershell
python -m pytest backend/tests/test_gpt_draft_store.py backend/tests/test_chapter_galaxy_asset.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: all selected tests pass.

- [ ] **Step 6: Ignore runtime artifacts and commit**

Append:

```gitignore
runtime/chapter_drafts/
.pytest_tmp/
```

Then:

```powershell
git add .gitignore backend/app/challenge/gpt_authoring_contract.py backend/app/challenge/gpt_draft_store.py backend/app/challenge/gpt_authoring_service.py backend/tests/test_gpt_draft_store.py
git commit -m "Add immutable GPT chapter draft workflow"
```

---

### Task 3: Add the authenticated Custom GPT Action API

**Files:**
- Create: `backend/app/api/gpt/__init__.py`
- Create: `backend/app/api/gpt/v1/__init__.py`
- Create: `backend/app/api/gpt/v1/auth.py`
- Create: `backend/app/api/gpt/v1/schemas.py`
- Create: `backend/app/api/gpt/v1/router.py`
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_gpt_authoring_api.py`

**Interfaces:**
- Consumes: `GptAuthoringService`.
- Produces: `router` with five Action operations.
- Produces: `require_gpt_authoring_key(request: Request) -> None`.

- [ ] **Step 1: Write failing API authentication and workflow tests**

```python
def test_gpt_contract_requires_bearer_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GPT_AUTHORING_KEY", "authoring-secret")
    monkeypatch.setenv("CHAPTER_DRAFT_ROOT", str(tmp_path))
    client = TestClient(create_app("mixed"))

    missing = client.get("/api/gpt/v1/contract")
    invalid = client.get(
        "/api/gpt/v1/contract",
        headers={"Authorization": "Bearer wrong"},
    )
    valid = client.get(
        "/api/gpt/v1/contract",
        headers={"Authorization": "Bearer authoring-secret"},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert valid.status_code == 200
    assert valid.json()["contract_version"] == "chapter-galaxy-v1"


def test_gpt_can_create_preview_ready_draft(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GPT_AUTHORING_KEY", "authoring-secret")
    monkeypatch.setenv("CHAPTER_DRAFT_ROOT", str(tmp_path))
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://math.example")
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/gpt/v1/drafts",
        headers={"Authorization": "Bearer authoring-secret"},
        json={
            "chapter_id": "galaxy_demo",
            "title": "Galaxy Demo",
            "source_markdown": VALID_GALAXY_MARKDOWN,
            "client_request_id": "request-001",
            "contract_version": "chapter-galaxy-v1",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "preview_ready"
    assert payload["preview_url"].startswith("https://math.example/trainer/chapter-review/")
    assert payload["metrics"]["systemCount"] == 1
```

- [ ] **Step 2: Run the API tests and verify routes are missing**

Run:

```powershell
python -m pytest backend/tests/test_gpt_authoring_api.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: tests fail with HTTP 404.

- [ ] **Step 3: Add strict request schemas**

```python
class GptDraftCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,79}$")
    title: str = Field(min_length=1, max_length=160)
    source_markdown: str = Field(min_length=1, max_length=750_000)
    client_request_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
    contract_version: Literal["chapter-galaxy-v1"]


class GptDraftUpdateRequest(GptDraftCreateRequest):
    expected_revision: int = Field(ge=1)
```

- [ ] **Step 4: Add constant-time Bearer authentication**

```python
def require_gpt_authoring_key(request: Request) -> None:
    configured = os.getenv("GPT_AUTHORING_KEY", "")
    supplied = request.headers.get("Authorization", "")
    expected = f"Bearer {configured}" if configured else ""
    if not configured or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "authoring_auth_invalid",
                "message": "A valid GPT authoring key is required.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
```

- [ ] **Step 5: Implement the Action router**

Use prefix `/api/gpt/v1` and exact operation IDs:

```python
@router.get("/contract", operation_id="getProjectContract")
def get_project_contract(request: Request) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    return chapter_authoring_contract()


@router.post("/drafts", status_code=201, operation_id="createChapterDraft")
async def create_chapter_draft(request: Request) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    parsed = GptDraftCreateRequest.model_validate(await request.json())
    return _service().create(DraftSubmission(**parsed.model_dump()))


@router.put("/drafts/{draft_id}", operation_id="updateChapterDraft")
async def update_chapter_draft(draft_id: str, request: Request) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    parsed = GptDraftUpdateRequest.model_validate(await request.json())
    values = parsed.model_dump()
    expected_revision = values.pop("expected_revision")
    return _service().revise(
        draft_id,
        expected_revision=expected_revision,
        submission=DraftSubmission(**values),
    )


@router.get("/drafts/{draft_id}", operation_id="getChapterDraft")
def get_chapter_draft(draft_id: str, request: Request) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    return _service().get(draft_id)


@router.post("/drafts/{draft_id}/validate", operation_id="validateChapterDraft")
def validate_chapter_draft(draft_id: str, request: Request) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    return _service().validate(draft_id)
```

Translate domain errors to stable 400, 404, or 409 responses. Do not add approve or publish endpoints to this router.

- [ ] **Step 6: Register the router only in mixed profile**

Add to `create_app`:

```python
if resolved_profile == AppProfile.MIXED:
    application.include_router(gpt_authoring_router)
```

Keep learner and internal profiles unchanged.

- [ ] **Step 7: Run API tests and commit**

Run:

```powershell
python -m pytest backend/tests/test_gpt_authoring_api.py backend/tests/test_challenge_frontend_api.py::test_challenge_api_is_only_registered_on_mixed_profile -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: all selected tests pass.

Commit:

```powershell
git add backend/app/api/gpt backend/app/config.py backend/app/main.py backend/tests/test_gpt_authoring_api.py
git commit -m "Add scoped Custom GPT authoring API"
```

---

### Task 4: Add separate human review authentication and exact-revision publishing

**Files:**
- Create: `backend/app/api/chapter_review/__init__.py`
- Create: `backend/app/api/chapter_review/v1/__init__.py`
- Create: `backend/app/api/chapter_review/v1/schemas.py`
- Create: `backend/app/api/chapter_review/v1/router.py`
- Modify: `backend/app/api/gpt/v1/auth.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_chapter_review_api.py`

**Interfaces:**
- Consumes: `ChapterDraftStore.load`, `ChapterDraftStore.mark_published`.
- Consumes: `build_chapter_publish_plan_dry_run`.
- Consumes: `execute_chapter_controlled_publish`.
- Produces: signed `chapter_review_session` Cookie.
- Produces: exact-revision approve/reject endpoints unavailable to GPT Actions.

- [ ] **Step 1: Write failing separation and approval tests**

```python
def test_gpt_key_cannot_approve_draft(configured_client, preview_ready_draft) -> None:
    response = configured_client.post(
        f"/api/chapter-review/{preview_ready_draft['draft_id']}/approve",
        headers={"Authorization": "Bearer authoring-secret"},
        json={
            "revision": preview_ready_draft["revision"],
            "content_hash": preview_ready_draft["content_hash"],
        },
    )

    assert response.status_code == 401


def test_review_session_publishes_exact_preview_revision(
    configured_client,
    preview_ready_draft,
    tmp_path: Path,
) -> None:
    login = configured_client.post(
        "/api/chapter-review/session",
        json={"review_key": "review-secret"},
    )
    assert login.status_code == 204

    response = configured_client.post(
        f"/api/chapter-review/{preview_ready_draft['draft_id']}/approve",
        json={
            "revision": preview_ready_draft["revision"],
            "content_hash": preview_ready_draft["content_hash"],
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "published"
    assert response.json()["formal_publish_executed"] is True


def test_approval_rejects_stale_hash(configured_client, preview_ready_draft) -> None:
    configured_client.post(
        "/api/chapter-review/session",
        json={"review_key": "review-secret"},
    )
    response = configured_client.post(
        f"/api/chapter-review/{preview_ready_draft['draft_id']}/approve",
        json={"revision": 1, "content_hash": "sha256:stale"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error_code"] == "approval_revision_mismatch"
```

- [ ] **Step 2: Run review tests and verify routes are absent**

Run:

```powershell
python -m pytest backend/tests/test_chapter_review_api.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: tests fail with HTTP 404.

- [ ] **Step 3: Implement signed review sessions**

Add:

```python
REVIEW_COOKIE_NAME = "chapter_review_session"
REVIEW_SESSION_TTL_SECONDS = 8 * 60 * 60


def issue_review_session(now: int | None = None) -> str:
    issued_at = int(time.time() if now is None else now)
    payload = f"chapter-review:{issued_at}"
    signature = hmac.new(
        _review_signing_key().encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return _urlsafe_encode(f"{payload}:{signature}")


def require_review_session(request: Request, now: int | None = None) -> None:
    token = request.cookies.get(REVIEW_COOKIE_NAME, "")
    if not _valid_review_token(token, int(time.time() if now is None else now)):
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "review_auth_required",
                "message": "A valid human review session is required.",
            },
        )
```

Use `CHAPTER_REVIEW_KEY` both to authenticate the session exchange and to derive the HMAC signing secret. Reject missing or equal GPT/review keys.

- [ ] **Step 4: Implement approve and reject schemas**

```python
class ReviewSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review_key: str = Field(min_length=1, max_length=512)


class ApproveDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class RejectDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=500)
```

- [ ] **Step 5: Implement exact-revision controlled publish**

The approve handler:

1. requires the review Cookie;
2. loads the requested immutable revision;
3. compares revision and hash using constant-time comparison;
4. requires `status == "preview_ready"`;
5. derives the complete review checklist from `HUMAN_REVIEW_CHECKS`;
6. builds a publish plan to obtain its hash;
7. calls `execute_chapter_controlled_publish` with:

```python
result = execute_chapter_controlled_publish(
    record["source_markdown"],
    reviewer="chapter-review-ui",
    decision="approve_for_candidate",
    checklist={code: True for code, _ in HUMAN_REVIEW_CHECKS},
    notes=f"Approved draft {draft_id} revision {parsed.revision}",
    target_root=publish_target_root(),
    allow_write=True,
    approval_phrase=APPROVAL_PHRASE,
    expected_publish_plan_hash=plan["publish_plan_hash"],
)
```

Only call `mark_published` when `result["status"] == "published"`.

- [ ] **Step 6: Register review router and run tests**

Run:

```powershell
python -m pytest backend/tests/test_chapter_review_api.py backend/tests/test_gpt_authoring_api.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit**

```powershell
git add backend/app/api/chapter_review backend/app/api/gpt/v1/auth.py backend/app/main.py backend/tests/test_chapter_review_api.py
git commit -m "Add human-only chapter review publishing"
```

---

### Task 5: Serve one galaxy asset contract for draft and published chapters

**Files:**
- Modify: `backend/app/api/chapter_review/v1/router.py`
- Modify: `backend/app/api/challenge/v1/router.py`
- Modify: `backend/tests/test_chapter_review_api.py`
- Modify: `backend/tests/test_challenge_frontend_api.py`

**Interfaces:**
- Produces: `GET /api/chapter-review/{draft_id}/galaxy?revision=N`.
- Produces: `GET /api/challenge/v1/chapters/{chapter_id}/galaxy`.
- Both return the same `ChapterGalaxyAsset` JSON shape.

- [ ] **Step 1: Add failing draft and published asset tests**

```python
def test_review_galaxy_returns_preview_asset(configured_client, preview_ready_draft) -> None:
    configured_client.post(
        "/api/chapter-review/session",
        json={"review_key": "review-secret"},
    )
    response = configured_client.get(
        f"/api/chapter-review/{preview_ready_draft['draft_id']}/galaxy",
        params={"revision": preview_ready_draft["revision"]},
    )

    assert response.status_code == 200
    assert response.json()["chapterId"] == preview_ready_draft["chapter_id"]


def test_published_galaxy_asset_is_read_only(configured_client, published_draft) -> None:
    response = configured_client.get(
        f"/api/challenge/v1/chapters/{published_draft['chapter_id']}/galaxy"
    )

    assert response.status_code == 200
    assert response.json()["chapterId"] == published_draft["chapter_id"]
```

- [ ] **Step 2: Run tests and verify 404**

Run:

```powershell
python -m pytest backend/tests/test_chapter_review_api.py backend/tests/test_challenge_frontend_api.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: the two new endpoint tests fail with HTTP 404.

- [ ] **Step 3: Implement the shared read contract**

Draft endpoint:

```python
@router.get("/{draft_id}/galaxy")
def get_draft_galaxy(
    draft_id: str,
    request: Request,
    revision: int | None = None,
) -> dict[str, Any]:
    require_review_session(request)
    record = _store().load(draft_id, revision)
    asset = record.get("galaxy_asset")
    if not isinstance(asset, dict):
        raise api_error(409, "preview_not_ready", "The draft has no valid galaxy asset.")
    return asset
```

Published endpoint:

```python
@router.get("/chapters/{chapter_id}/galaxy")
def get_published_chapter_galaxy(chapter_id: str) -> dict[str, Any]:
    record = _gpt_draft_store().find_published_by_chapter(chapter_id)
    if record is None or not isinstance(record.get("galaxy_asset"), dict):
        raise api_error(404, "chapter_galaxy_not_found", "Published galaxy asset not found.")
    return record["galaxy_asset"]
```

Validate path IDs before reading storage.

- [ ] **Step 4: Run tests and commit**

```powershell
python -m pytest backend/tests/test_chapter_review_api.py backend/tests/test_challenge_frontend_api.py -q --basetemp .pytest_tmp -p no:cacheprovider
git add backend/app/api/chapter_review/v1/router.py backend/app/api/challenge/v1/router.py backend/tests/test_chapter_review_api.py backend/tests/test_challenge_frontend_api.py
git commit -m "Serve draft and published galaxy assets"
```

Expected: all selected tests pass before the commit.

---

### Task 6: Generalize the approved galaxy scene to dynamic chapters

**Files:**
- Create: `frontend/space/galaxy-lab/chapter-data-loader.mjs`
- Create: `frontend/space/galaxy-lab/chapter-data-loader.test.mjs`
- Modify: `frontend/space/galaxy-lab/infinite-series-scene.mjs`
- Modify: `frontend/space/galaxy-lab/infinite-series-scene.test.mjs`
- Modify: `frontend/space/galaxy-lab/index.html`
- Modify: `backend/tests/test_challenge_frontend_api.py`

**Interfaces:**
- Produces: `resolveChapterRequest(search: string)`.
- Produces: `loadChapterData({ search, fetchImpl, fallbackChapter })`.
- Produces: generic `buildChapterSectors(chapter)`.
- Keeps: `buildInfiniteSeriesSectors` as an alias for existing callers.

- [ ] **Step 1: Write failing loader and generic-sector tests**

```javascript
import assert from 'node:assert/strict';
import test from 'node:test';
import {
  loadChapterData,
  resolveChapterRequest,
} from './chapter-data-loader.mjs';

test('resolves a formal chapter request', () => {
  assert.deepEqual(resolveChapterRequest('?chapter=power_series'), {
    kind: 'published',
    chapterId: 'power_series',
  });
});

test('resolves an immutable draft preview request', () => {
  assert.deepEqual(resolveChapterRequest('?draft=demo-abc&revision=2'), {
    kind: 'draft',
    draftId: 'demo-abc',
    revision: 2,
  });
});

test('loads the selected chapter from the API', async () => {
  const calls = [];
  const chapter = await loadChapterData({
    search: '?chapter=power_series',
    fallbackChapter: null,
    fetchImpl: async (url) => {
      calls.push(url);
      return { ok: true, json: async () => ({ chapterId: 'power_series' }) };
    },
  });
  assert.equal(chapter.chapterId, 'power_series');
  assert.deepEqual(calls, ['/api/challenge/v1/chapters/power_series/galaxy']);
});
```

Add to `infinite-series-scene.test.mjs`:

```javascript
test('generic partition never places more than three systems in one sector', () => {
  const synthetic = Object.assign({}, chapter, {
    systems: Array.from({ length: 7 }, (_, index) =>
      Object.assign({}, chapter.systems[index % chapter.systems.length], {
      id: `system-${index}`,
      title: `System ${index + 1}`,
      learningOrder: index + 1,
      })),
  });
  const sectors = buildChapterSectors(synthetic);
  assert.equal(sectors.flatMap((sector) => sector.systems).length, 7);
  assert.ok(sectors.every((sector) => sector.systems.length >= 2));
  assert.ok(sectors.every((sector) => sector.systems.length <= 3));
});
```

- [ ] **Step 2: Run Node tests and verify loader is missing**

Run:

```powershell
node --test frontend/space/galaxy-lab/chapter-data-loader.test.mjs frontend/space/galaxy-lab/infinite-series-scene.test.mjs
```

Expected: fails because `chapter-data-loader.mjs` and `buildChapterSectors` do not exist.

- [ ] **Step 3: Implement URL resolution and fetch**

```javascript
export function resolveChapterRequest(search = '') {
  const params = new URLSearchParams(search);
  const draftId = params.get('draft');
  if (draftId) {
    const revision = Number.parseInt(params.get('revision') || '', 10);
    return {
      kind: 'draft',
      draftId,
      revision: Number.isInteger(revision) && revision > 0 ? revision : null,
    };
  }
  return {
    kind: 'published',
    chapterId: params.get('chapter') || 'infinite_series',
  };
}


export async function loadChapterData({
  search = '',
  fetchImpl = fetch,
  fallbackChapter = null,
} = {}) {
  const request = resolveChapterRequest(search);
  const url = request.kind === 'draft'
    ? `/api/chapter-review/${encodeURIComponent(request.draftId)}/galaxy${
        request.revision ? `?revision=${request.revision}` : ''
      }`
    : `/api/challenge/v1/chapters/${encodeURIComponent(request.chapterId)}/galaxy`;
  const response = await fetchImpl(url, { credentials: 'same-origin' });
  if (response.ok) return response.json();
  if (request.kind === 'published' && request.chapterId === 'infinite_series' && fallbackChapter) {
    return fallbackChapter;
  }
  throw new Error(`chapter_load_failed:${response.status}`);
}
```

- [ ] **Step 4: Generalize sector partitioning**

Add `buildChapterSectors(chapter)` that:

- sorts systems by `learningOrder`;
- partitions each chapter into stable groups of two or three;
- preserves the current infinite-series distribution `[3, 2, 3, 2]`;
- never creates a one-system sector unless the complete chapter has only one system;
- names sectors from contained system titles instead of hard-coded calculus categories.

Keep:

```javascript
export const buildInfiniteSeriesSectors = buildChapterSectors;
```

Update `createSectorSceneConfig` to call `buildChapterSectors`.

- [ ] **Step 5: Replace the hard-coded import with async data loading**

Keep the existing fallback import, but make it fallback-only:

```javascript
import fallbackChapter from './infinite-series-data.mjs';
import { loadChapterData } from './chapter-data-loader.mjs';

const chapter = await loadChapterData({
  search: window.location.search,
  fallbackChapter,
});
```

Do not alter WebGL shaders, render targets, Boss compositor, star material, cosmic iframe, observatory-camera constants, or training-transition code.

- [ ] **Step 6: Run frontend tests and static serving tests**

```powershell
node --test frontend/space/galaxy-lab/chapter-data-loader.test.mjs frontend/space/galaxy-lab/infinite-series-scene.test.mjs frontend/space/galaxy-lab/observatory-camera.test.mjs
python -m pytest backend/tests/test_challenge_frontend_api.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit without dropping the existing uncommitted scene fixes**

```powershell
git add frontend/space/galaxy-lab/chapter-data-loader.mjs frontend/space/galaxy-lab/chapter-data-loader.test.mjs frontend/space/galaxy-lab/infinite-series-scene.mjs frontend/space/galaxy-lab/infinite-series-scene.test.mjs frontend/space/galaxy-lab/index.html backend/tests/test_challenge_frontend_api.py
git commit -m "Load dynamic chapters in the galaxy observatory"
```

Before commit, inspect the staged diff and confirm the existing semantic links, five-planet spacing, training focus handling, and render fallback changes remain present.

---

### Task 7: Add the one-click human review page

**Files:**
- Create: `frontend/chapter-review/index.html`
- Create: `frontend/chapter-review/review.js`
- Create: `frontend/chapter-review/review.css`
- Modify: `backend/tests/test_challenge_frontend_api.py`

**Interfaces:**
- Consumes: `/api/chapter-review/session`.
- Embeds: `/trainer/space/galaxy-lab/?draft=<id>&revision=<n>`.
- Consumes: `/api/gpt/v1/drafts/{draft_id}` only through server-provided review metadata endpoint, not with a GPT Key in browser code.
- Consumes: `/api/chapter-review/{draft_id}/approve` and `/reject`.

- [ ] **Step 1: Add failing static-page contract tests**

```python
def test_chapter_review_page_is_served_without_embedding_secrets() -> None:
    client = TestClient(create_app("mixed"))
    page = client.get("/trainer/chapter-review/")
    script = client.get("/trainer/chapter-review/review.js")

    assert page.status_code == 200
    assert 'id="review-login"' in page.text
    assert 'id="approve-draft"' in page.text
    assert 'id="galaxy-preview"' in page.text
    assert script.status_code == 200
    assert "/api/chapter-review/session" in script.text
    assert "/approve" in script.text
    assert "GPT_AUTHORING_KEY" not in page.text + script.text
    assert "CHAPTER_REVIEW_KEY" not in page.text + script.text
```

- [ ] **Step 2: Run the test and verify failure**

```powershell
python -m pytest backend/tests/test_challenge_frontend_api.py::test_chapter_review_page_is_served_without_embedding_secrets -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: HTTP 404 for the new page.

- [ ] **Step 3: Implement the review page**

The page contains:

```html
<form id="review-login" autocomplete="off">
  <label for="review-key">审核密钥</label>
  <input id="review-key" type="password" required>
  <button type="submit">进入审核</button>
</form>
<main id="review-workspace" hidden>
  <iframe id="galaxy-preview" title="章节知识网预览"></iframe>
  <section class="review-summary">
    <h1 id="draft-title">章节草稿</h1>
    <p id="draft-metrics"></p>
    <ul id="draft-issues"></ul>
    <button id="approve-draft" type="button">批准并发布当前预览</button>
    <button id="reject-draft" type="button">退回修改</button>
    <p id="review-result" role="status"></p>
  </section>
</main>
```

`review.js`:

- reads `draft` and `revision` from the review-page query string;
- exchanges the entered key for an HttpOnly Cookie;
- clears the password input immediately after the exchange;
- loads review metadata from a human-review endpoint;
- sets the iframe URL with
  `` `/trainer/space/galaxy-lab/?draft=${encodeURIComponent(draftId)}&revision=${revision}` ``;
- posts the currently displayed revision and content hash on approval;
- disables approve while the request is pending;
- displays the formal chapter URL after success;
- never stores the review key in localStorage, sessionStorage, a URL, or a JS global.

- [ ] **Step 4: Run page and API tests**

```powershell
python -m pytest backend/tests/test_challenge_frontend_api.py backend/tests/test_chapter_review_api.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```powershell
git add frontend/chapter-review/index.html frontend/chapter-review/review.js frontend/chapter-review/review.css backend/tests/test_challenge_frontend_api.py
git commit -m "Add one-click chapter review interface"
```

---

### Task 8: Deliver the Custom GPT Action package and setup guide

**Files:**
- Create: `docs/custom-gpt/chapter-authoring-actions.openapi.yaml`
- Create: `docs/custom-gpt/chapter-authoring-instructions.md`
- Create: `docs/custom-gpt/setup.md`
- Create: `docs/custom-gpt/example-conversation.md`
- Create: `.env.example`
- Create: `backend/tests/test_custom_gpt_action_contract.py`

**Interfaces:**
- Consumes: the five `/api/gpt/v1` operations.
- Produces: an importable OpenAPI 3.1 schema and copy-ready GPT Instructions.

- [ ] **Step 1: Write failing contract tests**

```python
def test_custom_gpt_action_schema_exposes_only_draft_operations() -> None:
    schema = yaml.safe_load(
        Path("docs/custom-gpt/chapter-authoring-actions.openapi.yaml").read_text(encoding="utf-8")
    )
    operation_ids = {
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    }

    assert operation_ids == {
        "getProjectContract",
        "createChapterDraft",
        "updateChapterDraft",
        "getChapterDraft",
        "validateChapterDraft",
    }
    serialized = json.dumps(schema)
    assert "approve" not in serialized
    assert "publish" not in serialized


def test_example_environment_contains_no_real_secret() -> None:
    text = Path(".env.example").read_text(encoding="utf-8")
    assert "GPT_AUTHORING_KEY=replace-with-a-long-random-secret" in text
    assert "CHAPTER_REVIEW_KEY=replace-with-a-different-long-random-secret" in text
    assert "sk-" not in text
```

- [ ] **Step 2: Run contract tests and verify missing files**

```powershell
python -m pytest backend/tests/test_custom_gpt_action_contract.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: fails because the Action schema does not exist.

- [ ] **Step 3: Create the OpenAPI Action schema**

Use OpenAPI `3.1.0`, server `https://your-domain.example`, HTTP Bearer security, stable error schemas, and exactly the five operation IDs tested above. The create body requires:

```yaml
required:
  - chapter_id
  - title
  - source_markdown
  - client_request_id
  - contract_version
properties:
  chapter_id:
    type: string
    pattern: '^[a-z0-9][a-z0-9_-]{1,79}$'
  title:
    type: string
    minLength: 1
    maxLength: 160
  source_markdown:
    type: string
    minLength: 1
    maxLength: 750000
  client_request_id:
    type: string
    minLength: 8
    maxLength: 128
  contract_version:
    type: string
    const: chapter-galaxy-v1
```

- [ ] **Step 4: Create copy-ready GPT Instructions**

The Instructions explicitly require:

1. call `getProjectContract` before authoring;
2. create a complete chapter, not a partial outline;
3. submit and inspect structured issues;
4. revise until `preview_ready`;
5. return the preview URL to the user;
6. never claim publication before the website approval result;
7. never ask for or repeat the API Key;
8. never invent a publish or approve Action.

- [ ] **Step 5: Add setup and example docs**

`setup.md` documents:

- public HTTPS requirement;
- copying `.env.example` values into the runtime environment;
- using different random secrets for GPT and human review;
- replacing only the OpenAPI `servers[0].url`;
- configuring GPT Action authentication as Bearer;
- importing the OpenAPI file;
- testing contract, invalid draft, valid draft, preview, and approval;
- keeping the GPT private during initial validation;
- privacy-policy and domain-verification considerations before public sharing.

`.env.example` contains:

```dotenv
APP_PROFILE=mixed
GPT_AUTHORING_KEY=replace-with-a-long-random-secret
CHAPTER_REVIEW_KEY=replace-with-a-different-long-random-secret
CHAPTER_DRAFT_ROOT=runtime/chapter_drafts
CHAPTER_REVIEW_SESSION_TTL_SECONDS=28800
PUBLIC_BASE_URL=https://your-domain.example
CHAPTER_PUBLISH_TARGET_ROOT=.
```

- [ ] **Step 6: Run contract tests and commit**

```powershell
python -m pytest backend/tests/test_custom_gpt_action_contract.py -q --basetemp .pytest_tmp -p no:cacheprovider
git add .env.example docs/custom-gpt backend/tests/test_custom_gpt_action_contract.py
git commit -m "Document Custom GPT chapter Actions setup"
```

Expected: all selected tests pass before the commit.

---

### Task 9: End-to-end regression verification and delivery

**Files:**
- Modify only if a failing test reveals a task-scoped defect.
- Create: `docs/custom-gpt/verification-report.md`

**Interfaces:**
- Verifies all earlier interfaces as one workflow.

- [ ] **Step 1: Run focused backend tests**

```powershell
python -m pytest backend/tests/test_chapter_galaxy_asset.py backend/tests/test_gpt_draft_store.py backend/tests/test_gpt_authoring_api.py backend/tests/test_chapter_review_api.py backend/tests/test_custom_gpt_action_contract.py backend/tests/test_challenge_frontend_api.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: all focused tests pass.

- [ ] **Step 2: Run frontend module tests**

```powershell
node --test frontend/space/galaxy-lab/chapter-data-loader.test.mjs frontend/space/galaxy-lab/infinite-series-scene.test.mjs frontend/space/galaxy-lab/observatory-camera.test.mjs
```

Expected: all frontend module tests pass.

- [ ] **Step 3: Run full backend regression**

```powershell
python -m pytest backend/tests -q --basetemp .pytest_tmp -p no:cacheprovider
```

Expected: all backend tests pass.

- [ ] **Step 4: Perform a local HTTP smoke workflow**

Start:

```powershell
$env:APP_PROFILE='mixed'
$env:GPT_AUTHORING_KEY='local-authoring-test-secret'
$env:CHAPTER_REVIEW_KEY='local-review-test-secret'
$env:CHAPTER_DRAFT_ROOT='runtime/chapter_drafts-smoke'
$env:CHAPTER_PUBLISH_TARGET_ROOT='runtime/publish-smoke'
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 4173
```

From a second shell:

1. call `/api/gpt/v1/contract` with the authoring Bearer key;
2. submit the test chapter fixture;
3. open the returned review URL;
4. establish a review session;
5. load the iframe preview;
6. approve the exact revision;
7. call the published galaxy endpoint.

Expected: each request succeeds and the formal asset equals the preview asset.

- [ ] **Step 5: Record evidence**

Create `docs/custom-gpt/verification-report.md` containing:

- focused pytest command and observed count;
- Node test command and observed count;
- full backend pytest command and observed count;
- smoke-test draft ID, revision, and status without keys;
- confirmation that GPT Action schema contains no approve/publish operation;
- confirmation that no secret is committed;
- known deployment prerequisite: replace the example domain and deploy behind HTTPS.

- [ ] **Step 6: Inspect repository scope and secrets**

Run:

```powershell
git diff --check
git status --short
rg -n "local-authoring-test-secret|local-review-test-secret|sk-[A-Za-z0-9_-]+" . -g '!runtime/**' -g '!.git/**'
```

Expected:

- `git diff --check` prints nothing;
- only intended implementation files plus pre-existing unrelated changes remain;
- secret scan prints nothing.

- [ ] **Step 7: Commit the verification report**

```powershell
git add docs/custom-gpt/verification-report.md
git commit -m "Verify Custom GPT chapter authoring workflow"
```

- [ ] **Step 8: Final repository close-out**

Run:

```powershell
git log --oneline -10
git status --short
```

Report the exact commits, verification results, remaining pre-existing uncommitted files, Custom GPT setup path, and the local review URL format. Do not claim that the Custom GPT can reach the project until a public HTTPS deployment URL has been configured.
