# Phase 4.8.3B Human Review Records

Status: human reviewer results recorded. This document records completed human review outcomes only. It does not re-review, re-score, modify, publish, import, or register any candidate.

## 1. Executive Decision

Phase 4.8.3B-3 exports the formal review records and recommendation summary from the completed human review steps:

- Phase 4.8.3B-1 hard-fail review by human reviewer.
- Phase 4.8.3B-2 full 100-point review by human reviewer.

This phase records the human reviewer's results as provided. Codex did not independently re-score, re-rank, re-select, or re-judge any candidate.

Human reviewer summary:

- 8/8 candidates have no hard fail.
- 8/8 candidates entered the second full scoring round.
- 4 candidates received `strong_candidate`.
- 4 candidates received `revise_then_review`.
- 0 candidates received `defer`.
- 0 candidates received `reject`.

The recommendation summary is a human reviewer recommendation for future formal publish planning only. It is not formal publish, not formal import, not a formal catalog selection, and not a manifest change.

## 2. Scope And Non-goals

In scope:

- record hard-fail review summary;
- record 100-point review results;
- record one per-candidate review record for all 8 candidates;
- record human reviewer candidate recommendation summary;
- record required changes before any later formal publish planning;
- update README with phase status and next recommended phase.

Out of scope:

- modifying authoring draft YAML;
- modifying dry-run previews;
- modifying validation reports;
- modifying the batch manifest;
- modifying the formal catalog;
- modifying `backend/catalog_data/manifest.yaml`;
- adding formal question YAML;
- executing formal publish or formal import;
- editing candidate content;
- regenerating questions;
- recomputing scores;
- making a new Codex-authored selection;
- modifying engines, API, learner projector, Local Trainer, coach output, CatalogValidator, or authoring/import CLI;
- adding endpoint, history, frontend, database, auth, LLM, mastery, review, or formal persistence;
- scoring integration;
- entering Phase 4.8.4 or Phase 4.9.

## 3. Review Inputs

Human reviewer results were recorded using these prior materials as context:

- `docs/phase_4_8_2_human_review_selection_plan.md`
- `docs/phase_4_8_3a_human_review_packet.md`
- Phase 4.8.3B-1 hard-fail review results supplied by the human reviewer.
- Phase 4.8.3B-2 full 100-point review results supplied by the human reviewer.

Candidate set:

- `ode-sep-cand-001`
- `ode-sep-cand-002`
- `ode-sep-cand-003`
- `ode-hom-cand-001`
- `ode-hom-cand-002`
- `ode-linear-cand-001`
- `ode-linear-cand-002`
- `ode-mixed-cand-001`

## 4. Hard-fail Review Summary

Overall hard-fail result:

- 8 candidates reviewed.
- 0 hard fails.
- 8 candidates can enter the second full scoring round.

Human reviewer noted that this does not mean all 8 are suitable for direct publication.

Main risks identified by the human reviewer:

- public prompts sometimes over-prompt the intended method;
- rubric keywords are sometimes too narrow;
- some primary `expected_answer` forms should be improved before publish planning.

Per-candidate hard-fail summary:

| Candidate | Hard fail | Quick result | Human reviewer note |
| --- | --- | --- | --- |
| `ode-sep-cand-001` | no | pass quick screen, minor revision needed | Math correct; node matches; prompt directly says separable, weakening trigger training; preferred main answer should be explicit `y=Ce^(3x^2/2)` with log form as alias. |
| `ode-sep-cand-002` | no | pass quick screen, minor revision needed | Math correct; trains rearrangement before separation; preferred main answer should be `y=C(1+x^2)` with log form as alias. |
| `ode-sep-cand-003` | no | pass quick screen | Math correct; initial value solution `y=3e^(x^2)` correct; validator stability for initial condition should be reviewed. |
| `ode-hom-cand-001` | no | pass quick screen, training value needs review | Math correct; prompt directly asks for `y=vx`, weakening homogeneous trigger training. |
| `ode-hom-cand-002` | no | pass quick screen, rubric needs review | Math correct; answer `(y/x)^2=2ln|x|+C` correct; rubric may be too tied to `y=vx`. |
| `ode-linear-cand-001` | no | pass quick screen | Math correct; standard integrating factor solution correct; prompt directly says integrating factor, so trigger training is weaker. |
| `ode-linear-cand-002` | no | pass quick screen | Math correct; standard form transformation and solution correct; high training value. |
| `ode-mixed-cand-001` | no | pass quick screen, needs rubric focus | Math correct; node binding to first-order linear is reasonable; rubric should better capture why forced separation is not the reliable method. |

## 5. Full Review Score Table

These scores are recorded exactly from the human reviewer result. Codex did not recalculate them.

