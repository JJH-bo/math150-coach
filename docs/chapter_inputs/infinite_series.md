# 无穷级数
chapter_id: infinite_series
title: 无穷级数
source_version: 2026-07-16_user_upload_set
generation_status: final
material_scope: 本次完整读取5份用户上传PDF，覆盖正项与交错判别、任意项级数、幂级数收敛域与求和函数、傅里叶级数。

## SourceDigest

### Included
- 通项趋零门槛、正项级数下降速度、比值判别、柯西根值判别、积分判别与 $p$ 级数尺度。
- 交错级数、莱布尼茨判别、方法失败后的后期单调与主项加误差修复。
- 任意项级数的绝对收敛、条件收敛、正负账本、结构拆解、操作安全与反例。
- 函数项级数逐点收敛、幂级数中心半径、阿贝尔内部外部结构、端点、缺项与逐项微积分。
- 幂级数求和函数的定义域、下标次数变形、基础展开、柯西乘积、递推转微分方程、隐藏系数与构造和函数。
- 傅里叶级数的周期与频率、系数正交提取、狄利克雷逐点收敛、奇偶性、半区间延拓和特殊点求数项和。

### Excluded
- 材料未系统覆盖的早期比较判别法与极限比较判别法证明，只作为已知先修模型调用。
- 一致收敛、函数项级数一致收敛判别及逐项运算的一般严格定理证明。
- 泰勒公式余项、解析函数理论、复变幂级数。
- 傅里叶级数的复指数形式、Parseval等式、系数平方和、完整狄利克雷定理证明及更高阶收敛理论。

### Prerequisites
- 数列极限、级数部分和定义、收敛必要条件。
- 正项比较思想、几何级数、$p$级数、调和级数。
- 一元函数极限、导数、反常积分、换元积分、分部积分。
- 基础三角函数、奇偶性、周期性与左右极限。

### DownstreamUses
- 幂级数展开、泰勒与麦克劳林级数、函数近似和微分方程求解。
- 利用函数恒等式或傅里叶展开求特殊数项级数。
- 后续概率统计、数值分析、信号与频域表示中对无穷展开的理解。

### InformationGaps
- 材料给出了傅里叶逐点收敛的左右极限平均结论，但未完整列出狄利克雷定理的全部充分条件；本文件只在材料所呈现的分段光滑课堂题型中使用该结论。
- 材料给出柯西乘积公式，但未系统陈述一般数项级数使用该公式的全部合法性条件；本文件将训练限制在共同绝对收敛的幂级数内部区间。
- 材料未提供统一的考研题目难度标尺；TrainingAssets中的 basic、standard、advanced 依据材料内部能力层级标注。

### SourceConflicts
- 无。五份材料在章节主线和结论上未发现实质冲突。

## GalaxyPlan
| system_id | macro_node_id | title | core_question | learning_order | visual_priority | recommended_depth | preferred_sector | planet_count | prerequisite_system_ids | boss_contribution | spacing_reason | source_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| infinite_series.system_01_foundations | infinite_series.system_01_foundations | 级数敛散的总门槛与结构识别 | 面对一个无穷级数，如何先排除无资格对象，再识别真正决定敛散的结构？ | 1 | high | far | upper_left | 4 | [] | 提供通项门槛、正项下降速度和判别法边界意识，阻止在综合题中无条件套公式。 | 这是全章入口，应与具体判别法星系留出空隙，避免把总门槛误看成某一种判别法。 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第2页“一页重建总地图”; 第3页“通项趋零只是入场券”; 第4页“正项级数” |
| infinite_series.system_02_geometric_tests | infinite_series.system_02_geometric_tests | 比值判别与根值判别的等比尾巴控制 | 怎样根据通项结构选择比值或根值，并把尾巴严格压到固定的收敛等比级数？ | 2 | high | far | left | 4 | infinite_series.system_01_foundations | 提供指数型、阶乘型和整体幂结构的快速判敛能力及固定 $k<1$ 的证明桥。 | 与积分判别分开，突出“等比尾巴”而非“连续面积尾巴”的不同方法链。 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第5页“比值判别法”; 第6页“柯西根值法”; 第11页“边界反例库” |
| infinite_series.system_03_integral_test | infinite_series.system_03_integral_test | 积分判别与 $p$ 级数尺度 | 什么时候能把离散级数尾巴转成连续面积尾巴，并用临界尺度判断收敛？ | 3 | medium | far | lower_left | 4 | infinite_series.system_01_foundations | 提供函数型、对数型正项级数的判敛能力和 $p=1$ 临界意识。 | 积分法依赖连续函数条件，必须与只看代数压缩率的比值根值星系保持独立。 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第7页“积分判别法”; 第4页正项级数方法对照; 第13页最终复盘页 |
| infinite_series.system_04_alternating_series | infinite_series.system_04_alternating_series | 交错抵消与莱布尼茨判别 | 怎样证明正负抵消是稳定的，并在莱布尼茨条件不直接可见时修复通项？ | 4 | high | middle | upper_left | 4 | infinite_series.system_01_foundations | 提供交错结构识别、单调与趋零条件验证、局部方法失败后的改造能力。 | 交错级数靠有序抵消而非绝对大小，需与正项判别星系明显分开。 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第8页“交错级数”; 第9页“莱布尼茨失败后的正确路线”; 第10页“主项+误差项” |
| infinite_series.system_05_arbitrary_terms | infinite_series.system_05_arbitrary_terms | 任意项级数的绝对收敛、条件收敛与结构拆解 | 符号与大小混合时，如何判断收敛依赖绝对大小还是正负抵消，并安全改造怪式子？ | 5 | high | middle | left | 5 | infinite_series.system_01_foundations,infinite_series.system_04_alternating_series | 提供绝对与条件收敛分类、正负账本根因诊断、结构拆解与反例防错。 | 该星系承接交错抵消但范围更广，应独立呈现账本模型与操作安全边界。 | 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第3页“为什么看绝对值”; 第4-5页“正负账本与绝对/条件收敛”; 第6-9页例题、操作与反例 |
| infinite_series.system_06_power_domain | infinite_series.system_06_power_domain | 函数项级数与幂级数收敛域 | 怎样把函数项级数逐点落地，并将幂级数的无穷多个点压缩成中心、半径和端点问题？ | 6 | high | middle | lower_left | 5 | infinite_series.system_02_geometric_tests,infinite_series.system_03_integral_test,infinite_series.system_05_arbitrary_terms | 提供逐点判敛、收敛半径计算、阿贝尔内部外部结构和端点单独验收。 | 这是从数项级数进入函数级数的结构跃迁，应与前五个数项星系留出明显层级间隔。 | 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第2-5页“逐点落地、中心半径、阿贝尔”; 第6-12页“半径、端点、缺项、一般函数项与变形” |
| infinite_series.system_07_sum_basics | infinite_series.system_07_sum_basics | 幂级数求和函数的基础转换工具 | 怎样把陌生幂级数整理成已知基础函数，并始终保留原级数的有效定义域？ | 7 | high | near | upper | 5 | infinite_series.system_06_power_domain | 提供定义域优先、下标次数对齐、已知展开识别、逐项微积分与柯西乘积能力。 | 该星系是“判敛散”到“求具体和”的升级，应靠近Boss但与高级构造保持独立。 | 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第2页“和函数=表达式+收敛域”; 第3-6页“变形、柯西乘积、展开式、先导后积与先积后导” |
| infinite_series.system_08_sum_advanced | infinite_series.system_08_sum_advanced | 递推、隐藏系数与构造和函数 | 当系数没有显式公式或原题没有变量时，怎样把隐藏关系升级为函数关系并恢复目标数值？ | 8 | high | near | lower | 4 | infinite_series.system_06_power_domain,infinite_series.system_07_sum_basics | 提供递推转微分方程、积分系数化简、人工引入变量和特殊点回收的综合转换能力。 | 该星系包含高级构造与综合链，应靠近Boss并与基础工具星系保持清晰先后关系。 | 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第7页“递推转微分方程”; 第8-9页“16.34隐藏系数、点火公式与构造S(x)”; 第10-11页综合地图 |
| infinite_series.system_09_fourier_representation | infinite_series.system_09_fourier_representation | 傅里叶表示、系数提取与半区间延拓 | 怎样把周期函数分解为兼容周期的三角波，并利用正交、奇偶与延拓高效得到系数？ | 9 | high | near | upper_left | 4 | infinite_series.system_01_foundations | 提供周期与频率含义、系数积分提取、奇偶消项和半区间补全能力。 | 傅里叶使用三角基底而非幂基底，应与幂级数星系保留视觉断层，同时在应用层与Boss汇合。 | 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第2-4页“主线、符号、系数提取”; 第6-8页“奇偶、半区间延拓与公式系统” |
| infinite_series.system_10_fourier_application | infinite_series.system_10_fourier_application | 傅里叶逐点收敛与特殊点应用 | 怎样在连续点、跳跃点和周期拼接点确定和函数值，并利用展开式提取数项级数？ | 10 | high | near | flexible | 4 | infinite_series.system_09_fourier_representation | 提供狄利克雷逐点取值、周期奇偶移点、分部积分求系数和特殊点提取数项和。 | 这是傅里叶星系的验收与全章应用出口，应靠近Boss但与表示星系保持先修箭头。 | 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第5页“狄利克雷”; 第9页“直接求和函数值”; 第10-11页“余弦展开与反求数项级数” |

layout_strategy: progressive_reveal
layout_strategy_reason: 本章实际包含10个独立方法链，按“数项判敛-幂级数-傅里叶”三阶段逐批显现；不缩小星球、不压缩星系间距，必要时配合近中远三条纵深带。

## GalaxyBoss
| id | title | covers_system_ids | integrated_learning_goal | entry_requirements | challenge_brief | success_evidence | failure_routing | source_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| infinite_series.boss | 黑洞验收：从敛散分类到函数展开与特殊和 | infinite_series.system_01_foundations,infinite_series.system_02_geometric_tests,infinite_series.system_03_integral_test,infinite_series.system_04_alternating_series,infinite_series.system_05_arbitrary_terms,infinite_series.system_06_power_domain,infinite_series.system_07_sum_basics,infinite_series.system_08_sum_advanced,infinite_series.system_09_fourier_representation,infinite_series.system_10_fourier_application | 在同一任务中识别对象、选择并组合判别方法，求幂级数收敛域与和函数，完成傅里叶展开和逐点取值，并给出可评分的条件、过程与结论。 | infinite_series.system_01_foundations.challenge,infinite_series.system_02_geometric_tests.challenge,infinite_series.system_03_integral_test.challenge,infinite_series.system_04_alternating_series.challenge,infinite_series.system_05_arbitrary_terms.challenge,infinite_series.system_06_power_domain.challenge,infinite_series.system_07_sum_basics.challenge,infinite_series.system_08_sum_advanced.challenge,infinite_series.system_09_fourier_representation.challenge,infinite_series.system_10_fourier_application.challenge | 三阶段综合任务：判定含扰动交错级数的收敛类型；求对数型幂级数的收敛域与和函数；计算半区间余弦级数并用特殊点提取平方倒数和。 | 所有方法触发正确，成立条件完整，关键变形与计算可复查，最终表达含收敛域或逐点取值规则，任一失败可精确路由到MicroNode。 | 通项门槛或结构路由错误 -> infinite_series.system_01_foundations.term_gate; 比值根值方法或边界错误 -> infinite_series.system_02_geometric_tests.geometric_proof_boundary; 积分条件或对数积分错误 -> infinite_series.system_03_integral_test.condition_check; 交错条件或拆项错误 -> infinite_series.system_04_alternating_series.failure_repair; 绝对条件分类错误 -> infinite_series.system_05_arbitrary_terms.convergence_classification; 半径或端点错误 -> infinite_series.system_06_power_domain.endpoint_judgement; 求和式漏定义域或变形错位 -> infinite_series.system_07_sum_basics.domain_first; 构造S或特殊值回收失败 -> infinite_series.system_08_sum_advanced.construct_sum_function; 傅里叶系数或延拓错误 -> infinite_series.system_09_fourier_representation.coefficient_extraction; 傅里叶逐点值或特殊点错误 -> infinite_series.system_10_fourier_application.dirichlet_value | 五份材料全章主线；重点见材料A第2-11页、材料B第3-9页、材料C第2-12页、材料D第2-10页、材料E第2-11页。 |

## MacroNodes
| id | title | knowledge_node_id |
| --- | --- | --- |
| infinite_series.system_01_foundations | 级数敛散的总门槛与结构识别 | series_convergence_foundations |
| infinite_series.system_02_geometric_tests | 比值判别与根值判别的等比尾巴控制 | ratio_root_geometric_control |
| infinite_series.system_03_integral_test | 积分判别与 $p$ 级数尺度 | integral_test_and_p_scale |
| infinite_series.system_04_alternating_series | 交错抵消与莱布尼茨判别 | alternating_series_leibniz |
| infinite_series.system_05_arbitrary_terms | 任意项级数的绝对收敛、条件收敛与结构拆解 | arbitrary_term_absolute_conditional |
| infinite_series.system_06_power_domain | 函数项级数与幂级数收敛域 | power_series_convergence_domain |
| infinite_series.system_07_sum_basics | 幂级数求和函数的基础转换工具 | power_series_sum_function_basics |
| infinite_series.system_08_sum_advanced | 递推、隐藏系数与构造和函数 | power_series_sum_function_advanced |
| infinite_series.system_09_fourier_representation | 傅里叶表示、系数提取与半区间延拓 | fourier_representation_coefficients |
| infinite_series.system_10_fourier_application | 傅里叶逐点收敛与特殊点应用 | fourier_pointwise_and_special_sums |

## MicroNodes
| id | macro_node_id | type | title | description |
| --- | --- | --- | --- | --- |
| infinite_series.system_01_foundations.term_gate | infinite_series.system_01_foundations | concept | 通项趋零门槛 | 能先检查 $a_n\to0$；成功时只把它当必要条件，失败时立即判发散；常见失败是把趋零直接当收敛。 |
| infinite_series.system_01_foundations.structure_classification | infinite_series.system_01_foundations | trigger | 级数结构分类 | 能从通项识别正项、交错、任意项、函数项或幂级数结构，并选择后续星系；常见失败是只凭外观套某个判别法。 |
| infinite_series.system_01_foundations.positive_tail_model | infinite_series.system_01_foundations | method | 正项尾巴模型 | 能解释正项级数没有抵消，必须用等比级数、$p$级数或积分尾巴控制下降速度；常见失败是只说“很小”。 |
| infinite_series.system_01_foundations.boundary_reasoning | infinite_series.system_01_foundations | expression | 工具失败边界 | 能规范表达“判别法无结论”与“级数发散”的区别，并用最小反例否定错误推出；常见失败是把极限等于1判死。 |
| infinite_series.system_02_geometric_tests.ratio_trigger | infinite_series.system_02_geometric_tests | trigger | 比值法触发识别 | 面对阶乘、连乘、递推或相邻项易约结构，能优先检查 $a_{n+1}/a_n$；常见失败是对整体 $n$ 次幂做冗长比值。 |
| infinite_series.system_02_geometric_tests.ratio_method | infinite_series.system_02_geometric_tests | method | 比值法执行与结论 | 能计算比值极限并按 $\rho<1$、$\rho>1$、$\rho=1$ 正确输出；常见失败是漏掉正项或绝对值条件。 |
| infinite_series.system_02_geometric_tests.root_method | infinite_series.system_02_geometric_tests | method | 根值法执行与结论 | 能对整体指数型结构计算 $\sqrt[n]{a_n}$ 并压到 $k^n$；常见失败是把根值极限等于1当结论。 |
| infinite_series.system_02_geometric_tests.geometric_proof_boundary | infinite_series.system_02_geometric_tests | expression | 固定 $k$ 证明桥与边界 | 能说明从极限到固定 $k<1$ 的尾巴控制，并用 $\sum1/n$ 与 $\sum1/n^2$ 解释边界无结论。 |
| infinite_series.system_03_integral_test.condition_check | infinite_series.system_03_integral_test | trigger | 积分判别条件检查 | 能确认 $a_n=f(n)$ 且 $f$ 后期正、连续、单调递减；常见失败是“看到函数就积分”。 |
| infinite_series.system_03_integral_test.continuous_tail | infinite_series.system_03_integral_test | concept | 离散尾巴与面积尾巴 | 能解释积分判别比较的是尾巴且有限项不改敛散；常见失败是把前几项异常当作方法失效。 |
| infinite_series.system_03_integral_test.p_series_scale | infinite_series.system_03_integral_test | method | $p$级数临界尺度 | 能以 $p>1$ 收敛、$p\le1$ 发散作为比较标尺；常见失败是把“比 $1/n$ 小”误当充分条件。 |
| infinite_series.system_03_integral_test.logarithmic_execution | infinite_series.system_03_integral_test | calculation | 对数型积分执行 | 能通过换元计算 $\int dx/[x(\ln x)^p]$ 并给出边界；常见失败是漏定义域或积分上下限。 |
| infinite_series.system_04_alternating_series.sign_magnitude_split | infinite_series.system_04_alternating_series | concept | 符号与幅度分离 | 能把 $(-1)^{n-1}u_n$ 中符号因子与正幅度 $u_n$ 分开；常见失败是对带符号通项检查单调。 |
| infinite_series.system_04_alternating_series.leibniz_trigger | infinite_series.system_04_alternating_series | trigger | 莱布尼茨条件验证 | 能验证 $u_n$ 后期单调不增且 $u_n\to0$；常见失败是只验证其中一个条件。 |
| infinite_series.system_04_alternating_series.partial_sum_proof | infinite_series.system_04_alternating_series | expression | 奇偶部分和夹逼 | 能用偶数部分和递增、奇数部分和递减且距离趋零解释收敛；常见失败是只背定理结论。 |
| infinite_series.system_04_alternating_series.failure_repair | infinite_series.system_04_alternating_series | transformation | 莱布尼茨失败后的修复 | 能区分方法失败与级数失败，并通过导数证明后期单调或拆成主项加绝对收敛误差；常见失败是直接判发散。 |
| infinite_series.system_05_arbitrary_terms.absolute_entry | infinite_series.system_05_arbitrary_terms | concept | 绝对值入口与蕴含证明 | 能证明 $\sum\lvert u_n\rvert$ 收敛推出 $\sum u_n$ 收敛，而不是误用 $u_n\le\lvert u_n\rvert$。 |
| infinite_series.system_05_arbitrary_terms.ledger_model | infinite_series.system_05_arbitrary_terms | concept | 正负账本模型 | 能构造 $p_n=(\lvert u_n\rvert+u_n)/2$、$q_n=(\lvert u_n\rvert-u_n)/2$ 并解释差与和。 |
| infinite_series.system_05_arbitrary_terms.convergence_classification | infinite_series.system_05_arbitrary_terms | method | 绝对与条件收敛分类 | 能先判绝对值级数，再结合原级数区分绝对收敛、条件收敛或发散；常见失败是绝对值发散便判原级数发散。 |
| infinite_series.system_05_arbitrary_terms.structure_decomposition | infinite_series.system_05_arbitrary_terms | transformation | 怪式子拆回已知结构 | 能利用奇偶拆项、有界因子、尾项尺度或题设乘积结构，把目标级数压回已知收敛对象。 |
| infinite_series.system_05_arbitrary_terms.operation_guard | infinite_series.system_05_arbitrary_terms | trigger | 保留抵消与破坏抵消 | 能判断分组、尾项平移、取绝对值、平方或改符号是否必然保留收敛，并给出反例。 |
| infinite_series.system_06_power_domain.pointwise_grounding | infinite_series.system_06_power_domain | concept | 固定 $x$ 的逐点落地 | 能区分第 $n$ 项函数 $u_n(x)$、函数项级数及收敛点集合；常见失败是把一项当整个无穷和。 |
| infinite_series.system_06_power_domain.center_radius | infinite_series.system_06_power_domain | concept | 中心、距离与阿贝尔结构 | 能解释收敛由 $\lvert x-x_0\rvert$ 控制，内部绝对收敛、外部发散而端点另判。 |
| infinite_series.system_06_power_domain.radius_execution | infinite_series.system_06_power_domain | calculation | 收敛半径计算 | 能对标准幂级数用系数比，也能对整个通项直接做比值或根值并解不等式。 |
| infinite_series.system_06_power_domain.endpoint_judgement | infinite_series.system_06_power_domain | method | 端点代回与收敛域合并 | 能把两个端点分别代回原数项级数判别，再用正确开闭端点写收敛域。 |
| infinite_series.system_06_power_domain.nonstandard_transform | infinite_series.system_06_power_domain | transformation | 缺项、一般函数项与操作变形 | 能处理 $x^{2n}$、中心平移、逐项求导积分及非幂函数项级数，并区分半径继承与端点变化。 |
| infinite_series.system_07_sum_basics.domain_first | infinite_series.system_07_sum_basics | concept | 和函数定义域优先 | 能把和函数写成“表达式加收敛域”，并拒绝用化简后函数的自然定义域替代原级数收敛域。 |
| infinite_series.system_07_sum_basics.index_alignment | infinite_series.system_07_sum_basics | transformation | 下标与次数对齐 | 能区分换编号、拆前项、提出 $x$ 的幂，并在合并前确认下标起点和次数一致。 |
| infinite_series.system_07_sum_basics.known_expansion | infinite_series.system_07_sum_basics | trigger | 基础展开式反向识别 | 能从 $1/n$、$n$、$n!$、交错符号或奇数次幂识别对数、导数型、指数或反三角原型。 |
| infinite_series.system_07_sum_basics.calculus_transform | infinite_series.system_07_sum_basics | method | 逐项求导积分消障碍 | 能根据 $n$ 在分子或分母选择求导或积分，并用 $S(0)$ 恢复常数及保留收敛域。 |
| infinite_series.system_07_sum_basics.cauchy_product | infinite_series.system_07_sum_basics | method | 柯西乘积系数卷积 | 能解释 $x^n$ 系数来自所有次数和为 $n$ 的组合，并在共同绝对收敛区间内使用。 |
| infinite_series.system_08_sum_advanced.recurrence_translation | infinite_series.system_08_sum_advanced | transformation | 系数递推转函数方程 | 能把 $a_n$、$na_n$、$(n+1)a_{n+1}$ 的关系翻译为 $S(x)$、$S'(x)$ 的方程，并正确移动下标。 |
| infinite_series.system_08_sum_advanced.hidden_coefficient | infinite_series.system_08_sum_advanced | method | 隐藏积分系数化简 | 能用三角换元把 $a_n$ 写成相邻积分量之差，再用递推比值消去未知积分。 |
| infinite_series.system_08_sum_advanced.construct_sum_function | infinite_series.system_08_sum_advanced | method | 人工构造 $S(x)$ | 能识别数项级数像某幂级数特殊点值，选择合适幂次引入 $x$，消掉分母后积分还原。 |
| infinite_series.system_08_sum_advanced.special_value_recovery | infinite_series.system_08_sum_advanced | method | 特殊点回收目标数值 | 能在求得 $S(x)$ 后验证端点可代性并代入特殊值，形成完整“化简-构造-求和-回收”链。 |
| infinite_series.system_09_fourier_representation.period_frequency | infinite_series.system_09_fourier_representation | concept | 周期、角度与频率 | 能区分 $2l$、$l$、$2\pi$、$\pi/l$ 与 $n$，并解释第 $n$ 个波在长度 $2l$ 内振动 $n$ 次。 |
| infinite_series.system_09_fourier_representation.coefficient_extraction | infinite_series.system_09_fourier_representation | method | 正交积分提取系数 | 能写出 $a_0,a_n,b_n$ 并解释“乘对应波再积一个完整周期”是频率检测。 |
| infinite_series.system_09_fourier_representation.parity_simplification | infinite_series.system_09_fourier_representation | trigger | 奇偶性消系数 | 能通过奇偶乘积与对称积分判断奇函数只剩正弦、偶函数只剩余弦。 |
| infinite_series.system_09_fourier_representation.half_range_extension | infinite_series.system_09_fourier_representation | transformation | 半区间奇偶延拓 | 能从 $[0,l]$ 构造奇延拓或偶延拓，区分补左半边与周期复制，并写对应半区间系数。 |
| infinite_series.system_10_fourier_application.dirichlet_value | infinite_series.system_10_fourier_application | concept | 狄利克雷逐点取值 | 能在连续点取原函数值，在跳跃或周期拼接点取左右极限平均，并忽略孤立点的人为值。 |
| infinite_series.system_10_fourier_application.point_mapping | infinite_series.system_10_fourier_application | method | 周期与奇偶移点 | 能先用周期性和奇偶性把目标点搬到基本区间，再用左右极限决定数值；常见失败是移点后直接代函数值。 |
| infinite_series.system_10_fourier_application.coefficient_calculation | infinite_series.system_10_fourier_application | calculation | 分部积分计算傅里叶系数 | 能对多项式余弦系数完成两次分部积分，处理边界项和 $(-1)^n$ 符号。 |
| infinite_series.system_10_fourier_application.special_point_sum | infinite_series.system_10_fourier_application | method | 特殊点提取数项和 | 能选择使三角因子统一为 $0,1,-1$ 的点，并先判断该点连续性，再解出目标数项级数。 |

