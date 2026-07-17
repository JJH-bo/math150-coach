# Chapter Material Understanding Codex Report

Status: Implemented by Codex
Date: 2026-07-04

## 1. Why this block matters

The final content production system cannot rely on a single loose text field. Users need to provide chapter material as notes, Markdown, PDF, Word, PPT, wrong-answer material, problem explanations, and multi-file bundles.

This phase adds the first material understanding layer before intelligent chapter generation.

## 2. Implemented block

New module:

- `backend/app/challenge/chapter_material_understanding.py`

It accepts a list of material items with:

- `material_type`;
- `filename`;
- plain `text`;
- or `content_base64` for binary materials.

Supported material types in this phase:

- `text`;
- `markdown`;
- `notes`;
- `wrong_answers`;
- `problem_solution`;
- `framework`;
- `pdf`;
- `docx`;
- `pptx`.

Word and PowerPoint are read through their zipped XML structure. PDF supports optional library extraction when available and a deterministic fallback for uncompressed/literal text streams.

## 3. Extracted Ability Evidence

The material understanding layer extracts:

- chapter topic;
- subject area;
- core concepts;
- core formulas;
- core theorem statements;
- typical problem types;
- entry triggers;
- method choices;
- key transformations;
- confusions;
- common errors;
- prerequisites;
- downstream uses;
- Mathematics I score value;
- false-pass risks.

The output is `chapter_material_understanding_v1` and includes a quality report.

## 4. API Integration

`POST /api/challenge/v1/authoring/chapter-draft/intelligent-generate` now accepts either:

- `source_text`;
- or `materials`;
- or both.

When materials are provided, the endpoint:

1. extracts material understanding;
2. uses the combined extracted text as the generation source;
3. returns a public material understanding summary;
4. carries extracted evidence into `knowledge_network.source_evidence`;
5. still builds the existing candidate preview and training question package.

The public summary does not echo full uploaded material text. It includes excerpts, hashes, extracted signals, and quality report.

## 5. Current Limitation

Superseded addendum, 2026-07-04:

The next block described here has now been partially implemented by the material-aware question generation phase. Source formulas, theorem wording, triggers, methods, common errors, and false-pass risks now flow into candidate `material_evidence` and generated runtime questions.

The remaining limitation is deeper worked-example authoring and correction/regeneration: generated tasks are source-specific but still templated, and the system still needs selective regeneration after human corrections or training feedback.

## 6. Verification

Focused verification:

```bash
python -m pytest backend/tests/test_chapter_material_understanding.py backend/tests/test_chapter_intelligent_importer.py backend/tests/test_chapter_publish_plan.py backend/tests/test_chapter_training_question_builder.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Result:

```text
9 passed
```

Full regression verification:

```text
backend/tests: 584 passed, 1 warning
golden evals: scoring 30/30, diagnosis 25/25, movement 12/12
synthetic diagnosis lab: 16/16
```

Strict real-attempt calibration remains release-blocked:

```text
root=5/8, repair=6/8, exact=4/8, grade=fail
```
