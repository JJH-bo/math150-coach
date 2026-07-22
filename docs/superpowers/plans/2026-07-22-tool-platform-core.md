# Custom GPT Tool Platform Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the stable Tool Platform Core and first verified symbolic-mathematics adapter so the Custom GPT can discover tools, submit idempotent durable jobs, inspect results, and retrieve validated artifacts through the existing Studio Action.

**Architecture:** Add a focused `app.tools` package for contracts, registry, repository, execution, permissions, and artifacts. Mount six stable Studio Action operations over this package and register adapters explicitly at application startup. The first adapter uses SymPy through structured operations; later packs register behind the same interfaces without changing the Action workflow.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SymPy 1.14, pytest, UTF-8 JSON, SHA-256 content hashes, existing Studio bearer authentication and idempotency ledger.

## Global Constraints

- The production Studio credential receives all seven scopes defined in `docs/superpowers/specs/2026-07-22-custom-gpt-tool-platform-design.md`.
- No tool receives `STUDIO_API_KEY`, arbitrary host paths, or an unrestricted host shell.
- Every mutable Action requires `Idempotency-Key`; key reuse with different arguments returns conflict.
- Tool inputs and results are strict JSON objects validated against the registered adapter contract.
- Job and artifact files are atomic, UTF-8, hash-addressed, and confined to `CLASSROOM_DATA_ROOT/tool-jobs`.
- The public tool workflow remains stable when new adapters are added.
- Existing classroom, model, preview, session, publish, and rollback tests remain green.

---

### Task 1: Tool contracts and registry

**Files:**
- Create: `backend/app/tools/__init__.py`
- Create: `backend/app/tools/contracts.py`
- Create: `backend/app/tools/registry.py`
- Test: `backend/tests/test_tool_registry.py`

**Interfaces:**
- Produces `ToolScope`, `ToolQualityTier`, `ToolExecutionMode`, `ToolDefinition`, `ToolArtifact`, `ToolError`, `ToolJob`, and `ToolAdapter`.
- Produces `ToolRegistry.register(adapter)`, `ToolRegistry.list(query=None, category=None, quality_tier=None)`, and `ToolRegistry.get(tool_id, version=None)`.

- [ ] **Step 1: Write failing registry tests**

```python
def test_registry_discovers_verified_tools_without_internal_ids():
    registry = ToolRegistry([FakeAdapter("math.symbolic", "1.0.0")])
    assert registry.list(query="symbolic")[0].tool_id == "math.symbolic"

def test_registry_rejects_duplicate_tool_versions():
    with pytest.raises(ToolRegistryConflictError):
        ToolRegistry([FakeAdapter("math.symbolic", "1.0.0"), FakeAdapter("math.symbolic", "1.0.0")])
```

- [ ] **Step 2: Run the registry tests and confirm missing-module failure**

Run: `python -m pytest backend/tests/test_tool_registry.py -q`

Expected: collection fails because `app.tools` does not exist.

- [ ] **Step 3: Implement strict contracts and deterministic registry ordering**

`ToolDefinition` must expose the design fields, forbid extras, validate semantic versions, require at least one output media type, and serialize JSON Schemas as dictionaries. `ToolRegistry.get()` selects the highest registered semantic version when version is omitted.

- [ ] **Step 4: Run registry tests**

Run: `python -m pytest backend/tests/test_tool_registry.py -q`

Expected: all registry tests pass.

- [ ] **Step 5: Commit the registry**

```powershell
git add backend/app/tools backend/tests/test_tool_registry.py
git commit -m "Build Studio tool registry"
```

### Task 2: Durable job and artifact repository

**Files:**
- Create: `backend/app/tools/repository.py`
- Test: `backend/tests/test_tool_job_repository.py`

**Interfaces:**
- Produces `ToolJobRepository.create`, `get`, `update`, `request_cancel`, `artifact_path`, and `promote_artifact`.
- Consumes `ToolJob` and `ToolArtifact` from Task 1.

- [ ] **Step 1: Write failing repository tests**

Tests must prove path traversal rejection, atomic job creation, state persistence, cancellation requests, artifact SHA-256/size/media metadata, and immutable artifact-name conflicts.

- [ ] **Step 2: Verify failures**

Run: `python -m pytest backend/tests/test_tool_job_repository.py -q`

Expected: failures caused by absent `ToolJobRepository`.

- [ ] **Step 3: Implement filesystem confinement and atomic persistence**

