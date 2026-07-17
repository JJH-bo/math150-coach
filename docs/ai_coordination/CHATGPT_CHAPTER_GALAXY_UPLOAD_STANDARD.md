# ChatGPT 章节内容上传与星系生成标准

> 适用对象：负责阅读教材、讲义、笔记、错题、题库或章节总结，并向 `math150-coach` 提交章节内容的 ChatGPT。
>
> 当前首个使用场景：根据用户随后提供的“无穷级数”章节材料生成可导入的章节内容。
>
> 本文是**上传契约**，不是仅供参考的建议。ChatGPT 必须输出一份完整、可追溯、可直接处理的 Markdown 结果，不能只给提纲、方案或把内容提取工作留给 Codex。

---

## 1. 最终目标

把一个章节整理成一个以最终 Boss 黑洞为视觉核心的知识星域：

- 一个章节由若干个**核心星系**组成；
- 一个核心星系只对应一个真正独立的核心知识模块；
- 每个核心星系固定包含 **3–5 个可见训练星球**；
- 每个训练星球对应一项可训练、可判断是否掌握的能力，不对应随意拆出的一条定义或一道孤立题目；
- 所有核心星系最终共同指向**一个全章 Boss**，Boss 负责综合验收；
- 星系数量服从章节内容，不为了画面对称强行凑数，也不为了减少工作量把不同方法硬塞进同一个星系；
- 内容较多时可以增加星系，但必须扩大扇形空间或使用不同纵深带，不能靠缩小星球、压缩间距或叠放星系来硬塞。

上传结果必须同时服务两件事：

1. 让视觉系统知道有多少个星系、每个星系有哪些星球、星系之间如何连接、它们与 Boss 的关系；
2. 让训练系统知道每个星球训练什么、用什么题验证、错误后修复到哪里、通过什么证据判定掌握。

---

## 2. 不可混淆的项目术语

| 项目概念 | 内容含义 | 视觉含义 | 数量规则 |
|---|---|---|---|
| Chapter | 一个完整学习章节 | 一个完整 Boss 星域 | 每次上传 1 个 |
| MacroNode / Core System | 一个可独立学习和验收的核心知识模块 | 一个由训练星球和连线组成的星系 | 由内容决定 |
| MicroNode / Training Planet | 一项可训练、可观察、可修复的能力 | 一个可点击训练星球 | 每个星系严格 3–5 个 |
| HiddenAbility | 用于诊断根因的更细能力 | 默认不可见，不新增星球 | 按诊断需要添加 |
| MacroChallenge | 一个模块的局部达标检查 | 星系内部的终点/汇入关系，不是新的 Boss 黑洞 | 通常每个星系 1 个 |
| GalaxyBoss | 全章综合验收 | 全章唯一的 Boss 黑洞 | 每章严格 1 个 |
| Edge | 先修、推导、转换、检查或修复关系 | 星系内部、星系之间和通向 Boss 的连线 | 每条都要有理由 |

### 2.1 最关键的区分

训练星球代表的是**能力节点**，不是题目数量。

错误示例：

- 把“例题 1、例题 2、例题 3、例题 4”直接做成四个星球；
- 把同一判断方法换四个数字后拆成四个星球；
- 把定义中的四句话机械拆成四个星球；
- 因为材料有二十页，就生成二十个可见星球。

正确做法：

- 先确定学习者真正需要形成的 3–5 项能力；
- 再为每项能力配置核心题、变式题、评分证据和错误修复；
- 更细的前置能力、易混点和错误根因写入 `HiddenAbilities`，不继续增加可见星球。

---

## 3. 核心星系如何划分

### 3.1 一个知识模块能独立成为星系的条件

候选模块原则上应同时满足下列条件：

1. 有明确且独立的学习目标；
2. 有相对稳定的题目触发信号或使用场景；
3. 有一套可描述的方法、判断链或操作流程；
4. 可以设计局部验收任务，判断学习者是否真正掌握；
5. 与相邻模块相比，至少在核心问题、方法边界或错误模式上有实质差异。

仅有一个公式、一个术语、一条孤立技巧或一道特殊题，通常不足以单独成为星系。它们应并入最相关的核心模块，作为训练星球内容或隐藏能力。

