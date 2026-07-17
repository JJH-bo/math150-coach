# AI Classroom Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first independent AI Classroom vertical slice so the Custom GPT can author, validate, version, publish, and roll back a freely structured classroom package, while the learner runtime can read the active package without any legacy challenge dependency.

**Architecture:** Add a new `app.classroom` domain and two API surfaces inside the existing FastAPI application. `/api/studio/v1` owns authenticated draft and release operations; `/api/classroom/v1` exposes only active immutable classroom content. Store JSON artifacts atomically on disk for the first slice, with revision checks, deterministic hashes, idempotency receipts, and no database dependency.

**Tech Stack:** Python 3, FastAPI, Pydantic v2, pytest, FastAPI TestClient, UTF-8 JSON files, existing `api_error` response shape.

## Global Constraints

- Do not import `ChallengeEngine`, scoring, diagnosis, mastery, question-bank, rollback/forward, review, or training modules from any new classroom package.
- A core module is one complete visible knowledge object; it may use zero or many optional segments and never requires fixed MicroNodes.
- The new runtime stores and returns classroom content only; it must not infer or expose mastery, scores, learner profiles, recommendations, review dates, or failure state.
- Studio writes require `Authorization: Bearer <STUDIO_API_KEY>`.
- Every mutable Studio request requires an `Idempotency-Key` header and an expected revision where an existing draft is changed.
- Published release files are immutable; publish and rollback change an atomic active-version pointer.
- Project A adds no new third-party dependency and no learner-facing frontend.
- JSON is written with UTF-8, `ensure_ascii=False`, sorted keys, and a trailing newline.
- Legacy APIs and tests stay green during Project A; product cutover and legacy deletion belong to Projects C and D.
- The accepted design is `docs/superpowers/specs/2026-07-18-ai-classroom-redesign-design.md`.

---

## File Structure

### New domain files

- `backend/app/classroom/__init__.py` — package exports only.
- `backend/app/classroom/models.py` — classroom package, content, draft, release, and receipt models.
- `backend/app/classroom/hashing.py` — canonical JSON and deterministic SHA-256 content hashes.
- `backend/app/classroom/validation.py` — cross-object validation and forbidden learner-analysis field checks.
- `backend/app/classroom/repository.py` — path-safe atomic JSON draft/release/active-pointer persistence.
- `backend/app/classroom/idempotency.py` — durable operation receipts and key-reuse conflict detection.
- `backend/app/classroom/authoring.py` — draft, validation, publish, and rollback orchestration.
- `backend/app/classroom/runtime.py` — read-only catalog, active package, and module projections.

### New Studio API files

- `backend/app/api/studio/__init__.py`
- `backend/app/api/studio/v1/__init__.py`
- `backend/app/api/studio/v1/auth.py` — bearer-key authentication.
- `backend/app/api/studio/v1/schemas.py` — strict request models.
- `backend/app/api/studio/v1/router.py` — capability, draft, publish, and rollback routes.

### New Classroom API files

- `backend/app/api/classroom/__init__.py`
- `backend/app/api/classroom/v1/__init__.py`
- `backend/app/api/classroom/v1/router.py` — learner-safe, read-only runtime routes.

### New data and tests

- `backend/classroom_data/seed/calculus-foundations.json` — one real classroom package with one complete module.
- `backend/tests/classroom_fixtures.py` — reusable valid payload builders.
- `backend/tests/test_classroom_models.py`
- `backend/tests/test_classroom_validation.py`
- `backend/tests/test_classroom_repository.py`
- `backend/tests/test_classroom_authoring.py`
- `backend/tests/test_studio_api.py`
- `backend/tests/test_classroom_runtime_api.py`
- `backend/tests/test_classroom_profile_wiring.py`

### Existing files modified

- `backend/app/main.py` — register Studio and Classroom routers by existing profile.
- `README.md` — describe the new foundation endpoints and local Studio key.

---

### Task 1: Classroom Package Domain

**Files:**
- Create: `backend/app/classroom/__init__.py`
- Create: `backend/app/classroom/models.py`
- Create: `backend/app/classroom/hashing.py`
- Create: `backend/tests/classroom_fixtures.py`
- Test: `backend/tests/test_classroom_models.py`

**Interfaces:**
- Produces: `ClassroomPackage`, `CoreModule`, `ContentBlock`, `DetailBranch`, `LearningSegment`, `DraftRecord`, `ReleaseRecord`, `ActivationReceipt`.
- Produces: `canonical_json(value: Any) -> str`.
- Produces: `content_hash(value: Any) -> str`.
- Consumes: Pydantic v2 only.

- [ ] **Step 1: Write the reusable valid package fixture**

Create `backend/tests/classroom_fixtures.py`:

```python
from __future__ import annotations

from typing import Any


def classroom_package_payload() -> dict[str, Any]:
    return {
        "schema_version": "classroom_package_v1",
        "package_id": "calculus-foundations",
        "title": "微积分基础课堂",
        "courses": [
            {
                "id": "math-1",
                "title": "高等数学",
                "chapters": [
                    {
                        "id": "limits",
                        "title": "极限",
                        "modules": [
                            {
                                "id": "limit-core",
                                "title": "极限的核心机制",
                                "summary": "从趋近过程理解极限，而不是把它当成代入规则。",
                                "blocks": [
                                    {
                                        "id": "limit-intro",
                                        "kind": "prose",
                                        "data": {
                                            "markdown": "极限描述的是变量趋近时，函数值稳定接近什么。"
                                        },
                                        "detail_branches": [
                                            {
                                                "id": "limit-intro-detail",
                                                "title": "为什么不是直接代入",
                                                "blocks": [
                                                    {
                                                        "id": "limit-intro-detail-prose",
                                                        "kind": "prose",
                                                        "data": {
                                                            "markdown": "趋近研究的是邻域行为，点值可以不存在或不同。"
                                                        },
                                                    }
                                                ],
                                            }
                                        ],
                                    },
                                    {
                                        "id": "limit-formula",
                                        "kind": "formula_explanation",
                                        "data": {
                                            "latex": "\\\\lim_{x\\\\to a}f(x)=L",
                                            "explanation": "当 x 足够接近 a 时，f(x) 可以任意接近 L。",
                                        },
                                    },
                                ],
                                "segments": [
                                    {
                                        "id": "limit-example-segment",
                                        "title": "用一个可消去间断点观察极限",
                                        "blocks": [
                                            {
                                                "id": "limit-example",
                                                "kind": "worked_example",
                                                "data": {
                                                    "prompt": "观察 (x²-1)/(x-1) 在 x→1 时的行为。",
                                                    "steps": [
                                                        "因式分解 x²-1=(x-1)(x+1)",
                                                        "在 x≠1 的邻域中化简为 x+1",
                                                        "因此趋近值为 2",
                                                    ],
                                                },
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                        "relations": [],
                    }
                ],
            }
        ],
        "model_instances": [],
        "assets": [],
    }
```

- [ ] **Step 2: Write failing domain-model tests**

Create `backend/tests/test_classroom_models.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.classroom.hashing import content_hash
from app.classroom.models import ClassroomPackage
from classroom_fixtures import classroom_package_payload


def test_package_accepts_free_module_blocks_and_optional_segments() -> None:
    package = ClassroomPackage.model_validate(classroom_package_payload())

    module = package.courses[0].chapters[0].modules[0]
    assert module.id == "limit-core"
    assert len(module.blocks) == 2
    assert len(module.segments) == 1
    assert module.blocks[0].detail_branches[0].blocks[0].kind == "prose"


def test_module_can_use_only_continuous_blocks_without_segments() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["modules"][0]["segments"] = []

    module = ClassroomPackage.model_validate(payload).courses[0].chapters[0].modules[0]

    assert module.blocks
    assert module.segments == []


def test_module_can_use_only_segments_without_top_level_blocks() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["modules"][0]["blocks"] = []

    module = ClassroomPackage.model_validate(payload).courses[0].chapters[0].modules[0]

    assert module.blocks == []
    assert module.segments


def test_empty_module_is_rejected() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["blocks"] = []
    module["segments"] = []

    with pytest.raises(ValidationError, match="at least one block or segment"):
        ClassroomPackage.model_validate(payload)


def test_unknown_content_block_fields_are_rejected() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["modules"][0]["blocks"][0]["score"] = 1

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ClassroomPackage.model_validate(payload)


def test_content_hash_is_stable_across_mapping_order() -> None:
    payload = classroom_package_payload()
    reordered = {key: payload[key] for key in reversed(payload)}

    assert content_hash(payload) == content_hash(reordered)
    assert content_hash(payload).startswith("sha256:")
```