## MacroChallenges
| id | macro_node_id | title | covers_micro_nodes |
| --- | --- | --- | --- |
| infinite_series.system_01_foundations.challenge | infinite_series.system_01_foundations | 级数敛散的总门槛与结构识别局部验收 | infinite_series.system_01_foundations.term_gate,infinite_series.system_01_foundations.structure_classification,infinite_series.system_01_foundations.positive_tail_model,infinite_series.system_01_foundations.boundary_reasoning |
| infinite_series.system_02_geometric_tests.challenge | infinite_series.system_02_geometric_tests | 比值判别与根值判别的等比尾巴控制局部验收 | infinite_series.system_02_geometric_tests.ratio_trigger,infinite_series.system_02_geometric_tests.ratio_method,infinite_series.system_02_geometric_tests.root_method,infinite_series.system_02_geometric_tests.geometric_proof_boundary |
| infinite_series.system_03_integral_test.challenge | infinite_series.system_03_integral_test | 积分判别与 $p$ 级数尺度局部验收 | infinite_series.system_03_integral_test.condition_check,infinite_series.system_03_integral_test.continuous_tail,infinite_series.system_03_integral_test.p_series_scale,infinite_series.system_03_integral_test.logarithmic_execution |
| infinite_series.system_04_alternating_series.challenge | infinite_series.system_04_alternating_series | 交错抵消与莱布尼茨判别局部验收 | infinite_series.system_04_alternating_series.sign_magnitude_split,infinite_series.system_04_alternating_series.leibniz_trigger,infinite_series.system_04_alternating_series.partial_sum_proof,infinite_series.system_04_alternating_series.failure_repair |
| infinite_series.system_05_arbitrary_terms.challenge | infinite_series.system_05_arbitrary_terms | 任意项级数的绝对收敛、条件收敛与结构拆解局部验收 | infinite_series.system_05_arbitrary_terms.absolute_entry,infinite_series.system_05_arbitrary_terms.ledger_model,infinite_series.system_05_arbitrary_terms.convergence_classification,infinite_series.system_05_arbitrary_terms.structure_decomposition,infinite_series.system_05_arbitrary_terms.operation_guard |
| infinite_series.system_06_power_domain.challenge | infinite_series.system_06_power_domain | 函数项级数与幂级数收敛域局部验收 | infinite_series.system_06_power_domain.pointwise_grounding,infinite_series.system_06_power_domain.center_radius,infinite_series.system_06_power_domain.radius_execution,infinite_series.system_06_power_domain.endpoint_judgement,infinite_series.system_06_power_domain.nonstandard_transform |
| infinite_series.system_07_sum_basics.challenge | infinite_series.system_07_sum_basics | 幂级数求和函数的基础转换工具局部验收 | infinite_series.system_07_sum_basics.domain_first,infinite_series.system_07_sum_basics.index_alignment,infinite_series.system_07_sum_basics.known_expansion,infinite_series.system_07_sum_basics.calculus_transform,infinite_series.system_07_sum_basics.cauchy_product |
| infinite_series.system_08_sum_advanced.challenge | infinite_series.system_08_sum_advanced | 递推、隐藏系数与构造和函数局部验收 | infinite_series.system_08_sum_advanced.recurrence_translation,infinite_series.system_08_sum_advanced.hidden_coefficient,infinite_series.system_08_sum_advanced.construct_sum_function,infinite_series.system_08_sum_advanced.special_value_recovery |
| infinite_series.system_09_fourier_representation.challenge | infinite_series.system_09_fourier_representation | 傅里叶表示、系数提取与半区间延拓局部验收 | infinite_series.system_09_fourier_representation.period_frequency,infinite_series.system_09_fourier_representation.coefficient_extraction,infinite_series.system_09_fourier_representation.parity_simplification,infinite_series.system_09_fourier_representation.half_range_extension |
| infinite_series.system_10_fourier_application.challenge | infinite_series.system_10_fourier_application | 傅里叶逐点收敛与特殊点应用局部验收 | infinite_series.system_10_fourier_application.dirichlet_value,infinite_series.system_10_fourier_application.point_mapping,infinite_series.system_10_fourier_application.coefficient_calculation,infinite_series.system_10_fourier_application.special_point_sum |

## SourceEvidence
| key | values |
| --- | --- |
| chapter_topic | 无穷级数从数项敛散到幂级数与傅里叶级数的完整能力链 |
| subject_area | 考研数学一; 高等数学; 无穷级数 |
| core_concepts | 部分和与通项必要条件; 正项尾巴下降速度; 交错抵消; 绝对收敛与条件收敛; 函数项级数收敛点与收敛域; 幂级数中心与半径; 和函数; 傅里叶三角基底与逐点收敛 |
| core_formulas | $\lim a_n\ne0$ 或不存在则 $\sum a_n$ 发散; 比值 $\rho=\lim\lvert a_{n+1}/a_n\rvert$; 根值 $\rho=\lim\sqrt[n]{\lvert a_n\rvert}$; $\sum1/n^p$ 在 $p>1$ 收敛且在 $p\le1$ 发散; $p_n=(\lvert u_n\rvert+u_n)/2$ 与 $q_n=(\lvert u_n\rvert-u_n)/2$; $R=1/\rho$ 适用于标准系数比存在情形; $\sum x^n=1/(1-x)$ 在 $\lvert x\rvert<1$; 傅里叶 $S(x)=a_0/2+\sum[a_n\cos(n\pi x/l)+b_n\sin(n\pi x/l)]$ |
| core_theorems | 比值判别：绝对比值极限小于1则绝对收敛，大于1则发散，等于1无结论; 根值判别同样三分; 积分判别要求后期正、连续、递减且与反常积分同敛散; 莱布尼茨：$u_n>0$、后期单调不增且趋零则交错级数收敛; 绝对收敛推出原级数收敛; 阿贝尔结构：幂级数半径内部绝对收敛、外部发散、端点另判; 傅里叶逐点规则：材料课堂条件下连续点取原值，跳跃与拼接点取左右极限平均 |
| typical_problem_types | 级数敛散与绝对条件分类; 判别法选择与边界; 有界扰动和合法拆项; 幂级数半径端点与收敛域; 逐项微积分求和函数; 递推系数转微分方程; 隐藏积分系数与特殊值; 半区间傅里叶展开; 傅里叶和函数点值与数项和 |
| entry_triggers | 通项不趋零; 阶乘或连乘; 整体n次幂; 正连续递减函数型通项; 显式交错符号; 任意符号先看绝对值; $a_n(x-x_0)^n$ 幂结构; 分母或分子含n; 递推给系数; 周期函数或半区间正弦余弦展开 |
| method_choices | 相邻项易约选比值; 整体指数选根值; 对数函数型正项选积分; 交错先验幅度单调趋零; 任意项先判绝对收敛再看抵消; 幂级数先半径后端点; 求和先收敛域再变形; 隐藏数项和像特殊点时构造S; 傅里叶先确定周期与延拓再算系数或取值 |
| key_transformations | $1/(n+\sin n)=1/n-\sin n/[n(n+\sin n)]$; 有理化根号扰动; $u_n=p_n-q_n$ 与 $\lvert u_n\rvert=p_n+q_n$; 幂级数下标与次数同步; 求导制造n、积分制造1/n; 递推式求和转S与S导数; $x=\sin t$ 把隐藏积分化为相邻b_n; 奇偶延拓补半区间; 分部积分降多项式次数 |
| confusions | $a_n\to0$ 与级数收敛; 判别法无结论与级数发散; 比值法与根值法; 正项调和与交错调和; 绝对收敛与条件收敛; 第n项函数与函数项级数; 半径与完整收敛域; 和函数表达式与原级数定义域; 奇偶延拓与周期延拓; 原函数点值与傅里叶和函数值 |
| common_errors | 分母加法错误拆倒数; 大分母倒数方向误判; 比值或根值极限1直接判; 莱布尼茨只验一个条件; 绝对值级数发散就判原级数发散; 缺项负端点自动写交错; 求和函数漏收敛域; 下标移动不同步; 积分还原漏S(0); 把2π当横轴周期; 周期奇偶移点后跳过狄利克雷 |
| prerequisites | 数列极限与部分和; 几何级数与p级数; 正项比较; 导数和反常积分; 换元与分部积分; 三角函数周期奇偶与左右极限 |
| downstream_uses | 泰勒幂级数; 函数近似; 微分方程; 特殊数项级数求和; 周期函数频率分解; 信号处理基础 |
| math1_value | score_value=高，覆盖数学一无穷级数判敛、幂级数收敛域与求和、傅里叶级数核心题链; false_pass_risk=高，最终答案易靠记忆或猜法得到但条件、端点、定义域与逐点值常缺失 |
| false_pass_risks | 只背判别法结论不解释固定尾巴; 只写收敛不分类绝对或条件; 只给半径不判端点; 只写和函数式不写收敛域; 只背傅里叶系数不理解正交; 只给特殊级数常数不展示选点与连续性 |

## HiddenAbilities
| id | owner_node_id | title | dimensions | why_exists | evidence_sources | failure_modes | repair_target_node_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| infinite_series.hidden.term_necessary | infinite_series.system_01_foundations.term_gate | 必要条件方向 | concept,expression | 防止把通项趋零误写为收敛充分条件 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第3页调和级数反例 | 看到 $a_n\to0$ 立即判收敛 | infinite_series.system_01_foundations.term_gate |
| infinite_series.hidden.fixed_k | infinite_series.system_02_geometric_tests.geometric_proof_boundary | 固定k统一控制 | process,expression | 比值略小于1若不统一，不能形成几何尾巴 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第5页证明闭环 | 每一项选择不同的 $k_n$ 或只写“越来越小” | infinite_series.system_02_geometric_tests.geometric_proof_boundary |
| infinite_series.hidden.rho_one | infinite_series.system_01_foundations.boundary_reasoning | 极限等于1无结论 | concept,method | 防止比值根值边界被误判 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第5-6页边界反例; 第11页反例库 | $\rho=1$ 直接写收敛或发散 | infinite_series.system_01_foundations.boundary_reasoning |
| infinite_series.hidden.integral_conditions | infinite_series.system_03_integral_test.condition_check | 积分判别三条件 | trigger,concept | 积分计算正确也可能因条件不成立而无效 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第7页 | 未验证正、连续、后期递减 | infinite_series.system_03_integral_test.condition_check |
| infinite_series.hidden.finite_tail | infinite_series.system_03_integral_test.continuous_tail | 有限项不改敛散 | concept,process | 支持所有“后期成立”判别 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第7页; 第11页反例库 | 因前几项异常拒绝使用尾部判别 | infinite_series.system_03_integral_test.continuous_tail |
| infinite_series.hidden.leibniz_object | infinite_series.system_04_alternating_series.sign_magnitude_split | 莱布尼茨检查幅度 | concept,trigger | 带符号项本身不单调，检查对象错误会破坏整条链 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第8页 | 检查 $(-1)^nu_n$ 单调 | infinite_series.system_04_alternating_series.sign_magnitude_split |
| infinite_series.hidden.eventual_monotone | infinite_series.system_04_alternating_series.leibniz_trigger | 后期单调即可 | method,process | 有限前项不影响敛散 | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第9页 | 要求从第一项起严格单调，导致误判 | infinite_series.system_04_alternating_series.leibniz_trigger |
| infinite_series.hidden.denominator_split | infinite_series.system_04_alternating_series.failure_repair | 分母不可拆倒数 | transformation | 这是用户材料明确锁定的个人bug | 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第10页“分子可拆，分母不能乱拆” | 写 $1/(A+B)=1/A+1/B$ | infinite_series.system_04_alternating_series.failure_repair |
| infinite_series.hidden.reciprocal_direction | infinite_series.system_05_arbitrary_terms.structure_decomposition | 倒数型极限方向 | calculation,concept | 分母趋无穷时整体趋零，是材料记录的真实卡点 | 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第6页例16.18个人卡点; 第10页备忘 | 把大分母的倒数误判为趋无穷 | infinite_series.system_05_arbitrary_terms.structure_decomposition |
| infinite_series.hidden.ledger_sign | infinite_series.system_05_arbitrary_terms.ledger_model | 负账本记录绝对大小 | concept | 防止把q_n当负数 | 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第4页账本定义 | 写 $q_n<0$ 或把 $u_n=p_n+q_n$ | infinite_series.system_05_arbitrary_terms.ledger_model |
| infinite_series.hidden.absolute_proof | infinite_series.system_05_arbitrary_terms.absolute_entry | 绝对收敛蕴含证明合法性 | process,expression | 任意项不能直接套正项比较 | 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第3-4页 | 仅写 $u_n\le\lvert u_n\rvert$ | infinite_series.system_05_arbitrary_terms.absolute_entry |
| infinite_series.hidden.cancellation_preservation | infinite_series.system_05_arbitrary_terms.operation_guard | 抵消结构保留 | migration,concept | 选择题常通过改符号或平方破坏条件收敛 | 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第7-9页 | 凭“项更小”判断变形必收敛 | infinite_series.system_05_arbitrary_terms.operation_guard |
| infinite_series.hidden.term_vs_series | infinite_series.system_06_power_domain.pointwise_grounding | 第n项与整个级数 | concept,expression | 函数项级数表达中最常见对象错位 | 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第3页 | 把 $u_n(x)$ 称为函数项级数 | infinite_series.system_06_power_domain.pointwise_grounding |
| infinite_series.hidden.radius_distance | infinite_series.system_06_power_domain.center_radius | 半径是距离 | concept | 防止把R写成某个x点 | 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第4页 | 把 $R$ 与右端点混为一谈 | infinite_series.system_06_power_domain.center_radius |
| infinite_series.hidden.endpoint_recheck | infinite_series.system_06_power_domain.endpoint_judgement | 端点单独代回 | trigger,method | 阿贝尔不管理端点 | 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第5、7页 | 由半径直接决定端点开闭 | infinite_series.system_06_power_domain.endpoint_judgement |
| infinite_series.hidden.missing_power_sign | infinite_series.system_06_power_domain.nonstandard_transform | 缺项幂次端点符号 | transformation,calculation | $x^{2n}$ 在负端点仍为正 | 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第8页 | 看到x=-1就自动写交错 | infinite_series.system_06_power_domain.nonstandard_transform |
| infinite_series.hidden.sum_domain | infinite_series.system_07_sum_basics.domain_first | 和函数定义域来源 | expression,final_answer | 化简式可能在原级数发散处仍有数值 | 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第2页 | 只写函数表达式或写x不等于奇点 | infinite_series.system_07_sum_basics.domain_first |
| infinite_series.hidden.index_sync | infinite_series.system_07_sum_basics.index_alignment | 下标通项同步 | transformation,process | 防止移动下标时改变项 | 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第3页 | 只改求和下限或只改系数下标 | infinite_series.system_07_sum_basics.index_alignment |
| infinite_series.hidden.s_zero | infinite_series.system_07_sum_basics.calculus_transform | S(0)恢复常数 | process,expression | 求导后积分会丢常数 | 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第5页 | 积分还原时漏C或S(0) | infinite_series.system_07_sum_basics.calculus_transform |
| infinite_series.hidden.recurrence_shift | infinite_series.system_08_sum_advanced.recurrence_translation | 递推下标翻译 | transformation,process | $(n+1)a_{n+1}$ 与S导数对应需精确移动 | 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第7页 | 多一个x或少一个x | infinite_series.system_08_sum_advanced.recurrence_translation |
| infinite_series.hidden.construct_trigger | infinite_series.system_08_sum_advanced.construct_sum_function | 构造S的触发条件 | trigger,migration | 不是所有不标准数项级数都应人工加x | 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第9-10页 | 看到分母就盲目构造 | infinite_series.system_08_sum_advanced.construct_sum_function |
| infinite_series.hidden.period_angle | infinite_series.system_09_fourier_representation.period_frequency | 横轴周期与角度一圈 | concept | 材料明确记录的长期混淆风险 | 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第3页; 第12页个人补丁 | 把2π当原函数横轴周期 | infinite_series.system_09_fourier_representation.period_frequency |
| infinite_series.hidden.orthogonality_meaning | infinite_series.system_09_fourier_representation.coefficient_extraction | 正交是频率检测 | concept,expression | 防止只会公式不理解乘积积分 | 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第4页 | 说不出为何乘对应波 | infinite_series.system_09_fourier_representation.coefficient_extraction |
| infinite_series.hidden.move_vs_value | infinite_series.system_10_fourier_application.point_mapping | 移点与取值分离 | process,concept | 周期奇偶只搬点，狄利克雷才取值 | 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第5、9、12页 | 移到基本区间后直接代某段函数值 | infinite_series.system_10_fourier_application.point_mapping |
| infinite_series.hidden.isolated_point | infinite_series.system_10_fourier_application.dirichlet_value | 孤立点修改不影响 | concept | 积分与左右极限都不受单点改变 | 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第5页 | 用人为点值作为傅里叶收敛值 | infinite_series.system_10_fourier_application.dirichlet_value |
| infinite_series.hidden.extension_distinction | infinite_series.system_09_fourier_representation.half_range_extension | 奇偶延拓与周期延拓 | transformation,concept | 一个补左半边，一个复制完整周期 | 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第7页 | 把两步混为“直接周期延拓” | infinite_series.system_09_fourier_representation.half_range_extension |

## CompareGuards
| id | title | node_ids | contrast |
| --- | --- | --- | --- |
| infinite_series.guard.term_vs_sum | 通项趋零与级数收敛 | infinite_series.system_01_foundations.term_gate,infinite_series.system_01_foundations.boundary_reasoning | 必要条件与充分条件不可倒置；最小区分证据是 $\sum1/n$。来源：材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》第3、11页。 |
| infinite_series.guard.ratio_vs_root | 比值法与根值法 | infinite_series.system_02_geometric_tests.ratio_trigger,infinite_series.system_02_geometric_tests.root_method | 比值看相邻压缩，根值看整体指数尺度；共同目标是固定等比尾巴。来源：材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》第5-6页。 |
| infinite_series.guard.method_vs_object | 判别法失败与级数失败 | infinite_series.system_01_foundations.boundary_reasoning,infinite_series.system_04_alternating_series.failure_repair | 边界或条件未验证只说明该工具无结论；最小证据是极限1的收敛与发散双反例。来源：材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》第3、9、11页。 |
| infinite_series.guard.positive_vs_alternating | 正项调和与交错调和 | infinite_series.system_03_integral_test.p_series_scale,infinite_series.system_04_alternating_series.leibniz_trigger | 同样幅度1/n，正项无抵消而发散，交错有序抵消而收敛。来源：材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》第7-8页。 |
| infinite_series.guard.absolute_vs_conditional | 绝对收敛与条件收敛 | infinite_series.system_05_arbitrary_terms.convergence_classification,infinite_series.system_05_arbitrary_terms.ledger_model | 绝对收敛两本账单独可收，条件收敛两本账都发散但差稳定。来源：材料B《16讲 06_任意项级数_高价值笔记_智慧版》第4-5页。 |
| infinite_series.guard.group_vs_sign_change | 相邻分组与改变符号 | infinite_series.system_05_arbitrary_terms.operation_guard,infinite_series.system_05_arbitrary_terms.structure_decomposition | 相邻加括号保留项与符号；减偶数项会破坏抵消。最小区分反例为交错调和。来源：材料B《16讲 06_任意项级数_高价值笔记_智慧版》第7-8页。 |
| infinite_series.guard.term_function_vs_series | 第n项函数与函数项级数 | infinite_series.system_06_power_domain.pointwise_grounding,infinite_series.system_06_power_domain.center_radius | $u_n(x)$ 是单项，$\sum u_n(x)$ 才是级数；最小证据是固定x后写成数项级数。来源：材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》第3页。 |
| infinite_series.guard.radius_vs_domain | 收敛半径与完整收敛域 | infinite_series.system_06_power_domain.center_radius,infinite_series.system_06_power_domain.endpoint_judgement | 半径只决定内部外部主体，完整收敛域还需两个端点。来源：材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》第4-7页。 |
| infinite_series.guard.formula_vs_sum_function | 化简表达式与和函数 | infinite_series.system_07_sum_basics.known_expansion,infinite_series.system_07_sum_basics.domain_first | 和函数必须带原级数收敛域；$1/(1-x)$ 在x=2有值但几何级数发散。来源：材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》第2页。 |
| infinite_series.guard.derivative_vs_integral | 逐项求导与逐项积分 | infinite_series.system_06_power_domain.nonstandard_transform,infinite_series.system_07_sum_basics.calculus_transform | 二者半径不变但端点可能不同；求导制造n，积分制造1/n并需恢复常数。来源：材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》第10-11页; 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》第5-6页。 |
| infinite_series.guard.odd_even_vs_periodic_extension | 奇偶延拓与周期延拓 | infinite_series.system_09_fourier_representation.half_range_extension,infinite_series.system_09_fourier_representation.period_frequency | 奇偶延拓补出[-l,0)，周期延拓把[-l,l]复制到全轴。来源：材料E《傅里叶级数_高价值章节笔记_蒋俊豪》第7页。 |
| infinite_series.guard.f_vs_S | 原函数点值与傅里叶和函数值 | infinite_series.system_10_fourier_application.dirichlet_value,infinite_series.system_10_fourier_application.point_mapping | 连续点S=f；跳跃点S取左右极限平均，孤立点人为值无效。来源：材料E《傅里叶级数_高价值章节笔记_蒋俊豪》第5页。 |
| infinite_series.guard.period_vs_angle | 横轴周期与三角角度 | infinite_series.system_09_fourier_representation.period_frequency,infinite_series.system_09_fourier_representation.coefficient_extraction | $2l$ 管横轴周期，$2\pi$ 管角度一圈，$\pi/l$ 负责换算。来源：材料E《傅里叶级数_高价值章节笔记_蒋俊豪》第3页。 |

## TransferNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| infinite_series.transfer.method_boundary | 边界判别迁移 | infinite_series.system_01_foundations.boundary_reasoning | infinite_series.system_01_foundations.boundary_reasoning | 把“工具无结论”从比值根值迁移到莱布尼茨、端点与傅里叶点值。来源：材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》第3、9页。 |
| infinite_series.transfer.exponential_structure | 指数结构迁移 | infinite_series.system_02_geometric_tests.root_method | infinite_series.system_02_geometric_tests.root_method | 从纯n次幂迁移到多项式乘指数、参数指数和递推比值。来源：材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》第4-6页。 |
| infinite_series.transfer.tail_invariance | 尾部不变性迁移 | infinite_series.system_03_integral_test.continuous_tail | infinite_series.system_03_integral_test.continuous_tail | 把有限项不改敛散迁移到后期单调、积分条件和端点之外的尾部判断。来源：材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》第7、11页。 |
| infinite_series.transfer.perturbation_split | 有界扰动拆解迁移 | infinite_series.system_04_alternating_series.failure_repair | infinite_series.system_04_alternating_series.failure_repair | 从n+sin n迁移到根号扰动和交错误差，证明不是机械套莱布尼茨。来源：材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》第9-10页。 |
| infinite_series.transfer.cancellation_guard | 抵消结构迁移 | infinite_series.system_05_arbitrary_terms.operation_guard | infinite_series.system_05_arbitrary_terms.operation_guard | 用反例判断取绝对值、平方、改符号和尾项平移的安全性。来源：材料B《16讲 06_任意项级数_高价值笔记_智慧版》第7-9页。 |
| infinite_series.transfer.pointwise_domain | 逐点判敛迁移 | infinite_series.system_06_power_domain.nonstandard_transform | infinite_series.system_06_power_domain.pointwise_grounding | 从幂级数迁移到一般函数项级数，避免见x就谈半径。来源：材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》第9页。 |
| infinite_series.transfer.expansion_recognition | 展开式识别迁移 | infinite_series.system_07_sum_basics.known_expansion | infinite_series.system_07_sum_basics.known_expansion | 由分母n、分子n、阶乘和奇数次幂选择不同基础函数。来源：材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》第4-6页。 |
| infinite_series.transfer.special_value_embedding | 特殊点嵌入迁移 | infinite_series.system_08_sum_advanced.construct_sum_function | infinite_series.system_08_sum_advanced.construct_sum_function | 把无变量级数识别为S(1)、S(1/2)等特殊值。来源：材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》第9-10页。 |
| infinite_series.transfer.half_range_choice | 半区间展开迁移 | infinite_series.system_09_fourier_representation.half_range_extension | infinite_series.system_09_fourier_representation.half_range_extension | 根据正弦或余弦目标反向选择奇延拓或偶延拓。来源：材料E《傅里叶级数_高价值章节笔记_蒋俊豪》第7-8页。 |
| infinite_series.transfer.special_point_choice | 傅里叶特殊点迁移 | infinite_series.system_10_fourier_application.special_point_sum | infinite_series.system_10_fourier_application.special_point_sum | 根据目标符号选择x=0、x=π等点，且先检查连续或拼接。来源：材料E《傅里叶级数_高价值章节笔记_蒋俊豪》第11页。 |

## SynthesisNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| infinite_series.synthesis.convergence_classify | 混合级数分类综合 | infinite_series.system_05_arbitrary_terms.convergence_classification | infinite_series.system_05_arbitrary_terms.convergence_classification | 组合通项门槛、正项尺度、交错抵消与绝对值分类。来源：材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》第2-11页; 材料B《16讲 06_任意项级数_高价值笔记_智慧版》第3-9页。 |
| infinite_series.synthesis.power_domain_sum | 幂级数从收敛域到和函数 | infinite_series.system_07_sum_basics.domain_first | infinite_series.system_06_power_domain.endpoint_judgement | 先求半径端点，再做变形与逐项微积分，最终输出表达式加定义域。来源：材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》第4-12页; 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》第2-6页。 |
| infinite_series.synthesis.hidden_to_value | 隐藏系数到特殊值 | infinite_series.system_08_sum_advanced.special_value_recovery | infinite_series.system_08_sum_advanced.hidden_coefficient | 组合三角换元、点火递推、构造S与端点代值。来源：材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》第8-10页。 |
| infinite_series.synthesis.fourier_full_chain | 傅里叶完整链 | infinite_series.system_10_fourier_application.special_point_sum | infinite_series.system_09_fourier_representation.coefficient_extraction | 组合周期基底、正交系数、奇偶延拓、狄利克雷和特殊点提取。来源：材料E《傅里叶级数_高价值章节笔记_蒋俊豪》第3-11页。 |
| infinite_series.synthesis.chapter_boss_route | 全章跨星系路由 | infinite_series.system_10_fourier_application.special_point_sum | infinite_series.system_01_foundations.structure_classification | 在一个任务中依次完成数项判敛、幂级数求域求和、傅里叶展开取值，并能按错误回到具体星球。来源：五份材料全章主线。 |

## Edges
| id | edge_type | source_id | target_id | reason |
| --- | --- | --- | --- | --- |
| infinite_series.edge.01_flow_1 | supports | infinite_series.system_01_foundations.term_gate | infinite_series.system_01_foundations.structure_classification | 本星系训练顺序：先形成通项趋零门槛，再进入级数结构分类。 |
| infinite_series.edge.01_flow_2 | supports | infinite_series.system_01_foundations.structure_classification | infinite_series.system_01_foundations.positive_tail_model | 本星系训练顺序：先形成级数结构分类，再进入正项尾巴模型。 |
| infinite_series.edge.01_flow_3 | supports | infinite_series.system_01_foundations.positive_tail_model | infinite_series.system_01_foundations.boundary_reasoning | 本星系训练顺序：先形成正项尾巴模型，再进入工具失败边界。 |
| infinite_series.edge.01_check_1 | checks | infinite_series.system_01_foundations.challenge | infinite_series.system_01_foundations.term_gate | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.01_check_2 | checks | infinite_series.system_01_foundations.challenge | infinite_series.system_01_foundations.structure_classification | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.01_check_3 | checks | infinite_series.system_01_foundations.challenge | infinite_series.system_01_foundations.positive_tail_model | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.01_check_4 | checks | infinite_series.system_01_foundations.challenge | infinite_series.system_01_foundations.boundary_reasoning | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.02_flow_1 | supports | infinite_series.system_02_geometric_tests.ratio_trigger | infinite_series.system_02_geometric_tests.ratio_method | 本星系训练顺序：先形成比值法触发识别，再进入比值法执行与结论。 |
| infinite_series.edge.02_flow_2 | supports | infinite_series.system_02_geometric_tests.ratio_method | infinite_series.system_02_geometric_tests.root_method | 本星系训练顺序：先形成比值法执行与结论，再进入根值法执行与结论。 |
| infinite_series.edge.02_flow_3 | supports | infinite_series.system_02_geometric_tests.root_method | infinite_series.system_02_geometric_tests.geometric_proof_boundary | 本星系训练顺序：先形成根值法执行与结论，再进入固定 $k$ 证明桥与边界。 |
| infinite_series.edge.02_check_1 | checks | infinite_series.system_02_geometric_tests.challenge | infinite_series.system_02_geometric_tests.ratio_trigger | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.02_check_2 | checks | infinite_series.system_02_geometric_tests.challenge | infinite_series.system_02_geometric_tests.ratio_method | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.02_check_3 | checks | infinite_series.system_02_geometric_tests.challenge | infinite_series.system_02_geometric_tests.root_method | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.02_check_4 | checks | infinite_series.system_02_geometric_tests.challenge | infinite_series.system_02_geometric_tests.geometric_proof_boundary | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.03_flow_1 | supports | infinite_series.system_03_integral_test.condition_check | infinite_series.system_03_integral_test.continuous_tail | 本星系训练顺序：先形成积分判别条件检查，再进入离散尾巴与面积尾巴。 |
| infinite_series.edge.03_flow_2 | supports | infinite_series.system_03_integral_test.continuous_tail | infinite_series.system_03_integral_test.p_series_scale | 本星系训练顺序：先形成离散尾巴与面积尾巴，再进入$p$级数临界尺度。 |
| infinite_series.edge.03_flow_3 | supports | infinite_series.system_03_integral_test.p_series_scale | infinite_series.system_03_integral_test.logarithmic_execution | 本星系训练顺序：先形成$p$级数临界尺度，再进入对数型积分执行。 |
| infinite_series.edge.03_check_1 | checks | infinite_series.system_03_integral_test.challenge | infinite_series.system_03_integral_test.condition_check | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.03_check_2 | checks | infinite_series.system_03_integral_test.challenge | infinite_series.system_03_integral_test.continuous_tail | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.03_check_3 | checks | infinite_series.system_03_integral_test.challenge | infinite_series.system_03_integral_test.p_series_scale | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.03_check_4 | checks | infinite_series.system_03_integral_test.challenge | infinite_series.system_03_integral_test.logarithmic_execution | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.04_flow_1 | supports | infinite_series.system_04_alternating_series.sign_magnitude_split | infinite_series.system_04_alternating_series.leibniz_trigger | 本星系训练顺序：先形成符号与幅度分离，再进入莱布尼茨条件验证。 |
| infinite_series.edge.04_flow_2 | supports | infinite_series.system_04_alternating_series.leibniz_trigger | infinite_series.system_04_alternating_series.partial_sum_proof | 本星系训练顺序：先形成莱布尼茨条件验证，再进入奇偶部分和夹逼。 |
| infinite_series.edge.04_flow_3 | supports | infinite_series.system_04_alternating_series.partial_sum_proof | infinite_series.system_04_alternating_series.failure_repair | 本星系训练顺序：先形成奇偶部分和夹逼，再进入莱布尼茨失败后的修复。 |
| infinite_series.edge.04_check_1 | checks | infinite_series.system_04_alternating_series.challenge | infinite_series.system_04_alternating_series.sign_magnitude_split | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.04_check_2 | checks | infinite_series.system_04_alternating_series.challenge | infinite_series.system_04_alternating_series.leibniz_trigger | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.04_check_3 | checks | infinite_series.system_04_alternating_series.challenge | infinite_series.system_04_alternating_series.partial_sum_proof | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.04_check_4 | checks | infinite_series.system_04_alternating_series.challenge | infinite_series.system_04_alternating_series.failure_repair | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.05_flow_1 | supports | infinite_series.system_05_arbitrary_terms.absolute_entry | infinite_series.system_05_arbitrary_terms.ledger_model | 本星系训练顺序：先形成绝对值入口与蕴含证明，再进入正负账本模型。 |
| infinite_series.edge.05_flow_2 | supports | infinite_series.system_05_arbitrary_terms.ledger_model | infinite_series.system_05_arbitrary_terms.convergence_classification | 本星系训练顺序：先形成正负账本模型，再进入绝对与条件收敛分类。 |
| infinite_series.edge.05_flow_3 | supports | infinite_series.system_05_arbitrary_terms.convergence_classification | infinite_series.system_05_arbitrary_terms.structure_decomposition | 本星系训练顺序：先形成绝对与条件收敛分类，再进入怪式子拆回已知结构。 |
| infinite_series.edge.05_flow_4 | supports | infinite_series.system_05_arbitrary_terms.structure_decomposition | infinite_series.system_05_arbitrary_terms.operation_guard | 本星系训练顺序：先形成怪式子拆回已知结构，再进入保留抵消与破坏抵消。 |
| infinite_series.edge.05_check_1 | checks | infinite_series.system_05_arbitrary_terms.challenge | infinite_series.system_05_arbitrary_terms.absolute_entry | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.05_check_2 | checks | infinite_series.system_05_arbitrary_terms.challenge | infinite_series.system_05_arbitrary_terms.ledger_model | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.05_check_3 | checks | infinite_series.system_05_arbitrary_terms.challenge | infinite_series.system_05_arbitrary_terms.convergence_classification | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.05_check_4 | checks | infinite_series.system_05_arbitrary_terms.challenge | infinite_series.system_05_arbitrary_terms.structure_decomposition | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.05_check_5 | checks | infinite_series.system_05_arbitrary_terms.challenge | infinite_series.system_05_arbitrary_terms.operation_guard | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.06_flow_1 | supports | infinite_series.system_06_power_domain.pointwise_grounding | infinite_series.system_06_power_domain.center_radius | 本星系训练顺序：先形成固定 $x$ 的逐点落地，再进入中心、距离与阿贝尔结构。 |
| infinite_series.edge.06_flow_2 | supports | infinite_series.system_06_power_domain.center_radius | infinite_series.system_06_power_domain.radius_execution | 本星系训练顺序：先形成中心、距离与阿贝尔结构，再进入收敛半径计算。 |
| infinite_series.edge.06_flow_3 | supports | infinite_series.system_06_power_domain.radius_execution | infinite_series.system_06_power_domain.endpoint_judgement | 本星系训练顺序：先形成收敛半径计算，再进入端点代回与收敛域合并。 |
| infinite_series.edge.06_flow_4 | supports | infinite_series.system_06_power_domain.endpoint_judgement | infinite_series.system_06_power_domain.nonstandard_transform | 本星系训练顺序：先形成端点代回与收敛域合并，再进入缺项、一般函数项与操作变形。 |
| infinite_series.edge.06_check_1 | checks | infinite_series.system_06_power_domain.challenge | infinite_series.system_06_power_domain.pointwise_grounding | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.06_check_2 | checks | infinite_series.system_06_power_domain.challenge | infinite_series.system_06_power_domain.center_radius | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.06_check_3 | checks | infinite_series.system_06_power_domain.challenge | infinite_series.system_06_power_domain.radius_execution | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.06_check_4 | checks | infinite_series.system_06_power_domain.challenge | infinite_series.system_06_power_domain.endpoint_judgement | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.06_check_5 | checks | infinite_series.system_06_power_domain.challenge | infinite_series.system_06_power_domain.nonstandard_transform | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.07_flow_1 | supports | infinite_series.system_07_sum_basics.domain_first | infinite_series.system_07_sum_basics.index_alignment | 本星系训练顺序：先形成和函数定义域优先，再进入下标与次数对齐。 |
| infinite_series.edge.07_flow_2 | supports | infinite_series.system_07_sum_basics.index_alignment | infinite_series.system_07_sum_basics.known_expansion | 本星系训练顺序：先形成下标与次数对齐，再进入基础展开式反向识别。 |
| infinite_series.edge.07_flow_3 | supports | infinite_series.system_07_sum_basics.known_expansion | infinite_series.system_07_sum_basics.calculus_transform | 本星系训练顺序：先形成基础展开式反向识别，再进入逐项求导积分消障碍。 |
| infinite_series.edge.07_flow_4 | supports | infinite_series.system_07_sum_basics.calculus_transform | infinite_series.system_07_sum_basics.cauchy_product | 本星系训练顺序：先形成逐项求导积分消障碍，再进入柯西乘积系数卷积。 |
| infinite_series.edge.07_check_1 | checks | infinite_series.system_07_sum_basics.challenge | infinite_series.system_07_sum_basics.domain_first | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.07_check_2 | checks | infinite_series.system_07_sum_basics.challenge | infinite_series.system_07_sum_basics.index_alignment | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.07_check_3 | checks | infinite_series.system_07_sum_basics.challenge | infinite_series.system_07_sum_basics.known_expansion | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.07_check_4 | checks | infinite_series.system_07_sum_basics.challenge | infinite_series.system_07_sum_basics.calculus_transform | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.07_check_5 | checks | infinite_series.system_07_sum_basics.challenge | infinite_series.system_07_sum_basics.cauchy_product | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.08_flow_1 | supports | infinite_series.system_08_sum_advanced.recurrence_translation | infinite_series.system_08_sum_advanced.hidden_coefficient | 本星系训练顺序：先形成系数递推转函数方程，再进入隐藏积分系数化简。 |
| infinite_series.edge.08_flow_2 | supports | infinite_series.system_08_sum_advanced.hidden_coefficient | infinite_series.system_08_sum_advanced.construct_sum_function | 本星系训练顺序：先形成隐藏积分系数化简，再进入人工构造 $S(x)$。 |
| infinite_series.edge.08_flow_3 | supports | infinite_series.system_08_sum_advanced.construct_sum_function | infinite_series.system_08_sum_advanced.special_value_recovery | 本星系训练顺序：先形成人工构造 $S(x)$，再进入特殊点回收目标数值。 |
| infinite_series.edge.08_check_1 | checks | infinite_series.system_08_sum_advanced.challenge | infinite_series.system_08_sum_advanced.recurrence_translation | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.08_check_2 | checks | infinite_series.system_08_sum_advanced.challenge | infinite_series.system_08_sum_advanced.hidden_coefficient | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.08_check_3 | checks | infinite_series.system_08_sum_advanced.challenge | infinite_series.system_08_sum_advanced.construct_sum_function | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.08_check_4 | checks | infinite_series.system_08_sum_advanced.challenge | infinite_series.system_08_sum_advanced.special_value_recovery | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.09_flow_1 | supports | infinite_series.system_09_fourier_representation.period_frequency | infinite_series.system_09_fourier_representation.coefficient_extraction | 本星系训练顺序：先形成周期、角度与频率，再进入正交积分提取系数。 |
| infinite_series.edge.09_flow_2 | supports | infinite_series.system_09_fourier_representation.coefficient_extraction | infinite_series.system_09_fourier_representation.parity_simplification | 本星系训练顺序：先形成正交积分提取系数，再进入奇偶性消系数。 |
| infinite_series.edge.09_flow_3 | supports | infinite_series.system_09_fourier_representation.parity_simplification | infinite_series.system_09_fourier_representation.half_range_extension | 本星系训练顺序：先形成奇偶性消系数，再进入半区间奇偶延拓。 |
| infinite_series.edge.09_check_1 | checks | infinite_series.system_09_fourier_representation.challenge | infinite_series.system_09_fourier_representation.period_frequency | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.09_check_2 | checks | infinite_series.system_09_fourier_representation.challenge | infinite_series.system_09_fourier_representation.coefficient_extraction | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.09_check_3 | checks | infinite_series.system_09_fourier_representation.challenge | infinite_series.system_09_fourier_representation.parity_simplification | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.09_check_4 | checks | infinite_series.system_09_fourier_representation.challenge | infinite_series.system_09_fourier_representation.half_range_extension | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.10_flow_1 | supports | infinite_series.system_10_fourier_application.dirichlet_value | infinite_series.system_10_fourier_application.point_mapping | 本星系训练顺序：先形成狄利克雷逐点取值，再进入周期与奇偶移点。 |
| infinite_series.edge.10_flow_2 | supports | infinite_series.system_10_fourier_application.point_mapping | infinite_series.system_10_fourier_application.coefficient_calculation | 本星系训练顺序：先形成周期与奇偶移点，再进入分部积分计算傅里叶系数。 |
| infinite_series.edge.10_flow_3 | supports | infinite_series.system_10_fourier_application.coefficient_calculation | infinite_series.system_10_fourier_application.special_point_sum | 本星系训练顺序：先形成分部积分计算傅里叶系数，再进入特殊点提取数项和。 |
| infinite_series.edge.10_check_1 | checks | infinite_series.system_10_fourier_application.challenge | infinite_series.system_10_fourier_application.dirichlet_value | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.10_check_2 | checks | infinite_series.system_10_fourier_application.challenge | infinite_series.system_10_fourier_application.point_mapping | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.10_check_3 | checks | infinite_series.system_10_fourier_application.challenge | infinite_series.system_10_fourier_application.coefficient_calculation | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.10_check_4 | checks | infinite_series.system_10_fourier_application.challenge | infinite_series.system_10_fourier_application.special_point_sum | 局部验收必须检查该可见能力节点。 |
| infinite_series.edge.cross_01_02 | supports | infinite_series.system_01_foundations.structure_classification | infinite_series.system_02_geometric_tests.ratio_trigger | 先识别正项与指数/阶乘结构，才能选择比值法。 |
| infinite_series.edge.cross_01_03 | supports | infinite_series.system_01_foundations.positive_tail_model | infinite_series.system_03_integral_test.condition_check | 正项尾巴模型为积分法提供方法入口。 |
| infinite_series.edge.cross_01_04 | supports | infinite_series.system_01_foundations.term_gate | infinite_series.system_04_alternating_series.leibniz_trigger | 莱布尼茨中的趋零条件建立在通项门槛上。 |
| infinite_series.edge.cross_04_05 | supports | infinite_series.system_04_alternating_series.failure_repair | infinite_series.system_05_arbitrary_terms.convergence_classification | 交错抵消经验升级为任意项的绝对与条件收敛分类。 |
| infinite_series.edge.cross_02_06 | supports | infinite_series.system_02_geometric_tests.ratio_method | infinite_series.system_06_power_domain.radius_execution | 幂级数固定x后常用比值根值求主体半径。 |
| infinite_series.edge.cross_03_06 | supports | infinite_series.system_03_integral_test.p_series_scale | infinite_series.system_06_power_domain.endpoint_judgement | 幂级数端点常回到p级数或对数型数项级数。 |
| infinite_series.edge.cross_05_06 | supports | infinite_series.system_05_arbitrary_terms.convergence_classification | infinite_series.system_06_power_domain.endpoint_judgement | 端点可能绝对或条件收敛，需要任意项分类。 |
| infinite_series.edge.cross_06_07 | requires | infinite_series.system_06_power_domain.endpoint_judgement | infinite_series.system_07_sum_basics.domain_first | 求和函数必须先获得原级数收敛域。 |
| infinite_series.edge.cross_07_08 | supports | infinite_series.system_07_sum_basics.calculus_transform | infinite_series.system_08_sum_advanced.construct_sum_function | 高级构造依赖基础逐项求导积分和原型识别。 |
| infinite_series.edge.cross_09_10 | requires | infinite_series.system_09_fourier_representation.half_range_extension | infinite_series.system_10_fourier_application.dirichlet_value | 必须先明确所展开的周期函数，才能判断逐点收敛值。 |
| infinite_series.edge.cross_08_10 | transfers_to | infinite_series.system_08_sum_advanced.special_value_recovery | infinite_series.system_10_fourier_application.special_point_sum | 两者共享“把数项和嵌入函数关系再代特殊点”的策略。 |
| infinite_series.edge.cross_01_09 | supports | infinite_series.system_01_foundations.structure_classification | infinite_series.system_09_fourier_representation.period_frequency | 傅里叶级数是另一类函数级数，需要从普通数项判别切换到三角基底结构。 |
| infinite_series.edge.hidden_repair_01 | repairs | infinite_series.hidden.term_necessary | infinite_series.system_01_foundations.term_gate | 诊断到“必要条件方向”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_02 | repairs | infinite_series.hidden.fixed_k | infinite_series.system_02_geometric_tests.geometric_proof_boundary | 诊断到“固定k统一控制”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_03 | repairs | infinite_series.hidden.rho_one | infinite_series.system_01_foundations.boundary_reasoning | 诊断到“极限等于1无结论”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_04 | repairs | infinite_series.hidden.integral_conditions | infinite_series.system_03_integral_test.condition_check | 诊断到“积分判别三条件”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_05 | repairs | infinite_series.hidden.finite_tail | infinite_series.system_03_integral_test.continuous_tail | 诊断到“有限项不改敛散”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_06 | repairs | infinite_series.hidden.leibniz_object | infinite_series.system_04_alternating_series.sign_magnitude_split | 诊断到“莱布尼茨检查幅度”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_07 | repairs | infinite_series.hidden.eventual_monotone | infinite_series.system_04_alternating_series.leibniz_trigger | 诊断到“后期单调即可”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_08 | repairs | infinite_series.hidden.denominator_split | infinite_series.system_04_alternating_series.failure_repair | 诊断到“分母不可拆倒数”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_09 | repairs | infinite_series.hidden.reciprocal_direction | infinite_series.system_05_arbitrary_terms.structure_decomposition | 诊断到“倒数型极限方向”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_10 | repairs | infinite_series.hidden.ledger_sign | infinite_series.system_05_arbitrary_terms.ledger_model | 诊断到“负账本记录绝对大小”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_11 | repairs | infinite_series.hidden.absolute_proof | infinite_series.system_05_arbitrary_terms.absolute_entry | 诊断到“绝对收敛蕴含证明合法性”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_12 | repairs | infinite_series.hidden.cancellation_preservation | infinite_series.system_05_arbitrary_terms.operation_guard | 诊断到“抵消结构保留”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_13 | repairs | infinite_series.hidden.term_vs_series | infinite_series.system_06_power_domain.pointwise_grounding | 诊断到“第n项与整个级数”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_14 | repairs | infinite_series.hidden.radius_distance | infinite_series.system_06_power_domain.center_radius | 诊断到“半径是距离”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_15 | repairs | infinite_series.hidden.endpoint_recheck | infinite_series.system_06_power_domain.endpoint_judgement | 诊断到“端点单独代回”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_16 | repairs | infinite_series.hidden.missing_power_sign | infinite_series.system_06_power_domain.nonstandard_transform | 诊断到“缺项幂次端点符号”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_17 | repairs | infinite_series.hidden.sum_domain | infinite_series.system_07_sum_basics.domain_first | 诊断到“和函数定义域来源”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_18 | repairs | infinite_series.hidden.index_sync | infinite_series.system_07_sum_basics.index_alignment | 诊断到“下标通项同步”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_19 | repairs | infinite_series.hidden.s_zero | infinite_series.system_07_sum_basics.calculus_transform | 诊断到“S(0)恢复常数”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_20 | repairs | infinite_series.hidden.recurrence_shift | infinite_series.system_08_sum_advanced.recurrence_translation | 诊断到“递推下标翻译”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_21 | repairs | infinite_series.hidden.construct_trigger | infinite_series.system_08_sum_advanced.construct_sum_function | 诊断到“构造S的触发条件”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_22 | repairs | infinite_series.hidden.period_angle | infinite_series.system_09_fourier_representation.period_frequency | 诊断到“横轴周期与角度一圈”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_23 | repairs | infinite_series.hidden.orthogonality_meaning | infinite_series.system_09_fourier_representation.coefficient_extraction | 诊断到“正交是频率检测”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_24 | repairs | infinite_series.hidden.move_vs_value | infinite_series.system_10_fourier_application.point_mapping | 诊断到“移点与取值分离”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_25 | repairs | infinite_series.hidden.isolated_point | infinite_series.system_10_fourier_application.dirichlet_value | 诊断到“孤立点修改不影响”失败时回到对应训练星球修复。 |
| infinite_series.edge.hidden_repair_26 | repairs | infinite_series.hidden.extension_distinction | infinite_series.system_09_fourier_representation.half_range_extension | 诊断到“奇偶延拓与周期延拓”失败时回到对应训练星球修复。 |
| infinite_series.edge.transfer_01 | transfers_to | infinite_series.system_01_foundations.boundary_reasoning | infinite_series.transfer.method_boundary | 该训练能力迁移到“边界判别迁移”。 |
| infinite_series.edge.transfer_repair_01 | repairs | infinite_series.transfer.method_boundary | infinite_series.system_01_foundations.boundary_reasoning | 迁移失败回到指定训练节点。 |
| infinite_series.edge.transfer_02 | transfers_to | infinite_series.system_02_geometric_tests.root_method | infinite_series.transfer.exponential_structure | 该训练能力迁移到“指数结构迁移”。 |
| infinite_series.edge.transfer_repair_02 | repairs | infinite_series.transfer.exponential_structure | infinite_series.system_02_geometric_tests.root_method | 迁移失败回到指定训练节点。 |
| infinite_series.edge.transfer_03 | transfers_to | infinite_series.system_03_integral_test.continuous_tail | infinite_series.transfer.tail_invariance | 该训练能力迁移到“尾部不变性迁移”。 |
| infinite_series.edge.transfer_repair_03 | repairs | infinite_series.transfer.tail_invariance | infinite_series.system_03_integral_test.continuous_tail | 迁移失败回到指定训练节点。 |
| infinite_series.edge.transfer_04 | transfers_to | infinite_series.system_04_alternating_series.failure_repair | infinite_series.transfer.perturbation_split | 该训练能力迁移到“有界扰动拆解迁移”。 |
| infinite_series.edge.transfer_repair_04 | repairs | infinite_series.transfer.perturbation_split | infinite_series.system_04_alternating_series.failure_repair | 迁移失败回到指定训练节点。 |
| infinite_series.edge.transfer_05 | transfers_to | infinite_series.system_05_arbitrary_terms.operation_guard | infinite_series.transfer.cancellation_guard | 该训练能力迁移到“抵消结构迁移”。 |
| infinite_series.edge.transfer_repair_05 | repairs | infinite_series.transfer.cancellation_guard | infinite_series.system_05_arbitrary_terms.operation_guard | 迁移失败回到指定训练节点。 |
| infinite_series.edge.transfer_06 | transfers_to | infinite_series.system_06_power_domain.nonstandard_transform | infinite_series.transfer.pointwise_domain | 该训练能力迁移到“逐点判敛迁移”。 |
| infinite_series.edge.transfer_repair_06 | repairs | infinite_series.transfer.pointwise_domain | infinite_series.system_06_power_domain.pointwise_grounding | 迁移失败回到指定训练节点。 |
| infinite_series.edge.transfer_07 | transfers_to | infinite_series.system_07_sum_basics.known_expansion | infinite_series.transfer.expansion_recognition | 该训练能力迁移到“展开式识别迁移”。 |
| infinite_series.edge.transfer_repair_07 | repairs | infinite_series.transfer.expansion_recognition | infinite_series.system_07_sum_basics.known_expansion | 迁移失败回到指定训练节点。 |
| infinite_series.edge.transfer_08 | transfers_to | infinite_series.system_08_sum_advanced.construct_sum_function | infinite_series.transfer.special_value_embedding | 该训练能力迁移到“特殊点嵌入迁移”。 |
| infinite_series.edge.transfer_repair_08 | repairs | infinite_series.transfer.special_value_embedding | infinite_series.system_08_sum_advanced.construct_sum_function | 迁移失败回到指定训练节点。 |
| infinite_series.edge.transfer_09 | transfers_to | infinite_series.system_09_fourier_representation.half_range_extension | infinite_series.transfer.half_range_choice | 该训练能力迁移到“半区间展开迁移”。 |
| infinite_series.edge.transfer_repair_09 | repairs | infinite_series.transfer.half_range_choice | infinite_series.system_09_fourier_representation.half_range_extension | 迁移失败回到指定训练节点。 |
| infinite_series.edge.transfer_10 | transfers_to | infinite_series.system_10_fourier_application.special_point_sum | infinite_series.transfer.special_point_choice | 该训练能力迁移到“傅里叶特殊点迁移”。 |
| infinite_series.edge.transfer_repair_10 | repairs | infinite_series.transfer.special_point_choice | infinite_series.system_10_fourier_application.special_point_sum | 迁移失败回到指定训练节点。 |
| infinite_series.edge.synthesis_01 | boss_checks | infinite_series.synthesis.convergence_classify | infinite_series.system_05_arbitrary_terms.challenge | 综合节点完成后进入所属星系局部验收。 |
| infinite_series.edge.synthesis_02 | boss_checks | infinite_series.synthesis.power_domain_sum | infinite_series.system_07_sum_basics.challenge | 综合节点完成后进入所属星系局部验收。 |
| infinite_series.edge.synthesis_03 | boss_checks | infinite_series.synthesis.hidden_to_value | infinite_series.system_08_sum_advanced.challenge | 综合节点完成后进入所属星系局部验收。 |
| infinite_series.edge.synthesis_04 | boss_checks | infinite_series.synthesis.fourier_full_chain | infinite_series.system_10_fourier_application.challenge | 综合节点完成后进入所属星系局部验收。 |
| infinite_series.edge.synthesis_05 | boss_checks | infinite_series.synthesis.chapter_boss_route | infinite_series.system_10_fourier_application.challenge | 综合节点完成后进入所属星系局部验收。 |
| infinite_series.edge.compare_01a | contrasts_with | infinite_series.guard.term_vs_sum | infinite_series.system_01_foundations.term_gate | 对比节点连接“通项必要条件”一侧。 |
| infinite_series.edge.compare_01b | contrasts_with | infinite_series.guard.term_vs_sum | infinite_series.system_01_foundations.boundary_reasoning | 对比节点连接“级数充分结论”一侧。 |
| infinite_series.edge.compare_02a | contrasts_with | infinite_series.guard.ratio_vs_root | infinite_series.system_02_geometric_tests.ratio_trigger | 对比节点连接比值法入口。 |
| infinite_series.edge.compare_02b | contrasts_with | infinite_series.guard.ratio_vs_root | infinite_series.system_02_geometric_tests.root_method | 对比节点连接根值法入口。 |
| infinite_series.edge.compare_03a | contrasts_with | infinite_series.guard.method_vs_object | infinite_series.system_01_foundations.boundary_reasoning | 对比节点连接“工具无结论”。 |
| infinite_series.edge.compare_03b | contrasts_with | infinite_series.guard.method_vs_object | infinite_series.system_04_alternating_series.failure_repair | 对比节点连接“对象仍需修复分析”。 |
| infinite_series.edge.compare_04a | contrasts_with | infinite_series.guard.positive_vs_alternating | infinite_series.system_03_integral_test.p_series_scale | 对比节点连接正项尺度。 |
| infinite_series.edge.compare_04b | contrasts_with | infinite_series.guard.positive_vs_alternating | infinite_series.system_04_alternating_series.leibniz_trigger | 对比节点连接交错抵消。 |
| infinite_series.edge.compare_05a | contrasts_with | infinite_series.guard.absolute_vs_conditional | infinite_series.system_05_arbitrary_terms.convergence_classification | 对比节点连接收敛分类。 |
| infinite_series.edge.compare_05b | contrasts_with | infinite_series.guard.absolute_vs_conditional | infinite_series.system_05_arbitrary_terms.ledger_model | 对比节点连接正负账本。 |
| infinite_series.edge.compare_06a | contrasts_with | infinite_series.guard.group_vs_sign_change | infinite_series.system_05_arbitrary_terms.operation_guard | 对比节点连接操作安全边界。 |
| infinite_series.edge.compare_06b | contrasts_with | infinite_series.guard.group_vs_sign_change | infinite_series.system_05_arbitrary_terms.structure_decomposition | 对比节点连接合法结构拆解。 |
| infinite_series.edge.compare_07a | contrasts_with | infinite_series.guard.term_function_vs_series | infinite_series.system_06_power_domain.pointwise_grounding | 对比节点连接单项函数。 |
| infinite_series.edge.compare_07b | contrasts_with | infinite_series.guard.term_function_vs_series | infinite_series.system_06_power_domain.center_radius | 对比节点连接整个幂级数结构。 |
| infinite_series.edge.compare_08a | contrasts_with | infinite_series.guard.radius_vs_domain | infinite_series.system_06_power_domain.center_radius | 对比节点连接主体半径。 |
| infinite_series.edge.compare_08b | contrasts_with | infinite_series.guard.radius_vs_domain | infinite_series.system_06_power_domain.endpoint_judgement | 对比节点连接完整端点判断。 |
| infinite_series.edge.compare_09a | contrasts_with | infinite_series.guard.formula_vs_sum_function | infinite_series.system_07_sum_basics.known_expansion | 对比节点连接化简表达式。 |
| infinite_series.edge.compare_09b | contrasts_with | infinite_series.guard.formula_vs_sum_function | infinite_series.system_07_sum_basics.domain_first | 对比节点连接和函数定义域。 |
| infinite_series.edge.compare_10a | contrasts_with | infinite_series.guard.derivative_vs_integral | infinite_series.system_06_power_domain.nonstandard_transform | 对比节点连接逐项运算后的结构变化。 |
| infinite_series.edge.compare_10b | contrasts_with | infinite_series.guard.derivative_vs_integral | infinite_series.system_07_sum_basics.calculus_transform | 对比节点连接求导积分工具选择。 |
| infinite_series.edge.compare_11a | contrasts_with | infinite_series.guard.odd_even_vs_periodic_extension | infinite_series.system_09_fourier_representation.half_range_extension | 对比节点连接奇偶补全。 |
| infinite_series.edge.compare_11b | contrasts_with | infinite_series.guard.odd_even_vs_periodic_extension | infinite_series.system_09_fourier_representation.period_frequency | 对比节点连接周期复制。 |
| infinite_series.edge.compare_12a | contrasts_with | infinite_series.guard.f_vs_S | infinite_series.system_10_fourier_application.dirichlet_value | 对比节点连接傅里叶逐点值。 |
| infinite_series.edge.compare_12b | contrasts_with | infinite_series.guard.f_vs_S | infinite_series.system_10_fourier_application.point_mapping | 对比节点连接原函数点值映射。 |
| infinite_series.edge.compare_13a | contrasts_with | infinite_series.guard.period_vs_angle | infinite_series.system_09_fourier_representation.period_frequency | 对比节点连接横轴周期。 |
| infinite_series.edge.compare_13b | contrasts_with | infinite_series.guard.period_vs_angle | infinite_series.system_09_fourier_representation.coefficient_extraction | 对比节点连接角频率系数。 |