### 3.2 合并规则

出现以下情况时，优先合并候选模块：

- 两者使用相同的题目触发信号和同一方法链；
- 一个只是另一个的直接步骤，不能独立验收；
- 两者各自只能产生 1–2 项可训练能力；
- 强行拆开后会产生大量重复题或重复连线；
- 区别只是教材排版标题不同，而不是学习能力不同。

### 3.3 拆分规则

出现以下情况时，优先拆分候选模块：

- 一个模块需要超过 5 个可见训练星球才能讲清楚；
- 同一标题下存在两套明显不同的触发条件、方法链或适用边界；
- 学习者可能掌握前半部分但完全不会后半部分，且两部分可以分别验收；
- 错误模式和修复路径明显分离；
- 模块之间存在清晰的先修关系，而不是并列细节。

### 3.4 星系数量

- 星系数量没有为了视觉整齐而设置的硬性总数；
- 一般章节常见为 3–6 个核心星系，但这只是经验范围，不是凑数要求；
- 内容确实丰富时可以超过 6 个；
- 超过 6 个时，ChatGPT 必须在 `GalaxyLayoutPlan` 中明确推荐以下至少一种策略：
  - `expanded_fan`：扩大扇形半径与观察空间；
  - `two_depth_bands`：使用近、远两条纵深带，但保持每个星系独立可读；
  - `progressive_reveal`：按学习阶段逐批显现，不在首屏同时堆满；
  - `chapter_split_recommended`：材料实际上包含两个可独立章节，建议拆章。
- 不允许使用“缩小星球”“缩小 Boss”“压缩星系间距”“让多个星系重叠”作为内容过多的解决方案。

### 3.5 每个星系的 3–5 个训练星球

每个星系必须严格有 3–5 个 `MicroNode`。可选类型只有：

- `concept`：理解定义、本质、对象或判定含义；
- `trigger`：识别何时使用本模块、从题干发现信号；
- `method`：选择并执行核心方法；
- `transformation`：完成等价变形、条件转换或表示转换；
- `calculation`：稳定完成关键计算；
- `expression`：写出完整条件、过程、结论或规范证明。

不要求每个星系把六种类型全部使用。应按模块真实结构选择 3–5 项：

- 偏定理与判定边界的模块，通常更重视 `concept / trigger / expression`；
- 偏方法执行的模块，通常更重视 `trigger / method / transformation / calculation`；
- 偏证明与综合表达的模块，通常更重视 `concept / method / expression`。

每个训练星球的描述必须回答：

1. 学习者要形成什么可观察能力；
2. 面对什么信号时应启动这项能力；
3. 成功表现是什么；
4. 最常见的失败是什么；
5. 失败后应回到哪个节点修复。

---

## 4. 全章 Boss 的规则

每章只允许一个视觉 `GalaxyBoss`。它不能只是最大、最难的一道常规题，而必须检查多个星系之间的综合调用。

Boss 至少应检查：

- 能否从复杂信息中识别需要调用哪些星系；
- 能否按正确顺序组合不同模块；
- 能否识别方法的适用条件和失效边界；
- 能否完成关键计算或推理；
- 能否给出规范、完整、可评分的最终表达；
- 失败后能否定位到具体星系和训练星球，而不是只返回“答案错误”。

`MacroChallenge` 是各星系的局部达标检查，不得被描述成第二个、第三个 Boss 黑洞。所有 `MacroChallenge` 最终汇入同一个 `GalaxyBoss`。

Boss 的失败路由必须至少精确到 `MicroNode`，例如：

```text
未识别适用条件 -> series.system_02.trigger
方法选择正确但变形失败 -> series.system_03.transformation
结论缺少必要条件 -> series.system_04.expression
```

---

## 5. 必须从上传材料中提取的内容

ChatGPT 必须阅读用户提供的全部材料，并提取下列信息。缺失时要明确标记信息缺口，不得凭感觉补写成确定事实。

### 5.1 章节边界

- 本章覆盖什么；
- 明确不覆盖什么；
- 需要哪些先修知识；
- 后续会被哪些章节或题型调用；
- 材料是否混入了本应属于其他章节的内容。

### 5.2 数学内容

