# Content-Addressed Classroom Asset Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build verified persistent image ingestion and transformation tools whose immutable outputs can be referenced and validated in published classrooms.

**Architecture:** A focused `AssetRepository` stores normalized image bytes and metadata by full SHA-256 under `CLASSROOM_DATA_ROOT`. Two Studio adapters use a shared image-validation module, while the package validator and learner API resolve the same immutable records. Existing tool jobs remain the execution and evidence boundary.

**Tech Stack:** Python 3.12+, Pillow 12.3.0, FastAPI, Pydantic 2, jsonschema 4.25.1, pytest, Playwright/Chromium, `studio_tools_v1`.

## Global Constraints

- Asset IDs are exactly `a-` followed by 64 lowercase hexadecimal characters.
- Content hashes are exactly `sha256:` followed by the same 64 characters.
- Base64 input is at most 12 MiB of text and 8 MiB after decoding.
- Source images are still PNG, JPEG, or WebP; 16–6000 pixels per side; at most 20 million pixels.
- Transform outputs are 32–4096 pixels per side and at most 16 million pixels.
- All accepted images are orientation-normalized and re-encoded without submitted metadata.
- No arbitrary URL, host path, SVG, script, animation, embedded file, or decoder option is accepted.
- Persistent learner bytes use a verified media type, ETag, and `public, max-age=31536000, immutable`.

---

### Task 1: Immutable asset repository

**Files:**
- Create: `backend/app/assets/models.py`
- Create: `backend/app/assets/repository.py`
- Create: `backend/app/assets/__init__.py`
- Test: `backend/tests/test_asset_repository.py`

**Interfaces:**
- Produces: `AssetRecord`, `AssetRepository.put(data, metadata)`, `AssetRepository.get(asset_id)`, and `AssetRepository.path(asset_id)`.
- Stores: `<root>/assets/sha256/<first-two-digest-chars>/<digest>/asset.<extension>` and `record.json`.

- [ ] **Step 1: Write failing repository tests**

```python
def test_repository_is_content_addressed_and_deduplicates(tmp_path):
    repository = AssetRepository(tmp_path)
    first, duplicate = repository.put(
        b"verified-image-bytes",
        media_type="image/png",
        extension="png",
        width=64,
        height=48,
        display_filename="diagram.png",
    )
    second, repeated = repository.put(
        b"verified-image-bytes",
        media_type="image/png",
        extension="png",
        width=64,
        height=48,
        display_filename="renamed.png",
    )
    assert first.asset_id == second.asset_id
    assert duplicate is False and repeated is True
    assert repository.path(first.asset_id).read_bytes() == b"verified-image-bytes"

def test_repository_rejects_unsafe_ids_and_detects_corruption(tmp_path):
    repository = AssetRepository(tmp_path)
    with pytest.raises(AssetPathError):
        repository.get("../outside")
    record, _ = repository.put(
        b"bytes", media_type="image/png", extension="png",
        width=32, height=32, display_filename="x.png",
    )
    repository.path(record.asset_id).write_bytes(b"tampered")
    with pytest.raises(AssetCorruptionError):
        repository.get(record.asset_id)
```

- [ ] **Step 2: Run the tests and confirm missing imports fail**

Run: `python -m pytest backend/tests/test_asset_repository.py -q`

Expected: collection fails because `app.assets.repository` does not exist.

- [ ] **Step 3: Implement strict models and atomic repository writes**

```python
class AssetRecord(StrictAssetModel):
    asset_id: str = Field(pattern=r"^a-[a-f0-9]{64}$")
    content_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    media_type: Literal["image/png", "image/jpeg", "image/webp"]
    extension: Literal["png", "jpg", "webp"]
    width: int = Field(ge=1, le=6000)
    height: int = Field(ge=1, le=6000)
    size_bytes: int = Field(ge=1, le=8 * 1024 * 1024)
    display_filename: str = Field(min_length=1, max_length=120)
    uri: str
    created_at: str

def put(self, data: bytes, *, media_type: str, extension: str,
        width: int, height: int, display_filename: str) -> tuple[AssetRecord, bool]:
    digest = hashlib.sha256(data).hexdigest()
    asset_id = f"a-{digest}"
    # Validate metadata, write bytes and record through sibling temporary files,
    # and return the existing verified record when the digest already exists.
```