## ErrorRepairMap
| root_cause | repair_target_node_id |
| --- | --- |
| concept_gap | infinite_series.system_01_foundations.term_gate |
| trigger_failure | infinite_series.system_01_foundations.structure_classification |
| method_error | infinite_series.system_01_foundations.boundary_reasoning |
| transformation_error | infinite_series.system_07_sum_basics.index_alignment |
| process_gap | infinite_series.system_02_geometric_tests.geometric_proof_boundary |
| calculation_error | infinite_series.system_03_integral_test.logarithmic_execution |
| condition_miss | infinite_series.system_06_power_domain.endpoint_judgement |
| formula_memory_error | infinite_series.system_09_fourier_representation.period_frequency |
| knowledge_confusion | infinite_series.system_05_arbitrary_terms.ledger_model |
| expression_weakness | infinite_series.system_07_sum_basics.domain_first |
| migration_failure | infinite_series.system_05_arbitrary_terms.operation_guard |
| synthesis_failure | infinite_series.system_08_sum_advanced.special_value_recovery |

## TrainingAssets

### infinite_series.system_01_foundations.term_gate
training_goal: 把通项极限作为必要门槛而非收敛结论。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第3页“$a_n\to0$只是入场券”
entry_trigger: 题目先问级数敛散，或通项极限明显可算时。
mastery_criteria: 能先算极限；不趋零时直接发散；趋零时明确继续分析。
repair_target_node_id: infinite_series.system_01_foundations.term_gate

#### CoreQuestion
question_id: infinite_series.system_01_foundations.term_gate.core_q01
question_kind: concept_judgement
difficulty: basic
target_dimensions: concept,trigger,expression
stem: |
  判断下列说法并说明理由：若 $a_n\to0$，则 $\sum_{n=1}^{\infty}a_n$ 收敛。再说明当 $\lim a_n\ne0$ 或极限不存在时能推出什么。
expected_answer: |
  说法错误。$a_n\to0$ 只是级数收敛的必要条件，不是充分条件，例如调和级数 $\sum 1/n$ 中通项趋零但级数发散。若 $\lim_{n\to\infty}a_n\ne0$ 或极限不存在，则级数必发散。
solution_outline:
  1. 先区分必要条件与充分条件。
  2. 给出调和级数反例。
  3. 写出通项不趋零时的发散结论。
rubric:
  - criterion: 必要性判断
    required_evidence: 明确“收敛必有通项趋零，但反向不成立”
  - criterion: 反例证据
    required_evidence: 写出 $1/n\to0$ 且 $\sum1/n$ 发散
  - criterion: 发散门槛
    required_evidence: 通项极限非零或不存在时直接判发散
common_errors:
  - error: 把 $a_n\to0$ 写成收敛充分条件
    root_cause: concept_gap
    repair_target_node_id: infinite_series.system_01_foundations.term_gate
false_pass_risks:
  - 只写“错误”但不给反例，不能证明理解必要与充分的方向。

#### TransferVariant
question_id: infinite_series.system_01_foundations.term_gate.transfer_v01
variant_relation: 把逻辑判断改为含参数的通项门槛，而不是重复同一反例。
stem: |
  设 $a_n=(n+\alpha)/(2n+1)$。讨论哪些 $\alpha$ 能使 $\sum a_n$ 有可能收敛，并说明是否已经能判收敛。
expected_answer: |
  对任意固定 $\alpha$，$a_n\to1/2\ne0$，所以级数必发散；不存在“有可能收敛”的参数。此处无需再用其他判别法。
mastery_evidence: 能把参数题先压到通项极限，而不是盲目继续套判别法。

### infinite_series.system_01_foundations.structure_classification
training_goal: 识别通项的符号与变量结构并路由到正确方法族。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第2页总地图; 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第3页任意项入口; 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第2-3页函数项逐点化
entry_trigger: 通项含固定符号、交错因子、任意符号或变量 $x$ 时。
mastery_criteria: 能说出对象类型、核心困难与下一步检查，而非直接给方法名。
repair_target_node_id: infinite_series.system_01_foundations.structure_classification

#### CoreQuestion
question_id: infinite_series.system_01_foundations.structure_classification.core_q01
question_kind: trigger_identification
difficulty: standard
target_dimensions: trigger,concept,method
stem: |
  对以下对象只做“结构路由”，不必完整判敛散：
  1. $\sum 1/(n\ln n)$；
  2. $\sum (-1)^{n-1}/\sqrt n$；
  3. $\sum u_n$，其中 $u_n$ 符号无规律；
  4. $\sum a_n(x-2)^n$。
expected_answer: |
  1. 正项函数型级数，先检查积分判别或与已知尺度比较。2. 交错级数，分离幅度 $u_n=1/\sqrt n$，检查莱布尼茨并另判绝对收敛。3. 任意项级数，先看 $\sum\lvert u_n\rvert$，若不收敛再分析抵消结构。4. 幂级数，固定 $x$ 后变数项级数，求中心2、半径与端点。
solution_outline:
  1. 判断是否含变量以及是否固定 $x$。
  2. 判断项是否非负、规则交错或任意符号。
  3. 指出对应星系的第一步。
rubric:
  - criterion: 对象分类
    required_evidence: 四类对象均分类正确
  - criterion: 触发链
    required_evidence: 每类给出正确第一检查
  - criterion: 边界意识
    required_evidence: 没有把“路由”冒充最终结论
common_errors:
  - error: 看到 $x$ 就直接谈半径，未确认是否幂结构
    root_cause: trigger_failure
    repair_target_node_id: infinite_series.system_06_power_domain.pointwise_grounding
false_pass_risks:
  - 若只写“积分法、莱布尼茨、绝对值、比值法”四个方法名，不算通过。

#### TransferVariant
question_id: infinite_series.system_01_foundations.structure_classification.transfer_v01
variant_relation: 加入一个含 $x$ 但不是幂级数的对象，检验是否真正识别结构。
stem: |
  对 $\sum_{n=1}^{\infty}e^{-nx}$ 进行结构路由，并说明为什么不能直接称其为“以0为中心的幂级数”。
expected_answer: |
  固定 $x$ 后它是公比为 $e^{-x}$ 的正项等比级数；收敛条件为 $e^{-x}<1$，即 $x>0$。它不是 $\sum a_n(x-x_0)^n$ 的幂结构，因此有收敛域但不谈收敛半径。
mastery_evidence: 能区分“含变量的函数项级数”与“幂级数”。

### infinite_series.system_01_foundations.positive_tail_model
training_goal: 理解正项级数只能靠尾项下降速度收住。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第4页“正项级数：没有抵消”
entry_trigger: 确认 $a_n\ge0$ 后，需要决定比较模型时。
mastery_criteria: 能用部分和单调不降解释为何必须控制尾巴，并指出几何与 $p$ 级数标尺。
repair_target_node_id: infinite_series.system_01_foundations.positive_tail_model

#### CoreQuestion
question_id: infinite_series.system_01_foundations.positive_tail_model.core_q01
question_kind: concept_judgement
difficulty: basic
target_dimensions: concept,method,expression
stem: |
  解释为什么正项级数的核心是“下降速度”，并判断“只要 $a_n$ 很小，级数就收敛”是否是可评分的结论。
expected_answer: |
  正项级数的部分和单调不降，没有负项抵消；要收敛，尾项总量必须有限，因此要把尾巴压到已知收敛模型，如 $k^n$ 且 $0<k<1$ 或 $1/n^p$ 且 $p>1$。说“很小”没有比较对象、指数或统一界，不能作为判敛证据。
solution_outline:
  1. 由 $a_n\ge0$ 得到部分和单调不降。
  2. 说明收敛需要尾巴有上界。
  3. 给出可执行的比较模型。
rubric:
  - criterion: 机制
    required_evidence: 指出没有抵消
  - criterion: 模型
    required_evidence: 至少给出一个严格收敛标尺
  - criterion: 表达
    required_evidence: 拒绝“很小”这种不可评分语言
common_errors:
  - error: 把通项趋零等同于下降足够快
    root_cause: concept_gap
    repair_target_node_id: infinite_series.system_01_foundations.term_gate
false_pass_risks:
  - 只列“比值、根值、积分”但不解释共同控制对象，不能通过。

#### TransferVariant
question_id: infinite_series.system_01_foundations.positive_tail_model.transfer_v01
variant_relation: 把抽象解释迁移到临界比较。
stem: |
  比较 $a_n=1/n$ 与 $b_n=1/n^2$：二者都趋零，为什么一个发散一个收敛？
expected_answer: |
  二者都通过通项门槛，但尾巴下降尺度不同。$1/n$ 位于 $p=1$ 临界线并发散；$1/n^2$ 对应 $p=2>1$，尾巴总量有限而收敛。
mastery_evidence: 能从“趋零”升级到“下降速度尺度”。

### infinite_series.system_01_foundations.boundary_reasoning
training_goal: 在工具无结论时停止错误推出并切换模型。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第3页边界意识; 第11页反例库
entry_trigger: 判别法极限落在边界，或定理条件没有验证出来时。
mastery_criteria: 能写“该方法无结论”，给出相反敛散反例，并提出下一条可用路线。
repair_target_node_id: infinite_series.system_01_foundations.boundary_reasoning

#### CoreQuestion
question_id: infinite_series.system_01_foundations.boundary_reasoning.core_q01
question_kind: expression_standard
difficulty: standard
target_dimensions: expression,method,migration
stem: |
  某正项级数用比值法得到极限 $\rho=1$。学生写“所以发散”。请指出逻辑错误，并给出最小反例证明 $\rho=1$ 时不能判。
expected_answer: |
  错误在于把“比值判别法无结论”写成“级数发散”。$\sum1/n$ 与 $\sum1/n^2$ 的相邻项比值极限都为1，但前者发散、后者收敛。因此只能更换比较、积分或其他结构判别。
solution_outline:
  1. 写出比值法在 $\rho=1$ 的状态。
  2. 给出一个收敛和一个发散反例。
  3. 说明下一步应换工具而非判死。
rubric:
  - criterion: 逻辑边界
    required_evidence: 明确“无结论”
  - criterion: 双反例
    required_evidence: 两个结果相反且比值极限同为1
  - criterion: 迁移
    required_evidence: 提出合理替代路线
common_errors:
  - error: 把判别法失败当级数失败
    root_cause: method_error
    repair_target_node_id: infinite_series.system_01_foundations.boundary_reasoning
false_pass_risks:
  - 只给一个反例只能否定其中一个方向，不能证明两种结论都可能。

#### TransferVariant
question_id: infinite_series.system_01_foundations.boundary_reasoning.transfer_v01
variant_relation: 将同一边界意识迁移到莱布尼茨条件。
stem: |
  若无法证明 $u_n$ 单调不增，能否断言 $\sum(-1)^{n-1}u_n$ 发散？写出规范答复。
expected_answer: |
  不能。莱布尼茨是充分条件；单调性未验证只说明该方法不能直接用。应尝试证明后期单调、改用绝对收敛、分组或拆成主项与可控误差。
mastery_evidence: 能把“工具失败不等于对象失败”迁移到另一判别法。

### infinite_series.system_02_geometric_tests.ratio_trigger
training_goal: 根据阶乘、连乘或相邻项结构触发比值法。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第4-5页方法对照与比值法
entry_trigger: 通项含 $n!$、连乘、递推或相邻项可大量约去时。
mastery_criteria: 能说明为什么相邻比值比直接估计通项更简洁。
repair_target_node_id: infinite_series.system_02_geometric_tests.ratio_trigger

#### CoreQuestion
question_id: infinite_series.system_02_geometric_tests.ratio_trigger.core_q01
question_kind: trigger_identification
difficulty: standard
target_dimensions: trigger,method
stem: |
  从“方法选择”角度说明为什么级数 $\sum_{n=1}^{\infty} n!/n^n$ 更适合先尝试比值法，并计算相邻项比值的极限。
expected_answer: |
  令 $a_n=n!/n^n$。相邻比值能约掉阶乘：
  $\dfrac{a_{n+1}}{a_n}=\dfrac{(n+1)!}{(n+1)^{n+1}}\dfrac{n^n}{n!}=(n/(n+1))^n\to e^{-1}<1$。
  因此比值法收敛。
solution_outline:
  1. 识别阶乘与相邻项约分。
  2. 正确化简比值。
  3. 由极限小于1得出收敛。