- [ ] **Step 3: Run the tests and verify the new package is missing**

Run:

```bash
pytest backend/tests/test_classroom_models.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'app.classroom'`.

- [ ] **Step 4: Implement deterministic hashing**

Create `backend/app/classroom/hashing.py`:

```python
from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel


def canonical_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return canonical_value(value.model_dump(mode="json", exclude_none=True))
    if isinstance(value, dict):
        return {str(key): canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonical_value(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def content_hash(value: Any) -> str:
    encoded = canonical_json(value).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
```

- [ ] **Step 5: Implement the classroom models**

Create `backend/app/classroom/models.py` with these exact public models and field names:

```python
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContentBlockKind(str, Enum):
    PROSE = "prose"
    HEADING = "heading"
    CALLOUT = "callout"
    MATH = "math"
    FORMULA_EXPLANATION = "formula_explanation"
    DERIVATION = "derivation"
    COMPARISON = "comparison"
    WORKED_EXAMPLE = "worked_example"
    CODE_EXPLANATION = "code_explanation"
    TABLE = "table"
    MATRIX = "matrix"
    IMAGE = "image"
    MODEL_REFERENCE = "model_reference"
    GROUP = "group"


class SourceAnchor(StrictModel):
    asset_id: str
    filename: str | None = None
    page: str | None = None
    section: str | None = None
    source_span: str | None = None
    note: str | None = None


class DetailBranch(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    blocks: list["ContentBlock"] = Field(min_length=1)


class ContentBlock(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    kind: ContentBlockKind
    data: dict[str, Any]
    source_anchor: SourceAnchor | None = None
    detail_branches: list[DetailBranch] = Field(default_factory=list)


class LearningSegment(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str | None = Field(default=None, max_length=240)
    blocks: list[ContentBlock] = Field(min_length=1)


class CoreModule(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    summary: str | None = None
    blocks: list[ContentBlock] = Field(default_factory=list)
    segments: list[LearningSegment] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_content(self) -> "CoreModule":
        if not self.blocks and not self.segments:
            raise ValueError("core module requires at least one block or segment")
        return self


class ModuleRelationKind(str, Enum):
    PREREQUISITE_CONTEXT = "prerequisite_context"
    CONCEPTUAL_DEPENDENCY = "conceptual_dependency"
    CONTRAST = "contrast"
    ANALOGY = "analogy"
    DERIVATION = "derivation"
    APPLICATION = "application"
    SHARED_MODEL = "shared_model"
    CHAPTER_SYNTHESIS = "chapter_synthesis"


class ModuleRelation(StrictModel):
    id: str
    kind: ModuleRelationKind
    source_module_id: str
    target_module_id: str
    label: str | None = None


class Chapter(StrictModel):
    id: str
    title: str
    modules: list[CoreModule] = Field(min_length=1)
    relations: list[ModuleRelation] = Field(default_factory=list)


class Course(StrictModel):
    id: str
    title: str
    chapters: list[Chapter] = Field(min_length=1)


class ModelInstanceReference(StrictModel):
    instance_id: str
    model_id: str
    model_version: str
    preset: str | None = None
    initial_state: dict[str, Any] = Field(default_factory=dict)


class AssetReference(StrictModel):
    asset_id: str
    media_type: str
    uri: str
    content_hash: str | None = None


class ClassroomPackage(StrictModel):
    schema_version: Literal["classroom_package_v1"]
    package_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,79}$")
    title: str = Field(min_length=1, max_length=240)
    courses: list[Course] = Field(min_length=1)
    model_instances: list[ModelInstanceReference] = Field(default_factory=list)
    assets: list[AssetReference] = Field(default_factory=list)


class DraftRecord(StrictModel):
    draft_id: str
    revision: int = Field(ge=1)
    content_hash: str
    package: ClassroomPackage


class ReleaseRecord(StrictModel):
    package_id: str
    version: str
    content_hash: str
    package: ClassroomPackage


class ActivationReceipt(StrictModel):
    action: Literal["publish", "rollback"]
    package_id: str
    active_version: str
    previous_version: str | None = None
    content_hash: str
    activated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
```

Create `backend/app/classroom/__init__.py`:

```python
from app.classroom.models import ClassroomPackage

__all__ = ["ClassroomPackage"]
```

- [ ] **Step 6: Run the model tests**

Run:

```bash
pytest backend/tests/test_classroom_models.py -q
```

Expected: `6 passed`.

- [ ] **Step 7: Commit the domain**

```bash
git add backend/app/classroom backend/tests/classroom_fixtures.py backend/tests/test_classroom_models.py
git commit -m "Build AI classroom package domain"
```

---

### Task 2: Cross-Object Classroom Validation

**Files:**
- Create: `backend/app/classroom/validation.py`
- Test: `backend/tests/test_classroom_validation.py`

**Interfaces:**
- Consumes: `ClassroomPackage`.
- Produces: `ValidationIssue`, `ClassroomValidationReport`.
- Produces: `ClassroomPackageValidator.validate(package: ClassroomPackage) -> ClassroomValidationReport`.

- [ ] **Step 1: Write failing validation tests**

Create `backend/tests/test_classroom_validation.py`:

```python
from __future__ import annotations

from app.classroom.models import ClassroomPackage
from app.classroom.validation import ClassroomPackageValidator
from classroom_fixtures import classroom_package_payload


def validate(payload: dict) -> object:
    package = ClassroomPackage.model_validate(payload)
    return ClassroomPackageValidator().validate(package)


def test_valid_package_passes_cross_object_validation() -> None:
    report = validate(classroom_package_payload())

    assert report.passed is True
    assert report.issues == []


def test_duplicate_content_ids_report_exact_path() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["blocks"][1]["id"] = module["blocks"][0]["id"]

    report = validate(payload)

    assert report.passed is False
    assert report.issues[0].code == "duplicate_object_id"
    assert report.issues[0].path.endswith(".blocks[1].id")


def test_unknown_relation_endpoint_is_rejected() -> None:
    payload = classroom_package_payload()
    chapter = payload["courses"][0]["chapters"][0]
    chapter["relations"] = [
        {
            "id": "relation-missing",
            "kind": "contrast",
            "source_module_id": "limit-core",
            "target_module_id": "missing-module",
        }
    ]

    report = validate(payload)

    assert {issue.code for issue in report.issues} == {"unknown_relation_target"}


def test_learner_analysis_keys_are_rejected_inside_flexible_data() -> None:
    payload = classroom_package_payload()
    block = payload["courses"][0]["chapters"][0]["modules"][0]["blocks"][0]
    block["data"]["mastery_state"] = {"score": 80}

    report = validate(payload)

    assert report.passed is False
    assert report.issues[0].code == "learner_analysis_field_forbidden"
    assert "mastery_state" in report.issues[0].path
```

- [ ] **Step 2: Verify the validator is missing**

Run:

```bash
pytest backend/tests/test_classroom_validation.py -q
```

Expected: collection fails because `app.classroom.validation` does not exist.

- [ ] **Step 3: Implement the validation report and validator**

Create `backend/app/classroom/validation.py`:

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.classroom.models import ClassroomPackage, ContentBlock


FORBIDDEN_LEARNER_ANALYSIS_KEYS = {
    "mastery_state",
    "diagnosis",
    "review_schedule",
    "question_bank",
    "boss_challenge",
    "learner_profile",
    "recommended_next_step",
    "ability_profile",
}


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Literal["error", "warning"]
    code: str
    path: str
    message: str


class ClassroomValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    issues: list[ValidationIssue]