- [ ] **Step 4: Run repository tests**

Run: `python -m pytest backend/tests/test_asset_repository.py -q`

Expected: all repository tests pass.

- [ ] **Step 5: Commit the repository**

```powershell
git add backend/app/assets backend/tests/test_asset_repository.py
git commit -m "Add immutable classroom asset repository"
```

### Task 2: Shared verified image normalization

**Files:**
- Create: `backend/app/assets/images.py`
- Test: `backend/tests/test_asset_images.py`

**Interfaces:**
- Produces: `normalize_image(data, declared_media_type, output_format) -> NormalizedImage`.
- Produces: `transform_image(record, source_path, request) -> NormalizedImage`.
- `NormalizedImage` contains bytes, media type, extension, width, height, source format, and stripped metadata evidence.

- [ ] **Step 1: Write failing image tests with generated fixtures**

```python
def test_normalization_sniffs_type_strips_metadata_and_is_repeatable():
    source = jpeg_fixture(size=(120, 80), exif_orientation=6, comment=b"secret")
    first = normalize_image(source, "image/jpeg", "png")
    second = normalize_image(source, "image/jpeg", "png")
    assert (first.width, first.height) == (80, 120)
    assert first.data == second.data
    with Image.open(io.BytesIO(first.data)) as image:
        assert image.getexif() == {}
        assert "comment" not in {key.lower() for key in image.info}

@pytest.mark.parametrize("case", ["mime-spoof", "animated", "too-small", "too-many-pixels"])
def test_invalid_images_are_rejected(case):
    with pytest.raises(AssetImageError):
        normalize_image(invalid_fixture(case), "image/png", "webp")
```

- [ ] **Step 2: Run tests and confirm the image module is absent**

Run: `python -m pytest backend/tests/test_asset_images.py -q`

Expected: collection fails because `app.assets.images` does not exist.

- [ ] **Step 3: Implement bounded decode and deterministic encoders**

```python
SUPPORTED = {
    "PNG": ("image/png", "png"),
    "JPEG": ("image/jpeg", "jpg"),
    "WEBP": ("image/webp", "webp"),
}

def normalize_image(data: bytes, declared_media_type: str,
                    output_format: str) -> NormalizedImage:
    if not 0 < len(data) <= 8 * 1024 * 1024:
        raise AssetImageError("decoded image must contain at most 8388608 bytes")
    with Image.open(io.BytesIO(data)) as opened:
        opened.verify()
    with Image.open(io.BytesIO(data)) as opened:
        if getattr(opened, "n_frames", 1) != 1:
            raise AssetImageError("animated images are not accepted")
        actual_media_type, _ = SUPPORTED.get(opened.format, (None, None))
        if actual_media_type != declared_media_type:
            raise AssetImageError("declared media type does not match image signature")
        oriented = ImageOps.exif_transpose(opened)
        pixels = oriented.width * oriented.height
        if not 16 <= oriented.width <= 6000 or not 16 <= oriented.height <= 6000:
            raise AssetImageError("image dimensions are outside the accepted range")
        if pixels > 20_000_000:
            raise AssetImageError("image exceeds the 20000000 pixel limit")
        return encode_pixels(oriented, output_format)
```

- [ ] **Step 4: Implement contain/cover transforms and alpha-safe JPEG output**

```python
def transform_image(source: Image.Image, *, width: int, height: int,
                    mode: Literal["contain", "cover"], output_format: str,
                    quality: int, allow_upscale: bool,
                    background: str) -> NormalizedImage:
    # Validate 32–4096 bounds and 16M output pixels, compute aspect-ratio-safe
    # geometry, use Image.Resampling.LANCZOS, composite RGBA before JPEG, and
    # pass the result through the same second-decode verification as ingestion.
```