rubric:
  - criterion: 触发依据
    required_evidence: 指出阶乘/相邻项约分
  - criterion: 计算
    required_evidence: 极限为 $e^{-1}$
  - criterion: 结论
    required_evidence: 说明正项级数收敛
common_errors:
  - error: 只写“像比值法”没有结构理由
    root_cause: trigger_failure
    repair_target_node_id: infinite_series.system_02_geometric_tests.ratio_trigger
false_pass_risks:
  - 猜出收敛但未写相邻比值，不算掌握触发能力。

#### TransferVariant
question_id: infinite_series.system_02_geometric_tests.ratio_trigger.transfer_v01
variant_relation: 将阶乘触发迁移到递推定义。
stem: |
  正项序列满足 $a_{n+1}=\dfrac{2n+1}{3n+4}a_n$ 且 $a_1>0$。判断 $\sum a_n$。
expected_answer: |
  相邻比值已由递推给出，极限为 $2/3<1$，故级数收敛。
mastery_evidence: 能从递推直接读取比值，而不是先硬求 $a_n$ 显式式。

### infinite_series.system_02_geometric_tests.ratio_method
training_goal: 完整执行比值判别并处理三种极限结果。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第5页“比值判别法”
entry_trigger: 已经选择比值法后。
mastery_criteria: 能写绝对值比值、极限、三分结论和必要的通项说明。
repair_target_node_id: infinite_series.system_02_geometric_tests.ratio_method

#### CoreQuestion
question_id: infinite_series.system_02_geometric_tests.ratio_method.core_q01
question_kind: calculation_execution
difficulty: standard
target_dimensions: method,calculation,final_answer
stem: |
  判断 $\sum_{n=1}^{\infty}\dfrac{3^n}{n!}$ 的敛散性，并写出比值法的完整判断链。
expected_answer: |
  设 $a_n=3^n/n!>0$。则 $a_{n+1}/a_n=3/(n+1)\to0<1$，故级数收敛。更具体地，后期可选固定 $k<1$ 使 $a_{n+1}\le ka_n$。
solution_outline:
  1. 定义正项通项。
  2. 计算相邻比值并求极限。
  3. 按 $\rho<1$ 得出收敛并可补固定 $k$。
rubric:
  - criterion: 计算式
    required_evidence: 比值为 $3/(n+1)$
  - criterion: 极限
    required_evidence: 极限0小于1
  - criterion: 结论
    required_evidence: 明确级数收敛
common_errors:
  - error: 把 $a_{n+1}/a_n<1$ 对每个早期项都当必要
    root_cause: condition_miss
    repair_target_node_id: infinite_series.system_02_geometric_tests.ratio_method
false_pass_risks:
  - 只写极限0而不写与1比较及结论，不算完整。

#### TransferVariant
question_id: infinite_series.system_02_geometric_tests.ratio_method.transfer_v01
variant_relation: 把结果改为通项不趋零的发散分支。
stem: |
  判断 $\sum_{n=1}^{\infty} n!/2^n$。
expected_answer: |
  $a_{n+1}/a_n=(n+1)/2\to\infty>1$，所以通项最终递增且不趋零，级数发散。
mastery_evidence: 能正确使用 $\rho>1$ 分支并关联通项门槛。

### infinite_series.system_02_geometric_tests.root_method
training_goal: 对整体 $n$ 次幂结构执行根值判别。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第6页“柯西根值法”
entry_trigger: 通项整体形如 $[r_n]^n$ 或含多个指数型因子时。
mastery_criteria: 能取 $n$ 次根还原底数，计算极限并压到等比级数。
repair_target_node_id: infinite_series.system_02_geometric_tests.root_method

#### CoreQuestion
question_id: infinite_series.system_02_geometric_tests.root_method.core_q01
question_kind: calculation_execution
difficulty: standard
target_dimensions: trigger,method,calculation
stem: |
  判断 $\sum_{n=1}^{\infty}\left(\dfrac{2n+1}{3n+2}\right)^n$。
expected_answer: |
  设 $a_n=((2n+1)/(3n+2))^n$。则 $\sqrt[n]{a_n}=(2n+1)/(3n+2)\to2/3<1$，故级数收敛。
solution_outline:
  1. 识别整体 $n$ 次幂。
  2. 取 $n$ 次根。
  3. 极限小于1并得收敛。
rubric:
  - criterion: 触发
    required_evidence: 选择根值而非冗长比值
  - criterion: 计算
    required_evidence: 根值极限 $2/3$
  - criterion: 结论
    required_evidence: 收敛
common_errors:
  - error: 忘记通项需非负或对绝对值取根
    root_cause: condition_miss
    repair_target_node_id: infinite_series.system_02_geometric_tests.root_method
false_pass_risks:
  - 直接看括号小于1但不证明统一远离1，可能造成伪通过。

#### TransferVariant
question_id: infinite_series.system_02_geometric_tests.root_method.transfer_v01
variant_relation: 把纯幂结构换成混合因子，检验是否会抓主指数。
stem: |
  判断 $\sum_{n=1}^{\infty} n^5(3/4)^n$，要求用根值思路。
expected_answer: |
  $\sqrt[n]{n^5(3/4)^n}=n^{5/n}(3/4)\to3/4<1$，故收敛。多项式因子不改变指数尺度。
mastery_evidence: 能识别 $n^{5/n}\to1$，不被多项式因子干扰。

### infinite_series.system_02_geometric_tests.geometric_proof_boundary
training_goal: 从极限构造固定 $k<1$ 并识别边界。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第5-6页证明桥与边界反例
entry_trigger: 需要解释判别法为什么成立或处理 $\rho=1$ 时。
mastery_criteria: 能写出极限定义到几何尾巴的控制链。
repair_target_node_id: infinite_series.system_02_geometric_tests.geometric_proof_boundary

#### CoreQuestion
question_id: infinite_series.system_02_geometric_tests.geometric_proof_boundary.core_q01
question_kind: expression_standard
difficulty: advanced
target_dimensions: concept,process,expression
stem: |
  设正项级数满足 $\lim a_{n+1}/a_n=\rho<1$。说明为何可以得到一个固定的收敛等比尾巴，而不是只说“比值小于1”。
expected_answer: |
  选择常数 $k$ 使 $\rho<k<1$。由极限定义，存在 $N$，当 $n\ge N$ 时 $a_{n+1}/a_n\le k$。迭代得 $a_{N+m}\le a_Nk^m$，故尾巴被 $a_N\sum_{m=0}^{\infty}k^m$ 控制而收敛。
solution_outline:
  1. 选取 $\rho<k<1$。
  2. 用极限得到统一的后期不等式。
  3. 迭代并比较等比尾巴。
rubric:
  - criterion: 固定常数
    required_evidence: $k$ 与 $n$ 无关
  - criterion: 尾巴控制
    required_evidence: 写出 $a_{N+m}\le a_Nk^m$
  - criterion: 结论
    required_evidence: 比较等比级数
common_errors:
  - error: 每个 $n$ 选择不同 $k_n$，无法统一控制
    root_cause: process_gap
    repair_target_node_id: infinite_series.system_02_geometric_tests.geometric_proof_boundary
false_pass_risks:
  - 只写“极限小于1所以收敛”没有证明桥，不算通过。

#### TransferVariant
question_id: infinite_series.system_02_geometric_tests.geometric_proof_boundary.transfer_v01
variant_relation: 迁移到根值法的固定界。
stem: |
  若 $\lim\sqrt[n]{a_n}=\rho<1$，写出与上题平行的控制链。
expected_answer: |
  选 $\rho<k<1$。后期 $\sqrt[n]{a_n}\le k$，所以 $a_n\le k^n$，由与收敛等比级数比较得原级数收敛。
mastery_evidence: 能看出比值与根值共享“固定等比尾巴”本质。

### infinite_series.system_03_integral_test.condition_check
training_goal: 在积分前验证正、连续、后期递减。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第7页积分判别条件
entry_trigger: 正项通项可写成 $f(n)$ 且准备使用积分判别时。
mastery_criteria: 能列全条件，并允许只要求后期成立。
repair_target_node_id: infinite_series.system_03_integral_test.condition_check

#### CoreQuestion
question_id: infinite_series.system_03_integral_test.condition_check.core_q01
question_kind: condition_transformation
difficulty: basic
target_dimensions: trigger,concept,expression
stem: |
  准备对 $\sum_{n=2}^{\infty}1/(n\ln n)$ 使用积分判别。请逐项验证使用条件。
expected_answer: |
  取 $f(x)=1/(x\ln x)$。在 $x\ge2$ 上，$f(x)>0$、连续；分母 $x\ln x$ 严格增大，所以 $f$ 单调递减。因此可用积分判别。
solution_outline:
  1. 定义连续函数 $f$。
  2. 验证正与连续。
  3. 验证后期递减。
rubric:
  - criterion: 函数对应
    required_evidence: $f(n)$ 等于通项
  - criterion: 三条件
    required_evidence: 正、连续、递减齐全
  - criterion: 尾部范围
    required_evidence: 说明从2起即可
common_errors:
  - error: 只因“有积分”就使用
    root_cause: condition_miss
    repair_target_node_id: infinite_series.system_03_integral_test.condition_check
false_pass_risks:
  - 直接计算积分但不验证递减，可能在不适用对象上蒙对。

#### TransferVariant
question_id: infinite_series.system_03_integral_test.condition_check.transfer_v01
variant_relation: 将递减性改为只在后期成立。
stem: |
  若 $f$ 在 $[1,10]$ 上有波动，但在 $[10,\infty)$ 上正、连续、递减，积分判别能否判断 $\sum f(n)$？
expected_answer: |
  能。敛散性由尾巴决定；从 $n=10$ 起使用积分判别，前面有限项只改变和的数值。
mastery_evidence: 能把条件理解为尾部条件而非全程苛刻条件。

### infinite_series.system_03_integral_test.continuous_tail
training_goal: 解释有限项不影响敛散及面积比较。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第7页“比较尾巴，不是前面有限项”
entry_trigger: 函数前段异常或需要改变起始下标时。
mastery_criteria: 能从部分和差一个常数解释有限项不改敛散，并描述矩形与曲线面积控制。
repair_target_node_id: infinite_series.system_03_integral_test.continuous_tail

#### CoreQuestion
question_id: infinite_series.system_03_integral_test.continuous_tail.core_q01
question_kind: concept_judgement
difficulty: standard
target_dimensions: concept,process,expression
stem: |
  为什么 $\sum_{n=1}^{\infty}f(n)$ 与 $\sum_{n=100}^{\infty}f(n)$ 敛散性相同？这与积分判别“只看尾巴”有什么关系？
expected_answer: |
  两者部分和只相差前99项的有限常数。一个尾巴若有有限极限，加减固定常数仍有有限极限；若尾巴无界或不收敛，有限常数也无法修复。因此积分判别只需在后期条件成立。
solution_outline:
  1. 写出两个级数相差有限和。
  2. 说明有限常数不改变极限存在性。
  3. 联系到后期条件。
rubric:
  - criterion: 代数关系
    required_evidence: 指出差为有限常数
  - criterion: 极限逻辑
    required_evidence: 说明收敛性不变
  - criterion: 方法迁移
    required_evidence: 后期可用积分法
common_errors:
  - error: 认为前几项大就必发散
    root_cause: concept_gap
    repair_target_node_id: infinite_series.system_03_integral_test.continuous_tail
false_pass_risks:
  - 只说“定理规定”而不解释部分和差值，不算掌握。

#### TransferVariant
question_id: infinite_series.system_03_integral_test.continuous_tail.transfer_v01
variant_relation: 迁移到修改单个项。
stem: |
  把一个收敛级数的第100项改成 $10^{100}$，敛散性是否改变？
expected_answer: |
  不改变。部分和从第100项以后整体只平移一个固定差值，仍收敛；和的数值改变。
mastery_evidence: 能区分“敛散性”与“和的具体数值”。

### infinite_series.system_03_integral_test.p_series_scale
training_goal: 用 $p$ 级数临界线建立比较尺度。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第7页$p$级数表
entry_trigger: 正项尾项近似幂次时。
mastery_criteria: 能准确使用 $p>1$ 与 $p\le1$，并说明 $p=1$ 是临界。
repair_target_node_id: infinite_series.system_03_integral_test.p_series_scale

#### CoreQuestion
question_id: infinite_series.system_03_integral_test.p_series_scale.core_q01
question_kind: method_selection
difficulty: basic
target_dimensions: method,concept,final_answer
stem: |
  判断 $\sum 1/n^{3/2}$ 与 $\sum1/\sqrt n$，并说明不能只说“二者都趋零”。
expected_answer: |
  第一项是 $p=3/2>1$ 的 $p$ 级数，收敛；第二项是 $p=1/2\le1$，发散。通项趋零只是必要门槛，真正差异是下降指数跨过了 $p=1$ 临界线。
solution_outline:
  1. 识别两个 $p$ 值。
  2. 调用临界结论。
  3. 联系通项门槛。
rubric:
  - criterion: 参数
    required_evidence: $3/2$ 与 $1/2$ 识别正确
  - criterion: 敛散
    required_evidence: 一收一发
  - criterion: 解释
    required_evidence: 指出临界线而非仅趋零
common_errors:
  - error: 把指数越大误判为项越大
    root_cause: knowledge_confusion
    repair_target_node_id: infinite_series.system_03_integral_test.p_series_scale
false_pass_risks:
  - 只写结果而没有 $p$ 值与临界比较，不算通过。

#### TransferVariant
question_id: infinite_series.system_03_integral_test.p_series_scale.transfer_v01
variant_relation: 把显式幂次改为极限比较。
stem: |
  判断 $\sum (2n+1)/(n^3+1)$。
expected_answer: |
  通项与 $1/n^2$ 极限比较：$[(2n+1)/(n^3+1)]/(1/n^2)\to2$，故与 $p=2$ 级数同敛，收敛。
mastery_evidence: 能把复杂有理式还原到 $p$ 级数主尺度。

### infinite_series.system_03_integral_test.logarithmic_execution
training_goal: 用换元完成对数型积分判别。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第4页“对数型适合积分”; 第7页积分主线
entry_trigger: 通项含 $n\ln n$ 或 $n(\ln n)^p$。
mastery_criteria: 能令 $t=\ln x$，计算反常积分并写出端点。
repair_target_node_id: infinite_series.system_03_integral_test.logarithmic_execution

#### CoreQuestion
question_id: infinite_series.system_03_integral_test.logarithmic_execution.core_q01
question_kind: calculation_execution
difficulty: standard
target_dimensions: trigger,transformation,calculation
stem: |
  判断 $\sum_{n=2}^{\infty}\dfrac{1}{n(\ln n)^2}$。
expected_answer: |
  取 $f(x)=1/[x(\ln x)^2]$，满足积分判别条件。令 $t=\ln x$，$dt=dx/x$：
  $\int_2^{\infty}dx/[x(\ln x)^2]=\int_{\ln2}^{\infty}t^{-2}dt=1/\ln2<\infty$。
  故级数收敛。
solution_outline:
  1. 验证条件。
  2. 作 $t=\ln x$ 换元。
  3. 反常积分有限并得结论。
rubric:
  - criterion: 换元
    required_evidence: $dt=dx/x$
  - criterion: 积分
    required_evidence: $t^{-2}$ 在无穷处可积
  - criterion: 结论
    required_evidence: 级数收敛
common_errors:
  - error: 把 $\ln x$ 当常数
    root_cause: calculation_error
    repair_target_node_id: infinite_series.system_03_integral_test.logarithmic_execution
false_pass_risks:
  - 只引用“对数型”而不算积分，无法证明掌握。

#### TransferVariant
question_id: infinite_series.system_03_integral_test.logarithmic_execution.transfer_v01
variant_relation: 改变对数幂次跨越临界。
stem: |
  判断 $\sum_{n=2}^{\infty}1/(n\ln n)$。
expected_answer: |
  换元后反常积分为 $\int_{\ln2}^{\infty}dt/t=\infty$，故级数发散。
mastery_evidence: 能识别对数层面的新临界 $p=1$。

### infinite_series.system_04_alternating_series.sign_magnitude_split
training_goal: 把交错符号和正幅度分开。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第8页交错级数定义
entry_trigger: 通项含 $(-1)^n$ 或 $(-1)^{n-1}$ 时。
mastery_criteria: 能明确莱布尼茨检查 $u_n>0$，而非整个带符号项。
repair_target_node_id: infinite_series.system_04_alternating_series.sign_magnitude_split

#### CoreQuestion
question_id: infinite_series.system_04_alternating_series.sign_magnitude_split.core_q01
question_kind: concept_judgement
difficulty: basic
target_dimensions: concept,trigger
stem: |
  对级数 $\sum(-1)^{n-1}(n+1)/n^2$，指出符号因子与幅度 $u_n$，并说明莱布尼茨要检查谁。
expected_answer: |
  符号因子是 $(-1)^{n-1}$，幅度是 $u_n=(n+1)/n^2>0$。莱布尼茨检查 $u_n$ 是否后期单调不增以及 $u_n\to0$，不检查带符号通项的单调性。
solution_outline:
  1. 分离符号。
  2. 写出正幅度。
  3. 指出两个检查条件。
rubric:
  - criterion: 对象
    required_evidence: $u_n$ 识别正确
  - criterion: 条件
    required_evidence: 单调不增且趋零
  - criterion: 排错
    required_evidence: 不对整个通项谈单调
common_errors:
  - error: 把 $(-1)^{n-1}u_n$ 当作需单调的对象
    root_cause: knowledge_confusion
    repair_target_node_id: infinite_series.system_04_alternating_series.sign_magnitude_split
false_pass_risks:
  - 只看见“交错”但未写出 $u_n$，不能进入后续判别。

#### TransferVariant
question_id: infinite_series.system_04_alternating_series.sign_magnitude_split.transfer_v01
variant_relation: 把交错符号藏在三角函数中。
stem: |
  说明 $\sum \cos(n\pi)/n$ 如何改写成标准交错形式。
expected_answer: |
  因 $\cos(n\pi)=(-1)^n$，级数为 $\sum(-1)^n/n$，幅度 $u_n=1/n$。
mastery_evidence: 能识别等价符号表示而非只认显式 $(-1)^n$。

### infinite_series.system_04_alternating_series.leibniz_trigger
training_goal: 验证后期单调和趋零。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第8页莱布尼茨条件
entry_trigger: 已分离出 $u_n>0$ 后。
mastery_criteria: 能用代数、导数或比较验证条件并给出收敛结论。
repair_target_node_id: infinite_series.system_04_alternating_series.leibniz_trigger

#### CoreQuestion
question_id: infinite_series.system_04_alternating_series.leibniz_trigger.core_q01
question_kind: calculation_execution
difficulty: standard
target_dimensions: trigger,calculation,final_answer
stem: |
  判断 $\sum_{n=1}^{\infty}(-1)^{n-1}/\sqrt n$。
expected_answer: |
  取 $u_n=1/\sqrt n>0$。它单调递减且 $u_n\to0$，故由莱布尼茨判别级数收敛。其绝对值级数 $\sum1/\sqrt n$ 发散，所以进一步可判为条件收敛。
solution_outline:
  1. 验证正性。
  2. 验证单调递减。
  3. 验证极限0并得收敛。
  4. 可补绝对收敛分类。
rubric:
  - criterion: 两条件
    required_evidence: 单调与趋零均出现
  - criterion: 结论
    required_evidence: 莱布尼茨收敛
  - criterion: 分类
    required_evidence: 若写条件收敛需验证绝对值发散
common_errors:
  - error: 只因交错就判收敛
    root_cause: condition_miss
    repair_target_node_id: infinite_series.system_04_alternating_series.leibniz_trigger
false_pass_risks:
  - 只给“条件收敛”最终标签而不验两个条件，不算通过。

#### TransferVariant
question_id: infinite_series.system_04_alternating_series.leibniz_trigger.transfer_v01
variant_relation: 让通项门槛直接失败。
stem: |
  判断 $\sum(-1)^n n/(n+1)$。
expected_answer: |
  幅度 $u_n=n/(n+1)\to1\ne0$，通项不趋零，级数发散；无需检查单调性。
mastery_evidence: 能优先使用必要门槛而不是机械完成全部条件。

### infinite_series.system_04_alternating_series.partial_sum_proof
training_goal: 用奇偶部分和解释莱布尼茨收敛。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第8页“偶数部分和与奇数部分和”
entry_trigger: 要求说明定理机制或证明时。
mastery_criteria: 能写两列单调有界及距离 $u_{2n+1}$ 或相邻项趋零。
repair_target_node_id: infinite_series.system_04_alternating_series.partial_sum_proof

#### CoreQuestion
question_id: infinite_series.system_04_alternating_series.partial_sum_proof.core_q01
question_kind: expression_standard
difficulty: advanced
target_dimensions: concept,process,expression
stem: |
  设 $u_n$ 单调不增且趋于0。用部分和说明 $\sum(-1)^{n-1}u_n$ 为什么收敛。
expected_answer: |
  偶数部分和 $S_{2m}=(u_1-u_2)+\cdots+(u_{2m-1}-u_{2m})$ 单调递增，并且 $S_{2m}\le u_1$，故收敛。奇数部分和 $S_{2m+1}=S_{2m}+u_{2m+1}$，而 $u_{2m+1}\to0$，所以奇偶两列趋于同一极限，整个部分和序列收敛。
solution_outline:
  1. 成对写偶数部分和。
  2. 证明单调与有界。
  3. 用相邻奇偶差趋零合并极限。
rubric:
  - criterion: 偶列
    required_evidence: 单调递增且有上界
  - criterion: 差距
    required_evidence: $S_{2m+1}-S_{2m}=u_{2m+1}\to0$
  - criterion: 整体
    required_evidence: 两子列同极限
common_errors:
  - error: 只说正负抵消，没有部分和证据
    root_cause: process_gap
    repair_target_node_id: infinite_series.system_04_alternating_series.partial_sum_proof
false_pass_risks:
  - 背诵“摆动越来越小”但不能落到两列部分和，不算证明能力。

#### TransferVariant
question_id: infinite_series.system_04_alternating_series.partial_sum_proof.transfer_v01
variant_relation: 要求解释单调条件的作用而非重复证明。
stem: |
  若 $u_n\to0$ 但忽大忽小，为什么上面的证明链可能断？
expected_answer: |
  成对差 $u_{2k-1}-u_{2k}$ 可能不再非负，偶数部分和不保证单调；奇偶两列也不一定从两侧稳定夹逼。趋零仍是必要的，但该证明与莱布尼茨条件不再可直接使用。
mastery_evidence: 能定位单调条件具体控制的证明环节。

### infinite_series.system_04_alternating_series.failure_repair
training_goal: 在单调性不明显时改造通项。
source_evidence: 材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第9-10页“方法失败与主项+误差项”
entry_trigger: 莱布尼茨条件难验证或通项含有界扰动时。
mastery_criteria: 能选择后期导数、主项加误差、绝对收敛或分组，而不直接判发散。
repair_target_node_id: infinite_series.system_04_alternating_series.failure_repair

#### CoreQuestion
question_id: infinite_series.system_04_alternating_series.failure_repair.core_q01
question_kind: condition_transformation
difficulty: advanced
target_dimensions: transformation,method,migration
stem: |
  判断 $\sum_{n=2}^{\infty}(-1)^{n-1}/(n+\sin n)$ 的敛散性。要求不把“单调性不明显”当作发散。
expected_answer: |
  利用
  $1/(n+\sin n)=1/n-\sin n/[n(n+\sin n)]$。
  原级数等于交错调和级数减去误差级数。第一部分收敛；对 $n\ge2$，误差绝对值不超过 $1/[n(n-1)]$，故绝对收敛。因此原级数收敛。其绝对值级数与 $\sum1/n$ 极限比较同敛而发散，所以原级数条件收敛。
solution_outline:
  1. 选择主项 $1/n$。
  2. 代数拆项正确。
  3. 误差绝对收敛。
  4. 绝对值级数发散并分类。
rubric:
  - criterion: 拆项
    required_evidence: 分母未乱拆且恒等式正确
  - criterion: 误差控制
    required_evidence: 给出 $O(1/n^2)$ 或明确比较
  - criterion: 分类
    required_evidence: 条件收敛