Use `Path.resolve()` containment checks, temporary sibling files followed by `replace`, artifact streaming hashes, and the existing identifier pattern `[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}`.

- [ ] **Step 4: Verify repository behavior**

Run: `python -m pytest backend/tests/test_tool_job_repository.py -q`

Expected: all repository tests pass.

- [ ] **Step 5: Commit durable jobs**

```powershell
git add backend/app/tools/repository.py backend/tests/test_tool_job_repository.py
git commit -m "Persist Studio tool jobs and artifacts"
```

### Task 3: Permissioned execution service

**Files:**
- Create: `backend/app/tools/execution.py`
- Test: `backend/tests/test_tool_execution.py`

**Interfaces:**
- Produces `ToolExecutionService.submit`, `run`, `get`, `cancel`, and `artifact`.
- Consumes `ToolRegistry`, `ToolJobRepository`, and `IdempotencyLedger`.

- [ ] **Step 1: Write failing execution tests**

Tests must prove required-scope enforcement, argument-schema rejection before job creation, same-key replay, different-payload idempotency conflict, success result persistence, structured adapter failure, timeout state, cancellation, and artifact promotion only after adapter success.

- [ ] **Step 2: Verify intended failures**

Run: `python -m pytest backend/tests/test_tool_execution.py -q`

Expected: failures caused by absent execution service.

- [ ] **Step 3: Implement execution phases**

The service creates a queued job, transitions to running, prepares a confined work directory, calls `adapter.execute(arguments, context)`, validates the structured result, promotes declared artifacts, and then writes succeeded. Any exception becomes a bounded `ToolError`; secrets and environment values are never serialized.

- [ ] **Step 4: Verify execution service**

Run: `python -m pytest backend/tests/test_tool_execution.py -q`

Expected: all execution tests pass.

- [ ] **Step 5: Commit execution service**

```powershell
git add backend/app/tools/execution.py backend/tests/test_tool_execution.py
git commit -m "Execute permissioned Studio tools"
```

### Task 4: Verified symbolic mathematics adapter

**Files:**
- Modify: `requirements.txt`
- Create: `backend/app/tools/adapters/__init__.py`
- Create: `backend/app/tools/adapters/symbolic_math.py`
- Test: `backend/tests/test_symbolic_math_tool.py`

**Interfaces:**
- Produces `SymbolicMathAdapter` registered as `math.symbolic@1.0.0`, quality tier `verified`, required scope `studio.compute`.
- Accepts operations `simplify`, `factor`, `expand`, `solve`, `differentiate`, `integrate`, `limit`, `series`, `matrix`, and `equivalent`.
- Returns plain expression, LaTeX, variables, assumptions, warnings, and operation-specific structured values.

- [ ] **Step 1: Add failing reference tests**

Reference cases must include polynomial factor/expand round trip, derivative and integral, one-sided limit, equation solving, matrix determinant/inverse, equivalent expressions under assumptions, malformed input, unsupported operation, and a complexity-limit rejection.

- [ ] **Step 2: Verify the adapter is absent**

Run: `python -m pytest backend/tests/test_symbolic_math_tool.py -q`

Expected: collection fails because `SymbolicMathAdapter` does not exist.

- [ ] **Step 3: Pin SymPy and implement structured parsing**

Add `sympy==1.14.0`. Parse only explicit expression strings with declared symbols and assumptions. Reject attribute access, code tokens, more than 64 symbols, expression strings over 20,000 characters, and results whose operation count exceeds the configured limit.

- [ ] **Step 4: Run symbolic reference tests**

Run: `python -m pytest backend/tests/test_symbolic_math_tool.py -q`

Expected: all symbolic tests pass.

- [ ] **Step 5: Commit symbolic mathematics**

```powershell
git add requirements.txt backend/app/tools/adapters backend/tests/test_symbolic_math_tool.py
git commit -m "Add verified symbolic mathematics tool"
```

### Task 5: Studio Action API

**Files:**
- Modify: `backend/app/api/studio/v1/schemas.py`
- Modify: `backend/app/api/studio/v1/router.py`
- Test: `backend/tests/test_tool_studio_api.py`
- Modify: `backend/tests/test_studio_api.py`

**Interfaces:**
- Produces operation IDs `listStudioTools`, `getStudioTool`, `submitStudioToolJob`, `getStudioToolJob`, `cancelStudioToolJob`, and `getStudioToolArtifact`.
- `CreateToolJobRequest` contains `tool_id`, optional `tool_version`, and strict `arguments`.

- [ ] **Step 1: Write failing authenticated API tests**