| Candidate | Score | Recommendation | Core judgment |
| --- | ---: | --- | --- |
| `ode-sep-cand-001` | 75 | `revise_then_review` | Math correct, but too basic and prompt gives away the method. |
| `ode-sep-cand-002` | 86 | `strong_candidate` | Good rearrangement-before-separation item; revise prompt and preferred answer form. |
| `ode-sep-cand-003` | 85.5 | `strong_candidate` | Valuable IVP item; validator stability for initial condition needs attention. |
| `ode-hom-cand-001` | 81 | `revise_then_review` | Math correct, but prompt directly gives `y=vx`, weakening trigger training. |
| `ode-hom-cand-002` | 82.5 | `revise_then_review` | Good idea and math correct, but rubric/validator support for equivalent substitutions is weak. |
| `ode-linear-cand-001` | 83.5 | `revise_then_review` | Correct standard linear item, but prompt gives away integrating factor. |
| `ode-linear-cand-002` | 89.5 | `strong_candidate` | Strong standard-form transformation item; high training value. |
| `ode-mixed-cand-001` | 91.5 | `strong_candidate` | Best method-recognition item; rubric should better capture why not forced separation. |

Recommendation counts:

- `strong_candidate`: 4
- `revise_then_review`: 4
- `defer`: 0
- `reject`: 0

## 6. Per-candidate Review Records

### `ode-sep-cand-001`

- Candidate ID: `draft-ode-sep-cand-001`
- Question ID: `ode-sep-cand-001`
- Hard fail triggered: no
- Hard fail reason: none
- Weighted score: 75
- Recommendation: `revise_then_review`
- Reviewer summary: 数学正确，`dy/dx=3xy` 的通解方向正确；但题目太基础，public prompt 直接说 separable / separate variables，削弱题眼识别训练价值。
- Required changes before publish planning:
  - prompt 改成让学生自己判断方法，不要直接写 separable / separate variables；
  - expected_answer 主答案建议改为 `y=Ce^(3x^2/2)`；
  - log form 保留为 alias。
- Reviewer final note: 可作为入门题保留，但不是优先发布项。

### `ode-sep-cand-002`

- Candidate ID: `draft-ode-sep-cand-002`
- Question ID: `ode-sep-cand-002`
- Hard fail triggered: no
- Hard fail reason: none
- Weighted score: 86
- Recommendation: `strong_candidate`
- Reviewer summary: 比 001 更好，训练“先整理再分离变量”，符合考研数学一微分方程得分能力训练。
- Required changes before publish planning:
  - prompt 减少方法提示，不要直接说 becomes separable；
  - expected_answer 主答案建议改为 `y=C(1+x^2)`；
  - `ln|y|=ln(1+x^2)+C` 保留为 alias 或 trusted equivalent form。
- Reviewer final note: 推荐进入后续 formal publish planning 的首选候选之一。

### `ode-sep-cand-003`

- Candidate ID: `draft-ode-sep-cand-003`
- Question ID: `ode-sep-cand-003`
- Hard fail triggered: no
- Hard fail reason: none
- Weighted score: 85.5
- Recommendation: `strong_candidate`
- Reviewer summary: 初值条件提高训练价值；数学正确，`y=3e^(x^2)` 正确。
- Required changes before publish planning:
  - 重点确认 validator 对 initial condition 的处理是否稳定；
  - answer aliases 保留 `exp(x^2)`、空格变体等合理形式。
- Reviewer final note: 可进入后续 formal publish planning，但要重点看 initial-condition validator 可靠性。

### `ode-hom-cand-001`

- Candidate ID: `draft-ode-hom-cand-001`
- Question ID: `ode-hom-cand-001`
- Hard fail triggered: no
- Hard fail reason: none
- Weighted score: 81
- Recommendation: `revise_then_review`
- Reviewer summary: 数学正确，但 prompt 直接要求 `y=vx`，削弱一阶齐次题眼识别训练。
- Required changes before publish planning:
  - prompt 改成“判断方程类型并求解”，不要直接指定 `y=vx`；
  - 保留 ratio structure hint，但不要直接喂替换方法。
- Reviewer final note: 可保留为齐次方程基础题，但发布前必须弱化方法提示。

### `ode-hom-cand-002`

- Candidate ID: `draft-ode-hom-cand-002`
- Question ID: `ode-hom-cand-002`
- Hard fail triggered: no
- Hard fail reason: none
- Weighted score: 82.5
- Recommendation: `revise_then_review`
- Reviewer summary: 数学正确，训练价值不错；但 rubric 偏窄，可能漏判等价 ratio substitution 或表达形式。
- Required changes before publish planning:
  - 增强 answer_aliases；
  - 增加 expected_patterns 以支持等价表达；
  - 不要让 rubric 过度绑定唯一关键词 `y=vx`。