common_errors:
  - error: 把 $1/(n+\sin n)$ 错拆成 $1/n+1/\sin n$
    root_cause: transformation_error
    repair_target_node_id: infinite_series.system_04_alternating_series.failure_repair
false_pass_risks:
  - 只凭“像交错调和”猜收敛，没有控制扰动，不能通过。

#### TransferVariant
question_id: infinite_series.system_04_alternating_series.failure_repair.transfer_v01
variant_relation: 将有界扰动改为根号扰动，检验有理化策略。
stem: |
  面对含 $1/(\sqrt n+(-1)^n)$ 的级数，说明第一步应如何把分母改造成可比较尺度。
expected_answer: |
  应乘共轭有理化：$1/(\sqrt n+(-1)^n)=(\sqrt n-(-1)^n)/(n-1)$，再按 $1/\sqrt n$ 主尺度与更小误差分析；不能拆分母倒数。
mastery_evidence: 能迁移“合法改造而非乱拆分母”的原则。

### infinite_series.system_05_arbitrary_terms.absolute_entry
training_goal: 证明绝对收敛推出原级数收敛。
source_evidence: 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第3-4页“造非负通项并代数回收”
entry_trigger: 任意项级数准备通过绝对值回到正项世界时。
mastery_criteria: 能构造 $\lvert u_n\rvert+u_n$ 并用比较法完成证明。
repair_target_node_id: infinite_series.system_05_arbitrary_terms.absolute_entry

#### CoreQuestion
question_id: infinite_series.system_05_arbitrary_terms.absolute_entry.core_q01
question_kind: expression_standard
difficulty: advanced
target_dimensions: concept,process,expression
stem: |
  证明：若 $\sum\lvert u_n\rvert$ 收敛，则 $\sum u_n$ 收敛。不得只写 $u_n\le\lvert u_n\rvert$。
expected_answer: |
  有 $0\le\lvert u_n\rvert+u_n\le2\lvert u_n\rvert$。由比较判别法，$\sum(\lvert u_n\rvert+u_n)$ 收敛。又
  $u_n=(\lvert u_n\rvert+u_n)-\lvert u_n\rvert$，所以 $\sum u_n$ 是两个收敛级数之差，故收敛。
solution_outline:
  1. 构造非负对象。
  2. 用比较法证明其级数收敛。
  3. 代数回收 $u_n$。
rubric:
  - criterion: 非负比较
    required_evidence: 写出双边不等式
  - criterion: 线性回收
    required_evidence: 写出差式
  - criterion: 结论
    required_evidence: 原级数收敛
common_errors:
  - error: 直接用 $u_n\le\lvert u_n\rvert$ 套正项比较
    root_cause: method_error
    repair_target_node_id: infinite_series.system_05_arbitrary_terms.absolute_entry
false_pass_risks:
  - 结论正确但比较对象可能为负，证明不合法。

#### TransferVariant
question_id: infinite_series.system_05_arbitrary_terms.absolute_entry.transfer_v01
variant_relation: 迁移到正部和负部构造。
stem: |
  用 $p_n=(\lvert u_n\rvert+u_n)/2$、$q_n=(\lvert u_n\rvert-u_n)/2$ 给出另一种证明思路。
expected_answer: |
  $0\le p_n,q_n\le\lvert u_n\rvert$，故两级数均收敛；又 $u_n=p_n-q_n$，所以原级数收敛。
mastery_evidence: 能用账本模型复现同一定理而非背单一路径。

### infinite_series.system_05_arbitrary_terms.ledger_model
training_goal: 理解正负账本及条件收敛根因。
source_evidence: 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第4-5页“正负账本模型”
entry_trigger: 需要解释绝对/条件收敛的底层结构时。
mastery_criteria: 能说明原级数是差、绝对值级数是和，并证明条件收敛时两本账都发散。
repair_target_node_id: infinite_series.system_05_arbitrary_terms.ledger_model

#### CoreQuestion
question_id: infinite_series.system_05_arbitrary_terms.ledger_model.core_q01
question_kind: concept_judgement
difficulty: advanced
target_dimensions: concept,process,expression
stem: |
  设 $p_n=(\lvert u_n\rvert+u_n)/2$、$q_n=(\lvert u_n\rvert-u_n)/2$。写出它们的含义，并证明若 $\sum u_n$ 条件收敛，则 $\sum p_n$ 与 $\sum q_n$ 都发散。
expected_answer: |
  $p_n$ 记录正项，$q_n$ 记录负项的绝对大小；$u_n=p_n-q_n$，$\lvert u_n\rvert=p_n+q_n$。若假设 $\sum p_n$ 收敛，由 $q_n=p_n-u_n$ 且 $\sum u_n$ 收敛可得 $\sum q_n$ 也收敛，进而 $\sum\lvert u_n\rvert$ 收敛，与条件收敛矛盾。因此两者都发散。
solution_outline:
  1. 解释两个账本。
  2. 写出差与和。
  3. 用反证排除一边收敛。
rubric:
  - criterion: 定义
    required_evidence: $p_n,q_n\ge0$ 且含义正确
  - criterion: 恒等式
    required_evidence: 差与和正确
  - criterion: 反证
    required_evidence: 推出绝对值级数收敛的矛盾
common_errors:
  - error: 把 $q_n$ 理解为负数本身
    root_cause: knowledge_confusion
    repair_target_node_id: infinite_series.system_05_arbitrary_terms.ledger_model
false_pass_risks:
  - 只背两个公式但不能解释条件收敛“两边无限、差值稳定”，不算通过。

#### TransferVariant
question_id: infinite_series.system_05_arbitrary_terms.ledger_model.transfer_v01
variant_relation: 用具体交错调和级数解释账本。
stem: |
  对 $u_n=(-1)^{n-1}/n$，说明正账本和负账本分别是什么量级。
expected_answer: |
  正账本收集奇数倒数，负账本收集偶数倒数的绝对值；两者都像调和级数的一半而发散，但交错差值收敛。
mastery_evidence: 能把抽象账本映射到具体项。

### infinite_series.system_05_arbitrary_terms.convergence_classification
training_goal: 完成绝对、条件或发散的三分分类。
source_evidence: 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第3-5页主线与两种收敛
entry_trigger: 任意项或交错级数需要最终分类时。
mastery_criteria: 能先判原级数，再判绝对值级数，且不从绝对值发散直接推原级数发散。
repair_target_node_id: infinite_series.system_05_arbitrary_terms.convergence_classification

#### CoreQuestion
question_id: infinite_series.system_05_arbitrary_terms.convergence_classification.core_q01
question_kind: method_selection
difficulty: standard
target_dimensions: trigger,method,final_answer
stem: |
  分类 $\sum_{n=1}^{\infty}(-1)^{n-1}/n^2$ 与 $\sum_{n=1}^{\infty}(-1)^{n-1}/n$。
expected_answer: |
  第一项的绝对值级数 $\sum1/n^2$ 收敛，所以绝对收敛。第二项由莱布尼茨收敛，但绝对值级数 $\sum1/n$ 发散，所以条件收敛。
solution_outline:
  1. 分别判断原级数与绝对值级数。
  2. 对两个对象给出不同分类。
rubric:
  - criterion: 第一项
    required_evidence: 绝对收敛
  - criterion: 第二项
    required_evidence: 条件收敛
  - criterion: 证据
    required_evidence: 说明所用 $p$ 级数或莱布尼茨
common_errors:
  - error: 认为所有交错级数都是条件收敛
    root_cause: knowledge_confusion
    repair_target_node_id: infinite_series.system_05_arbitrary_terms.convergence_classification
false_pass_risks:
  - 只写“都收敛”掩盖了抗扰动强度差异，不算掌握分类。

#### TransferVariant
question_id: infinite_series.system_05_arbitrary_terms.convergence_classification.transfer_v01
variant_relation: 加入原级数自身发散的第三类。
stem: |
  分类 $\sum(-1)^n$。
expected_answer: |
  通项不趋零，原级数发散；无需讨论绝对或条件收敛。
mastery_evidence: 能把三分分类与通项门槛连起来。

### infinite_series.system_05_arbitrary_terms.structure_decomposition
training_goal: 把目标拆成题设已知的收敛结构。
source_evidence: 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第6-7页例16.17、16.18、16.19
entry_trigger: 目标通项由奇偶子列、有界因子或两个已知量乘积组成时。
mastery_criteria: 能找到主结构、写合法恒等变形并给出比较。
repair_target_node_id: infinite_series.system_05_arbitrary_terms.structure_decomposition

#### CoreQuestion
question_id: infinite_series.system_05_arbitrary_terms.structure_decomposition.core_q01
question_kind: condition_transformation
difficulty: advanced
target_dimensions: transformation,method,calculation
stem: |
  已知 $\sum n u_n$ 绝对收敛，$\sum v_n/n$ 收敛。证明 $\sum u_nv_n$ 绝对收敛。
expected_answer: |
  因 $\sum v_n/n$ 收敛，故 $v_n/n\to0$，于是后期 $\lvert v_n/n\rvert\le1$。写
  $u_nv_n=(nu_n)(v_n/n)$，则后期 $\lvert u_nv_n\rvert\le\lvert nu_n\rvert$。由比较法，$\sum\lvert u_nv_n\rvert$ 收敛。
solution_outline:
  1. 按题设结构拆乘积。
  2. 由级数收敛推出通项趋零并有界。
  3. 绝对值比较。
rubric:
  - criterion: 拆法
    required_evidence: $(nu_n)(v_n/n)$
  - criterion: 有界性
    required_evidence: 后期绝对值不超过1
  - criterion: 结论
    required_evidence: 绝对收敛
common_errors:
  - error: 把“条件收敛”误用成绝对值级数收敛
    root_cause: method_error
    repair_target_node_id: infinite_series.system_05_arbitrary_terms.structure_decomposition
false_pass_risks:
  - 直接说两个收敛级数逐项乘积必收敛，没有定理依据。

#### TransferVariant
question_id: infinite_series.system_05_arbitrary_terms.structure_decomposition.transfer_v01
variant_relation: 迁移到有界振荡乘可求和主项。
stem: |
  证明 $\sum(1/\sqrt n-1/\sqrt{n+1})\sin(n+k)$ 绝对收敛。
expected_answer: |
  利用 $\lvert\sin(n+k)\rvert\le1$，绝对值不超过 $1/\sqrt n-1/\sqrt{n+1}$；右侧为望远镜级数并收敛，故原级数绝对收敛。
mastery_evidence: 能识别有界因子不是主角并压到望远镜主项。

### infinite_series.system_05_arbitrary_terms.operation_guard
training_goal: 判断操作是否保留原抵消结构。
source_evidence: 材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第7-9页“必然与不必然、反例库”
entry_trigger: 选择题给出由已知收敛级数变形得到的新级数时。
mastery_criteria: 能区分线性/分组/尾项平移与取绝对值、平方、改符号，并用反例。
repair_target_node_id: infinite_series.system_05_arbitrary_terms.operation_guard

#### CoreQuestion
question_id: infinite_series.system_05_arbitrary_terms.operation_guard.core_q01
question_kind: confusion_compare
difficulty: advanced
target_dimensions: trigger,concept,migration
stem: |
  已知 $\sum u_n$ 收敛。判断下列结论是否必然成立：
  A. $\sum(u_{2n-1}+u_{2n})$；
  B. $\sum(u_{2n-1}-u_{2n})$；
  C. $\sum(u_n+u_{n+1})$；
  D. $\sum\lvert u_n\rvert$。
expected_answer: |
  A必然：只是相邻分组，不改项序与符号。B不必然：可能翻转偶数项符号，例如交错调和变成正项调和型。C必然：等于原级数与尾项平移之和。D不必然：条件收敛级数给出反例。
solution_outline:
  1. 逐项判断是否改变抵消。
  2. 对不必然项给出反例机制。
  3. 对必然项给出部分和或线性关系。
rubric:
  - criterion: A
    required_evidence: 必然并说明分组
  - criterion: B
    required_evidence: 不必然并说明翻符号
  - criterion: C
    required_evidence: 必然并说明尾项平移
  - criterion: D
    required_evidence: 不必然并举条件收敛
common_errors:
  - error: 凭“项变小”判断所有操作安全
    root_cause: migration_failure
    repair_target_node_id: infinite_series.system_05_arbitrary_terms.operation_guard
false_pass_risks:
  - 只猜四个真假而无结构理由，不能证明会迁移。

#### TransferVariant
question_id: infinite_series.system_05_arbitrary_terms.operation_guard.transfer_v01
variant_relation: 加入平方操作检验反例构造。
stem: |
  已知 $\sum u_n$ 收敛，$\sum u_n^2$ 是否必然收敛？
expected_answer: |
  不必然。取 $u_n=(-1)^{n-1}/\sqrt n$，原级数由莱布尼茨收敛，但 $u_n^2=1/n$，平方级数发散。
mastery_evidence: 能主动构造“消符号后暴露调和尺度”的反例。

### infinite_series.system_06_power_domain.pointwise_grounding
training_goal: 把函数项级数固定为数项级数再判。
source_evidence: 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第2-3页“固定x，函数项级数才落地”
entry_trigger: 面对 $\sum u_n(x)$ 或含参数的无穷级数时。
mastery_criteria: 能区分第n项、整个级数、收敛点与收敛域。
repair_target_node_id: infinite_series.system_06_power_domain.pointwise_grounding

#### CoreQuestion
question_id: infinite_series.system_06_power_domain.pointwise_grounding.core_q01
question_kind: concept_judgement
difficulty: basic
target_dimensions: concept,trigger,expression
stem: |
  解释 $u_n(x)$、$\sum u_n(x)$、收敛点和收敛域的区别，并说明为什么要先固定 $x=x_0$。
expected_answer: |
  $u_n(x)$ 只是第 $n$ 项函数；$\sum u_n(x)$ 是函数项级数。若固定 $x=x_0$ 后数项级数 $\sum u_n(x_0)$ 收敛，则 $x_0$ 是收敛点；所有收敛点组成收敛域。固定 $x$ 后才能调用数项级数判别法。
solution_outline:
  1. 区分单项与无穷和。
  2. 定义收敛点。
  3. 定义收敛域并说明逐点化。
rubric:
  - criterion: 对象
    required_evidence: 四个概念不混淆
  - criterion: 落地
    required_evidence: 明确代入后是数项级数
  - criterion: 表达
    required_evidence: 不把 $u_n(x)$ 写成级数
common_errors:
  - error: 把第n项当整个函数项级数
    root_cause: concept_gap
    repair_target_node_id: infinite_series.system_06_power_domain.pointwise_grounding
false_pass_risks:
  - 只说“找定义域”但不解释逐点数项化，不算通过。

#### TransferVariant
question_id: infinite_series.system_06_power_domain.pointwise_grounding.transfer_v01
variant_relation: 用具体函数项级数求一个点。
stem: |
  对 $\sum_{n=1}^{\infty}x^n/n$，判断 $x=1/2$ 是否为收敛点。
expected_answer: |
  代入后为 $\sum(1/2)^n/n$，可与收敛几何级数 $\sum(1/2)^n$ 比较，故收敛；$1/2$ 是收敛点。
mastery_evidence: 能把抽象定义落到一次具体代入。

### infinite_series.system_06_power_domain.center_radius
training_goal: 理解幂级数的中心距离结构与阿贝尔分区。
source_evidence: 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第4-5页“中心+半径、阿贝尔”
entry_trigger: 确认对象是 $\sum a_n(x-x_0)^n$ 后。
mastery_criteria: 能解释半径是距离，内部绝对收敛、外部发散、端点另判。
repair_target_node_id: infinite_series.system_06_power_domain.center_radius

#### CoreQuestion
question_id: infinite_series.system_06_power_domain.center_radius.core_q01
question_kind: concept_judgement
difficulty: standard
target_dimensions: concept,expression
stem: |
  对幂级数 $\sum a_n(x-3)^n$，说明“中心3、收敛半径R”各是什么意思，并写出内部、外部和端点三类。
expected_answer: |
  中心是 $x_0=3$，半径 $R$ 是允许 $x$ 离中心的距离阈值。$\lvert x-3\rvert<R$ 时绝对收敛；$\lvert x-3\rvert>R$ 时发散；$x=3\pm R$ 必须分别代回原级数判断。
solution_outline:
  1. 识别中心。
  2. 把半径表述为距离。
  3. 写出三类区域。
rubric:
  - criterion: 中心
    required_evidence: 3
  - criterion: 主体
    required_evidence: 内绝对收敛外发散
  - criterion: 端点
    required_evidence: 两个点另判
common_errors:
  - error: 把R当某个x值
    root_cause: knowledge_confusion
    repair_target_node_id: infinite_series.system_06_power_domain.center_radius
false_pass_risks:
  - 只写区间 $(3-R,3+R)$ 而不说明端点状态，不算完整。

#### TransferVariant
question_id: infinite_series.system_06_power_domain.center_radius.transfer_v01
variant_relation: 迁移到中心平移。
stem: |
  若 $\sum a_nx^n$ 半径为2，则 $\sum a_n(x+5)^n$ 的中心和内部区间是什么？
expected_answer: |
  中心为 $-5$，半径仍为2，内部区间为 $(-7,-3)$；端点仍需另判。
mastery_evidence: 能把“距离结构”迁移到平移而非重算系数。

### infinite_series.system_06_power_domain.radius_execution
training_goal: 计算标准与一般形式的收敛半径。
source_evidence: 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第6页“方法一与方法二”
entry_trigger: 需要求幂级数主体收敛区间时。
mastery_criteria: 能先对整个通项做比值根值并解小于1，而非口号式“令x小于1”。
repair_target_node_id: infinite_series.system_06_power_domain.radius_execution

#### CoreQuestion
question_id: infinite_series.system_06_power_domain.radius_execution.core_q01
question_kind: calculation_execution
difficulty: standard
target_dimensions: method,calculation,expression
stem: |
  求 $\sum_{n=1}^{\infty}\dfrac{n}{3^n}(x-2)^n$ 的收敛半径与内部区间。
expected_answer: |
  通项绝对比值为
  $\dfrac{n+1}{n}\dfrac{\lvert x-2\rvert}{3}\to\lvert x-2\rvert/3$。
  令比值极限小于1，得 $\lvert x-2\rvert<3$，所以 $R=3$，内部区间 $(-1,5)$。端点另判。
solution_outline:
  1. 写整个通项。
  2. 计算比值极限。
  3. 解距离不等式并给R。
rubric:
  - criterion: 比值
    required_evidence: 极限 $\lvert x-2\rvert/3$
  - criterion: 不等式
    required_evidence: 小于1
  - criterion: 结果
    required_evidence: $R=3$ 与内部区间
common_errors:
  - error: 直接写“令x<1”
    root_cause: expression_weakness
    repair_target_node_id: infinite_series.system_06_power_domain.radius_execution
false_pass_risks:
  - 只套 $R=1/\rho$ 而未处理中心与绝对值，可能碰巧答对。

#### TransferVariant
question_id: infinite_series.system_06_power_domain.radius_execution.transfer_v01
variant_relation: 改成根值更自然的系数。
stem: |
  求 $\sum_{n=1}^{\infty}((n+1)/(2n+1))^n(x+1)^n$ 的半径。
expected_answer: |
  根值为 $[(n+1)/(2n+1)]\lvert x+1\rvert\to\lvert x+1\rvert/2$，故内部 $\lvert x+1\rvert<2$，$R=2$。
mastery_evidence: 能根据整体n次幂切换根值法。

### infinite_series.system_06_power_domain.endpoint_judgement
training_goal: 分别代回端点并合并开闭区间。
source_evidence: 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第7页例 $\sum x^n/n$
entry_trigger: 已得到 $\lvert x-x_0\rvert<R$ 后。
mastery_criteria: 能在每个端点生成数项级数、判敛散并写最终收敛域。
repair_target_node_id: infinite_series.system_06_power_domain.endpoint_judgement

#### CoreQuestion
question_id: infinite_series.system_06_power_domain.endpoint_judgement.core_q01
question_kind: calculation_execution
difficulty: standard
target_dimensions: method,calculation,final_answer
stem: |
  求 $\sum_{n=1}^{\infty}x^n/n$ 的收敛域。
expected_answer: |
  比值法给 $\lvert x\rvert<1$。端点 $x=1$ 时为调和级数，发散；$x=-1$ 时为交错调和级数，收敛。因此收敛域为 $[-1,1)$。
solution_outline:
  1. 求主体半径。
  2. 分别代入两端。
  3. 使用数项级数判别。
  4. 写正确开闭区间。
rubric:
  - criterion: 内部
    required_evidence: $\lvert x\rvert<1$
  - criterion: 右端
    required_evidence: 发散
  - criterion: 左端
    required_evidence: 收敛
  - criterion: 收敛域
    required_evidence: $[-1,1)$
common_errors:
  - error: 把两个端点一起继承
    root_cause: condition_miss
    repair_target_node_id: infinite_series.system_06_power_domain.endpoint_judgement
false_pass_risks:
  - 只写 $R=1$ 或 $(-1,1)$，不算完成收敛域。

#### TransferVariant
question_id: infinite_series.system_06_power_domain.endpoint_judgement.transfer_v01
variant_relation: 改变端点行为而半径不变。
stem: |
  求 $\sum_{n=1}^{\infty}x^n/n^2$ 的收敛域。
expected_answer: |
  半径仍为1。$x=1$ 时 $\sum1/n^2$ 收敛；$x=-1$ 时绝对收敛。因此收敛域为 $[-1,1]$。
mastery_evidence: 能理解半径相同不代表端点相同。

### infinite_series.system_06_power_domain.nonstandard_transform
training_goal: 处理缺项、一般函数项及求导积分后的端点。
source_evidence: 材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第8-12页“缺项、一般函数项、逐项微积分与抽象变形”
entry_trigger: 幂次不是n、对象非幂级数或级数被求导积分时。
mastery_criteria: 能对整个通项判别，继承半径但重新检查端点。
repair_target_node_id: infinite_series.system_06_power_domain.nonstandard_transform

#### CoreQuestion
question_id: infinite_series.system_06_power_domain.nonstandard_transform.core_q01
question_kind: condition_transformation
difficulty: advanced
target_dimensions: transformation,method,migration
stem: |
  求 $\sum_{n=1}^{\infty}x^{2n}/n$ 的收敛域，并说明为什么不能把端点符号想当然。
expected_answer: |
  把 $y=x^2$，主体要求 $\lvert x^2\rvert<1$，即 $\lvert x\rvert<1$。当 $x=1$ 或 $x=-1$ 时，$x^{2n}=1$，两端都变成 $\sum1/n$，均发散。因此收敛域为 $(-1,1)$。
solution_outline:
  1. 识别缺项幂次。
  2. 解 $\lvert x^2\rvert<1$。
  3. 两端分别代入并注意偶次幂符号。
rubric:
  - criterion: 主体
    required_evidence: $\lvert x\rvert<1$
  - criterion: 端点
    required_evidence: 两端均为调和级数
  - criterion: 结论
    required_evidence: 开区间
common_errors:
  - error: 误把 $x=-1$ 端点当交错
    root_cause: knowledge_confusion
    repair_target_node_id: infinite_series.system_06_power_domain.nonstandard_transform
false_pass_risks:
  - 只因看到负端点就写交错，属于典型伪掌握。

#### TransferVariant
question_id: infinite_series.system_06_power_domain.nonstandard_transform.transfer_v01
variant_relation: 从缺项迁移到非幂函数项级数。
stem: |
  求 $\sum_{n=1}^{\infty}e^{-nx}$ 的收敛域，并说明是否存在收敛半径。
expected_answer: |
  固定x后是公比 $e^{-x}$ 的几何级数。收敛需 $e^{-x}<1$，即 $x>0$。它不是幂级数，因此只有收敛域 $(0,\infty)$，不定义“中心+半径”。
mastery_evidence: 能处理一般函数项级数而不滥用半径语言。

### infinite_series.system_07_sum_basics.domain_first
training_goal: 把和函数写成表达式与原级数收敛域的组合。
source_evidence: 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第2页“和函数不是表达式”
entry_trigger: 题目要求幂级数和函数或用基础展开式时。
mastery_criteria: 能先求或继承原级数收敛域，并拒绝用化简式自然定义域替代。
repair_target_node_id: infinite_series.system_07_sum_basics.domain_first