- 定义、定理、性质、结论；
- 所有成立条件、使用边界和例外；
- 核心公式和符号含义；
- 典型问题类型；
- 题干触发信号；
- 方法选择依据；
- 标准步骤与关键变形；
- 规范表达要求；
- 易混概念与对比点；
- 常见错误、伪掌握和漏条件；
- 跨模块综合方式；
- 能证明掌握的最小证据。

### 5.3 来源证据

每个核心星系、训练星球和 Boss 都必须写 `source_evidence`，指向上传材料中的章节标题、页码、题号、段落标题或可辨认的原文位置。

如果上传内容没有页码，可使用稳定的语义定位，例如：

```text
材料A > 第三节“判定方法” > 例4后的总结
课堂笔记 > “常见误区”小节 > 第2条
错题集 > 题目ID S-017
```

不允许只写“来自教材”“来自用户材料”这类无法复查的来源。

### 5.4 冲突和缺口

出现下列情况时必须单独列出：

- 不同材料给出的符号或结论不一致；
- 题目答案与定理条件冲突；
- 某个核心模块只有结论，没有方法说明或训练题；
- 材料不足以确定难度、边界或 Boss 综合方式；
- ChatGPT 对某段识别结果不确定。

使用 `InformationGaps` 和 `SourceConflicts` 记录，不得默默猜测。

---

## 6. 星系空间与扇形布局提示

ChatGPT 不负责输出最终三维坐标，但必须提供足够的语义布局信息，让视觉系统不需要重新猜测内容层级。

### 6.1 布局原则

- Boss 黑洞是全章唯一视觉中心和尺度参照；
- 各核心星系分布在 Boss 的有限扇形观察空间内，而不是完整 360 度环绕；
- 一个星系内部的 3–5 个星球保持聚合，不能散落到其他星系之间；
- 星系之间保持明显空隙，连线不能让三个星系看起来像一个大团；
- 学习先修关系可以映射为远近纵深，但不能因此把所有星系排成一条直线；
- 视觉优先级高不等于离 Boss 最近；必须结合学习顺序、综合贡献和遮挡风险说明；
- 内容增加时优先扩大空间，不降低已验收的星球、Boss、连线和星空画面质量。

### 6.2 ChatGPT 需要提供的布局语义

每个星系至少给出：

- `learning_order`：建议学习顺序；
- `visual_priority`：`high / medium / low`；
- `recommended_depth`：`near / middle / far`；
- `preferred_sector`：`upper_left / left / lower_left / upper / lower / flexible`；
- `prerequisite_system_ids`：先修星系；
- `boss_contribution`：它向最终 Boss 提供什么能力；
- `spacing_reason`：为什么要与某些星系明显分开。

这些只是语义提示。禁止用绝对像素、屏幕坐标或未经项目验证的 Three.js 坐标冒充最终布局。

---

## 7. 上传文件的强制结构

最终交付必须是一个完整 Markdown 文件。除 `source_evidence` 中引用原材料名称外，所有 ID 必须使用稳定的英文小写标识，不得含空格，推荐格式：

```text
<chapter_id>.<system_id>.<node_role>
```

示例：

```text
infinite_series.system_01
infinite_series.system_01.trigger
infinite_series.system_01.method
infinite_series.boss
```

ID 一旦生成，在后续修改中不得因标题润色而随意变化。

### 7.0 Markdown 兼容性规则

- 文件必须保存为 UTF-8；
- 本文规定的二级标题和表格列名必须原样保留；
- ID 列表和能力维度列表使用英文逗号分隔；
- `SourceEvidence.values` 中的多项内容使用英文分号分隔；
- 表格单元格内不得出现原始竖线字符 `|`，因为它会被解析为新列；绝对值、条件竖线等数学符号应改写为 `\lvert ... \rvert`、文字条件或其他不含原始竖线的 LaTeX；
- 表格单元格内不写真实换行，长题干、长答案和评分细则放到后面的 `TrainingAssets` 块；
- 不得省略必需列，不得用自然语言改写类型枚举；
- 空值确实不可避免时写 `unknown` 并同时登记到 `InformationGaps`，不能删除整列。

### 7.1 文件头