- [ ] **Step 5: Run image tests and commit**

Run: `python -m pytest backend/tests/test_asset_images.py -q`

Expected: all image tests pass.

```powershell
git add backend/app/assets/images.py backend/tests/test_asset_images.py
git commit -m "Add verified classroom image normalization"
```

### Task 3: Studio asset tools

**Files:**
- Create: `backend/app/tools/adapters/asset_images.py`
- Modify: `backend/app/api/studio/v1/router.py`
- Test: `backend/tests/test_asset_tools.py`
- Modify: `backend/tests/test_tool_studio_api.py`

**Interfaces:**
- Produces: `AssetIngestAdapter(asset_repository, tool_job_repository)` with ID `asset.ingest@1.0.0` and scope `studio.author`.
- Produces: `AssetTransformAdapter(asset_repository)` with ID `asset.transform@1.0.0` and scope `studio.render`.
- Both return `asset`, `duplicate`, and `validation`; both emit image and `validation-report.json` job artifacts.

- [ ] **Step 1: Write failing adapter tests**

```python
def test_ingest_upload_and_prior_job_artifact_produce_same_asset(tmp_path):
    repository = AssetRepository(tmp_path)
    jobs = seeded_succeeded_plot_job(tmp_path, png_fixture())
    upload = AssetIngestAdapter(repository, jobs).execute(
        {"filename": "curve.png", "declared_media_type": "image/png",
         "content_base64": base64.b64encode(png_fixture()).decode(),
         "output_format": "png", "alt_text": "A labeled curve."},
        context(tmp_path / "upload"),
    )
    chained = AssetIngestAdapter(repository, jobs).execute(
        {"filename": "curve.png", "source_job_id": SEEDED_JOB_ID,
         "source_artifact_name": "figure.png", "output_format": "png",
         "alt_text": "A labeled curve."},
        context(tmp_path / "chained"),
    )
    assert upload.result["asset"]["asset_id"] == chained.result["asset"]["asset_id"]
    assert chained.result["duplicate"] is True

def test_transform_creates_bounded_content_addressed_variant(tmp_path):
    output = adapter.execute(
        {"asset_id": source.asset_id, "width": 320, "height": 180,
         "mode": "cover", "output_format": "webp", "quality": 88,
         "allow_upscale": False, "background": "#ffffff"}, context(tmp_path))
    assert output.result["asset"]["media_type"] == "image/webp"
    assert output.result["asset"]["width"] == 320
    assert output.result["asset"]["height"] == 180
```

- [ ] **Step 2: Run adapter tests and confirm imports fail**

Run: `python -m pytest backend/tests/test_asset_tools.py -q`

Expected: collection fails because the adapters do not exist.

- [ ] **Step 3: Implement strict tool definitions and source selection**

```python
class AssetIngestAdapter:
    definition = ToolDefinition(
        tool_id="asset.ingest", version="1.0.0",
        category="asset", quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.AUTHOR, execution_mode=ToolExecutionMode.SYNC,
        deterministic=True, cacheable=True, timeout_seconds=30,
        max_artifacts=2, max_artifact_bytes=16 * 1024 * 1024,
        input_schema=INGEST_SCHEMA, output_schema=ASSET_OUTPUT_SCHEMA,
        output_media_types=["image/png", "image/jpeg", "image/webp", "application/json"],
        quality_gates=["mime_signature_match", "bounded_still_image", "metadata_removed",
                       "second_decode_verified", "content_addressed_storage"],
        upstream_project="Pillow", license="HPND",
    )
```

- [ ] **Step 4: Register both adapters using shared persistent repositories**