#### CoreQuestion
question_id: infinite_series.system_07_sum_basics.domain_first.core_q01
question_kind: expression_standard
difficulty: basic
target_dimensions: concept,expression,final_answer
stem: |
  写出几何级数 $\sum_{n=0}^{\infty}x^n$ 的和函数，并解释为什么不能只写 $1/(1-x)$ 或条件 $x\ne1$。
expected_answer: |
  $S(x)=1/(1-x)$，但只在原级数收敛域 $\lvert x\rvert<1$ 成立。$x=2$ 时右侧有值而原级数发散，说明化简式的自然定义域不是和函数定义域。
solution_outline:
  1. 写表达式。
  2. 写 $\lvert x\rvert<1$。
  3. 用反例说明定义域来源。
rubric:
  - criterion: 表达式
    required_evidence: $1/(1-x)$
  - criterion: 收敛域
    required_evidence: $\lvert x\rvert<1$
  - criterion: 解释
    required_evidence: 原级数决定定义域
common_errors:
  - error: 漏写收敛域
    root_cause: expression_weakness
    repair_target_node_id: infinite_series.system_07_sum_basics.domain_first
false_pass_risks:
  - 只有最终函数式视为半个答案。

#### TransferVariant
question_id: infinite_series.system_07_sum_basics.domain_first.transfer_v01
variant_relation: 把基础式替换变量并追踪定义域。
stem: |
  求 $\sum_{n=0}^{\infty}(2x-1)^n$ 的和函数。
expected_answer: |
  当 $\lvert2x-1\rvert<1$，即 $0<x<1$ 时，和为 $1/[1-(2x-1)]=1/[2(1-x)]$。
mastery_evidence: 能同步变换表达式与收敛域。

### infinite_series.system_07_sum_basics.index_alignment
training_goal: 在合并前统一下标起点和幂次。
source_evidence: 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第3页“恒等变形”
entry_trigger: 多个级数需要相加、相减、求导积分或套原型时。
mastery_criteria: 能说明每次变形是换编号、拆前项还是提出幂，并验证项未改变。
repair_target_node_id: infinite_series.system_07_sum_basics.index_alignment

#### CoreQuestion
question_id: infinite_series.system_07_sum_basics.index_alignment.core_q01
question_kind: condition_transformation
difficulty: standard
target_dimensions: transformation,process,expression
stem: |
  把 $\sum_{n=1}^{\infty}a_{n-1}x^{n-1}$ 改写成从 $n=0$ 开始的形式，并说明为什么这是换编号而非删项。
expected_answer: |
  令 $m=n-1$，当 $n=1$ 时 $m=0$，故级数为 $\sum_{m=0}^{\infty}a_mx^m$。每个原项一一对应，只改变编号，没有删项或增项。
solution_outline:
  1. 定义新下标。
  2. 同步改变上下限、系数下标和幂次。
  3. 说明项的一一对应。
rubric:
  - criterion: 变换
    required_evidence: 三处同步
  - criterion: 起点
    required_evidence: 0
  - criterion: 解释
    required_evidence: 换编号不改项
common_errors:
  - error: 只改求和号下标，通项不改
    root_cause: transformation_error
    repair_target_node_id: infinite_series.system_07_sum_basics.index_alignment
false_pass_risks:
  - 结果碰巧形式相似但未说明一一对应，仍可能在复杂题中错位。

#### TransferVariant
question_id: infinite_series.system_07_sum_basics.index_alignment.transfer_v01
variant_relation: 检验拆前项与提出幂的组合。
stem: |
  将 $\sum_{n=0}^{\infty}a_nx^{n+1}$ 与 $a_0+\sum_{n=1}^{\infty}a_nx^n$ 分别整理。
expected_answer: |
  第一式为 $x\sum_{n=0}^{\infty}a_nx^n$；第二式正好等于 $\sum_{n=0}^{\infty}a_nx^n$。前者提出幂，后者把缺失的第0项补回。
mastery_evidence: 能区分“通项次数变形”与“下标起点补项”。

### infinite_series.system_07_sum_basics.known_expansion
training_goal: 根据系数障碍反向识别基础展开。
source_evidence: 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第4页“已知展开式反向识别”
entry_trigger: 通项出现 $1/n$、$n$、$n!$、交错或奇数次幂时。
mastery_criteria: 能指出由几何级数经过何种替换、求导或积分得到目标。
repair_target_node_id: infinite_series.system_07_sum_basics.known_expansion

#### CoreQuestion
question_id: infinite_series.system_07_sum_basics.known_expansion.core_q01
question_kind: method_selection
difficulty: standard
target_dimensions: trigger,method,migration
stem: |
  求 $\sum_{n=1}^{\infty}(-1)^{n-1}x^n/n$ 的和函数及内部收敛区间。
expected_answer: |
  由 $-\ln(1-t)=\sum t^n/n$，令 $t=-x$ 或直接对几何级数积分，得到
  $\sum_{n=1}^{\infty}(-1)^{n-1}x^n/n=\ln(1+x)$，内部 $\lvert x\rvert<1$；端点需另判。
solution_outline:
  1. 识别 $1/n$ 来自积分。
  2. 处理交错符号。
  3. 给出表达式与内部域。
rubric:
  - criterion: 原型
    required_evidence: 对数展开
  - criterion: 符号
    required_evidence: $\ln(1+x)$
  - criterion: 定义域
    required_evidence: 至少写内部 $\lvert x\rvert<1$
common_errors:
  - error: 把 $(-1)^{n+1}$ 与 $(-1)^{n-1}$ 误判不同
    root_cause: formula_memory_error
    repair_target_node_id: infinite_series.system_07_sum_basics.known_expansion
false_pass_risks:
  - 背出答案但解释不了替换或积分来源，迁移能力不足。

#### TransferVariant
question_id: infinite_series.system_07_sum_basics.known_expansion.transfer_v01
variant_relation: 换成阶乘结构。
stem: |
  求 $\sum_{n=0}^{\infty}x^n/n!$。
expected_answer: |
  这是 $e^x$ 的泰勒展开，对所有实数 $x$ 收敛，和函数为 $e^x$。
mastery_evidence: 能从系数结构切换到另一基础模型。

### infinite_series.system_07_sum_basics.calculus_transform
training_goal: 通过求导或积分消除系数n，并恢复常数。
source_evidence: 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第5-6页“先导后积、先积后导”
entry_trigger: 分母或分子含 $n$，直接原型不明显时。
mastery_criteria: 能说明选择原因、逐项运算、$S(0)$ 与收敛域。
repair_target_node_id: infinite_series.system_07_sum_basics.calculus_transform

#### CoreQuestion
question_id: infinite_series.system_07_sum_basics.calculus_transform.core_q01
question_kind: calculation_execution
difficulty: standard
target_dimensions: method,transformation,calculation,expression
stem: |
  从几何级数出发求 $S(x)=\sum_{n=1}^{\infty}x^n/n$。必须说明为什么求导后还要积分以及 $S(0)$ 的作用。
expected_answer: |
  求导得 $S'(x)=\sum_{n=1}^{\infty}x^{n-1}=1/(1-x)$，$\lvert x\rvert<1$。因此
  $S(x)=S(0)+\int_0^xdt/(1-t)=-\ln(1-x)$。这里 $S(0)=0$ 固定了积分常数；收敛域由原级数决定。
solution_outline:
  1. 求导消掉分母n。
  2. 识别几何级数。
  3. 定积分还原并写S(0)。
  4. 保留收敛域。
rubric:
  - criterion: 导数
    required_evidence: $1/(1-x)$
  - criterion: 还原
    required_evidence: $-\ln(1-x)$
  - criterion: 常数
    required_evidence: $S(0)=0$
  - criterion: 域
    required_evidence: $\lvert x\rvert<1$
common_errors:
  - error: 积分后漏常数
    root_cause: process_gap
    repair_target_node_id: infinite_series.system_07_sum_basics.calculus_transform
false_pass_risks:
  - 只背 $-\ln(1-x)$ 而未展示消障碍链，不算方法掌握。

#### TransferVariant
question_id: infinite_series.system_07_sum_basics.calculus_transform.transfer_v01
variant_relation: 改为分子有n的逆向操作。
stem: |
  求 $\sum_{n=1}^{\infty}nx^n$。
expected_answer: |
  由 $\sum_{n=0}^{\infty}x^n=1/(1-x)$ 求导得 $\sum_{n=1}^{\infty}nx^{n-1}=1/(1-x)^2$，再乘x：$\sum nx^n=x/(1-x)^2$，$\lvert x\rvert<1$。
mastery_evidence: 能根据障碍位置决定求导并处理幂次。

### infinite_series.system_07_sum_basics.cauchy_product
training_goal: 理解卷积系数并在合法域内相乘。
source_evidence: 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第3页“柯西乘积”
entry_trigger: 系数形如 $\sum_{i=0}^na_ib_{n-i}$ 时。
mastery_criteria: 能从次数组合解释系数，而非死背公式；能声明在共同绝对收敛域内。
repair_target_node_id: infinite_series.system_07_sum_basics.cauchy_product

#### CoreQuestion
question_id: infinite_series.system_07_sum_basics.cauchy_product.core_q01
question_kind: calculation_execution
difficulty: advanced
target_dimensions: concept,method,calculation
stem: |
  设 $A(x)=\sum_{n=0}^{\infty}a_nx^n$，$B(x)=\sum_{n=0}^{\infty}b_nx^n$ 在 $\lvert x\rvert<R$ 内绝对收敛。写出 $A(x)B(x)$ 中 $x^3$ 的系数并解释来源。
expected_answer: |
  次数和为3的组合是 $(0,3),(1,2),(2,1),(3,0)$，所以系数为 $a_0b_3+a_1b_2+a_2b_1+a_3b_0$。一般系数为 $\sum_{i=0}^na_ib_{n-i}$。
solution_outline:
  1. 列出所有次数组合。
  2. 写出系数。
  3. 说明共同绝对收敛区间。
rubric:
  - criterion: 组合
    required_evidence: 四项无漏无重
  - criterion: 公式
    required_evidence: 卷积形式
  - criterion: 条件
    required_evidence: 在共同绝对收敛域使用
common_errors:
  - error: 只取 $a_3b_3$
    root_cause: concept_gap
    repair_target_node_id: infinite_series.system_07_sum_basics.cauchy_product
false_pass_risks:
  - 背一般公式但不能列出低阶组合，可能没有理解来源。

#### TransferVariant
question_id: infinite_series.system_07_sum_basics.cauchy_product.transfer_v01
variant_relation: 用几何级数平方得到可识别系数。
stem: |
  利用 $(\sum_{n=0}^{\infty}x^n)^2$ 求 $\sum_{n=0}^{\infty}(n+1)x^n$。
expected_answer: |
  每个 $x^n$ 有 $n+1$ 组次数组合，所以左侧平方为 $\sum(n+1)x^n$；右侧为 $1/(1-x)^2$，$\lvert x\rvert<1$。
mastery_evidence: 能从卷积组合数反向识别系数。

### infinite_series.system_08_sum_advanced.recurrence_translation
training_goal: 把系数递推翻译成 $S$ 与 $S'$ 的关系。
source_evidence: 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第7页“递推式怎么变成微分方程”
entry_trigger: 只给 $a_{n+1}$ 与 $a_n$ 的关系而无显式公式时。
mastery_criteria: 能展开前三项核对下标，并正确识别 $na_nx^{n-1}$ 与导数。
repair_target_node_id: infinite_series.system_08_sum_advanced.recurrence_translation

#### CoreQuestion
question_id: infinite_series.system_08_sum_advanced.recurrence_translation.core_q01
question_kind: condition_transformation
difficulty: advanced
target_dimensions: transformation,process,calculation
stem: |
  设 $a_0=1$，$(n+1)a_{n+1}=2a_n$。令 $S(x)=\sum_{n=0}^{\infty}a_nx^n$，求 $S$ 满足的微分方程并求 $S(x)$。
expected_answer: |
  两边乘 $x^n$ 并从 $n=0$ 求和：左侧 $\sum(n+1)a_{n+1}x^n=S'(x)$，右侧 $2\sum a_nx^n=2S(x)$。故 $S'=2S$，且 $S(0)=a_0=1$，所以 $S(x)=e^{2x}$。
solution_outline:
  1. 选择乘 $x^n$。
  2. 正确移动下标得到S'。
  3. 形成微分方程。
  4. 用初值求解。
rubric:
  - criterion: 翻译
    required_evidence: $S'=2S$
  - criterion: 初值
    required_evidence: $S(0)=1$
  - criterion: 解
    required_evidence: $e^{2x}$
common_errors:
  - error: 把 $(n+1)a_{n+1}$ 误写成 $xS'$
    root_cause: transformation_error
    repair_target_node_id: infinite_series.system_08_sum_advanced.recurrence_translation
false_pass_risks:
  - 只从递推猜 $a_n=2^n/n!$ 虽可得答案，但未展示本节点训练的函数翻译。

#### TransferVariant
question_id: infinite_series.system_08_sum_advanced.recurrence_translation.transfer_v01
variant_relation: 让递推同时出现n与常数项。
stem: |
  设 $na_n=a_{n-1}$ 对 $n\ge1$，$a_0=1$。用和函数法求 $S(x)$。
expected_answer: |
  乘 $x^{n-1}$ 求和得 $S'(x)=S(x)$，初值1，所以 $S=e^x$。
mastery_evidence: 能调整乘幂使两边对齐。

### infinite_series.system_08_sum_advanced.hidden_coefficient
training_goal: 通过换元与递推比值消除积分定义系数。
source_evidence: 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第8页“16.34隐藏系数与点火公式”
entry_trigger: 系数由一族相邻幂次积分定义时。
mastery_criteria: 能识别目标是求相邻积分比值，而不是逐个算积分。
repair_target_node_id: infinite_series.system_08_sum_advanced.hidden_coefficient

#### CoreQuestion
question_id: infinite_series.system_08_sum_advanced.hidden_coefficient.core_q01
question_kind: condition_transformation
difficulty: advanced
target_dimensions: transformation,method,calculation
stem: |
  设 $b_n=\int_0^{\pi/2}\sin^nt\,dt$，且 $a_n=\int_0^1x^n\sqrt{1-x^2}\,dx$。证明 $a_n/b_n=1/(n+2)$。
expected_answer: |
  令 $x=\sin t$，则 $dx=\cos tdt$、$\sqrt{1-x^2}=\cos t$，故
  $a_n=\int_0^{\pi/2}\sin^nt\cos^2t\,dt=b_n-b_{n+2}$。
  点火递推给 $b_{n+2}=(n+1)b_n/(n+2)$，所以 $a_n/b_n=1-(n+1)/(n+2)=1/(n+2)$。
solution_outline:
  1. 三角换元。
  2. 把 $\cos^2t$ 写为 $1-\sin^2t$。
  3. 使用相邻积分递推。
  4. 求比值。
rubric:
  - criterion: 换元
    required_evidence: $a_n=b_n-b_{n+2}$
  - criterion: 递推
    required_evidence: $b_{n+2}/b_n=(n+1)/(n+2)$
  - criterion: 结果
    required_evidence: $1/(n+2)$
common_errors:
  - error: 花大量时间求每个 $b_n$ 的具体值
    root_cause: method_error
    repair_target_node_id: infinite_series.system_08_sum_advanced.hidden_coefficient
false_pass_risks:
  - 只写点火公式名称而不说明它提供的是比值关系，不算通过。

#### TransferVariant
question_id: infinite_series.system_08_sum_advanced.hidden_coefficient.transfer_v01
variant_relation: 将根号结构改写但仍要求相邻积分。
stem: |
  若积分中出现 $x^n(1-x^2)^{3/2}$，说明三角换元后应优先寻找什么结构。
expected_answer: |
  令 $x=\sin t$ 后得到 $\sin^nt\cos^4t$。应把 $\cos^4t=(1-\sin^2t)^2$ 展开为 $b_n-2b_{n+2}+b_{n+4}$，再用相邻递推比值化简。
mastery_evidence: 能把“相邻积分线性组合”迁移到更高次余因子。

### infinite_series.system_08_sum_advanced.construct_sum_function
training_goal: 为特殊点数项和选择幂次并构造 $S(x)$。
source_evidence: 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第9页“为什么构造S(x)”
entry_trigger: 原题无x但通项含 $1/(n+r)$、交错或像某幂级数在特殊点的值时。
mastery_criteria: 能根据求导后消分母来选择 $x$ 的指数，并写从构造到积分的链。
repair_target_node_id: infinite_series.system_08_sum_advanced.construct_sum_function

#### CoreQuestion
question_id: infinite_series.system_08_sum_advanced.construct_sum_function.core_q01
question_kind: method_selection
difficulty: advanced
target_dimensions: trigger,method,transformation
stem: |
  为 $\sum_{n=1}^{\infty}(-1)^n/(n+2)$ 构造一个幂级数，使求导能消掉分母，并求其和。
expected_answer: |
  构造 $S(x)=\sum_{n=1}^{\infty}(-1)^nx^{n+2}/(n+2)$。则
  $S'(x)=\sum_{n=1}^{\infty}(-1)^nx^{n+1}=x\sum_{n=1}^{\infty}(-1)^nx^n=-x^2/(1+x)$，$\lvert x\rvert<1$。
  由 $S(0)=0$，积分得 $S(x)=x-x^2/2-\ln(1+x)$。取 $x=1$ 的收敛端点，原和为 $S(1)=1/2-\ln2$。
solution_outline:
  1. 指数选n+2。
  2. 求导消分母。
  3. 识别几何级数。
  4. 积分还原并代1。
rubric:
  - criterion: 构造
    required_evidence: 目标和对应 $S(1)$
  - criterion: 导数
    required_evidence: $-x^2/(1+x)$
  - criterion: 还原
    required_evidence: $x-x^2/2-\ln(1+x)$
  - criterion: 数值
    required_evidence: $1/2-\ln2$
common_errors:
  - error: 随意选 $x^n$ 导致分母无法消去
    root_cause: method_error
    repair_target_node_id: infinite_series.system_08_sum_advanced.construct_sum_function
false_pass_risks:
  - 直接引用已知对数级数求和，未显示“构造触发与指数选择”，不算本节点通过。

#### TransferVariant
question_id: infinite_series.system_08_sum_advanced.construct_sum_function.transfer_v01
variant_relation: 改变偏移量。
stem: |
  为 $\sum_{n=0}^{\infty}(-1)^n/(n+3)$ 说明应构造何种 $S(x)$，无需完整积分。
expected_answer: |
  构造 $S(x)=\sum_{n=0}^{\infty}(-1)^nx^{n+3}/(n+3)$，则 $S'(x)=x^2/(1+x)$，目标和为 $S(1)$。
mastery_evidence: 能依据分母偏移同步选择幂次。

### infinite_series.system_08_sum_advanced.special_value_recovery
training_goal: 验证特殊点代入并完成综合回收。
source_evidence: 材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第8-10页“先化简隐藏系数-构造-代值”
entry_trigger: 已求出和函数，需要回到原无变量数项级数时。
mastery_criteria: 能检查特殊点是否在收敛域或端点可收敛，写出最终数值与完整链。
repair_target_node_id: infinite_series.system_08_sum_advanced.special_value_recovery

#### CoreQuestion
question_id: infinite_series.system_08_sum_advanced.special_value_recovery.core_q01
question_kind: synthesis_decomposition
difficulty: advanced
target_dimensions: synthesis,expression,final_answer
stem: |
  复述例16.34的完整逻辑链：为什么原题 $\sum_{n=1}^{\infty}(-1)^na_n/b_n$ 最终等于 $1/2-\ln2$？
expected_answer: |
  先由三角换元和点火递推得 $a_n/b_n=1/(n+2)$。原题化为 $\sum(-1)^n/(n+2)$。构造 $S(x)=\sum(-1)^nx^{n+2}/(n+2)$，求得 $S(x)=x-x^2/2-\ln(1+x)$。原级数在 $x=1$ 为收敛端点，因此代入得 $S(1)=1/2-\ln2$。
solution_outline:
  1. 化简隐藏系数。
  2. 构造指数匹配的S。
  3. 求和函数。
  4. 检查x=1可代并回收。
rubric:
  - criterion: 系数化简
    required_evidence: $1/(n+2)$
  - criterion: 构造与求和
    required_evidence: 函数式正确
  - criterion: 端点
    required_evidence: 说明原级数收敛
  - criterion: 最终值
    required_evidence: $1/2-\ln2$
common_errors:
  - error: 求得函数后不检查x=1是否合法
    root_cause: condition_miss
    repair_target_node_id: infinite_series.system_08_sum_advanced.special_value_recovery
false_pass_risks:
  - 只给最终常数无法区分记忆答案与综合能力。

#### TransferVariant
question_id: infinite_series.system_08_sum_advanced.special_value_recovery.transfer_v01
variant_relation: 改用幂级数内部点而非端点。
stem: |
  若目标和为 $\sum_{n=1}^{\infty}(-1)^n/[2^{n+2}(n+2)]$，如何从同一 $S(x)$ 回收？
expected_answer: |
  它等于 $S(1/2)$，直接代入 $x=1/2$；该点位于 $\lvert x\rvert<1$ 内，无需端点额外判别。
mastery_evidence: 能识别不同数项和对应不同特殊点。

### infinite_series.system_09_fourier_representation.period_frequency
training_goal: 区分横轴周期、内部角度与频率编号。
source_evidence: 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第3页“每个符号到底在干什么”
entry_trigger: 面对周期 $2l$ 的傅里叶公式或更换区间时。
mastery_criteria: 能解释 $\pi/l$ 的换算和第n波最小周期 $2l/n$。
repair_target_node_id: infinite_series.system_09_fourier_representation.period_frequency

#### CoreQuestion
question_id: infinite_series.system_09_fourier_representation.period_frequency.core_q01
question_kind: concept_judgement
difficulty: standard
target_dimensions: concept,expression
stem: |
  周期为 $2l$ 的傅里叶项为何写成 $\sin(n\pi x/l)$？解释 $2l,l,2\pi,\pi/l,n$ 的不同角色。
expected_answer: |
  $2l$ 是原函数横轴上的完整周期，$l$ 是半周期；$2\pi$ 是三角角度一圈。$\pi/l$ 把横轴距离换算成角度：$x$ 增加 $2l$ 时角度增加 $2\pi$。$n$ 表示在一个总周期内振动n次，第n波最小周期为 $2l/n$。
solution_outline:
  1. 区分横轴与角度。
  2. 解释换算率。
  3. 解释n与最小周期。
rubric:
  - criterion: 周期
    required_evidence: $2l$
  - criterion: 换算
    required_evidence: $\pi/l$
  - criterion: 频率
    required_evidence: $T_n=2l/n$
common_errors:
  - error: 把 $\pi$ 当原函数周期
    root_cause: knowledge_confusion
    repair_target_node_id: infinite_series.system_09_fourier_representation.period_frequency
false_pass_risks:
  - 只背公式但不能说明为什么总周期兼容，不算通过。

#### TransferVariant
question_id: infinite_series.system_09_fourier_representation.period_frequency.transfer_v01
variant_relation: 代入具体半周期。
stem: |
  当 $l=\pi$ 时，为什么三角项化为 $\sin nx,\cos nx$？
expected_answer: |
  因 $n\pi x/l=n\pi x/\pi=nx$。此处是换算率简化，不是说原函数周期变成 $\pi$；完整周期仍为 $2\pi$。
mastery_evidence: 能在具体公式中保持周期与角度的区分。

### infinite_series.system_09_fourier_representation.coefficient_extraction
training_goal: 用正交积分提取对应频率含量。
source_evidence: 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第4页“乘对应波再积分”
entry_trigger: 需要计算 $a_n,b_n$ 或解释系数意义时。
mastery_criteria: 能写公式并说明不同频率在完整周期积分抵消。
repair_target_node_id: infinite_series.system_09_fourier_representation.coefficient_extraction