```markdown
# [章节标题]
chapter_id: [稳定英文ID]
title: [中文章节标题]
source_version: [用户材料版本或上传日期]
generation_status: final
material_scope: [一句话说明本次读取了哪些材料]
```

`generation_status` 必须为 `final` 才能交给 Codex。草稿、候选方案和未完成提纲不得作为开发交接物。

### 7.2 SourceDigest

```markdown
## SourceDigest

### Included
- [本章明确覆盖的内容]

### Excluded
- [明确不在本章处理的内容]

### Prerequisites
- [先修知识]

### DownstreamUses
- [后续用途]

### InformationGaps
- [缺失信息；没有则写“无”]

### SourceConflicts
- [材料冲突；没有则写“无”]
```

### 7.3 GalaxyPlan

一行对应一个核心星系。`planet_count` 只能是 3、4 或 5。

`GalaxyPlan` 是当前三维星系组合层的扩展数据，不替代后面的章节导入器核心表。

```markdown
## GalaxyPlan
| system_id | macro_node_id | title | core_question | learning_order | visual_priority | recommended_depth | preferred_sector | planet_count | prerequisite_system_ids | boss_contribution | spacing_reason | source_evidence |
|---|---|---|---|---:|---|---|---|---:|---|---|---|---|
| [id] | [MacroNode id] | [标题] | [本星系解决的核心问题] | 1 | high | middle | upper_left | 4 | [] | [为Boss提供的能力] | [保持独立空间的理由] | [来源定位] |
```

如果星系超过 6 个，紧接着增加：

```markdown
layout_strategy: expanded_fan | two_depth_bands | progressive_reveal | chapter_split_recommended
layout_strategy_reason: [为什么选择该策略]
```

### 7.4 GalaxyBoss

只能有一行。

`GalaxyBoss` 是当前三维视觉层对多个局部 `MacroChallenge` 的唯一 Boss 聚合描述。当前章节导入器不会把它当作核心图节点，因此：

- 不要在核心 `Edges` 表中直接使用 `GalaxyBoss.id` 作为端点；
- 使用 `covers_system_ids`、`boss_contribution` 和 `failure_routing` 描述视觉汇聚关系；
- 核心训练图仍由每个 `MacroChallenge` 检查所属 `MicroNode`；
- 星系组合阶段再把这些局部验收统一映射到一个视觉 Boss 黑洞。

```markdown
## GalaxyBoss
| id | title | covers_system_ids | integrated_learning_goal | entry_requirements | challenge_brief | success_evidence | failure_routing | source_evidence |
|---|---|---|---|---|---|---|---|---|
| [chapter_id.boss] | [Boss标题] | [全部system_id] | [综合目标] | [进入条件] | [综合任务摘要] | [通过证据] | [失败到MicroNode的映射] | [来源定位] |
```

### 7.5 MacroNodes

此表与当前项目章节导入器一致。一行对应一个核心星系。

```markdown
## MacroNodes
| id | title | knowledge_node_id |
|---|---|---|
| [macro id] | [核心模块标题] | [稳定知识节点ID] |
```

### 7.6 MicroNodes

每个 `macro_node_id` 必须恰好出现 3–5 行。

```markdown
## MicroNodes
| id | macro_node_id | type | title | description |
|---|---|---|---|---|
| [micro id] | [所属macro id] | concept/trigger/method/transformation/calculation/expression | [能力标题] | [可观察训练目标、成功表现和失败表现] |
```

### 7.7 MacroChallenges

每个核心星系通常一行。它是模块局部验收，不是额外视觉 Boss。

```markdown
## MacroChallenges
| id | macro_node_id | title | covers_micro_nodes |
|---|---|---|---|
| [challenge id] | [macro id] | [局部验收标题] | [本星系全部micro id] |
```

### 7.8 SourceEvidence

此表是当前训练题生成器读取材料证据的核心入口，不能用前面的说明文字代替。

