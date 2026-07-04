# Chapter Material-Aware Questions Codex Report

Status: Implemented by Codex
Date: 2026-07-04

## 1. Why this block matters

The material understanding layer could extract formulas, theorem statements, triggers, methods, common errors, and false-pass risks. However, the generated `questions.yaml` still used mostly generic ability skeletons.

This phase connects material evidence to the runtime question package.

## 2. Implemented block

Material evidence now flows through:

```text
materials
-> material understanding
-> intelligent generated SourceEvidence markdown section
-> chapter candidate material_evidence
-> training question package
-> questions.yaml
```

Changed files:

- `backend/app/challenge/chapter_intelligent_importer.py`
- `backend/app/challenge/chapter_draft_importer.py`
- `backend/app/challenge/chapter_candidate_builder.py`
- `backend/app/challenge/chapter_training_question_builder.py`

## 3. Runtime Question Improvements

Generated questions can now include source-specific evidence in:

- stem;
- prompt;
- expected answer;
- solution outline;
- rubric required keywords;
- rubric expected patterns for formula-sensitive dimensions;
- validator config;
- false-pass risks;
- common-error repair cues;
- variant relation metadata.

The question package quality gate now treats missing source material evidence as an error when a candidate has material evidence.

## 4. Source Evidence Safety

The candidate keeps only public material evidence such as:

- core concepts;
- core formulas;
- core theorems;
- typical problem types;
- entry triggers;
- method choices;
- key transformations;
- confusions;
- common errors;
- prerequisites;
- downstream uses;
- Mathematics I value;
- false-pass risks.

It does not keep authoring reviewer metadata or trusted learner-hidden answer fields.

## 5. Current Limitation

This is deterministic material-aware generation. It does not yet solve full mathematical authoring:

- worked examples are not parsed into executable step templates;
- formula equivalence is not normalized by a symbolic engine;
- generated tasks are source-specific but still templated;
- real scanned PDF/OCR remains outside this phase.

The next high-value block is content package correction/regeneration: allow a human or feedback report to patch nodes/questions/rubrics and regenerate only affected assets with an audit diff.

## 6. Verification

Focused verification:

```bash
python -m pytest backend/tests/test_chapter_material_understanding.py backend/tests/test_chapter_intelligent_importer.py backend/tests/test_chapter_candidate_builder.py backend/tests/test_chapter_training_question_builder.py backend/tests/test_chapter_publish_plan.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

Result:

```text
13 passed
```

Full regression verification:

```text
backend/tests: 585 passed, 1 warning
golden evals: scoring 30/30, diagnosis 25/25, movement 12/12
synthetic diagnosis lab: 16/16
```

Strict real-attempt calibration remains release-blocked:

```text
root=5/8, repair=6/8, exact=4/8, grade=fail
```