Tests must assert bearer auth, stable operation IDs, searchable discovery, idempotency-header requirement, symbolic job submission, polling, cancellation response, artifact 404 mapping, and absence of secrets from every response.

- [ ] **Step 2: Verify routes are missing**

Run: `python -m pytest backend/tests/test_tool_studio_api.py -q`

Expected: 404 failures for new paths.

- [ ] **Step 3: Register the default tool runtime and routes**

Construct the default registry with `SymbolicMathAdapter`, persist under `CLASSROOM_DATA_ROOT/tool-jobs`, and reuse the Studio dependency/auth/error conventions. Submit execution through `BackgroundTasks` while preserving a durable queued response.

- [ ] **Step 4: Verify API and OpenAPI**

Run: `python -m pytest backend/tests/test_tool_studio_api.py backend/tests/test_studio_api.py -q`

Expected: all tests pass and the six operation IDs exist.

- [ ] **Step 5: Commit Action surface**

```powershell
git add backend/app/api/studio/v1 backend/tests/test_tool_studio_api.py backend/tests/test_studio_api.py
git commit -m "Expose Studio tool job Actions"
```

### Task 6: Custom GPT autonomy instructions and capability contract

**Files:**
- Modify: `docs/custom-gpt-instructions.md`
- Modify: `backend/app/api/studio/v1/schemas.py`
- Modify: `backend/app/api/studio/v1/router.py`
- Test: `backend/tests/test_tool_studio_api.py`

**Interfaces:**
- Studio capabilities expose `tool_protocol_version="studio_tools_v1"`, granted scopes, verified-tool default policy, and durable-job support.
- Instructions teach discovery-first selection, async polling, artifact retrieval, repair on structured errors, and no requests for internal IDs or routine confirmation.

- [ ] **Step 1: Add failing capability and documentation contract tests**

Assert all seven scopes are exposed, `math.symbolic` is discoverable as verified, instructions name every tool operation ID, and no instruction asks the user for the Studio key or internal IDs.

- [ ] **Step 2: Update capability schemas and instructions**

Document that the Custom GPT must call discovery, select the highest verified version, submit with a unique idempotency key, poll until terminal state, download required artifacts, and use repair hints before retrying.

- [ ] **Step 3: Verify contracts**

Run: `python -m pytest backend/tests/test_tool_studio_api.py backend/tests/test_production_integration.py -q`

Expected: all tests pass.

- [ ] **Step 4: Commit GPT contract**

```powershell
git add docs/custom-gpt-instructions.md backend/app/api/studio/v1 backend/tests/test_tool_studio_api.py
git commit -m "Teach Custom GPT the Studio tool protocol"
```

### Task 7: End-to-end verification and publishable evidence

**Files:**
- Create: `docs/preview-artifacts/tool-platform-core/tool-registry.json`
- Create: `docs/preview-artifacts/tool-platform-core/symbolic-job.json`
- Create: `docs/preview-artifacts/tool-platform-core/openapi-operation-ids.json`
- Modify: `README.md`

**Interfaces:**
- Produces reproducible evidence that an authenticated Action client can discover and execute `math.symbolic` through the running FastAPI service.

- [ ] **Step 1: Run the focused and full suites**

Run:

```powershell
python -m pytest backend/tests/test_tool_registry.py backend/tests/test_tool_job_repository.py backend/tests/test_tool_execution.py backend/tests/test_symbolic_math_tool.py backend/tests/test_tool_studio_api.py -q
python -m pytest -q
```

Expected: zero failures.

- [ ] **Step 2: Run all frontend/model tests**

Run: `node --test frontend/classroom/*.test.mjs frontend/model-runtime/*.test.mjs`

Expected: zero failures.

- [ ] **Step 3: Generate runtime evidence**

Start a temporary mixed-profile server with a generated Studio key and temporary `CLASSROOM_DATA_ROOT`. Use an authenticated HTTP client to save sanitized discovery, completed symbolic job, and OpenAPI operation-ID JSON. Evidence must omit the key and local temporary path.

- [ ] **Step 4: Inspect Git state and commit**

```powershell
git diff --check
git status --short
git add README.md docs/preview-artifacts/tool-platform-core
git commit -m "Document Studio tool platform core"
git push origin HEAD
```

- [ ] **Step 5: Continue with the Mathematics and Plot Pack**

Create the next plan from `docs/superpowers/specs/2026-07-22-custom-gpt-tool-platform-design.md`; the full goal remains active until every completion-evidence item in the specification is proven.