- Reviewer final note: 若修好 rubric/aliases，可作为补齐 `ode_homogeneous_first_order` 节点覆盖的候选。

### `ode-linear-cand-001`

- Candidate ID: `draft-ode-linear-cand-001`
- Question ID: `ode-linear-cand-001`
- Hard fail triggered: no
- Hard fail reason: none
- Weighted score: 83.5
- Recommendation: `revise_then_review`
- Reviewer summary: 数学正确，是标准一阶线性方程题；但 prompt 直接写 use integrating factor，入口训练偏弱。
- Required changes before publish planning:
  - prompt 改成 `Solve y' + 2y = e^x. State the equation type and solve it.`
  - 不要直接写 integrating factor；
  - 保留 integrating factor 作为 trusted rubric method 项，而非 public prompt 直接提示。
- Reviewer final note: 可作为一阶线性入门题，但不如 `ode-linear-cand-002` 优先。

### `ode-linear-cand-002`

- Candidate ID: `draft-ode-linear-cand-002`
- Question ID: `ode-linear-cand-002`
- Hard fail triggered: no
- Hard fail reason: none
- Weighted score: 89.5
- Recommendation: `strong_candidate`
- Reviewer summary: 本批较强候选；要求先化为标准形 `y'+2y=3x`，再用一阶线性方法，训练价值明显。
- Required changes before publish planning:
  - rubric/aliases 允许 `3x/2 - 3/4 + C e^(-2x)` 的顺序、空格和等价形式；
  - 保持标准形转化作为核心 scoring 点。
- Reviewer final note: 推荐进入后续 formal publish planning 的首选候选之一。

### `ode-mixed-cand-001`

- Candidate ID: `draft-ode-mixed-cand-001`
- Question ID: `ode-mixed-cand-001`
- Hard fail triggered: no
- Hard fail reason: none
- Weighted score: 91.5
- Recommendation: `strong_candidate`
- Reviewer summary: 本批最有题型识别价值的题之一；训练学生不要强行分离变量，而要识别一阶线性形式。
- Required changes before publish planning:
  - rubric 补充一个 trigger/diagnostic 项，检查学生是否说明这不是标准可分离形式，而是 `y' + P(x)y = Q(x)`；
  - 避免只用 `linear`、`integrating factor` 关键词就高分；
  - answer aliases 保留 `xy=x^3/3+C` 与 `y=x^2/3+C/x`。
- Reviewer final note: 推荐进入后续 formal publish planning 的首选候选之一。

## 7. Candidate Recommendation Summary

This section records the human reviewer recommendation summary. It is not a formal publish decision, not a formal catalog selection, not a manifest change, and not a direct instruction to publish.

Human reviewer recommended top 3 for later formal publish planning:

1. `ode-linear-cand-002`
2. `ode-mixed-cand-001`
3. `ode-sep-cand-002`

If a later phase needs 5 candidates, human reviewer suggested adding:

4. `ode-sep-cand-003`
5. `ode-hom-cand-002`

Backup but not priority:

- `ode-linear-cand-001`
- `ode-hom-cand-001`
- `ode-sep-cand-001`

## 8. Required Changes Before Publish Planning

Cross-candidate required change themes:

- reduce public prompt over-hinting where method names are directly provided;
- improve main answer form for separable general-solution candidates;
- keep equivalent answer forms as aliases;
- improve rubric reliability where keyword matching is too narrow;
- improve validator and aliases for initial-value or equivalent-form cases;
- strengthen mixed-recognition rubric so it captures why forced separation is not the reliable method;
- keep trusted scoring material out of learner-facing outputs.

Candidate-specific required changes are recorded in each per-candidate review record above.

## 9. Boundary Confirmation

Phase 4.8.3B-3 confirms:

- no draft YAML modified;
- no preview modified;
- no validation report modified;
- no batch manifest modified;
- no formal catalog modified;
- no `backend/catalog_data/manifest.yaml` modification;
- no formal question YAML added;
- no formal publish;
- no formal import;
- no candidate content edits;
- no engine changes;
- no API changes;
- no learner projector changes;
- no Local Trainer changes;
- no coach_output changes;
- no CatalogValidator changes;
- no authoring/import CLI changes;
- no endpoint added;
- no history/frontend/database/auth/LLM/mastery/review/formal persistence;
- no scoring integration;
- trusted-only review content must not be exposed to learner-facing outputs.

## 10. Recommended Next Step

Recommended next phase:

```text
Phase 4.8.4 Formal Publish Planning For Selected Candidates
```

Important boundary:

- Phase 4.8.4 should still be planning, not direct publish.
- It should decide how to safely revise and prepare the human reviewer recommended candidates for a later explicit publish workflow.
- It should not directly edit the formal catalog or manifest without a separate explicit approval.
