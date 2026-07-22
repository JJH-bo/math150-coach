# Presentation and Document Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the Custom GPT verified, discoverable tools that transform one strict semantic lesson document into editable PPTX, self-contained Reveal-style HTML, print-quality PDF, and a portable lesson package with consistent content and rendered QA.

**Architecture:** Introduce a shared `semantic_lesson_v1` contract and narrative validator, then keep each renderer behind its own adapter while reusing the same normalized lesson. Browser-based render workers create page/slide evidence inside the job workspace; validators inspect structure, text fitting, page count, pixels, links, fonts, hashes, and cross-format content identity before artifact promotion.

**Tech Stack:** Python 3.12, Pydantic v2, PptxGenJS 4.0.1, Playwright 1.61.1, Chromium, Reveal-compatible local HTML/CSS/JS, pypdf, pdfplumber, Poppler, pytest, Node.js.

## Global Constraints

- The semantic source contains audience, learning objective, central takeaway, narrative arc, and audience-facing slides; it never contains production prompts, secrets, file paths, or executable code.
- Title slides use at least 50pt titles; slide titles at least 35pt; subheads at least 24pt; body text at least 16pt.
- Every slide has exactly one narrative job and primary claim; the deck opens deliberately and closes by resolving the learning objective.
- No output is `verified` unless every rendered page/slide has zero overflow and unintended overlap findings.
- All formats derive from the same normalized content hash and report it in their result and manifest.
- Renderers receive only a job-local JSON source and job-local output directory.

---

### Task 1: Semantic lesson contract and narrative validator

**Files:**
- Create: `backend/app/tools/lesson_contracts.py`
- Create: `backend/app/tools/lesson_validation.py`
- Test: `backend/tests/test_semantic_lesson.py`

**Interfaces:**
- Produces `SemanticLesson`, `LessonSlide`, `LessonTemplate`, `normalize_lesson(arguments)`, and `validate_lesson(lesson)`.
- Consumed by every export adapter and worker payload.

- [ ] Write failing tests proving strict fields, safe audience-facing copy, title/body budgets, one claim per slide, deliberate opening/closing, formula blocks, speaker notes, and stable content hashes.
- [ ] Run `python -m pytest backend/tests/test_semantic_lesson.py -q`; expect missing-module failure.
- [ ] Implement Pydantic models with `extra="forbid"`, 2-30 slides, template enum, UTF-8 normalization, prompt/secret/path-token rejection, narrative sequencing, and deterministic JSON hashing.
- [ ] Re-run the test and commit with `Build semantic lesson export contract`.

### Task 2: Browser-rendered Reveal/HTML exporter

**Files:**
- Create: `backend/app/tools/adapters/reveal_export.py`
- Create: `tools/render_semantic_lesson.cjs`
- Test: `backend/tests/test_reveal_export_tool.py`

**Interfaces:**
- Produces `export.reveal@1.0.0` and job-local `lesson.html`, `lesson.pdf`, `slide-*.png`, `render-report.json`, and `lesson-spec.json`.
- Node worker consumes only `--input`, `--output`, and configured browser path.

- [ ] Write failing reference tests for a four-slide calculus lesson, keyboard navigation, responsive/print styles, formula visibility, per-slide PNGs, PDF page count, no horizontal overflow, and malformed/overfull content rejection.
- [ ] Run the focused test; expect the adapter import to fail.
- [ ] Implement self-contained local HTML (no CDN), browser screenshot/PDF rendering, DOM overflow checks, font-size checks, and pixel nonblank checks.
- [ ] Re-run, visually inspect the montage, and commit with `Add verified Reveal lesson exporter`.

### Task 3: Editable PPTX exporter

**Files:**
- Modify: `package.json`
- Modify: `package-lock.json`
- Create: `backend/app/tools/adapters/pptx_export.py`
- Create: `tools/render_pptx_lesson.cjs`
- Test: `backend/tests/test_pptx_export_tool.py`

**Interfaces:**
- Produces `export.pptx@1.0.0`, editable native text/shapes, formula SVG, speaker notes, `lesson.pptx`, per-slide preview PNGs, montage, layout report, and OOXML validation report.

- [ ] Write failing tests that inspect the PPTX ZIP, slide count, notes, editable text, minimum font sizes, content hash, preview images, and zero overlap/overflow warnings.
- [ ] Run the focused test; expect missing adapter/worker failure.
- [ ] Pin PptxGenJS 4.0.1, implement four intentional layout families, compute text-fit budgets before generation, render a browser twin from the same geometry, and validate OOXML plus browser previews.
- [ ] Render every slide, inspect full-size previews and montage, fix all warnings, re-run tests, and commit with `Add verified editable PPTX exporter`.

### Task 4: PDF and portable HTML/package adapters

**Files:**
- Create: `backend/app/tools/adapters/pdf_export.py`
- Create: `backend/app/tools/adapters/html_export.py`
- Create: `backend/app/tools/adapters/package_export.py`
- Test: `backend/tests/test_document_export_tools.py`

**Interfaces:**
- Produces `export.pdf`, `export.html`, and `export.package`, all version `1.0.0`.
- Reuses the Reveal renderer and normalized semantic lesson rather than independently rewriting content.

- [ ] Write failing tests for PDF metadata/page count/text extraction/rendered PNGs, self-contained HTML/no external requests, package manifest hashes, and cross-format content-hash equality.
- [ ] Run focused tests; expect imports to fail.
- [ ] Implement adapters, PDF inspection, HTML resource audit, ZIP path containment, dependency manifest, and verification report.
- [ ] Re-run and commit with `Add verified lesson document exports`.

### Task 5: Registry, Action evidence, and GPT selection policy

**Files:**
- Modify: `backend/app/api/studio/v1/router.py`
- Modify: `backend/tests/test_tool_studio_api.py`
- Modify: `docs/custom-gpt-instructions.md`
- Modify: `tools/generate_tool_platform_evidence.py`
- Modify: `README.md`

**Interfaces:**
- Registers five export adapters in the default registry without changing the six public tool-job Actions.

- [ ] Add failing discovery and output-selection tests: PPTX for editable presenting, Reveal for interactive presenting, PDF for fixed distribution, HTML for browser lesson, package for archival transfer.
- [ ] Register adapters and update instructions to select by learning intent, not a fixed default.
- [ ] Generate one source lesson into at least PPTX, PDF, and HTML; inspect every page/slide; assert equal source hashes and no secret/local-path leakage.
- [ ] Run full Python and frontend/model suites, dependency checks, `git diff --check`, commit by cohesive scope, and push the branch.