class ClassroomPackageValidator:
    def validate(self, package: ClassroomPackage) -> ClassroomValidationReport:
        issues: list[ValidationIssue] = []
        seen_ids: dict[str, str] = {}

        def record_id(object_id: str, path: str) -> None:
            previous = seen_ids.get(object_id)
            if previous is not None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="duplicate_object_id",
                        path=path,
                        message=f"Object id {object_id!r} is already used at {previous}.",
                    )
                )
            else:
                seen_ids[object_id] = path

        for course_index, course in enumerate(package.courses):
            course_path = f"courses[{course_index}]"
            record_id(course.id, f"{course_path}.id")
            for chapter_index, chapter in enumerate(course.chapters):
                chapter_path = f"{course_path}.chapters[{chapter_index}]"
                record_id(chapter.id, f"{chapter_path}.id")
                module_ids = {module.id for module in chapter.modules}
                for module_index, module in enumerate(chapter.modules):
                    module_path = f"{chapter_path}.modules[{module_index}]"
                    record_id(module.id, f"{module_path}.id")
                    for block_index, block in enumerate(module.blocks):
                        self._validate_block(
                            block,
                            f"{module_path}.blocks[{block_index}]",
                            record_id,
                            issues,
                        )
                    for segment_index, segment in enumerate(module.segments):
                        segment_path = f"{module_path}.segments[{segment_index}]"
                        record_id(segment.id, f"{segment_path}.id")
                        for block_index, block in enumerate(segment.blocks):
                            self._validate_block(
                                block,
                                f"{segment_path}.blocks[{block_index}]",
                                record_id,
                                issues,
                            )
                for relation_index, relation in enumerate(chapter.relations):
                    relation_path = f"{chapter_path}.relations[{relation_index}]"
                    record_id(relation.id, f"{relation_path}.id")
                    if relation.source_module_id not in module_ids:
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                code="unknown_relation_source",
                                path=f"{relation_path}.source_module_id",
                                message="Relation source module does not exist in this chapter.",
                            )
                        )
                    if relation.target_module_id not in module_ids:
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                code="unknown_relation_target",
                                path=f"{relation_path}.target_module_id",
                                message="Relation target module does not exist in this chapter.",
                            )
                        )

        return ClassroomValidationReport(
            passed=not any(issue.severity == "error" for issue in issues),
            issues=issues,
        )

    def _validate_block(
        self,
        block: ContentBlock,
        path: str,
        record_id: Any,
        issues: list[ValidationIssue],
    ) -> None:
        record_id(block.id, f"{path}.id")
        self._find_forbidden_keys(block.data, f"{path}.data", issues)
        for branch_index, branch in enumerate(block.detail_branches):
            branch_path = f"{path}.detail_branches[{branch_index}]"
            record_id(branch.id, f"{branch_path}.id")
            for block_index, child in enumerate(branch.blocks):
                self._validate_block(
                    child,
                    f"{branch_path}.blocks[{block_index}]",
                    record_id,
                    issues,
                )

    def _find_forbidden_keys(
        self,
        value: Any,
        path: str,
        issues: list[ValidationIssue],
    ) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in FORBIDDEN_LEARNER_ANALYSIS_KEYS:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="learner_analysis_field_forbidden",
                            path=child_path,
                            message=f"Classroom content cannot contain learner-analysis field {key!r}.",
                        )
                    )
                self._find_forbidden_keys(child, child_path, issues)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._find_forbidden_keys(child, f"{path}[{index}]", issues)
```

- [ ] **Step 4: Run validation tests**

Run:

```bash
pytest backend/tests/test_classroom_validation.py -q
```

Expected: `4 passed`.

- [ ] **Step 5: Commit validation**

```bash
git add backend/app/classroom/validation.py backend/tests/test_classroom_validation.py
git commit -m "Validate AI classroom package structure"
```

---

### Task 3: Atomic Draft and Release Repository

**Files:**
- Create: `backend/app/classroom/repository.py`
- Test: `backend/tests/test_classroom_repository.py`

**Interfaces:**
- Consumes: `ClassroomPackage`, `DraftRecord`, `ReleaseRecord`, `ActivationReceipt`, `content_hash`.
- Produces: `ClassroomRepository`.
- Produces exceptions: `ClassroomNotFoundError`, `ClassroomConflictError`, `ClassroomPathError`.
- Produces methods:
  - `create_draft(draft_id: str, package: ClassroomPackage) -> DraftRecord`
  - `get_draft(draft_id: str) -> DraftRecord`
  - `update_draft(draft_id: str, expected_revision: int, package: ClassroomPackage) -> DraftRecord`
  - `publish(draft_id: str, expected_revision: int) -> ActivationReceipt`
  - `rollback(package_id: str, version: str) -> ActivationReceipt`
  - `get_active_release(package_id: str) -> ReleaseRecord`
  - `list_active_releases() -> list[ReleaseRecord]`

- [ ] **Step 1: Write failing repository tests**

Create `backend/tests/test_classroom_repository.py`:

```python
from __future__ import annotations

import json

import pytest

from app.classroom.models import ClassroomPackage
from app.classroom.repository import (
    ClassroomConflictError,
    ClassroomPathError,
    ClassroomRepository,
)
from classroom_fixtures import classroom_package_payload


def package() -> ClassroomPackage:
    return ClassroomPackage.model_validate(classroom_package_payload())


def test_create_and_update_draft_use_revisions_and_atomic_json(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)
    created = repository.create_draft("limits-draft", package())
    payload = created.package.model_copy(update={"title": "更新后的课堂"})

    updated = repository.update_draft("limits-draft", 1, payload)

    assert created.revision == 1
    assert updated.revision == 2
    assert repository.get_draft("limits-draft").package.title == "更新后的课堂"
    stored = json.loads((tmp_path / "drafts" / "limits-draft.json").read_text("utf-8"))
    assert stored["revision"] == 2
    assert not list((tmp_path / "drafts").glob("*.tmp"))


def test_stale_draft_revision_is_rejected(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)
    repository.create_draft("limits-draft", package())

    with pytest.raises(ClassroomConflictError, match="expected revision 2"):
        repository.update_draft("limits-draft", 2, package())


def test_publish_creates_immutable_release_and_active_pointer(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)
    repository.create_draft("limits-draft", package())

    receipt = repository.publish("limits-draft", 1)
    active = repository.get_active_release("calculus-foundations")

    assert receipt.action == "publish"
    assert receipt.active_version.startswith("r-")
    assert active.version == receipt.active_version
    assert active.package.package_id == "calculus-foundations"


def test_rollback_repoints_active_release_without_mutating_release(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)
    repository.create_draft("limits-draft", package())
    first = repository.publish("limits-draft", 1)
    changed = package().model_copy(update={"title": "第二版"})
    repository.update_draft("limits-draft", 1, changed)
    second = repository.publish("limits-draft", 2)

    receipt = repository.rollback("calculus-foundations", first.active_version)

    assert receipt.previous_version == second.active_version
    assert repository.get_active_release("calculus-foundations").version == first.active_version
    assert (
        tmp_path
        / "packages"
        / "calculus-foundations"
        / "releases"
        / f"{second.active_version}.json"
    ).exists()


def test_path_traversal_identifiers_are_rejected(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)

    with pytest.raises(ClassroomPathError):
        repository.create_draft("../outside", package())
```

- [ ] **Step 2: Verify repository tests fail**

Run:

```bash
pytest backend/tests/test_classroom_repository.py -q
```

Expected: collection fails because `app.classroom.repository` does not exist.

- [ ] **Step 3: Implement the repository**

Create `backend/app/classroom/repository.py`. Use the following public structure and exact file layout:

```python
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.classroom.hashing import content_hash
from app.classroom.models import (
    ActivationReceipt,
    ClassroomPackage,
    DraftRecord,
    ReleaseRecord,
)


SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")


class ClassroomRepositoryError(ValueError):
    pass


class ClassroomNotFoundError(ClassroomRepositoryError):
    pass


class ClassroomConflictError(ClassroomRepositoryError):
    pass


class ClassroomPathError(ClassroomRepositoryError):
    pass


class ClassroomRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def create_draft(self, draft_id: str, package: ClassroomPackage) -> DraftRecord:
        path = self._draft_path(draft_id)
        if path.exists():
            raise ClassroomConflictError(f"draft already exists: {draft_id}")
        record = DraftRecord(
            draft_id=draft_id,
            revision=1,
            content_hash=content_hash(package),
            package=package,
        )
        self._write_json(path, record)
        return record

    def get_draft(self, draft_id: str) -> DraftRecord:
        return DraftRecord.model_validate(self._read_json(self._draft_path(draft_id)))

    def update_draft(
        self,
        draft_id: str,
        expected_revision: int,
        package: ClassroomPackage,
    ) -> DraftRecord:
        current = self.get_draft(draft_id)
        if current.revision != expected_revision:
            raise ClassroomConflictError(
                f"draft {draft_id} is revision {current.revision}; "
                f"expected revision {expected_revision}"
            )
        record = DraftRecord(
            draft_id=draft_id,
            revision=current.revision + 1,
            content_hash=content_hash(package),
            package=package,
        )
        self._write_json(self._draft_path(draft_id), record)
        return record

    def publish(self, draft_id: str, expected_revision: int) -> ActivationReceipt:
        draft = self.get_draft(draft_id)
        if draft.revision != expected_revision:
            raise ClassroomConflictError(
                f"draft {draft_id} is revision {draft.revision}; "
                f"expected revision {expected_revision}"
            )
        version = f"r-{draft.content_hash.removeprefix('sha256:')[:16]}"
        release = ReleaseRecord(
            package_id=draft.package.package_id,
            version=version,
            content_hash=draft.content_hash,
            package=draft.package,
        )
        release_path = self._release_path(draft.package.package_id, version)
        if not release_path.exists():
            self._write_json(release_path, release)
        previous = self._read_active_version(draft.package.package_id)
        receipt = ActivationReceipt(
            action="publish",
            package_id=draft.package.package_id,
            active_version=version,
            previous_version=previous,
            content_hash=draft.content_hash,
        )
        self._write_active_pointer(receipt)
        return receipt

    def rollback(self, package_id: str, version: str) -> ActivationReceipt:
        target = ReleaseRecord.model_validate(
            self._read_json(self._release_path(package_id, version))
        )
        previous = self._read_active_version(package_id)
        receipt = ActivationReceipt(
            action="rollback",
            package_id=package_id,
            active_version=target.version,
            previous_version=previous,
            content_hash=target.content_hash,
        )
        self._write_active_pointer(receipt)
        return receipt

    def get_active_release(self, package_id: str) -> ReleaseRecord:
        version = self._read_active_version(package_id)
        if version is None:
            raise ClassroomNotFoundError(f"active package not found: {package_id}")
        return ReleaseRecord.model_validate(
            self._read_json(self._release_path(package_id, version))
        )

    def list_active_releases(self) -> list[ReleaseRecord]:
        active_root = self.root / "active"
        if not active_root.exists():
            return []
        releases = [
            self.get_active_release(path.stem)
            for path in active_root.glob("*.json")
        ]
        return sorted(releases, key=lambda item: item.package_id)

    def _draft_path(self, draft_id: str) -> Path:
        return self.root / "drafts" / f"{self._safe_id(draft_id)}.json"

    def _release_path(self, package_id: str, version: str) -> Path:
        return (
            self.root
            / "packages"
            / self._safe_id(package_id)
            / "releases"
            / f"{self._safe_id(version)}.json"
        )

    def _active_path(self, package_id: str) -> Path:
        return self.root / "active" / f"{self._safe_id(package_id)}.json"

    def _safe_id(self, value: str) -> str:
        if not SAFE_ID.fullmatch(value):
            raise ClassroomPathError(f"unsafe classroom identifier: {value}")
        return value

    def _read_active_version(self, package_id: str) -> str | None:
        path = self._active_path(package_id)
        if not path.exists():
            return None
        return str(self._read_json(path)["active_version"])

    def _write_active_pointer(self, receipt: ActivationReceipt) -> None:
        self._write_json(
            self._active_path(receipt.package_id),
            {
                "package_id": receipt.package_id,
                "active_version": receipt.active_version,
                "content_hash": receipt.content_hash,
                "activated_at": receipt.activated_at,
            },
        )

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise ClassroomNotFoundError(f"classroom artifact not found: {path.name}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ClassroomRepositoryError(
                f"invalid classroom artifact: {path.name}"
            ) from exc
        if not isinstance(value, dict):
            raise ClassroomRepositoryError(
                f"classroom artifact root must be an object: {path.name}"
            )
        return value

    def _write_json(self, path: Path, value: BaseModel | dict[str, Any]) -> None:
        payload = (
            value.model_dump(mode="json", exclude_none=True)
            if isinstance(value, BaseModel)
            else value
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f"{path.suffix}.{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
```

- [ ] **Step 4: Run repository tests**

Run:

```bash
pytest backend/tests/test_classroom_repository.py -q
```

Expected: `5 passed`.

- [ ] **Step 5: Commit persistence**

```bash
git add backend/app/classroom/repository.py backend/tests/test_classroom_repository.py
git commit -m "Persist classroom drafts and releases"
```

---

### Task 4: Idempotent Authoring Service

**Files:**
- Create: `backend/app/classroom/idempotency.py`
- Create: `backend/app/classroom/authoring.py`
- Test: `backend/tests/test_classroom_authoring.py`

**Interfaces:**
- Consumes: `ClassroomRepository`, `ClassroomPackageValidator`.
- Produces: `IdempotencyLedger.execute(scope, key, request_payload, operation) -> dict[str, Any]`.
- Produces: `ClassroomAuthoringService` methods returning JSON-safe dictionaries.
- Produces: `IdempotencyConflictError`, `ClassroomValidationError`.

- [ ] **Step 1: Write failing authoring tests**

Create `backend/tests/test_classroom_authoring.py`:

```python
from __future__ import annotations

import pytest

from app.classroom.authoring import (
    ClassroomAuthoringService,
    ClassroomValidationError,
)
from app.classroom.idempotency import IdempotencyConflictError, IdempotencyLedger
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from classroom_fixtures import classroom_package_payload


def service(tmp_path) -> ClassroomAuthoringService:
    repository = ClassroomRepository(tmp_path)
    ledger = IdempotencyLedger(tmp_path / "operations")
    return ClassroomAuthoringService(repository, ledger)


def test_repeated_create_with_same_key_returns_same_receipt(tmp_path) -> None:
    authoring = service(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())

    first = authoring.create_draft("limits", package, idempotency_key="create-1")
    second = authoring.create_draft("limits", package, idempotency_key="create-1")

    assert first == second
    assert first["revision"] == 1


def test_reusing_key_with_different_request_is_rejected(tmp_path) -> None:
    authoring = service(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())
    authoring.create_draft("limits", package, idempotency_key="create-1")
    changed = package.model_copy(update={"title": "不同请求"})

    with pytest.raises(IdempotencyConflictError):
        authoring.create_draft("limits", changed, idempotency_key="create-1")


def test_invalid_cross_object_package_cannot_publish(tmp_path) -> None:
    authoring = service(tmp_path)
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["relations"] = [
        {
            "id": "broken-relation",
            "kind": "contrast",
            "source_module_id": "limit-core",
            "target_module_id": "missing",
        }
    ]
    package = ClassroomPackage.model_validate(payload)
    authoring.create_draft("limits", package, idempotency_key="create-1")

    with pytest.raises(ClassroomValidationError) as exc:
        authoring.publish("limits", 1, idempotency_key="publish-1")

    assert exc.value.report.issues[0].code == "unknown_relation_target"


def test_publish_and_rollback_return_explicit_receipts(tmp_path) -> None:
    authoring = service(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())
    authoring.create_draft("limits", package, idempotency_key="create-1")
    published = authoring.publish("limits", 1, idempotency_key="publish-1")

    rolled_back = authoring.rollback(
        package.package_id,
        published["active_version"],
        idempotency_key="rollback-1",
    )

    assert published["action"] == "publish"
    assert rolled_back["action"] == "rollback"
    assert rolled_back["active_version"] == published["active_version"]
```

- [ ] **Step 2: Verify authoring modules are missing**

Run:

```bash
pytest backend/tests/test_classroom_authoring.py -q
```

Expected: collection fails because `app.classroom.authoring` does not exist.

- [ ] **Step 3: Implement the idempotency ledger**

Create `backend/app/classroom/idempotency.py`:

```python
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable

from app.classroom.hashing import content_hash


class IdempotencyConflictError(ValueError):
    pass


class IdempotencyLedger:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def execute(
        self,
        scope: str,
        key: str,
        request_payload: Any,
        operation: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        request_hash = content_hash(request_payload)
        path = self._path(scope, key)
        if path.exists():
            stored = json.loads(path.read_text(encoding="utf-8"))
            if stored["request_hash"] != request_hash:
                raise IdempotencyConflictError(
                    f"idempotency key {key!r} was reused with a different request"
                )
            return dict(stored["response"])
        response = operation()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(
                {"request_hash": request_hash, "response": response},
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return response

    def _path(self, scope: str, key: str) -> Path:
        digest = hashlib.sha256(f"{scope}:{key}".encode("utf-8")).hexdigest()
        return self.root / f"{digest}.json"
```

- [ ] **Step 4: Implement the authoring service**

Create `backend/app/classroom/authoring.py`:

```python
from __future__ import annotations

from app.classroom.idempotency import IdempotencyLedger
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from app.classroom.validation import (
    ClassroomPackageValidator,
    ClassroomValidationReport,
)


class ClassroomValidationError(ValueError):
    def __init__(self, report: ClassroomValidationReport) -> None:
        super().__init__("classroom package validation failed")
        self.report = report


class ClassroomAuthoringService:
    def __init__(
        self,
        repository: ClassroomRepository,
        ledger: IdempotencyLedger,
        validator: ClassroomPackageValidator | None = None,
    ) -> None:
        self.repository = repository
        self.ledger = ledger
        self.validator = validator or ClassroomPackageValidator()

    def create_draft(
        self,
        draft_id: str,
        package: ClassroomPackage,
        *,
        idempotency_key: str,
    ) -> dict:
        return self.ledger.execute(
            f"create-draft:{draft_id}",
            idempotency_key,
            package,
            lambda: self.repository.create_draft(draft_id, package).model_dump(
                mode="json", exclude_none=True
            ),
        )

    def get_draft(self, draft_id: str) -> dict:
        return self.repository.get_draft(draft_id).model_dump(
            mode="json", exclude_none=True
        )

    def update_draft(
        self,
        draft_id: str,
        expected_revision: int,
        package: ClassroomPackage,
        *,
        idempotency_key: str,
    ) -> dict:
        request = {
            "expected_revision": expected_revision,
            "package": package.model_dump(mode="json", exclude_none=True),
        }
        return self.ledger.execute(
            f"update-draft:{draft_id}",
            idempotency_key,
            request,
            lambda: self.repository.update_draft(
                draft_id, expected_revision, package
            ).model_dump(mode="json", exclude_none=True),
        )

    def validate(self, draft_id: str) -> dict:
        record = self.repository.get_draft(draft_id)
        return self.validator.validate(record.package).model_dump(mode="json")

    def publish(
        self,
        draft_id: str,
        expected_revision: int,
        *,
        idempotency_key: str,
    ) -> dict:
        record = self.repository.get_draft(draft_id)
        report = self.validator.validate(record.package)
        if not report.passed:
            raise ClassroomValidationError(report)
        return self.ledger.execute(
            f"publish:{draft_id}",
            idempotency_key,
            {"expected_revision": expected_revision, "hash": record.content_hash},
            lambda: self.repository.publish(
                draft_id, expected_revision
            ).model_dump(mode="json", exclude_none=True),
        )

    def rollback(
        self,
        package_id: str,
        version: str,
        *,
        idempotency_key: str,
    ) -> dict:
        return self.ledger.execute(
            f"rollback:{package_id}",
            idempotency_key,
            {"version": version},
            lambda: self.repository.rollback(package_id, version).model_dump(
                mode="json", exclude_none=True
            ),
        )
```

- [ ] **Step 5: Run authoring tests**

Run:

```bash
pytest backend/tests/test_classroom_authoring.py -q
```

Expected: `4 passed`.

- [ ] **Step 6: Commit the authoring service**

```bash
git add backend/app/classroom/idempotency.py backend/app/classroom/authoring.py backend/tests/test_classroom_authoring.py
git commit -m "Add reliable classroom authoring service"
```

---

### Task 5: Authenticated Studio Capability and Authoring API

**Files:**
- Create: `backend/app/api/studio/__init__.py`
- Create: `backend/app/api/studio/v1/__init__.py`
- Create: `backend/app/api/studio/v1/auth.py`
- Create: `backend/app/api/studio/v1/schemas.py`
- Create: `backend/app/api/studio/v1/router.py`
- Test: `backend/tests/test_studio_api.py`

**Interfaces:**
- Consumes: `ClassroomAuthoringService`.
- Produces: `router` at `/api/studio/v1`.
- Produces operations with stable IDs:
  - `getStudioCapabilities`
  - `createClassroomDraft`
  - `getClassroomDraft`
  - `updateClassroomDraft`
  - `validateClassroomDraft`
  - `publishClassroomDraft`
  - `rollbackClassroomPackage`

- [ ] **Step 1: Write failing Studio API tests**

Create `backend/tests/test_studio_api.py`:

```python
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.studio.v1.router import create_studio_router
from app.classroom.authoring import ClassroomAuthoringService
from app.classroom.idempotency import IdempotencyLedger
from app.classroom.repository import ClassroomRepository
from classroom_fixtures import classroom_package_payload


def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("STUDIO_API_KEY", "studio-test-key")
    service = ClassroomAuthoringService(
        ClassroomRepository(tmp_path),
        IdempotencyLedger(tmp_path / "operations"),
    )
    app = FastAPI()
    app.include_router(create_studio_router(lambda: service))
    return TestClient(app)


def headers(key: str = "studio-test-key", operation: str = "operation-1") -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Idempotency-Key": operation,
    }


def test_studio_rejects_missing_and_invalid_bearer_key(tmp_path, monkeypatch) -> None:
    studio = client(tmp_path, monkeypatch)

    assert studio.get("/api/studio/v1/capabilities").status_code == 401
    assert studio.get(
        "/api/studio/v1/capabilities",
        headers={"Authorization": "Bearer wrong"},
    ).status_code == 401


def test_capabilities_describe_free_modules_and_no_analysis_systems(
    tmp_path, monkeypatch
) -> None:
    response = client(tmp_path, monkeypatch).get(
        "/api/studio/v1/capabilities",
        headers=headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "classroom_package_v1"
    assert payload["module_structure"] == "free_composition"
    assert "formula_explanation" in payload["content_block_kinds"]
    assert payload["learner_analysis_capabilities"] == []


def test_create_validate_publish_and_rollback_workflow(tmp_path, monkeypatch) -> None:
    studio = client(tmp_path, monkeypatch)
    created = studio.post(
        "/api/studio/v1/drafts",
        headers=headers(operation="create"),
        json={"draft_id": "limits", "package": classroom_package_payload()},
    )
    validated = studio.post(
        "/api/studio/v1/drafts/limits/validate",
        headers={"Authorization": "Bearer studio-test-key"},
    )
    published = studio.post(
        "/api/studio/v1/drafts/limits/publish",
        headers=headers(operation="publish"),
        json={"expected_revision": 1},
    )
    version = published.json()["active_version"]
    rolled_back = studio.post(
        "/api/studio/v1/packages/calculus-foundations/rollback",
        headers=headers(operation="rollback"),
        json={"version": version},
    )

    assert created.status_code == 201
    assert validated.json()["passed"] is True
    assert published.status_code == 200
    assert rolled_back.json()["active_version"] == version


def test_update_requires_correct_revision_and_idempotency_key(
    tmp_path, monkeypatch
) -> None:
    studio = client(tmp_path, monkeypatch)
    studio.post(
        "/api/studio/v1/drafts",
        headers=headers(operation="create"),
        json={"draft_id": "limits", "package": classroom_package_payload()},
    )
    payload = classroom_package_payload()
    payload["title"] = "更新后的课堂"

    stale = studio.put(
        "/api/studio/v1/drafts/limits",
        headers=headers(operation="update"),
        json={"expected_revision": 2, "package": payload},
    )

    assert stale.status_code == 409
    assert stale.json()["detail"]["error_code"] == "classroom_revision_conflict"
```

- [ ] **Step 2: Verify Studio modules are missing**

Run:

```bash
pytest backend/tests/test_studio_api.py -q
```

Expected: collection fails because `app.api.studio.v1.router` does not exist.

- [ ] **Step 3: Implement Studio authentication**

Create `backend/app/api/studio/v1/auth.py`:

```python
from __future__ import annotations

import os
import secrets

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.schemas import api_error


bearer = HTTPBearer(auto_error=False)


def require_studio_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> None:
    configured = os.getenv("STUDIO_API_KEY", "")
    if not configured:
        raise api_error(
            503,
            "studio_api_key_not_configured",
            "STUDIO_API_KEY is not configured.",
        )
    provided = credentials.credentials if credentials else ""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise api_error(401, "studio_auth_required", "Studio bearer authentication is required.")
    if not secrets.compare_digest(provided, configured):
        raise api_error(401, "studio_auth_invalid", "Studio bearer authentication failed.")
```

- [ ] **Step 4: Implement strict Studio request schemas**

Create `backend/app/api/studio/v1/schemas.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.classroom.models import ClassroomPackage


class StudioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateDraftRequest(StudioRequest):
    draft_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
    package: ClassroomPackage


class UpdateDraftRequest(StudioRequest):
    expected_revision: int = Field(ge=1)
    package: ClassroomPackage


class PublishDraftRequest(StudioRequest):
    expected_revision: int = Field(ge=1)


class RollbackPackageRequest(StudioRequest):
    version: str = Field(pattern=r"^r-[a-f0-9]{16}$")
```

- [ ] **Step 5: Implement the Studio router**

Create `backend/app/api/studio/v1/router.py` with `create_studio_router(service_factory)` so tests can inject a temporary service. Use `api_error` for all mapped failures and require `Idempotency-Key` on mutable routes:

```python
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.studio.v1.auth import require_studio_key
from app.api.studio.v1.schemas import (
    CreateDraftRequest,
    PublishDraftRequest,
    RollbackPackageRequest,
    UpdateDraftRequest,
)
from app.api.v1.schemas import api_error
from app.classroom.authoring import (
    ClassroomAuthoringService,
    ClassroomValidationError,
)
from app.classroom.idempotency import IdempotencyConflictError, IdempotencyLedger
from app.classroom.models import ContentBlockKind
from app.classroom.repository import (
    ClassroomConflictError,
    ClassroomNotFoundError,
    ClassroomRepository,
    ClassroomRepositoryError,
)


ServiceFactory = Callable[[], ClassroomAuthoringService]


def default_service() -> ClassroomAuthoringService:
    root = Path(os.getenv("CLASSROOM_DATA_ROOT", Path.cwd() / "classroom_data"))
    return ClassroomAuthoringService(
        ClassroomRepository(root),
        IdempotencyLedger(root / "operations"),
    )


def create_studio_router(
    service_factory: ServiceFactory = default_service,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/studio/v1",
        tags=["classroom-studio"],
        dependencies=[Depends(require_studio_key)],
    )

    @router.get("/capabilities", operation_id="getStudioCapabilities")
    def capabilities() -> dict:
        return {
            "studio_version": "studio_v1",
            "schema_version": "classroom_package_v1",
            "module_structure": "free_composition",
            "content_block_kinds": [kind.value for kind in ContentBlockKind],
            "mutable_operations_require_idempotency_key": True,
            "learner_analysis_capabilities": [],
        }

    @router.post("/drafts", status_code=201, operation_id="createClassroomDraft")
    def create_draft(
        request: CreateDraftRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: service_factory().create_draft(
                request.draft_id,
                request.package,
                idempotency_key=idempotency_key,
            )
        )

    @router.get("/drafts/{draft_id}", operation_id="getClassroomDraft")
    def get_draft(draft_id: str) -> dict:
        return _map_errors(lambda: service_factory().get_draft(draft_id))

    @router.put("/drafts/{draft_id}", operation_id="updateClassroomDraft")
    def update_draft(
        draft_id: str,
        request: UpdateDraftRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: service_factory().update_draft(
                draft_id,
                request.expected_revision,
                request.package,
                idempotency_key=idempotency_key,
            )
        )

    @router.post(
        "/drafts/{draft_id}/validate",
        operation_id="validateClassroomDraft",
    )
    def validate_draft(draft_id: str) -> dict:
        return _map_errors(lambda: service_factory().validate(draft_id))

    @router.post(
        "/drafts/{draft_id}/publish",
        operation_id="publishClassroomDraft",
    )
    def publish_draft(
        draft_id: str,
        request: PublishDraftRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: service_factory().publish(
                draft_id,
                request.expected_revision,
                idempotency_key=idempotency_key,
            )
        )

    @router.post(
        "/packages/{package_id}/rollback",
        operation_id="rollbackClassroomPackage",
    )
    def rollback_package(
        package_id: str,
        request: RollbackPackageRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: service_factory().rollback(
                package_id,
                request.version,
                idempotency_key=idempotency_key,
            )
        )

    return router


def _map_errors(operation: Callable[[], dict]) -> dict:
    try:
        return operation()
    except ClassroomValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "classroom_validation_failed",
                "message": "Classroom package validation failed.",
                "validation": exc.report.model_dump(mode="json"),
            },
        )
    except IdempotencyConflictError as exc:
        raise api_error(409, "idempotency_key_conflict", str(exc))
    except ClassroomConflictError as exc:
        raise api_error(409, "classroom_revision_conflict", str(exc))
    except ClassroomNotFoundError as exc:
        raise api_error(404, "classroom_not_found", str(exc))
    except ClassroomRepositoryError as exc:
        raise api_error(400, "classroom_repository_error", str(exc))


router = create_studio_router()
```

Create empty `__init__.py` files for `backend/app/api/studio/` and `backend/app/api/studio/v1/`.

- [ ] **Step 6: Run Studio API tests**

Run:

```bash
pytest backend/tests/test_studio_api.py -q
```

Expected: `4 passed`.

- [ ] **Step 7: Verify OpenAPI operation IDs**

Run:

```bash
pytest backend/tests/test_studio_api.py -q
```

Expected: no duplicate-operation warnings and all tests pass.

- [ ] **Step 8: Commit the Studio API**

```bash
git add backend/app/api/studio backend/tests/test_studio_api.py
git commit -m "Expose authenticated AI classroom Studio API"
```

---

### Task 6: Read-Only Classroom Runtime API

**Files:**
- Create: `backend/app/classroom/runtime.py`
- Create: `backend/app/api/classroom/__init__.py`
- Create: `backend/app/api/classroom/v1/__init__.py`
- Create: `backend/app/api/classroom/v1/router.py`
- Test: `backend/tests/test_classroom_runtime_api.py`

**Interfaces:**
- Consumes: active `ReleaseRecord` values from `ClassroomRepository`.
- Produces: `ClassroomRuntimeService.catalog()`, `active_package(package_id)`, and `module(package_id, module_id)`.
- Produces: public routes:
  - `GET /api/classroom/v1/catalog`
  - `GET /api/classroom/v1/packages/{package_id}`
  - `GET /api/classroom/v1/packages/{package_id}/modules/{module_id}`

- [ ] **Step 1: Write failing runtime API tests**

Create `backend/tests/test_classroom_runtime_api.py`:

```python
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.classroom.v1.router import create_classroom_router
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from app.classroom.runtime import ClassroomRuntimeService
from classroom_fixtures import classroom_package_payload


def client(tmp_path) -> TestClient:
    repository = ClassroomRepository(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())
    repository.create_draft("limits", package)
    repository.publish("limits", 1)
    app = FastAPI()
    app.include_router(
        create_classroom_router(lambda: ClassroomRuntimeService(repository))
    )
    return TestClient(app)


def test_catalog_lists_only_active_packages(tmp_path) -> None:
    response = client(tmp_path).get("/api/classroom/v1/catalog")

    assert response.status_code == 200
    assert response.json()["packages"][0]["package_id"] == "calculus-foundations"


def test_active_package_returns_release_context_and_content(tmp_path) -> None:
    response = client(tmp_path).get(
        "/api/classroom/v1/packages/calculus-foundations"
    )

    assert response.status_code == 200
    assert response.json()["version"].startswith("r-")
    assert response.json()["package"]["courses"][0]["chapters"][0]["id"] == "limits"


def test_module_projection_keeps_complete_module_content(tmp_path) -> None:
    response = client(tmp_path).get(
        "/api/classroom/v1/packages/calculus-foundations/modules/limit-core"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"]["id"] == "limit-core"
    assert len(payload["module"]["blocks"]) == 2
    assert payload["module"]["segments"][0]["id"] == "limit-example-segment"


def test_runtime_payload_has_no_learner_analysis_fields(tmp_path) -> None:
    response = client(tmp_path).get(
        "/api/classroom/v1/packages/calculus-foundations"
    )
    serialized = response.text

    for forbidden in (
        "mastery",
        "diagnosis",
        "score",
        "review_schedule",
        "recommended_next_step",
        "boss_challenge",
    ):
        assert forbidden not in serialized
```

- [ ] **Step 2: Verify runtime modules are missing**

Run:

```bash
pytest backend/tests/test_classroom_runtime_api.py -q
```

Expected: collection fails because `app.classroom.runtime` does not exist.

- [ ] **Step 3: Implement the runtime service**

Create `backend/app/classroom/runtime.py`:

```python
from __future__ import annotations

from app.classroom.repository import ClassroomNotFoundError, ClassroomRepository


class ClassroomRuntimeService:
    def __init__(self, repository: ClassroomRepository) -> None:
        self.repository = repository

    def catalog(self) -> dict:
        packages = [
            {
                "package_id": release.package_id,
                "title": release.package.title,
                "version": release.version,
                "content_hash": release.content_hash,
                "courses": [
                    {"id": course.id, "title": course.title}
                    for course in release.package.courses
                ],
            }
            for release in self.repository.list_active_releases()
        ]
        return {"runtime_version": "classroom_runtime_v1", "packages": packages}

    def active_package(self, package_id: str) -> dict:
        release = self.repository.get_active_release(package_id)
        return release.model_dump(mode="json", exclude_none=True)

    def module(self, package_id: str, module_id: str) -> dict:
        release = self.repository.get_active_release(package_id)
        for course in release.package.courses:
            for chapter in course.chapters:
                for module in chapter.modules:
                    if module.id == module_id:
                        return {
                            "package_id": release.package_id,
                            "version": release.version,
                            "content_hash": release.content_hash,
                            "course": {"id": course.id, "title": course.title},
                            "chapter": {"id": chapter.id, "title": chapter.title},
                            "module": module.model_dump(
                                mode="json", exclude_none=True
                            ),
                        }
        raise ClassroomNotFoundError(
            f"module {module_id!r} not found in package {package_id!r}"
        )
```

- [ ] **Step 4: Implement the Classroom router**

Create `backend/app/api/classroom/v1/router.py`:

```python
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from fastapi import APIRouter

from app.api.v1.schemas import api_error
from app.classroom.repository import (
    ClassroomNotFoundError,
    ClassroomRepository,
    ClassroomRepositoryError,
)
from app.classroom.runtime import ClassroomRuntimeService


RuntimeFactory = Callable[[], ClassroomRuntimeService]


def default_runtime() -> ClassroomRuntimeService:
    root = Path(os.getenv("CLASSROOM_DATA_ROOT", Path.cwd() / "classroom_data"))
    return ClassroomRuntimeService(ClassroomRepository(root))


def create_classroom_router(
    runtime_factory: RuntimeFactory = default_runtime,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/classroom/v1",
        tags=["classroom-runtime"],
    )

    @router.get("/catalog", operation_id="getClassroomCatalog")
    def catalog() -> dict:
        return runtime_factory().catalog()

    @router.get(
        "/packages/{package_id}",
        operation_id="getActiveClassroomPackage",
    )
    def active_package(package_id: str) -> dict:
        return _map_errors(
            lambda: runtime_factory().active_package(package_id)
        )

    @router.get(
        "/packages/{package_id}/modules/{module_id}",
        operation_id="getClassroomModule",
    )
    def module(package_id: str, module_id: str) -> dict:
        return _map_errors(
            lambda: runtime_factory().module(package_id, module_id)
        )

    return router


def _map_errors(operation: Callable[[], dict]) -> dict:
    try:
        return operation()
    except ClassroomNotFoundError as exc:
        raise api_error(404, "classroom_not_found", str(exc))
    except ClassroomRepositoryError as exc:
        raise api_error(400, "classroom_repository_error", str(exc))


router = create_classroom_router()
```

Create empty `__init__.py` files for `backend/app/api/classroom/` and `backend/app/api/classroom/v1/`.

- [ ] **Step 5: Run runtime API tests**

Run:

```bash
pytest backend/tests/test_classroom_runtime_api.py -q
```

Expected: `4 passed`.

- [ ] **Step 6: Commit runtime reads**

```bash
git add backend/app/classroom/runtime.py backend/app/api/classroom backend/tests/test_classroom_runtime_api.py
git commit -m "Expose read-only AI classroom runtime"
```

---

### Task 7: Application Profile Wiring

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_classroom_profile_wiring.py`
- Test: `backend/tests/test_phase_4_1_app_profile_gating.py`

**Interfaces:**
- Consumes: `studio_v1_router`, `classroom_v1_router`.
- Produces:
  - `internal`: old internal API plus authenticated Studio API.
  - `learner`: old learner API plus read-only Classroom API.
  - `mixed`: all existing APIs plus Studio and Classroom APIs.

- [ ] **Step 1: Write failing profile tests**

Create `backend/tests/test_classroom_profile_wiring.py`:

```python
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def paths(profile: str) -> set[str]:
    return set(TestClient(create_app(profile)).get("/openapi.json").json()["paths"])


def test_internal_and_mixed_profiles_expose_studio() -> None:
    assert "/api/studio/v1/capabilities" in paths("internal")
    assert "/api/studio/v1/capabilities" in paths("mixed")
    assert "/api/studio/v1/capabilities" not in paths("learner")


def test_learner_and_mixed_profiles_expose_classroom_runtime() -> None:
    assert "/api/classroom/v1/catalog" in paths("learner")
    assert "/api/classroom/v1/catalog" in paths("mixed")
    assert "/api/classroom/v1/catalog" not in paths("internal")


def test_new_classroom_routes_do_not_remove_legacy_routes_yet() -> None:
    mixed = paths("mixed")

    assert "/api/challenge/v1/health" in mixed
    assert "/api/classroom/v1/catalog" in mixed
    assert "/api/studio/v1/capabilities" in mixed
```

- [ ] **Step 2: Verify profile tests fail**

Run:

```bash
pytest backend/tests/test_classroom_profile_wiring.py -q
```

Expected: three failures because the new routers are not registered.

- [ ] **Step 3: Register the routers in `create_app`**

Modify `backend/app/main.py` imports:

```python
from app.api.classroom.v1.router import router as classroom_v1_router
from app.api.studio.v1.router import router as studio_v1_router
```

Modify the profile registration without changing existing route ownership:

```python
    if resolved_profile in {AppProfile.INTERNAL, AppProfile.MIXED}:
        application.include_router(api_v1_router)
        application.include_router(studio_v1_router)
    if resolved_profile in {AppProfile.LEARNER, AppProfile.MIXED}:
        application.include_router(learner_v1_router)
        application.include_router(classroom_v1_router)
```

Change only the FastAPI metadata to describe the transition accurately:

```python
    application = FastAPI(
        title="Math150 AI Classroom",
        version="0.2.0",
        description="AI Classroom Studio and runtime alongside isolated legacy APIs.",
    )
```

Keep `/trainer` mounting unchanged until Project C.

- [ ] **Step 4: Run the new and existing profile tests**

Run:

```bash
pytest backend/tests/test_classroom_profile_wiring.py backend/tests/test_phase_4_1_app_profile_gating.py -q
```

Expected: all tests pass; existing profile assertions remain valid.

- [ ] **Step 5: Commit app wiring**

```bash
git add backend/app/main.py backend/tests/test_classroom_profile_wiring.py
git commit -m "Wire Studio and classroom API profiles"
```

---

### Task 8: Seed Package, Action Contract, Documentation, and Full Verification

**Files:**
- Create: `backend/classroom_data/seed/calculus-foundations.json`
- Modify: `README.md`
- Modify: `backend/tests/test_studio_api.py`
- Modify: `backend/tests/test_classroom_runtime_api.py`

**Interfaces:**
- Consumes: all Project A interfaces.
- Produces: one checked-in classroom package example and a verified OpenAPI contract suitable for Custom GPT Action configuration.

- [ ] **Step 1: Add the real seed package**

Create `backend/classroom_data/seed/calculus-foundations.json` with this complete UTF-8 JSON:

```json
{
  "assets": [],
  "courses": [
    {
      "chapters": [
        {
          "id": "limits",
          "modules": [
            {
              "blocks": [
                {
                  "data": {
                    "markdown": "极限描述的是变量趋近时，函数值稳定接近什么。"
                  },
                  "detail_branches": [
                    {
                      "blocks": [
                        {
                          "data": {
                            "markdown": "趋近研究的是邻域行为，点值可以不存在或不同。"
                          },
                          "id": "limit-intro-detail-prose",
                          "kind": "prose"
                        }
                      ],
                      "id": "limit-intro-detail",
                      "title": "为什么不是直接代入"
                    }
                  ],
                  "id": "limit-intro",
                  "kind": "prose"
                },
                {
                  "data": {
                    "explanation": "当 x 足够接近 a 时，f(x) 可以任意接近 L。",
                    "latex": "\\lim_{x\\to a}f(x)=L"
                  },
                  "id": "limit-formula",
                  "kind": "formula_explanation"
                }
              ],
              "id": "limit-core",
              "segments": [
                {
                  "blocks": [
                    {
                      "data": {
                        "prompt": "观察 (x²-1)/(x-1) 在 x→1 时的行为。",
                        "steps": [
                          "因式分解 x²-1=(x-1)(x+1)",
                          "在 x≠1 的邻域中化简为 x+1",
                          "因此趋近值为 2"
                        ]
                      },
                      "id": "limit-example",
                      "kind": "worked_example"
                    }
                  ],
                  "id": "limit-example-segment",
                  "title": "用一个可消去间断点观察极限"
                }
              ],
              "summary": "从趋近过程理解极限，而不是把它当成代入规则。",
              "title": "极限的核心机制"
            }
          ],
          "relations": [],
          "title": "极限"
        }
      ],
      "id": "math-1",
      "title": "高等数学"
    }
  ],
  "model_instances": [],
  "package_id": "calculus-foundations",
  "schema_version": "classroom_package_v1",
  "title": "微积分基础课堂"
}
```

This seed contains no question, score, diagnosis, mastery, review, recommendation, or Boss fields.

Validate that the seed and fixture stay identical by adding this test to `backend/tests/test_classroom_models.py`:

```python
import json
from pathlib import Path


def test_checked_in_seed_matches_the_valid_package_contract() -> None:
    seed_path = (
        Path(__file__).resolve().parents[1]
        / "classroom_data"
        / "seed"
        / "calculus-foundations.json"
    )
    seed = json.loads(seed_path.read_text(encoding="utf-8"))

    package = ClassroomPackage.model_validate(seed)

    assert package.package_id == "calculus-foundations"
    assert package.courses[0].chapters[0].modules[0].id == "limit-core"
```

- [ ] **Step 2: Add Action-contract assertions**

Append to `backend/tests/test_studio_api.py`:

```python
def test_openapi_has_stable_action_operation_ids(tmp_path, monkeypatch) -> None:
    schema = client(tmp_path, monkeypatch).get("/openapi.json").json()
    operations = {
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }

    assert {
        "getStudioCapabilities",
        "createClassroomDraft",
        "getClassroomDraft",
        "updateClassroomDraft",
        "validateClassroomDraft",
        "publishClassroomDraft",
        "rollbackClassroomPackage",
    } <= operations
```

- [ ] **Step 3: Document the Project A workflow**

Add a new top-level `AI Classroom Foundation` section near the start of `README.md`:

````markdown
## AI Classroom Foundation

The new product path is an AI-generated interactive classroom. Project A adds:

- authenticated authoring and release operations under `/api/studio/v1`;
- read-only active classroom content under `/api/classroom/v1`;
- freely composed core modules with content blocks and local detail branches;
- deterministic drafts, releases, publish, and rollback;
- no scoring, diagnosis, mastery, review, recommendation, question-bank, or Boss dependency.

For local Studio calls, set a project-owned key:

```powershell
$env:STUDIO_API_KEY = "replace-with-a-local-secret"
$env:CLASSROOM_DATA_ROOT = "$PWD\\backend\\classroom_data\\local"
uvicorn app.main:app --app-dir backend --reload
```

The Custom GPT calls the Studio through its Action. The project does not call the Custom GPT and does not require an OpenAI API key for this route.

Use `Authorization: Bearer <STUDIO_API_KEY>` for Studio requests and add an `Idempotency-Key` header to every mutable operation.
````

- [ ] **Step 4: Run all Project A tests**

Run:

```bash
pytest backend/tests/test_classroom_models.py backend/tests/test_classroom_validation.py backend/tests/test_classroom_repository.py backend/tests/test_classroom_authoring.py backend/tests/test_studio_api.py backend/tests/test_classroom_runtime_api.py backend/tests/test_classroom_profile_wiring.py -q
```

Expected: all selected tests pass with `0 failed`.

- [ ] **Step 5: Run the full regression suite**

Run:

```bash
pytest -q
```

Expected: the complete suite passes with `0 failed`.

- [ ] **Step 6: Run legacy evals to prove isolation**

Run:

```bash
python evals/run_evals.py
```

Expected:

```text
Scoring 30/30 passed
Diagnosis 25/25 passed
Movement 12/12 passed
```

These evals are retained only as regression evidence that Project A did not accidentally damage old code. They are not part of the new product acceptance criteria.

- [ ] **Step 7: Verify no legacy imports exist in the new product**

Run:

```bash
rg -n "from app\\.(challenge|services|training|logic_graph)|import app\\.(challenge|services|training|logic_graph)" backend/app/classroom backend/app/api/studio backend/app/api/classroom
```

Expected: no matches.

- [ ] **Step 8: Inspect the final diff**

Run:

```bash
git status --short
git diff --check
git diff --stat
```

Expected:

- only Project A classroom files, tests, seed data, `backend/app/main.py`, and `README.md` are changed;
- `git diff --check` prints no errors.

- [ ] **Step 9: Commit the completed vertical slice**

```bash
git add README.md backend/classroom_data/seed/calculus-foundations.json backend/tests/test_classroom_models.py backend/tests/test_studio_api.py
git commit -m "Document AI classroom foundation slice"
```

- [ ] **Step 10: Push the completed Project A branch**

```bash
git push origin HEAD
```

Expected: the remote branch advances to the final Project A commit.

---

## Project A Completion Gate

Project A is complete only when all of the following are true:

- a Custom GPT-compatible OpenAPI surface exposes stable Studio operation IDs;
- Studio authentication uses the project-owned bearer key;
- GPT can create, read, update, and validate a classroom draft;
- repeated mutable calls are safe through durable idempotency receipts;
- stale revisions are rejected with structured `409` errors;
- GPT can publish and roll back immutable classroom releases;
- the Runtime catalog and module endpoints expose only active content;
- one module can freely mix continuous blocks, optional segments, and recursive detail branches;
- no new classroom code imports or returns legacy challenge or learner-analysis concepts;
- all Project A tests, the full regression suite, and legacy isolation evals pass.

Projects B, C, and D receive separate implementation plans after this gate passes.