#### CoreQuestion
question_id: infinite_series.system_09_fourier_representation.coefficient_extraction.core_q01
question_kind: expression_standard
difficulty: standard
target_dimensions: concept,method,expression
stem: |
  设 $f(x)=3\cos(\pi x/l)+2\sin(2\pi x/l)$。不用完整积分计算，说明为什么第一余弦系数 $a_1=3$。
expected_answer: |
  计算 $a_1$ 时把f乘 $\cos(\pi x/l)$ 并在 $[-l,l]$ 积分。$3\cos^2(\pi x/l)$ 留下；$2\sin(2\pi x/l)\cos(\pi x/l)$ 与目标频率正交，完整周期积分为0。除以l后读出3。
solution_outline:
  1. 写出检测波。
  2. 说明目标项留下。
  3. 说明其他频率抵消。
  4. 归一化得到系数。
rubric:
  - criterion: 检测器
    required_evidence: 乘对应余弦
  - criterion: 正交
    required_evidence: 交叉项积分0
  - criterion: 结果
    required_evidence: $a_1=3$
common_errors:
  - error: 把系数当随意积分结果，不理解频率选择
    root_cause: concept_gap
    repair_target_node_id: infinite_series.system_09_fourier_representation.coefficient_extraction
false_pass_risks:
  - 直接从原式“看出3”但不能解释积分机制，不算通过。

#### TransferVariant
question_id: infinite_series.system_09_fourier_representation.coefficient_extraction.transfer_v01
variant_relation: 改成不存在的频率。
stem: |
  对同一f，解释为什么 $a_3=0$。
expected_answer: |
  原函数没有第三余弦频率；乘 $\cos(3\pi x/l)$ 后，所有项都与之正交，完整周期积分为0。
mastery_evidence: 能把零系数解释为“对应频率成分不存在”。

### infinite_series.system_09_fourier_representation.parity_simplification
training_goal: 由奇偶乘积和对称积分消去系数。
source_evidence: 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第6页“奇正弦、偶余弦”
entry_trigger: 函数在对称区间已知奇偶性时。
mastery_criteria: 能从乘积奇偶性推导系数为零，而非仅背口诀。
repair_target_node_id: infinite_series.system_09_fourier_representation.parity_simplification

#### CoreQuestion
question_id: infinite_series.system_09_fourier_representation.parity_simplification.core_q01
question_kind: condition_transformation
difficulty: standard
target_dimensions: trigger,concept,expression
stem: |
  若 $f$ 是 $[-l,l]$ 上的奇函数，证明其傅里叶级数只含正弦项。
expected_answer: |
  $a_0$ 的被积函数f为奇函数，对称积分为0。对任意n，余弦为偶函数，所以 $f(x)\cos(n\pi x/l)$ 为奇函数，对称积分为0，故 $a_n=0$。正弦项可能保留，因此只含正弦项。
solution_outline:
  1. 处理常数项。
  2. 判断奇乘偶。
  3. 用对称积分为0。
rubric:
  - criterion: a0
    required_evidence: $0$
  - criterion: an
    required_evidence: $0$ 且理由完整
  - criterion: 结论
    required_evidence: 只剩bn正弦项
common_errors:
  - error: 只背“奇正弦”无因果链
    root_cause: expression_weakness
    repair_target_node_id: infinite_series.system_09_fourier_representation.parity_simplification
false_pass_risks:
  - 结论正确但不能处理新乘积或半区间公式，不算掌握。

#### TransferVariant
question_id: infinite_series.system_09_fourier_representation.parity_simplification.transfer_v01
variant_relation: 迁移到偶函数。
stem: |
  若f是偶函数，哪些系数为0？为什么半区间积分出现 $2/l$？
expected_answer: |
  正弦为奇函数，偶乘奇为奇，对称积分0，所以 $b_n=0$。保留的偶被积函数在左右两半积分相等，故 $\int_{-l}^lg=2\int_0^lg$，系数前出现 $2/l$。
mastery_evidence: 能从同一机制推出偶余弦与半区间因子。

### infinite_series.system_09_fourier_representation.half_range_extension
training_goal: 从半区间构造奇或偶周期延拓。
source_evidence: 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第7-8页“半区间延拓与公式系统”
entry_trigger: 题目只给 $[0,l]$ 并要求正弦或余弦展开时。
mastery_criteria: 能先补左半边再周期延拓，区分两种延拓代表不同全局函数。
repair_target_node_id: infinite_series.system_09_fourier_representation.half_range_extension

#### CoreQuestion
question_id: infinite_series.system_09_fourier_representation.half_range_extension.core_q01
question_kind: condition_transformation
difficulty: standard
target_dimensions: transformation,concept,expression
stem: |
  已知 $f(x)=x$ 在 $[0,l]$。分别写出奇延拓与偶延拓在 $[-l,l]$ 的表达，并说明为什么两种展开不矛盾。
expected_answer: |
  奇延拓为 $F_o(x)=x$，满足 $F_o(-x)=-F_o(x)$，产生正弦级数；偶延拓为 $F_e(x)=\lvert x\rvert$，满足 $F_e(-x)=F_e(x)$，产生余弦级数。二者在 $[0,l]$ 都等于原f，但在负半轴及周期复制后是不同函数，因此不矛盾。
solution_outline:
  1. 写奇延拓。
  2. 写偶延拓。
  3. 说明后续周期为2l。
  4. 解释不矛盾。
rubric:
  - criterion: 奇延拓
    required_evidence: $x$
  - criterion: 偶延拓
    required_evidence: $\lvert x\rvert$
  - criterion: 区别
    required_evidence: 原区间相同、全局函数不同
common_errors:
  - error: 把奇偶延拓与周期延拓混成同一步
    root_cause: knowledge_confusion
    repair_target_node_id: infinite_series.system_09_fourier_representation.half_range_extension
false_pass_risks:
  - 只说“正弦用奇、余弦用偶”但不会补左半边，不算通过。

#### TransferVariant
question_id: infinite_series.system_09_fourier_representation.half_range_extension.transfer_v01
variant_relation: 要求从目标展开类型反向选择延拓。
stem: |
  只给 $[0,2]$ 上函数，题目要求余弦级数。应如何补全和确定周期？
expected_answer: |
  先在 $[-2,2]$ 做偶延拓 $F(-x)=F(x)$，再以 $2l=4$ 为周期复制到全轴；系数使用半区间余弦公式。
mastery_evidence: 能从题目要求反向决定延拓与周期。

### infinite_series.system_10_fourier_application.dirichlet_value
training_goal: 根据左右极限确定傅里叶和函数逐点值。
source_evidence: 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第5页“狄利克雷收敛定理”
entry_trigger: 求 $S(x_0)$ 或讨论跳跃、端点、孤立点修改时。
mastery_criteria: 能分连续点、跳跃点和周期拼接端点，并写平均值。
repair_target_node_id: infinite_series.system_10_fourier_application.dirichlet_value

#### CoreQuestion
question_id: infinite_series.system_10_fourier_application.dirichlet_value.core_q01
question_kind: concept_judgement
difficulty: standard
target_dimensions: concept,trigger,expression
stem: |
  某周期函数在 $x_0$ 左极限为2、右极限为6，但人为定义 $f(x_0)=100$。其傅里叶和函数在 $x_0$ 的值是多少？为什么？
expected_answer: |
  $S(x_0)=[2+6]/2=4$。逐点收敛值由左右极限决定，不由孤立点的人为值决定；修改有限个孤立点也不改变系数积分。
solution_outline:
  1. 识别跳跃点。
  2. 取左右极限平均。
  3. 解释孤立点不影响。
rubric:
  - criterion: 数值
    required_evidence: 4
  - criterion: 定理
    required_evidence: 左右极限平均
  - criterion: 机制
    required_evidence: 孤立点不改积分
common_errors:
  - error: 直接代 $f(x_0)=100$
    root_cause: concept_gap
    repair_target_node_id: infinite_series.system_10_fourier_application.dirichlet_value
false_pass_risks:
  - 只算平均数但不能说明为何忽略点值，理解不完整。

#### TransferVariant
question_id: infinite_series.system_10_fourier_application.dirichlet_value.transfer_v01
variant_relation: 迁移到周期拼接端点。
stem: |
  在基本区间右端点，左极限来自本周期、右极限来自哪里？应怎样取值？
expected_answer: |
  右极限来自下一周期复制后的起点值；仍取拼接两侧极限的平均。
mastery_evidence: 能把跳跃规则迁移到周期端点。

### infinite_series.system_10_fourier_application.point_mapping
training_goal: 先移点再用狄利克雷取值。
source_evidence: 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第9页课堂例题一
entry_trigger: 求远离基本区间的S(x)且已知周期与奇偶性时。
mastery_criteria: 能严格区分周期/奇偶只负责搬点，最终取值由左右极限决定。
repair_target_node_id: infinite_series.system_10_fourier_application.point_mapping

#### CoreQuestion
question_id: infinite_series.system_10_fourier_application.point_mapping.core_q01
question_kind: calculation_execution
difficulty: advanced
target_dimensions: method,process,final_answer
stem: |
  设题中余弦展开对应偶周期函数，周期为2，且在 $[0,1]$ 上
  $f(x)=x$ 对 $0\le x\le1/2$，$f(x)=2-2x$ 对 $1/2<x\le1$。求 $S(-5/2)$。
expected_answer: |
  周期性给 $S(-5/2)=S(-1/2)$；偶性给 $S(-1/2)=S(1/2)$。在 $1/2$ 处左极限为 $1/2$，右极限为1，所以 $S(1/2)=(1/2+1)/2=3/4$。
solution_outline:
  1. 周期移到-1/2。
  2. 偶性移到1/2。
  3. 识别跳跃点。
  4. 左右极限平均。
rubric:
  - criterion: 移点
    required_evidence: 两步正确
  - criterion: 左右极限
    required_evidence: $1/2$ 与1
  - criterion: 结果
    required_evidence: $3/4$
common_errors:
  - error: 移点后直接用某一侧函数值
    root_cause: process_gap
    repair_target_node_id: infinite_series.system_10_fourier_application.point_mapping
false_pass_risks:
  - 只给3/4但没有移点链，不能定位其掌握了哪一步。

#### TransferVariant
question_id: infinite_series.system_10_fourier_application.point_mapping.transfer_v01
variant_relation: 改变目标点但保持同一函数。
stem: |
  求 $S(5/2)$。
expected_answer: |
  周期性 $S(5/2)=S(1/2)$，同样是跳跃平均，结果 $3/4$。
mastery_evidence: 能自主选择最短周期移点，不机械照抄负号步骤。

### infinite_series.system_10_fourier_application.coefficient_calculation
training_goal: 用分部积分求多项式余弦系数。
source_evidence: 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第10页课堂例题二
entry_trigger: 半区间多项式要求余弦展开时。
mastery_criteria: 能正确计算a0和an，处理两次分部积分及边界符号。
repair_target_node_id: infinite_series.system_10_fourier_application.coefficient_calculation

#### CoreQuestion
question_id: infinite_series.system_10_fourier_application.coefficient_calculation.core_q01
question_kind: calculation_execution
difficulty: advanced
target_dimensions: calculation,process,expression
stem: |
  对 $f(x)=1-x^2$，$0\le x\le\pi$，求其余弦级数的 $a_0$ 与 $a_n$。
expected_answer: |
  偶延拓且 $l=\pi$。
  $a_0=(2/\pi)\int_0^\pi(1-x^2)dx=2-2\pi^2/3$。
  $a_n=(2/\pi)\int_0^\pi(1-x^2)\cos nx\,dx=-(2/\pi)I$，其中 $I=\int_0^\pi x^2\cos nx\,dx=2\pi(-1)^n/n^2$，故 $a_n=4(-1)^{n+1}/n^2$。
solution_outline:
  1. 确定l与余弦公式。
  2. 计算a0。
  3. 两次分部积分计算I。
  4. 化简符号。
rubric:
  - criterion: a0
    required_evidence: $2-2\pi^2/3$
  - criterion: I
    required_evidence: $2\pi(-1)^n/n^2$
  - criterion: an
    required_evidence: $4(-1)^{n+1}/n^2$
common_errors:
  - error: 忘记展开式常数项是a0/2
    root_cause: formula_memory_error
    repair_target_node_id: infinite_series.system_10_fourier_application.coefficient_calculation
false_pass_risks:
  - 只背最终展开式而不展示边界项与符号来源，不能证明计算稳定。

#### TransferVariant
question_id: infinite_series.system_10_fourier_application.coefficient_calculation.transfer_v01
variant_relation: 改为奇延拓的一次分部积分。
stem: |
  对 $f(x)=x$，$0<x<\pi$，做正弦展开时求 $b_n$。
expected_answer: |
  $b_n=(2/\pi)\int_0^\pi x\sin nx\,dx=2(-1)^{n+1}/n$。
mastery_evidence: 能迁移半区间公式与分部积分到正弦系数。

### infinite_series.system_10_fourier_application.special_point_sum
training_goal: 从傅里叶恒等式选择特殊点提取数项级数。
source_evidence: 材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第11页“特殊点清理三角因子”
entry_trigger: 已知傅里叶展开且目标和不含三角因子时。
mastery_criteria: 能选择点使三角因子统一，先判连续性，再解出目标和。
repair_target_node_id: infinite_series.system_10_fourier_application.special_point_sum

#### CoreQuestion
question_id: infinite_series.system_10_fourier_application.special_point_sum.core_q01
question_kind: method_selection
difficulty: advanced
target_dimensions: trigger,method,calculation,final_answer
stem: |
  由
  $1-x^2=1-\pi^2/3+4\sum_{n=1}^{\infty}(-1)^{n+1}\cos(nx)/n^2$
  求 $\sum_{n=1}^{\infty}(-1)^{n+1}/n^2$。
expected_answer: |
  取 $x=0$，因为 $\cos(n\cdot0)=1$，且0是偶延拓后的连续点，左边取 $f(0)=1$。于是
  $1=1-\pi^2/3+4S$，得 $S=\pi^2/12$。
solution_outline:
  1. 说明选x=0的目的。
  2. 检查连续点。
  3. 代入并解方程。
rubric:
  - criterion: 触发
    required_evidence: 所有余弦统一为1
  - criterion: 取值
    required_evidence: 左边为1
  - criterion: 结果
    required_evidence: $\pi^2/12$
common_errors:
  - error: 以为“消掉cos”必须让它变0
    root_cause: knowledge_confusion
    repair_target_node_id: infinite_series.system_10_fourier_application.special_point_sum
false_pass_risks:
  - 直接背出π²/12而不写选点与连续性，不能通过。

#### TransferVariant
question_id: infinite_series.system_10_fourier_application.special_point_sum.transfer_v01
variant_relation: 选择另一个点提取非交错平方倒数和。
stem: |
  在同一展开式中取 $x=\pi$，可得到哪个级数和？给出结果。
expected_answer: |
  $\cos(n\pi)=(-1)^n$，乘原系数 $(-1)^{n+1}$ 后恒为-1。左边 $1-\pi^2$，所以
  $1-\pi^2=1-\pi^2/3-4\sum1/n^2$，解得 $\sum1/n^2=\pi^2/6$。
mastery_evidence: 能根据目标符号选择不同特殊点并处理端点连续/拼接值。

## BossTrainingAsset

boss_id: infinite_series.boss
question_kind: boss_acceptance
title: 黑洞验收：三种无穷展开的一体化调用
covers_system_ids: infinite_series.system_01_foundations,infinite_series.system_02_geometric_tests,infinite_series.system_03_integral_test,infinite_series.system_04_alternating_series,infinite_series.system_05_arbitrary_terms,infinite_series.system_06_power_domain,infinite_series.system_07_sum_basics,infinite_series.system_08_sum_advanced,infinite_series.system_09_fourier_representation,infinite_series.system_10_fourier_application
covers_micro_nodes: infinite_series.system_01_foundations.term_gate,infinite_series.system_02_geometric_tests.root_method,infinite_series.system_04_alternating_series.failure_repair,infinite_series.system_05_arbitrary_terms.convergence_classification,infinite_series.system_06_power_domain.endpoint_judgement,infinite_series.system_07_sum_basics.known_expansion,infinite_series.system_08_sum_advanced.construct_sum_function,infinite_series.system_09_fourier_representation.half_range_extension,infinite_series.system_10_fourier_application.coefficient_calculation,infinite_series.system_10_fourier_application.special_point_sum
source_evidence: 材料A第2-11页; 材料B第3-9页; 材料C第3-7页; 材料D第2-9页; 材料E第5-11页
stem: |
  完成以下三个相互关联的阶段，所有结论必须写成立条件和过程证据。

  **阶段A：数项级数分类**
  1. 判断 $\sum_{n=1}^{\infty}\left(\dfrac{2n+1}{3n+2}\right)^n$。
  2. 判断并分类 $\sum_{n=2}^{\infty}\dfrac{(-1)^{n-1}}{n+\sin n}$。

  **阶段B：幂级数收敛域与和函数**
  求 $F(x)=\sum_{n=1}^{\infty}(-1)^{n-1}x^n/n$ 的完整收敛域与和函数。

  **阶段C：傅里叶展开与特殊数项和**
  对 $f(x)=1-x^2$，$0\le x\le\pi$ 作余弦级数展开，并由该展开求
  $\sum_{n=1}^{\infty}(-1)^{n+1}/n^2$。
expected_answer: |
  **阶段A-1**：取n次根，极限为 $2/3<1$，故正项级数收敛。

  **阶段A-2**：
  $1/(n+\sin n)=1/n-\sin n/[n(n+\sin n)]$。原级数等于交错调和级数减去一个绝对收敛误差级数，因此收敛。绝对值级数与 $\sum1/n$ 极限比较同敛而发散，所以原级数条件收敛。

  **阶段B**：比值或根值给 $\lvert x\rvert<1$。$x=1$ 时为交错调和级数，收敛；$x=-1$ 时为负调和级数，发散，故收敛域为 $(-1,1]$。在 $\lvert x\rvert<1$ 内对几何级数积分得 $F(x)=\ln(1+x)$，并由端点收敛延伸到 $x=1$，$F(1)=\ln2$。

  **阶段C**：偶延拓，$l=\pi$。
  $a_0=(2/\pi)\int_0^\pi(1-x^2)dx=2-2\pi^2/3$；
  $a_n=(2/\pi)\int_0^\pi(1-x^2)\cos nx\,dx=4(-1)^{n+1}/n^2$。
  因此
  $1-x^2=1-\pi^2/3+4\sum_{n=1}^{\infty}(-1)^{n+1}\cos(nx)/n^2$。
  取连续点 $x=0$，所有余弦等于1，得目标和 $\pi^2/12$。
solution_outline:
  1. 先按通项结构为两类数项级数选择根值与“主项加误差”路线，并完成绝对/条件分类。
  2. 固定x求幂级数主体半径，分别判断两个端点，再用逐项积分识别对数和函数。
  3. 选择偶延拓并计算常数项与一般余弦系数，形成完整傅里叶展开。
  4. 选择连续特殊点清理三角因子，解出数项级数，并在所有阶段写完整条件。
rubric:
  - criterion: 结构识别与方法选择
    required_evidence: 根值法用于整体n次幂，扰动交错级数使用合法恒等拆项而非乱拆分母。
  - criterion: 收敛分类
    required_evidence: 明确证明第二个数项级数收敛且绝对值级数发散，结论为条件收敛。
  - criterion: 幂级数完整收敛域
    required_evidence: 主体 $\lvert x\rvert<1$ 与两个端点分别代回，最终 $(-1,1]$。
  - criterion: 和函数与定义域
    required_evidence: $F(x)=\ln(1+x)$ 并说明原级数定义域，不以对数自然定义域代替。
  - criterion: 傅里叶系数过程
    required_evidence: 写出a0、an的积分与至少两次分部积分关键结果。
  - criterion: 特殊点提取
    required_evidence: 说明选择x=0使余弦统一为1且该点连续，得到 $\pi^2/12$。
failure_routing:
  - observed_failure: 未先检查通项结构或把根值极限等于1当结论
    root_cause: trigger_failure
    repair_target_node_id: infinite_series.system_01_foundations.structure_classification
  - observed_failure: 把 $1/(n+\sin n)$ 拆成两个倒数
    root_cause: transformation_error
    repair_target_node_id: infinite_series.system_04_alternating_series.failure_repair
  - observed_failure: 只写收敛未判绝对或条件
    root_cause: expression_weakness
    repair_target_node_id: infinite_series.system_05_arbitrary_terms.convergence_classification
  - observed_failure: 只写半径1或漏判端点
    root_cause: condition_miss
    repair_target_node_id: infinite_series.system_06_power_domain.endpoint_judgement
  - observed_failure: 写出ln(1+x)但没有原级数收敛域
    root_cause: expression_weakness
    repair_target_node_id: infinite_series.system_07_sum_basics.domain_first
  - observed_failure: 傅里叶常数项多一倍或an符号错误
    root_cause: formula_memory_error
    repair_target_node_id: infinite_series.system_10_fourier_application.coefficient_calculation
  - observed_failure: 直接背平方倒数和而没有选点与连续性
    root_cause: synthesis_failure
    repair_target_node_id: infinite_series.system_10_fourier_application.special_point_sum
false_pass_risks:
  - 只写三个最终答案，无法证明方法选择、端点、定义域和傅里叶逐点规则真正掌握。
  - 扰动级数可能凭“像交错调和”猜对，但未证明误差绝对收敛。
  - 对数和函数与平方倒数和属于常见结论，必须用过程证据防止背答案通过。
entry_requirements:
  - infinite_series.system_01_foundations.challenge
  - infinite_series.system_02_geometric_tests.challenge
  - infinite_series.system_03_integral_test.challenge
  - infinite_series.system_04_alternating_series.challenge
  - infinite_series.system_05_arbitrary_terms.challenge
  - infinite_series.system_06_power_domain.challenge
  - infinite_series.system_07_sum_basics.challenge
  - infinite_series.system_08_sum_advanced.challenge
  - infinite_series.system_09_fourier_representation.challenge
  - infinite_series.system_10_fourier_application.challenge

## DeliveryChecklist
| check | result | evidence |
| --- | --- | --- |
| 每个MacroNode都对应一个GalaxyPlan星系 | pass | 10个MacroNode与10个GalaxyPlan行一一对应。 |
| 每个星系严格有3–5个MicroNode | pass | infinite_series.system_01_foundations=4; infinite_series.system_02_geometric_tests=4; infinite_series.system_03_integral_test=4; infinite_series.system_04_alternating_series=4; infinite_series.system_05_arbitrary_terms=5; infinite_series.system_06_power_domain=5; infinite_series.system_07_sum_basics=5; infinite_series.system_08_sum_advanced=4; infinite_series.system_09_fourier_representation=4; infinite_series.system_10_fourier_application=4 |
| 没有把单道题或孤立公式误当成星球 | pass | 42个可见节点均描述可观察能力；题目仅存在于TrainingAssets。 |
| 每个MicroNode都有核心题和迁移变式 | pass | 43个MicroNode均有CoreQuestion与TransferVariant。 |
| 每个星系都有局部MacroChallenge | pass | 10个星系均配置1个MacroChallenge。 |
| 全章只有一个GalaxyBoss | pass | Boss ID=infinite_series.boss。 |
| Boss覆盖多个星系并能路由失败 | pass | 覆盖10个星系，7类可观察失败均精确路由到MicroNode。 |
| 所有内容节点都有source_evidence或evidence_sources | pass | GalaxyPlan与Boss有source_evidence；42个MicroNode在TrainingAssets有source_evidence；HiddenAbilities有evidence_sources；Transfer与Synthesis的why_exists内含来源。 |
| 所有可见节点都没有成为孤立节点 | pass | 139条语义边覆盖全部MicroNode的内部流程与局部检查，并包含跨星系、迁移和修复关系。 |
| 所有高频错误都有repair_target_node_id | pass | 26个隐藏能力、全部训练题common_errors、Boss失败路由与12类ErrorRepairMap均有修复节点。 |
| 星系超过6个时已提供扩容策略 | pass | 使用progressive_reveal，并配置far、middle、near纵深带。 |
| 材料冲突和信息缺口已显式列出 | pass | SourceDigest中的InformationGaps与SourceConflicts已填写。 |