```markdown
## SourceEvidence
| key | values |
|---|---|
| chapter_topic | [章节主题] |
| subject_area | [学科范围] |
| core_concepts | [概念1]; [概念2] |
| core_formulas | [公式1]; [公式2] |
| core_theorems | [定理1及完整条件]; [定理2及完整条件] |
| typical_problem_types | [题型1]; [题型2] |
| entry_triggers | [题眼1]; [题眼2] |
| method_choices | [选择依据1]; [选择依据2] |
| key_transformations | [关键转化1]; [关键转化2] |
| confusions | [易混点1]; [易混点2] |
| common_errors | [错误1]; [错误2] |
| prerequisites | [先修1]; [先修2] |
| downstream_uses | [后续用途1]; [后续用途2] |
| math1_value | score_value=[得分价值], false_pass_risk=[伪通过风险] |
| false_pass_risks | [风险1]; [风险2] |
```

公式、定理和错误不能只写关键词。例如应写完整成立条件、结论和错误表现，而不是只写“某判别法”“条件问题”。

### 7.9 HiddenAbilities

隐藏能力用于根因诊断，可以多于可见星球，但必须是原子、可辨认、可修复的能力。

```markdown
## HiddenAbilities
| id | owner_node_id | title | dimensions | why_exists | evidence_sources | failure_modes | repair_target_node_id |
|---|---|---|---|---|---|---|---|
| [ability id] | [macro/micro id] | [能力标题] | [维度列表] | [为什么必须诊断] | [题目或过程证据] | [可观察失败] | [修复到哪个micro id] |
```

`dimensions` 必须使用当前项目已支持的评分维度：

- `concept`
- `trigger`
- `method`
- `transformation`
- `process`
- `calculation`
- `final_answer`
- `expression`
- `migration`

### 7.10 CompareGuards

所有高频易混概念都应显式比较。

```markdown
## CompareGuards
| id | title | node_ids | contrast |
|---|---|---|---|
| [guard id] | [对比标题] | [相关node id] | [判别边界、常见混淆和最小区分证据] |
```

### 7.11 TransferNodes

```markdown
## TransferNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
|---|---|---|---|---|
| [transfer id] | [迁移任务标题] | [所属node id] | [失败修复node id] | [为什么能证明不是机械记忆] |
```

### 7.12 SynthesisNodes

```markdown
## SynthesisNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
|---|---|---|---|---|
| [synthesis id] | [综合任务标题] | [所属node id] | [失败修复node id] | [需要组合哪些能力] |
```

### 7.13 Edges

每条边必须有语义，不能只因为画面好看而连接。

允许的 `edge_type`：

- `requires`
- `supports`
- `derives_to`
- `transforms_to`
- `contrasts_with`
- `commonly_confused_with`
- `checks`
- `repairs`
- `transfers_to`
- `boss_checks`
- `blocks`

```markdown
## Edges
| id | edge_type | source_id | target_id | reason |
|---|---|---|---|---|
| [edge id] | requires | [source id] | [target id] | [具体依赖理由] |
```

边至少要覆盖：

- 每个星系内部的主要训练顺序；
- 星系之间真实存在的先修或支持关系；
- 每个局部验收对本星系训练星球的检查；
- 每个综合逻辑节点通向所属 `MacroChallenge` 的 `boss_checks` 关系；
- 错误后从诊断能力回到训练星球的修复关系。

全章唯一视觉 Boss 的跨星系汇聚关系写在 `GalaxyBoss` 和 `GalaxyPlan.boss_contribution` 中，不要为了表现汇聚而给核心 `Edges` 添加导入器未知端点。

### 7.14 ErrorRepairMap

`root_cause` 使用下列标准错误类型之一：

- `concept_gap`
- `trigger_failure`
- `method_error`
- `transformation_error`
- `process_gap`
- `calculation_error`
- `condition_miss`
- `formula_memory_error`
- `knowledge_confusion`
- `expression_weakness`
- `migration_failure`
- `synthesis_failure`

```markdown
## ErrorRepairMap
| root_cause | repair_target_node_id |
|---|---|
| [标准错误类型] | [micro id] |
```

---

## 8. 每个训练星球的题目内容

每个 `MicroNode` 至少提供：

1. 一道核心训练题；
2. 一道不只是改数字的迁移变式；
3. 明确答案或期望输出；
4. 可逐项判断的评分标准；
5. 常见错误和错误根因；
6. 修复目标；
7. 防止“蒙对”或只写最终答案的伪通过规则。