```python
def default_tool_service() -> ToolExecutionService:
    root, _ = _data_roots()
    jobs = ToolJobRepository(root)
    assets = AssetRepository(root)
    registry = ToolRegistry([
        SymbolicMathAdapter(), NumericMathAdapter(), MathVerifyAdapter(),
        GraphMathAdapter(), PlotAdapter(), DiagramAdapter(),
        Geometry2dAdapter(), Scene3dAdapter(), TemplateListAdapter(),
        TemplateInstantiateAdapter(), RevealExportAdapter(),
        PptxExportAdapter(), PdfExportAdapter(), HtmlExportAdapter(),
        PackageExportAdapter(),
        AssetIngestAdapter(assets, jobs),
        AssetTransformAdapter(assets),
    ])
    return ToolExecutionService(registry, jobs, IdempotencyLedger(root / "tool-idempotency"))
```

- [ ] **Step 5: Run focused tool tests and commit**

Run: `python -m pytest backend/tests/test_asset_tools.py backend/tests/test_tool_studio_api.py -q`

Expected: both tools are `verified`, the verified registry count is 17, and all tests pass.

```powershell
git add backend/app/tools/adapters/asset_images.py backend/app/api/studio/v1/router.py backend/tests/test_asset_tools.py backend/tests/test_tool_studio_api.py
git commit -m "Add verified persistent image tools"
```

### Task 4: Publication and learner runtime integration

**Files:**
- Modify: `backend/app/classroom/validation.py`
- Modify: `backend/app/classroom/authoring.py`
- Modify: `backend/app/api/classroom/v1/router.py`
- Modify: `backend/app/classroom/runtime.py`
- Modify: `backend/app/api/studio/v1/router.py`
- Modify: `frontend/classroom/content-renderer.js`
- Test: `backend/tests/test_classroom_assets.py`
- Modify: `frontend/classroom/content-renderer.test.mjs`

**Interfaces:**
- Produces: `GET /api/classroom/v1/assets/{asset_id}`.
- Adds: `asset_resolver: Callable[[str], AssetRecord] | None` to `ClassroomPackageValidator`.
- Requires image blocks to use repository-backed package assets and nonblank alt text.

- [ ] **Step 1: Write failing validation and HTTP tests**

```python
def test_package_rejects_undeclared_and_tampered_image_assets(asset_repository):
    package = package_with_image_block(asset_id="a-" + "1" * 64)
    report = ClassroomPackageValidator(asset_resolver=asset_repository.get).validate(package)
    assert {issue.code for issue in report.issues} >= {"unregistered_asset", "undeclared_image_asset"}

def test_learner_asset_response_is_immutable(client, stored_asset):
    response = client.get(f"/api/classroom/v1/assets/{stored_asset.asset_id}")
    assert response.status_code == 200
    assert response.headers["etag"] == f'"{stored_asset.content_hash.removeprefix("sha256:")}"'
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert response.content == asset_repository.path(stored_asset.asset_id).read_bytes()
```

- [ ] **Step 2: Run focused tests and confirm missing integration fails**

Run: `python -m pytest backend/tests/test_classroom_assets.py -q`

Expected: failures show absent asset resolver and learner endpoint.

- [ ] **Step 3: Add cross-object asset validation**

```python
asset_records = {}
for index, declared in enumerate(package.assets):
    path = f"assets[{index}]"
    record_id(declared.asset_id, f"{path}.asset_id")
    expected_uri = f"/api/classroom/v1/assets/{declared.asset_id}"
    # Resolve the immutable record and emit exact issues for unknown ID,
    # content-hash mismatch, media mismatch, or noncanonical URI.
```

- [ ] **Step 4: Add learner bytes route and canonical image rendering**

```python
@router.get("/assets/{asset_id}", operation_id="getClassroomAsset")
def asset(asset_id: str) -> FileResponse:
    record, path = runtime_factory().asset(asset_id)
    return FileResponse(
        path, media_type=record.media_type,
        headers={"ETag": f'"{record.content_hash[7:]}"',
                 "Cache-Control": "public, max-age=31536000, immutable"},
    )
```

- [ ] **Step 5: Run backend and frontend tests and commit**

Run: `python -m pytest backend/tests/test_classroom_assets.py backend/tests/test_classroom_validation.py backend/tests/test_studio_api.py -q`