使用以下重复块，每个 `MicroNode` 一块：

```markdown
## TrainingAssets

### [micro_node_id]
training_goal: [这颗星球训练的唯一核心能力]
source_evidence: [来源定位]
entry_trigger: [学习者在什么信号下应调用该能力]
mastery_criteria: [什么证据才算掌握]
repair_target_node_id: [失败后的修复节点]

#### CoreQuestion
question_id: [稳定题目ID]
question_kind: concept_judgement | trigger_identification | method_selection | condition_transformation | calculation_execution | expression_standard
difficulty: basic | standard | advanced
target_dimensions: [能力维度]
stem: |
  [完整题干，使用 Markdown/LaTeX]
expected_answer: |
  [完整答案，不只写最终数值]
solution_outline:
  1. [关键步骤1]
  2. [关键步骤2]
rubric:
  - criterion: [评分点]
    required_evidence: [必须出现的证据]
  - criterion: [评分点]
    required_evidence: [必须出现的证据]
common_errors:
  - error: [错误表现]
    root_cause: [标准错误类型]
    repair_target_node_id: [micro id]
false_pass_risks:
  - [只看最终答案可能造成的误判]

#### TransferVariant
question_id: [稳定变式ID]
variant_relation: [与核心题相比改变了什么结构、条件或表示]
stem: |
  [不能只是替换数字]
expected_answer: |
  [完整答案]
mastery_evidence: [该变式为什么能证明迁移能力]
```

可额外使用的综合题型：

- `confusion_compare`
- `transfer_variant`
- `synthesis_decomposition`
- `boss_acceptance`

### 8.1 题目质量底线

- 题干信息必须完整，数学符号使用 Markdown/LaTeX；
- 所有定理条件、定义域、收敛条件、符号约定不得省略；
- `expected_answer` 必须与 `solution_outline` 和 `rubric` 一致；
- 评分标准必须验证过程证据，不能只比最终答案；
- 变式必须改变结构、条件、表示或方法选择，不能只改数值；
- 常见错误必须能回到一个明确的修复节点；
- 不得在题干中泄露需要学习者判断的方法；
- 不得使用“理解即可”“自行判断”“略”等无法执行的描述。

---

## 9. Boss 训练资产

在所有 `TrainingAssets` 后增加一个全章 Boss 块：

```markdown
## BossTrainingAsset

boss_id: [chapter_id.boss]
question_kind: boss_acceptance
title: [Boss任务标题]
covers_system_ids: [全部相关system id]
covers_micro_nodes: [被综合检查的micro id]
source_evidence: [来源定位]
stem: |
  [完整综合任务]
expected_answer: |
  [完整答案]
solution_outline:
  1. [识别与拆解]
  2. [模块调用顺序]
  3. [关键推理或计算]
  4. [结论与条件]
rubric:
  - criterion: [跨星系评分点]
    required_evidence: [必须出现的证据]
failure_routing:
  - observed_failure: [可观察失败]
    root_cause: [标准错误类型]
    repair_target_node_id: [具体micro id]
false_pass_risks:
  - [Boss可能被误判通过的方式]
entry_requirements:
  - [进入Boss前必须达到的局部验收]
```

Boss 不得只覆盖一个星系。如果材料不足以支持真正综合题，应在 `InformationGaps` 中说明，而不是伪造一个仅仅更长的常规题。

---

## 10. 完整性检查

ChatGPT 在提交前必须逐项自检，并把结果附在文件末尾。

```markdown
## DeliveryChecklist
| check | result | evidence |
|---|---|---|
| 每个MacroNode都对应一个GalaxyPlan星系 | pass/fail | [证据] |
| 每个星系严格有3–5个MicroNode | pass/fail | [逐星系列出数量] |
| 没有把单道题或孤立公式误当成星球 | pass/fail | [说明] |
| 每个MicroNode都有核心题和迁移变式 | pass/fail | [覆盖统计] |
| 每个星系都有局部MacroChallenge | pass/fail | [覆盖统计] |
| 全章只有一个GalaxyBoss | pass/fail | [Boss ID] |
| Boss覆盖多个星系并能路由失败 | pass/fail | [覆盖与路由统计] |
| 所有内容节点都有source_evidence或evidence_sources | pass/fail | [缺失数量必须为0] |
| 所有可见节点都没有成为孤立节点 | pass/fail | [边覆盖统计] |
| 所有高频错误都有repair_target_node_id | pass/fail | [映射统计] |
| 星系超过6个时已提供扩容策略 | pass/not_applicable/fail | [策略] |
| 材料冲突和信息缺口已显式列出 | pass/fail | [位置] |
```

任意硬性检查为 `fail` 时，`generation_status` 不得写 `final`，也不得交给 Codex。

---

## 11. ChatGPT 向 Codex 交付时必须包含的内容

### 11.1 最小有效交付

ChatGPT 必须交付：

- 一份按本文生成的完整 `.md` 文件；
- 文件的准确仓库路径，推荐：
  `docs/chapter_inputs/<chapter_id>.md`；
- 本次使用的材料清单；
- 章节划分结果和每个星系的 3–5 个训练星球；
- 全章唯一 Boss 及其失败路由；
- 所有信息缺口、材料冲突和非目标；
- `DeliveryChecklist` 的通过证据。

### 11.2 无效交付

以下内容不能作为有效交付：

- “建议把本章分成若干模块”之类的讨论稿；
- 只有星系标题，没有训练星球、题目、答案和修复映射；
- 让 Codex “自行阅读原材料并提取”；
- 只给提示词，不给最终章节文件；
- 把尚未解决的关键内容标成已完成；
- 只说“已上传 GitHub”，却不给文件路径、提交或可验证结果。

### 11.3 涉及代码时的额外硬门槛

本标准主要要求 ChatGPT 生成章节内容，通常不要求修改算法代码。

但如果交付任务同时要求新增或修改导入、拆分、排布、判定等算法，则 ChatGPT 必须先完成：

- 可运行的算法实现；
- 准确文件路径；
- 对应测试或可复查的运行证据；
- 明确说明 Codex 只需要优化、调试、集成还是审查。

不能只写算法思路后把从零实现工作转交给 Codex。

---

## 12. 可直接复制给 ChatGPT 的执行指令

```text
请完整阅读《ChatGPT 章节内容上传与星系生成标准》，再处理我提供的全部章节材料。

你必须交付一份 generation_status: final 的完整 Markdown 章节文件，而不是提纲或建议。

核心规则：
1. 一个独立核心知识模块对应一个星系；
2. 每个星系严格包含 3–5 个可见训练星球；
3. 星球代表可训练能力，不代表单道题、孤立公式或教材小标题；
4. 更细的诊断能力进入 HiddenAbilities，不能通过堆星球解决；
5. 星系数量由实际内容决定，内容多时扩大扇形空间或分纵深带，不能缩小和挤压节点；
6. 全章只有一个视觉 GalaxyBoss，各星系 MacroChallenge 只是局部验收；
7. 每个训练星球必须有核心题、迁移变式、答案、评分证据、常见错误、伪通过风险和修复节点；
8. 所有节点必须有可复查的 source_evidence；
9. 不确定、缺失或冲突的内容必须分别写入 InformationGaps 和 SourceConflicts，禁止默默编造；
10. 最后填写 DeliveryChecklist，任何硬性项失败都不能标记 final。

请严格使用标准中规定的章节顺序、表格列名、节点类型、边类型和错误类型。输出文件之外不要夹带讨论性文字。
```

---

## 13. 针对“无穷级数”首次上传的特别提醒

首次使用本标准处理无穷级数章节时，ChatGPT 仍然必须以用户实际上传材料为准，不能仅凭通用教材目录预设星系。

尤其需要检查：

- 用户材料中的“无穷级数”究竟覆盖到什么边界；
- 看似相邻的判定、变换或计算是否具有独立的方法链，是否应拆成不同星系；
- 每个星系能否稳定收敛为 3–5 项训练能力；
- 是否存在大量只适合成为隐藏能力的条件检查和易混点；
- 最终 Boss 是否真的需要跨多个星系进行选择、组合和表达；
- 如果材料不完整，哪些位置只能生成临时占位，不能伪装成最终知识结论。

不要提前按照常见课程目录替用户决定模块。先做证据提取，再做能力聚类，最后生成星系。