Run: `node --test frontend/classroom/content-renderer.test.mjs frontend/classroom/static-contract.test.mjs`

Expected: all focused tests pass and external image URLs are rejected.

```powershell
git add backend/app/classroom backend/app/api frontend/classroom backend/tests/test_classroom_assets.py
git commit -m "Require verified assets in published classrooms"
```

### Task 5: Public protocol evidence, documentation, and regression

**Files:**
- Modify: `tools/generate_tool_platform_evidence.py`
- Create: `tools/capture_classroom_asset.cjs`
- Modify: `README.md`
- Modify: `docs/custom-gpt-instructions.md`
- Generate: `docs/preview-artifacts/tool-platform-core/asset-ingest/*`
- Generate: `docs/preview-artifacts/tool-platform-core/asset-transform/*`
- Test: `backend/tests/test_asset_evidence.py`

**Interfaces:**
- Adds real Studio jobs named `asset-ingest` and `asset-transform` to the checked-in evidence pack.
- Adds browser report fields `natural_width`, `natural_height`, `nonblank`, `console_errors`, and `failed_requests`.

- [ ] **Step 1: Write the evidence contract test**

```python
def test_checked_in_asset_evidence_is_real_and_secret_free():
    ingest = read_json(EVIDENCE / "asset-ingest-job.json")
    transformed = read_json(EVIDENCE / "asset-transform-job.json")
    browser = read_json(EVIDENCE / "asset-transform/browser-report.json")
    assert ingest["state"] == transformed["state"] == "succeeded"
    assert transformed["result"]["asset"]["uri"].startswith("/api/classroom/v1/assets/a-")
    assert browser["natural_width"] == 640
    assert browser["natural_height"] == 360
    assert browser["nonblank"] is True
    assert browser["console_errors"] == browser["failed_requests"] == []
```

- [ ] **Step 2: Extend evidence generation through the public API**

```python
jobs["asset-ingest"] = submit_and_wait(
    origin, studio_key, idempotency_key="evidence-ingest-plot-v1",
    tool_id="asset.ingest",
    arguments={"filename": "quadratic.png", "source_job_id": jobs["plot"]["job_id"],
               "source_artifact_name": "figure.png", "output_format": "png",
               "alt_text": "A symmetric quadratic curve with its minimum at the origin."},
)
jobs["asset-transform"] = submit_and_wait(
    origin, studio_key, idempotency_key="evidence-transform-plot-v1",
    tool_id="asset.transform",
    arguments={"asset_id": jobs["asset-ingest"]["result"]["asset"]["asset_id"],
               "width": 640, "height": 360, "mode": "cover",
               "output_format": "webp", "quality": 88,
               "allow_upscale": False, "background": "#ffffff"},
)
```

- [ ] **Step 3: Capture the stable learner URL in real Chromium**

Run: `python tools/generate_tool_platform_evidence.py`

Expected: registry total is 17; both asset jobs succeed; browser report has no console errors, failed requests, clipping, blank pixels, secret, or temporary path.

- [ ] **Step 4: Update operator and Custom GPT instructions**

Document the sequence `discover → generate or upload → ingest → transform → declare package asset → author image block → validate → publish`, including the rule that arbitrary web URLs are never inserted directly.

- [ ] **Step 5: Run full verification**

Run: `python -m pytest -q`

Run: `node --test frontend/classroom/*.test.mjs frontend/model-runtime/*.test.mjs`

Run: `python -m pip check`

Run: `pnpm install --frozen-lockfile --offline`

Run: `git diff --check`

Expected: all tests pass, dependencies are consistent, the lockfile is unchanged, and the diff check is clean.

- [ ] **Step 6: Commit evidence and documentation**

```powershell
git add README.md docs/custom-gpt-instructions.md docs/preview-artifacts/tool-platform-core tools/generate_tool_platform_evidence.py tools/capture_classroom_asset.cjs backend/tests/test_asset_evidence.py
git commit -m "Prove classroom assets end to end"
```
