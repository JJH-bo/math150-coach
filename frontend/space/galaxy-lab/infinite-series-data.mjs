export default {
  "chapterId": "infinite_series",
  "title": "无穷级数",
  "systems": [
    {
      "id": "infinite_series.system_01_foundations",
      "macroNodeId": "infinite_series.system_01_foundations",
      "title": "级数敛散的总门槛与结构识别",
      "coreQuestion": "面对一个无穷级数，如何先排除无资格对象，再识别真正决定敛散的结构？",
      "learningOrder": 1,
      "visualPriority": "high",
      "recommendedDepth": "far",
      "preferredSector": "upper_left",
      "prerequisiteSystemIds": [],
      "bossContribution": "提供通项门槛、正项下降速度和判别法边界意识，阻止在综合题中无条件套公式。",
      "spacingReason": "这是全章入口，应与具体判别法星系留出空隙，避免把总门槛误看成某一种判别法。",
      "sourceEvidence": "材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第2页“一页重建总地图”; 第3页“通项趋零只是入场券”; 第4页“正项级数”",
      "planets": [
        {
          "id": "infinite_series.system_01_foundations.term_gate",
          "macroId": "infinite_series.system_01_foundations",
          "type": "concept",
          "title": "通项趋零门槛",
          "description": "能先检查 $a_n\\to0$；成功时只把它当必要条件，失败时立即判发散；常见失败是把趋零直接当收敛。",
          "training": {
            "goal": "把通项极限作为必要门槛而非收敛结论。",
            "entryTrigger": "题目先问级数敛散，或通项极限明显可算时。",
            "masteryCriteria": "能先算极限；不趋零时直接发散；趋零时明确继续分析。",
            "repairTargetNodeId": "infinite_series.system_01_foundations.term_gate",
            "questionId": "infinite_series.system_01_foundations.term_gate.core_q01",
            "kind": "concept_judgement",
            "difficulty": "basic",
            "targetDimensions": [
              "concept",
              "trigger",
              "expression"
            ],
            "stem": "判断下列说法并说明理由：若 $a_n\\to0$，则 $\\sum_{n=1}^{\\infty}a_n$ 收敛。再说明当 $\\lim a_n\\ne0$ 或极限不存在时能推出什么。",
            "expectedAnswer": "说法错误。$a_n\\to0$ 只是级数收敛的必要条件，不是充分条件，例如调和级数 $\\sum 1/n$ 中通项趋零但级数发散。若 $\\lim_{n\\to\\infty}a_n\\ne0$ 或极限不存在，则级数必发散。",
            "variant": {
              "questionId": "infinite_series.system_01_foundations.term_gate.transfer_v01",
              "relation": "把逻辑判断改为含参数的通项门槛，而不是重复同一反例。",
              "stem": "设 $a_n=(n+\\alpha)/(2n+1)$。讨论哪些 $\\alpha$ 能使 $\\sum a_n$ 有可能收敛，并说明是否已经能判收敛。",
              "expectedAnswer": "对任意固定 $\\alpha$，$a_n\\to1/2\\ne0$，所以级数必发散；不存在“有可能收敛”的参数。此处无需再用其他判别法。",
              "masteryEvidence": "能把参数题先压到通项极限，而不是盲目继续套判别法。"
            }
          }
        },
        {
          "id": "infinite_series.system_01_foundations.structure_classification",
          "macroId": "infinite_series.system_01_foundations",
          "type": "trigger",
          "title": "级数结构分类",
          "description": "能从通项识别正项、交错、任意项、函数项或幂级数结构，并选择后续星系；常见失败是只凭外观套某个判别法。",
          "training": {
            "goal": "识别通项的符号与变量结构并路由到正确方法族。",
            "entryTrigger": "通项含固定符号、交错因子、任意符号或变量 $x$ 时。",
            "masteryCriteria": "能说出对象类型、核心困难与下一步检查，而非直接给方法名。",
            "repairTargetNodeId": "infinite_series.system_01_foundations.structure_classification",
            "questionId": "infinite_series.system_01_foundations.structure_classification.core_q01",
            "kind": "trigger_identification",
            "difficulty": "standard",
            "targetDimensions": [
              "trigger",
              "concept",
              "method"
            ],
            "stem": "对以下对象只做“结构路由”，不必完整判敛散：\n1. $\\sum 1/(n\\ln n)$；\n2. $\\sum (-1)^{n-1}/\\sqrt n$；\n3. $\\sum u_n$，其中 $u_n$ 符号无规律；\n4. $\\sum a_n(x-2)^n$。",
            "expectedAnswer": "1. 正项函数型级数，先检查积分判别或与已知尺度比较。2. 交错级数，分离幅度 $u_n=1/\\sqrt n$，检查莱布尼茨并另判绝对收敛。3. 任意项级数，先看 $\\sum\\lvert u_n\\rvert$，若不收敛再分析抵消结构。4. 幂级数，固定 $x$ 后变数项级数，求中心2、半径与端点。",
            "variant": {
              "questionId": "infinite_series.system_01_foundations.structure_classification.transfer_v01",
              "relation": "加入一个含 $x$ 但不是幂级数的对象，检验是否真正识别结构。",
              "stem": "对 $\\sum_{n=1}^{\\infty}e^{-nx}$ 进行结构路由，并说明为什么不能直接称其为“以0为中心的幂级数”。",
              "expectedAnswer": "固定 $x$ 后它是公比为 $e^{-x}$ 的正项等比级数；收敛条件为 $e^{-x}<1$，即 $x>0$。它不是 $\\sum a_n(x-x_0)^n$ 的幂结构，因此有收敛域但不谈收敛半径。",
              "masteryEvidence": "能区分“含变量的函数项级数”与“幂级数”。"
            }
          }
        },
        {
          "id": "infinite_series.system_01_foundations.positive_tail_model",
          "macroId": "infinite_series.system_01_foundations",
          "type": "method",
          "title": "正项尾巴模型",
          "description": "能解释正项级数没有抵消，必须用等比级数、$p$级数或积分尾巴控制下降速度；常见失败是只说“很小”。",
          "training": {
            "goal": "理解正项级数只能靠尾项下降速度收住。",
            "entryTrigger": "确认 $a_n\\ge0$ 后，需要决定比较模型时。",
            "masteryCriteria": "能用部分和单调不降解释为何必须控制尾巴，并指出几何与 $p$ 级数标尺。",
            "repairTargetNodeId": "infinite_series.system_01_foundations.positive_tail_model",
            "questionId": "infinite_series.system_01_foundations.positive_tail_model.core_q01",
            "kind": "concept_judgement",
            "difficulty": "basic",
            "targetDimensions": [
              "concept",
              "method",
              "expression"
            ],
            "stem": "解释为什么正项级数的核心是“下降速度”，并判断“只要 $a_n$ 很小，级数就收敛”是否是可评分的结论。",
            "expectedAnswer": "正项级数的部分和单调不降，没有负项抵消；要收敛，尾项总量必须有限，因此要把尾巴压到已知收敛模型，如 $k^n$ 且 $0<k<1$ 或 $1/n^p$ 且 $p>1$。说“很小”没有比较对象、指数或统一界，不能作为判敛证据。",
            "variant": {
              "questionId": "infinite_series.system_01_foundations.positive_tail_model.transfer_v01",
              "relation": "把抽象解释迁移到临界比较。",
              "stem": "比较 $a_n=1/n$ 与 $b_n=1/n^2$：二者都趋零，为什么一个发散一个收敛？",
              "expectedAnswer": "二者都通过通项门槛，但尾巴下降尺度不同。$1/n$ 位于 $p=1$ 临界线并发散；$1/n^2$ 对应 $p=2>1$，尾巴总量有限而收敛。",
              "masteryEvidence": "能从“趋零”升级到“下降速度尺度”。"
            }
          }
        },
        {
          "id": "infinite_series.system_01_foundations.boundary_reasoning",
          "macroId": "infinite_series.system_01_foundations",
          "type": "expression",
          "title": "工具失败边界",
          "description": "能规范表达“判别法无结论”与“级数发散”的区别，并用最小反例否定错误推出；常见失败是把极限等于1判死。",
          "training": {
            "goal": "在工具无结论时停止错误推出并切换模型。",
            "entryTrigger": "判别法极限落在边界，或定理条件没有验证出来时。",
            "masteryCriteria": "能写“该方法无结论”，给出相反敛散反例，并提出下一条可用路线。",
            "repairTargetNodeId": "infinite_series.system_01_foundations.boundary_reasoning",
            "questionId": "infinite_series.system_01_foundations.boundary_reasoning.core_q01",
            "kind": "expression_standard",
            "difficulty": "standard",
            "targetDimensions": [
              "expression",
              "method",
              "migration"
            ],
            "stem": "某正项级数用比值法得到极限 $\\rho=1$。学生写“所以发散”。请指出逻辑错误，并给出最小反例证明 $\\rho=1$ 时不能判。",
            "expectedAnswer": "错误在于把“比值判别法无结论”写成“级数发散”。$\\sum1/n$ 与 $\\sum1/n^2$ 的相邻项比值极限都为1，但前者发散、后者收敛。因此只能更换比较、积分或其他结构判别。",
            "variant": {
              "questionId": "infinite_series.system_01_foundations.boundary_reasoning.transfer_v01",
              "relation": "将同一边界意识迁移到莱布尼茨条件。",
              "stem": "若无法证明 $u_n$ 单调不增，能否断言 $\\sum(-1)^{n-1}u_n$ 发散？写出规范答复。",
              "expectedAnswer": "不能。莱布尼茨是充分条件；单调性未验证只说明该方法不能直接用。应尝试证明后期单调、改用绝对收敛、分组或拆成主项与可控误差。",
              "masteryEvidence": "能把“工具失败不等于对象失败”迁移到另一判别法。"
            }
          }
        }
      ]
    },
    {
      "id": "infinite_series.system_02_geometric_tests",
      "macroNodeId": "infinite_series.system_02_geometric_tests",
      "title": "比值判别与根值判别的等比尾巴控制",
      "coreQuestion": "怎样根据通项结构选择比值或根值，并把尾巴严格压到固定的收敛等比级数？",
      "learningOrder": 2,
      "visualPriority": "high",
      "recommendedDepth": "far",
      "preferredSector": "left",
      "prerequisiteSystemIds": [
        "infinite_series.system_01_foundations"
      ],
      "bossContribution": "提供指数型、阶乘型和整体幂结构的快速判敛能力及固定 $k<1$ 的证明桥。",
      "spacingReason": "与积分判别分开，突出“等比尾巴”而非“连续面积尾巴”的不同方法链。",
      "sourceEvidence": "材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第5页“比值判别法”; 第6页“柯西根值法”; 第11页“边界反例库”",
      "planets": [
        {
          "id": "infinite_series.system_02_geometric_tests.ratio_trigger",
          "macroId": "infinite_series.system_02_geometric_tests",
          "type": "trigger",
          "title": "比值法触发识别",
          "description": "面对阶乘、连乘、递推或相邻项易约结构，能优先检查 $a_{n+1}/a_n$；常见失败是对整体 $n$ 次幂做冗长比值。",
          "training": {
            "goal": "根据阶乘、连乘或相邻项结构触发比值法。",
            "entryTrigger": "通项含 $n!$、连乘、递推或相邻项可大量约去时。",
            "masteryCriteria": "能说明为什么相邻比值比直接估计通项更简洁。",
            "repairTargetNodeId": "infinite_series.system_02_geometric_tests.ratio_trigger",
            "questionId": "infinite_series.system_02_geometric_tests.ratio_trigger.core_q01",
            "kind": "trigger_identification",
            "difficulty": "standard",
            "targetDimensions": [
              "trigger",
              "method"
            ],
            "stem": "从“方法选择”角度说明为什么级数 $\\sum_{n=1}^{\\infty} n!/n^n$ 更适合先尝试比值法，并计算相邻项比值的极限。",
            "expectedAnswer": "令 $a_n=n!/n^n$。相邻比值能约掉阶乘：\n$\\dfrac{a_{n+1}}{a_n}=\\dfrac{(n+1)!}{(n+1)^{n+1}}\\dfrac{n^n}{n!}=(n/(n+1))^n\\to e^{-1}<1$。\n因此比值法收敛。",
            "variant": {
              "questionId": "infinite_series.system_02_geometric_tests.ratio_trigger.transfer_v01",
              "relation": "将阶乘触发迁移到递推定义。",
              "stem": "正项序列满足 $a_{n+1}=\\dfrac{2n+1}{3n+4}a_n$ 且 $a_1>0$。判断 $\\sum a_n$。",
              "expectedAnswer": "相邻比值已由递推给出，极限为 $2/3<1$，故级数收敛。",
              "masteryEvidence": "能从递推直接读取比值，而不是先硬求 $a_n$ 显式式。"
            }
          }
        },
        {
          "id": "infinite_series.system_02_geometric_tests.ratio_method",
          "macroId": "infinite_series.system_02_geometric_tests",
          "type": "method",
          "title": "比值法执行与结论",
          "description": "能计算比值极限并按 $\\rho<1$、$\\rho>1$、$\\rho=1$ 正确输出；常见失败是漏掉正项或绝对值条件。",
          "training": {
            "goal": "完整执行比值判别并处理三种极限结果。",
            "entryTrigger": "已经选择比值法后。",
            "masteryCriteria": "能写绝对值比值、极限、三分结论和必要的通项说明。",
            "repairTargetNodeId": "infinite_series.system_02_geometric_tests.ratio_method",
            "questionId": "infinite_series.system_02_geometric_tests.ratio_method.core_q01",
            "kind": "calculation_execution",
            "difficulty": "standard",
            "targetDimensions": [
              "method",
              "calculation",
              "final_answer"
            ],
            "stem": "判断 $\\sum_{n=1}^{\\infty}\\dfrac{3^n}{n!}$ 的敛散性，并写出比值法的完整判断链。",
            "expectedAnswer": "设 $a_n=3^n/n!>0$。则 $a_{n+1}/a_n=3/(n+1)\\to0<1$，故级数收敛。更具体地，后期可选固定 $k<1$ 使 $a_{n+1}\\le ka_n$。",
            "variant": {
              "questionId": "infinite_series.system_02_geometric_tests.ratio_method.transfer_v01",
              "relation": "把结果改为通项不趋零的发散分支。",
              "stem": "判断 $\\sum_{n=1}^{\\infty} n!/2^n$。",
              "expectedAnswer": "$a_{n+1}/a_n=(n+1)/2\\to\\infty>1$，所以通项最终递增且不趋零，级数发散。",
              "masteryEvidence": "能正确使用 $\\rho>1$ 分支并关联通项门槛。"
            }
          }
        },
        {
          "id": "infinite_series.system_02_geometric_tests.root_method",
          "macroId": "infinite_series.system_02_geometric_tests",
          "type": "method",
          "title": "根值法执行与结论",
          "description": "能对整体指数型结构计算 $\\sqrt[n]{a_n}$ 并压到 $k^n$；常见失败是把根值极限等于1当结论。",
          "training": {
            "goal": "对整体 $n$ 次幂结构执行根值判别。",
            "entryTrigger": "通项整体形如 $[r_n]^n$ 或含多个指数型因子时。",
            "masteryCriteria": "能取 $n$ 次根还原底数，计算极限并压到等比级数。",
            "repairTargetNodeId": "infinite_series.system_02_geometric_tests.root_method",
            "questionId": "infinite_series.system_02_geometric_tests.root_method.core_q01",
            "kind": "calculation_execution",
            "difficulty": "standard",
            "targetDimensions": [
              "trigger",
              "method",
              "calculation"
            ],
            "stem": "判断 $\\sum_{n=1}^{\\infty}\\left(\\dfrac{2n+1}{3n+2}\\right)^n$。",
            "expectedAnswer": "设 $a_n=((2n+1)/(3n+2))^n$。则 $\\sqrt[n]{a_n}=(2n+1)/(3n+2)\\to2/3<1$，故级数收敛。",
            "variant": {
              "questionId": "infinite_series.system_02_geometric_tests.root_method.transfer_v01",
              "relation": "把纯幂结构换成混合因子，检验是否会抓主指数。",
              "stem": "判断 $\\sum_{n=1}^{\\infty} n^5(3/4)^n$，要求用根值思路。",
              "expectedAnswer": "$\\sqrt[n]{n^5(3/4)^n}=n^{5/n}(3/4)\\to3/4<1$，故收敛。多项式因子不改变指数尺度。",
              "masteryEvidence": "能识别 $n^{5/n}\\to1$，不被多项式因子干扰。"
            }
          }
        },
        {
          "id": "infinite_series.system_02_geometric_tests.geometric_proof_boundary",
          "macroId": "infinite_series.system_02_geometric_tests",
          "type": "expression",
          "title": "固定 $k$ 证明桥与边界",
          "description": "能说明从极限到固定 $k<1$ 的尾巴控制，并用 $\\sum1/n$ 与 $\\sum1/n^2$ 解释边界无结论。",
          "training": {
            "goal": "从极限构造固定 $k<1$ 并识别边界。",
            "entryTrigger": "需要解释判别法为什么成立或处理 $\\rho=1$ 时。",
            "masteryCriteria": "能写出极限定义到几何尾巴的控制链。",
            "repairTargetNodeId": "infinite_series.system_02_geometric_tests.geometric_proof_boundary",
            "questionId": "infinite_series.system_02_geometric_tests.geometric_proof_boundary.core_q01",
            "kind": "expression_standard",
            "difficulty": "advanced",
            "targetDimensions": [
              "concept",
              "process",
              "expression"
            ],
            "stem": "设正项级数满足 $\\lim a_{n+1}/a_n=\\rho<1$。说明为何可以得到一个固定的收敛等比尾巴，而不是只说“比值小于1”。",
            "expectedAnswer": "选择常数 $k$ 使 $\\rho<k<1$。由极限定义，存在 $N$，当 $n\\ge N$ 时 $a_{n+1}/a_n\\le k$。迭代得 $a_{N+m}\\le a_Nk^m$，故尾巴被 $a_N\\sum_{m=0}^{\\infty}k^m$ 控制而收敛。",
            "variant": {
              "questionId": "infinite_series.system_02_geometric_tests.geometric_proof_boundary.transfer_v01",
              "relation": "迁移到根值法的固定界。",
              "stem": "若 $\\lim\\sqrt[n]{a_n}=\\rho<1$，写出与上题平行的控制链。",
              "expectedAnswer": "选 $\\rho<k<1$。后期 $\\sqrt[n]{a_n}\\le k$，所以 $a_n\\le k^n$，由与收敛等比级数比较得原级数收敛。",
              "masteryEvidence": "能看出比值与根值共享“固定等比尾巴”本质。"
            }
          }
        }
      ]
    },
    {
      "id": "infinite_series.system_03_integral_test",
      "macroNodeId": "infinite_series.system_03_integral_test",
      "title": "积分判别与 $p$ 级数尺度",
      "coreQuestion": "什么时候能把离散级数尾巴转成连续面积尾巴，并用临界尺度判断收敛？",
      "learningOrder": 3,
      "visualPriority": "medium",
      "recommendedDepth": "far",
      "preferredSector": "lower_left",
      "prerequisiteSystemIds": [
        "infinite_series.system_01_foundations"
      ],
      "bossContribution": "提供函数型、对数型正项级数的判敛能力和 $p=1$ 临界意识。",
      "spacingReason": "积分法依赖连续函数条件，必须与只看代数压缩率的比值根值星系保持独立。",
      "sourceEvidence": "材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第7页“积分判别法”; 第4页正项级数方法对照; 第13页最终复盘页",
      "planets": [
        {
          "id": "infinite_series.system_03_integral_test.condition_check",
          "macroId": "infinite_series.system_03_integral_test",
          "type": "trigger",
          "title": "积分判别条件检查",
          "description": "能确认 $a_n=f(n)$ 且 $f$ 后期正、连续、单调递减；常见失败是“看到函数就积分”。",
          "training": {
            "goal": "在积分前验证正、连续、后期递减。",
            "entryTrigger": "正项通项可写成 $f(n)$ 且准备使用积分判别时。",
            "masteryCriteria": "能列全条件，并允许只要求后期成立。",
            "repairTargetNodeId": "infinite_series.system_03_integral_test.condition_check",
            "questionId": "infinite_series.system_03_integral_test.condition_check.core_q01",
            "kind": "condition_transformation",
            "difficulty": "basic",
            "targetDimensions": [
              "trigger",
              "concept",
              "expression"
            ],
            "stem": "准备对 $\\sum_{n=2}^{\\infty}1/(n\\ln n)$ 使用积分判别。请逐项验证使用条件。",
            "expectedAnswer": "取 $f(x)=1/(x\\ln x)$。在 $x\\ge2$ 上，$f(x)>0$、连续；分母 $x\\ln x$ 严格增大，所以 $f$ 单调递减。因此可用积分判别。",
            "variant": {
              "questionId": "infinite_series.system_03_integral_test.condition_check.transfer_v01",
              "relation": "将递减性改为只在后期成立。",
              "stem": "若 $f$ 在 $[1,10]$ 上有波动，但在 $[10,\\infty)$ 上正、连续、递减，积分判别能否判断 $\\sum f(n)$？",
              "expectedAnswer": "能。敛散性由尾巴决定；从 $n=10$ 起使用积分判别，前面有限项只改变和的数值。",
              "masteryEvidence": "能把条件理解为尾部条件而非全程苛刻条件。"
            }
          }
        },
        {
          "id": "infinite_series.system_03_integral_test.continuous_tail",
          "macroId": "infinite_series.system_03_integral_test",
          "type": "concept",
          "title": "离散尾巴与面积尾巴",
          "description": "能解释积分判别比较的是尾巴且有限项不改敛散；常见失败是把前几项异常当作方法失效。",
          "training": {
            "goal": "解释有限项不影响敛散及面积比较。",
            "entryTrigger": "函数前段异常或需要改变起始下标时。",
            "masteryCriteria": "能从部分和差一个常数解释有限项不改敛散，并描述矩形与曲线面积控制。",
            "repairTargetNodeId": "infinite_series.system_03_integral_test.continuous_tail",
            "questionId": "infinite_series.system_03_integral_test.continuous_tail.core_q01",
            "kind": "concept_judgement",
            "difficulty": "standard",
            "targetDimensions": [
              "concept",
              "process",
              "expression"
            ],
            "stem": "为什么 $\\sum_{n=1}^{\\infty}f(n)$ 与 $\\sum_{n=100}^{\\infty}f(n)$ 敛散性相同？这与积分判别“只看尾巴”有什么关系？",
            "expectedAnswer": "两者部分和只相差前99项的有限常数。一个尾巴若有有限极限，加减固定常数仍有有限极限；若尾巴无界或不收敛，有限常数也无法修复。因此积分判别只需在后期条件成立。",
            "variant": {
              "questionId": "infinite_series.system_03_integral_test.continuous_tail.transfer_v01",
              "relation": "迁移到修改单个项。",
              "stem": "把一个收敛级数的第100项改成 $10^{100}$，敛散性是否改变？",
              "expectedAnswer": "不改变。部分和从第100项以后整体只平移一个固定差值，仍收敛；和的数值改变。",
              "masteryEvidence": "能区分“敛散性”与“和的具体数值”。"
            }
          }
        },
        {
          "id": "infinite_series.system_03_integral_test.p_series_scale",
          "macroId": "infinite_series.system_03_integral_test",
          "type": "method",
          "title": "$p$级数临界尺度",
          "description": "能以 $p>1$ 收敛、$p\\le1$ 发散作为比较标尺；常见失败是把“比 $1/n$ 小”误当充分条件。",
          "training": {
            "goal": "用 $p$ 级数临界线建立比较尺度。",
            "entryTrigger": "正项尾项近似幂次时。",
            "masteryCriteria": "能准确使用 $p>1$ 与 $p\\le1$，并说明 $p=1$ 是临界。",
            "repairTargetNodeId": "infinite_series.system_03_integral_test.p_series_scale",
            "questionId": "infinite_series.system_03_integral_test.p_series_scale.core_q01",
            "kind": "method_selection",
            "difficulty": "basic",
            "targetDimensions": [
              "method",
              "concept",
              "final_answer"
            ],
            "stem": "判断 $\\sum 1/n^{3/2}$ 与 $\\sum1/\\sqrt n$，并说明不能只说“二者都趋零”。",
            "expectedAnswer": "第一项是 $p=3/2>1$ 的 $p$ 级数，收敛；第二项是 $p=1/2\\le1$，发散。通项趋零只是必要门槛，真正差异是下降指数跨过了 $p=1$ 临界线。",
            "variant": {
              "questionId": "infinite_series.system_03_integral_test.p_series_scale.transfer_v01",
              "relation": "把显式幂次改为极限比较。",
              "stem": "判断 $\\sum (2n+1)/(n^3+1)$。",
              "expectedAnswer": "通项与 $1/n^2$ 极限比较：$[(2n+1)/(n^3+1)]/(1/n^2)\\to2$，故与 $p=2$ 级数同敛，收敛。",
              "masteryEvidence": "能把复杂有理式还原到 $p$ 级数主尺度。"
            }
          }
        },
        {
          "id": "infinite_series.system_03_integral_test.logarithmic_execution",
          "macroId": "infinite_series.system_03_integral_test",
          "type": "calculation",
          "title": "对数型积分执行",
          "description": "能通过换元计算 $\\int dx/[x(\\ln x)^p]$ 并给出边界；常见失败是漏定义域或积分上下限。",
          "training": {
            "goal": "用换元完成对数型积分判别。",
            "entryTrigger": "通项含 $n\\ln n$ 或 $n(\\ln n)^p$。",
            "masteryCriteria": "能令 $t=\\ln x$，计算反常积分并写出端点。",
            "repairTargetNodeId": "infinite_series.system_03_integral_test.logarithmic_execution",
            "questionId": "infinite_series.system_03_integral_test.logarithmic_execution.core_q01",
            "kind": "calculation_execution",
            "difficulty": "standard",
            "targetDimensions": [
              "trigger",
              "transformation",
              "calculation"
            ],
            "stem": "判断 $\\sum_{n=2}^{\\infty}\\dfrac{1}{n(\\ln n)^2}$。",
            "expectedAnswer": "取 $f(x)=1/[x(\\ln x)^2]$，满足积分判别条件。令 $t=\\ln x$，$dt=dx/x$：\n$\\int_2^{\\infty}dx/[x(\\ln x)^2]=\\int_{\\ln2}^{\\infty}t^{-2}dt=1/\\ln2<\\infty$。\n故级数收敛。",
            "variant": {
              "questionId": "infinite_series.system_03_integral_test.logarithmic_execution.transfer_v01",
              "relation": "改变对数幂次跨越临界。",
              "stem": "判断 $\\sum_{n=2}^{\\infty}1/(n\\ln n)$。",
              "expectedAnswer": "换元后反常积分为 $\\int_{\\ln2}^{\\infty}dt/t=\\infty$，故级数发散。",
              "masteryEvidence": "能识别对数层面的新临界 $p=1$。"
            }
          }
        }
      ]
    },
    {
      "id": "infinite_series.system_04_alternating_series",
      "macroNodeId": "infinite_series.system_04_alternating_series",
      "title": "交错抵消与莱布尼茨判别",
      "coreQuestion": "怎样证明正负抵消是稳定的，并在莱布尼茨条件不直接可见时修复通项？",
      "learningOrder": 4,
      "visualPriority": "high",
      "recommendedDepth": "middle",
      "preferredSector": "upper_left",
      "prerequisiteSystemIds": [
        "infinite_series.system_01_foundations"
      ],
      "bossContribution": "提供交错结构识别、单调与趋零条件验证、局部方法失败后的改造能力。",
      "spacingReason": "交错级数靠有序抵消而非绝对大小，需与正项判别星系明显分开。",
      "sourceEvidence": "材料A《16讲 04-05_最高价值复盘材料_蒋俊豪(1)》 > 第8页“交错级数”; 第9页“莱布尼茨失败后的正确路线”; 第10页“主项+误差项”",
      "planets": [
        {
          "id": "infinite_series.system_04_alternating_series.sign_magnitude_split",
          "macroId": "infinite_series.system_04_alternating_series",
          "type": "concept",
          "title": "符号与幅度分离",
          "description": "能把 $(-1)^{n-1}u_n$ 中符号因子与正幅度 $u_n$ 分开；常见失败是对带符号通项检查单调。",
          "training": {
            "goal": "把交错符号和正幅度分开。",
            "entryTrigger": "通项含 $(-1)^n$ 或 $(-1)^{n-1}$ 时。",
            "masteryCriteria": "能明确莱布尼茨检查 $u_n>0$，而非整个带符号项。",
            "repairTargetNodeId": "infinite_series.system_04_alternating_series.sign_magnitude_split",
            "questionId": "infinite_series.system_04_alternating_series.sign_magnitude_split.core_q01",
            "kind": "concept_judgement",
            "difficulty": "basic",
            "targetDimensions": [
              "concept",
              "trigger"
            ],
            "stem": "对级数 $\\sum(-1)^{n-1}(n+1)/n^2$，指出符号因子与幅度 $u_n$，并说明莱布尼茨要检查谁。",
            "expectedAnswer": "符号因子是 $(-1)^{n-1}$，幅度是 $u_n=(n+1)/n^2>0$。莱布尼茨检查 $u_n$ 是否后期单调不增以及 $u_n\\to0$，不检查带符号通项的单调性。",
            "variant": {
              "questionId": "infinite_series.system_04_alternating_series.sign_magnitude_split.transfer_v01",
              "relation": "把交错符号藏在三角函数中。",
              "stem": "说明 $\\sum \\cos(n\\pi)/n$ 如何改写成标准交错形式。",
              "expectedAnswer": "因 $\\cos(n\\pi)=(-1)^n$，级数为 $\\sum(-1)^n/n$，幅度 $u_n=1/n$。",
              "masteryEvidence": "能识别等价符号表示而非只认显式 $(-1)^n$。"
            }
          }
        },
        {
          "id": "infinite_series.system_04_alternating_series.leibniz_trigger",
          "macroId": "infinite_series.system_04_alternating_series",
          "type": "trigger",
          "title": "莱布尼茨条件验证",
          "description": "能验证 $u_n$ 后期单调不增且 $u_n\\to0$；常见失败是只验证其中一个条件。",
          "training": {
            "goal": "验证后期单调和趋零。",
            "entryTrigger": "已分离出 $u_n>0$ 后。",
            "masteryCriteria": "能用代数、导数或比较验证条件并给出收敛结论。",
            "repairTargetNodeId": "infinite_series.system_04_alternating_series.leibniz_trigger",
            "questionId": "infinite_series.system_04_alternating_series.leibniz_trigger.core_q01",
            "kind": "calculation_execution",
            "difficulty": "standard",
            "targetDimensions": [
              "trigger",
              "calculation",
              "final_answer"
            ],
            "stem": "判断 $\\sum_{n=1}^{\\infty}(-1)^{n-1}/\\sqrt n$。",
            "expectedAnswer": "取 $u_n=1/\\sqrt n>0$。它单调递减且 $u_n\\to0$，故由莱布尼茨判别级数收敛。其绝对值级数 $\\sum1/\\sqrt n$ 发散，所以进一步可判为条件收敛。",
            "variant": {
              "questionId": "infinite_series.system_04_alternating_series.leibniz_trigger.transfer_v01",
              "relation": "让通项门槛直接失败。",
              "stem": "判断 $\\sum(-1)^n n/(n+1)$。",
              "expectedAnswer": "幅度 $u_n=n/(n+1)\\to1\\ne0$，通项不趋零，级数发散；无需检查单调性。",
              "masteryEvidence": "能优先使用必要门槛而不是机械完成全部条件。"
            }
          }
        },
        {
          "id": "infinite_series.system_04_alternating_series.partial_sum_proof",
          "macroId": "infinite_series.system_04_alternating_series",
          "type": "expression",
          "title": "奇偶部分和夹逼",
          "description": "能用偶数部分和递增、奇数部分和递减且距离趋零解释收敛；常见失败是只背定理结论。",
          "training": {
            "goal": "用奇偶部分和解释莱布尼茨收敛。",
            "entryTrigger": "要求说明定理机制或证明时。",
            "masteryCriteria": "能写两列单调有界及距离 $u_{2n+1}$ 或相邻项趋零。",
            "repairTargetNodeId": "infinite_series.system_04_alternating_series.partial_sum_proof",
            "questionId": "infinite_series.system_04_alternating_series.partial_sum_proof.core_q01",
            "kind": "expression_standard",
            "difficulty": "advanced",
            "targetDimensions": [
              "concept",
              "process",
              "expression"
            ],
            "stem": "设 $u_n$ 单调不增且趋于0。用部分和说明 $\\sum(-1)^{n-1}u_n$ 为什么收敛。",
            "expectedAnswer": "偶数部分和 $S_{2m}=(u_1-u_2)+\\cdots+(u_{2m-1}-u_{2m})$ 单调递增，并且 $S_{2m}\\le u_1$，故收敛。奇数部分和 $S_{2m+1}=S_{2m}+u_{2m+1}$，而 $u_{2m+1}\\to0$，所以奇偶两列趋于同一极限，整个部分和序列收敛。",
            "variant": {
              "questionId": "infinite_series.system_04_alternating_series.partial_sum_proof.transfer_v01",
              "relation": "要求解释单调条件的作用而非重复证明。",
              "stem": "若 $u_n\\to0$ 但忽大忽小，为什么上面的证明链可能断？",
              "expectedAnswer": "成对差 $u_{2k-1}-u_{2k}$ 可能不再非负，偶数部分和不保证单调；奇偶两列也不一定从两侧稳定夹逼。趋零仍是必要的，但该证明与莱布尼茨条件不再可直接使用。",
              "masteryEvidence": "能定位单调条件具体控制的证明环节。"
            }
          }
        },
        {
          "id": "infinite_series.system_04_alternating_series.failure_repair",
          "macroId": "infinite_series.system_04_alternating_series",
          "type": "transformation",
          "title": "莱布尼茨失败后的修复",
          "description": "能区分方法失败与级数失败，并通过导数证明后期单调或拆成主项加绝对收敛误差；常见失败是直接判发散。",
          "training": {
            "goal": "在单调性不明显时改造通项。",
            "entryTrigger": "莱布尼茨条件难验证或通项含有界扰动时。",
            "masteryCriteria": "能选择后期导数、主项加误差、绝对收敛或分组，而不直接判发散。",
            "repairTargetNodeId": "infinite_series.system_04_alternating_series.failure_repair",
            "questionId": "infinite_series.system_04_alternating_series.failure_repair.core_q01",
            "kind": "condition_transformation",
            "difficulty": "advanced",
            "targetDimensions": [
              "transformation",
              "method",
              "migration"
            ],
            "stem": "判断 $\\sum_{n=2}^{\\infty}(-1)^{n-1}/(n+\\sin n)$ 的敛散性。要求不把“单调性不明显”当作发散。",
            "expectedAnswer": "利用\n$1/(n+\\sin n)=1/n-\\sin n/[n(n+\\sin n)]$。\n原级数等于交错调和级数减去误差级数。第一部分收敛；对 $n\\ge2$，误差绝对值不超过 $1/[n(n-1)]$，故绝对收敛。因此原级数收敛。其绝对值级数与 $\\sum1/n$ 极限比较同敛而发散，所以原级数条件收敛。",
            "variant": {
              "questionId": "infinite_series.system_04_alternating_series.failure_repair.transfer_v01",
              "relation": "将有界扰动改为根号扰动，检验有理化策略。",
              "stem": "面对含 $1/(\\sqrt n+(-1)^n)$ 的级数，说明第一步应如何把分母改造成可比较尺度。",
              "expectedAnswer": "应乘共轭有理化：$1/(\\sqrt n+(-1)^n)=(\\sqrt n-(-1)^n)/(n-1)$，再按 $1/\\sqrt n$ 主尺度与更小误差分析；不能拆分母倒数。",
              "masteryEvidence": "能迁移“合法改造而非乱拆分母”的原则。"
            }
          }
        }
      ]
    },
    {
      "id": "infinite_series.system_05_arbitrary_terms",
      "macroNodeId": "infinite_series.system_05_arbitrary_terms",
      "title": "任意项级数的绝对收敛、条件收敛与结构拆解",
      "coreQuestion": "符号与大小混合时，如何判断收敛依赖绝对大小还是正负抵消，并安全改造怪式子？",
      "learningOrder": 5,
      "visualPriority": "high",
      "recommendedDepth": "middle",
      "preferredSector": "left",
      "prerequisiteSystemIds": [
        "infinite_series.system_01_foundations",
        "infinite_series.system_04_alternating_series"
      ],
      "bossContribution": "提供绝对与条件收敛分类、正负账本根因诊断、结构拆解与反例防错。",
      "spacingReason": "该星系承接交错抵消但范围更广，应独立呈现账本模型与操作安全边界。",
      "sourceEvidence": "材料B《16讲 06_任意项级数_高价值笔记_智慧版》 > 第3页“为什么看绝对值”; 第4-5页“正负账本与绝对/条件收敛”; 第6-9页例题、操作与反例",
      "planets": [
        {
          "id": "infinite_series.system_05_arbitrary_terms.absolute_entry",
          "macroId": "infinite_series.system_05_arbitrary_terms",
          "type": "concept",
          "title": "绝对值入口与蕴含证明",
          "description": "能证明 $\\sum\\lvert u_n\\rvert$ 收敛推出 $\\sum u_n$ 收敛，而不是误用 $u_n\\le\\lvert u_n\\rvert$。",
          "training": {
            "goal": "证明绝对收敛推出原级数收敛。",
            "entryTrigger": "任意项级数准备通过绝对值回到正项世界时。",
            "masteryCriteria": "能构造 $\\lvert u_n\\rvert+u_n$ 并用比较法完成证明。",
            "repairTargetNodeId": "infinite_series.system_05_arbitrary_terms.absolute_entry",
            "questionId": "infinite_series.system_05_arbitrary_terms.absolute_entry.core_q01",
            "kind": "expression_standard",
            "difficulty": "advanced",
            "targetDimensions": [
              "concept",
              "process",
              "expression"
            ],
            "stem": "证明：若 $\\sum\\lvert u_n\\rvert$ 收敛，则 $\\sum u_n$ 收敛。不得只写 $u_n\\le\\lvert u_n\\rvert$。",
            "expectedAnswer": "有 $0\\le\\lvert u_n\\rvert+u_n\\le2\\lvert u_n\\rvert$。由比较判别法，$\\sum(\\lvert u_n\\rvert+u_n)$ 收敛。又\n$u_n=(\\lvert u_n\\rvert+u_n)-\\lvert u_n\\rvert$，所以 $\\sum u_n$ 是两个收敛级数之差，故收敛。",
            "variant": {
              "questionId": "infinite_series.system_05_arbitrary_terms.absolute_entry.transfer_v01",
              "relation": "迁移到正部和负部构造。",
              "stem": "用 $p_n=(\\lvert u_n\\rvert+u_n)/2$、$q_n=(\\lvert u_n\\rvert-u_n)/2$ 给出另一种证明思路。",
              "expectedAnswer": "$0\\le p_n,q_n\\le\\lvert u_n\\rvert$，故两级数均收敛；又 $u_n=p_n-q_n$，所以原级数收敛。",
              "masteryEvidence": "能用账本模型复现同一定理而非背单一路径。"
            }
          }
        },
        {
          "id": "infinite_series.system_05_arbitrary_terms.ledger_model",
          "macroId": "infinite_series.system_05_arbitrary_terms",
          "type": "concept",
          "title": "正负账本模型",
          "description": "能构造 $p_n=(\\lvert u_n\\rvert+u_n)/2$、$q_n=(\\lvert u_n\\rvert-u_n)/2$ 并解释差与和。",
          "training": {
            "goal": "理解正负账本及条件收敛根因。",
            "entryTrigger": "需要解释绝对/条件收敛的底层结构时。",
            "masteryCriteria": "能说明原级数是差、绝对值级数是和，并证明条件收敛时两本账都发散。",
            "repairTargetNodeId": "infinite_series.system_05_arbitrary_terms.ledger_model",
            "questionId": "infinite_series.system_05_arbitrary_terms.ledger_model.core_q01",
            "kind": "concept_judgement",
            "difficulty": "advanced",
            "targetDimensions": [
              "concept",
              "process",
              "expression"
            ],
            "stem": "设 $p_n=(\\lvert u_n\\rvert+u_n)/2$、$q_n=(\\lvert u_n\\rvert-u_n)/2$。写出它们的含义，并证明若 $\\sum u_n$ 条件收敛，则 $\\sum p_n$ 与 $\\sum q_n$ 都发散。",
            "expectedAnswer": "$p_n$ 记录正项，$q_n$ 记录负项的绝对大小；$u_n=p_n-q_n$，$\\lvert u_n\\rvert=p_n+q_n$。若假设 $\\sum p_n$ 收敛，由 $q_n=p_n-u_n$ 且 $\\sum u_n$ 收敛可得 $\\sum q_n$ 也收敛，进而 $\\sum\\lvert u_n\\rvert$ 收敛，与条件收敛矛盾。因此两者都发散。",
            "variant": {
              "questionId": "infinite_series.system_05_arbitrary_terms.ledger_model.transfer_v01",
              "relation": "用具体交错调和级数解释账本。",
              "stem": "对 $u_n=(-1)^{n-1}/n$，说明正账本和负账本分别是什么量级。",
              "expectedAnswer": "正账本收集奇数倒数，负账本收集偶数倒数的绝对值；两者都像调和级数的一半而发散，但交错差值收敛。",
              "masteryEvidence": "能把抽象账本映射到具体项。"
            }
          }
        },
        {
          "id": "infinite_series.system_05_arbitrary_terms.convergence_classification",
          "macroId": "infinite_series.system_05_arbitrary_terms",
          "type": "method",
          "title": "绝对与条件收敛分类",
          "description": "能先判绝对值级数，再结合原级数区分绝对收敛、条件收敛或发散；常见失败是绝对值发散便判原级数发散。",
          "training": {
            "goal": "完成绝对、条件或发散的三分分类。",
            "entryTrigger": "任意项或交错级数需要最终分类时。",
            "masteryCriteria": "能先判原级数，再判绝对值级数，且不从绝对值发散直接推原级数发散。",
            "repairTargetNodeId": "infinite_series.system_05_arbitrary_terms.convergence_classification",
            "questionId": "infinite_series.system_05_arbitrary_terms.convergence_classification.core_q01",
            "kind": "method_selection",
            "difficulty": "standard",
            "targetDimensions": [
              "trigger",
              "method",
              "final_answer"
            ],
            "stem": "分类 $\\sum_{n=1}^{\\infty}(-1)^{n-1}/n^2$ 与 $\\sum_{n=1}^{\\infty}(-1)^{n-1}/n$。",
            "expectedAnswer": "第一项的绝对值级数 $\\sum1/n^2$ 收敛，所以绝对收敛。第二项由莱布尼茨收敛，但绝对值级数 $\\sum1/n$ 发散，所以条件收敛。",
            "variant": {
              "questionId": "infinite_series.system_05_arbitrary_terms.convergence_classification.transfer_v01",
              "relation": "加入原级数自身发散的第三类。",
              "stem": "分类 $\\sum(-1)^n$。",
              "expectedAnswer": "通项不趋零，原级数发散；无需讨论绝对或条件收敛。",
              "masteryEvidence": "能把三分分类与通项门槛连起来。"
            }
          }
        },
        {
          "id": "infinite_series.system_05_arbitrary_terms.structure_decomposition",
          "macroId": "infinite_series.system_05_arbitrary_terms",
          "type": "transformation",
          "title": "怪式子拆回已知结构",
          "description": "能利用奇偶拆项、有界因子、尾项尺度或题设乘积结构，把目标级数压回已知收敛对象。",
          "training": {
            "goal": "把目标拆成题设已知的收敛结构。",
            "entryTrigger": "目标通项由奇偶子列、有界因子或两个已知量乘积组成时。",
            "masteryCriteria": "能找到主结构、写合法恒等变形并给出比较。",
            "repairTargetNodeId": "infinite_series.system_05_arbitrary_terms.structure_decomposition",
            "questionId": "infinite_series.system_05_arbitrary_terms.structure_decomposition.core_q01",
            "kind": "condition_transformation",
            "difficulty": "advanced",
            "targetDimensions": [
              "transformation",
              "method",
              "calculation"
            ],
            "stem": "已知 $\\sum n u_n$ 绝对收敛，$\\sum v_n/n$ 收敛。证明 $\\sum u_nv_n$ 绝对收敛。",
            "expectedAnswer": "因 $\\sum v_n/n$ 收敛，故 $v_n/n\\to0$，于是后期 $\\lvert v_n/n\\rvert\\le1$。写\n$u_nv_n=(nu_n)(v_n/n)$，则后期 $\\lvert u_nv_n\\rvert\\le\\lvert nu_n\\rvert$。由比较法，$\\sum\\lvert u_nv_n\\rvert$ 收敛。",
            "variant": {
              "questionId": "infinite_series.system_05_arbitrary_terms.structure_decomposition.transfer_v01",
              "relation": "迁移到有界振荡乘可求和主项。",
              "stem": "证明 $\\sum(1/\\sqrt n-1/\\sqrt{n+1})\\sin(n+k)$ 绝对收敛。",
              "expectedAnswer": "利用 $\\lvert\\sin(n+k)\\rvert\\le1$，绝对值不超过 $1/\\sqrt n-1/\\sqrt{n+1}$；右侧为望远镜级数并收敛，故原级数绝对收敛。",
              "masteryEvidence": "能识别有界因子不是主角并压到望远镜主项。"
            }
          }
        },
        {
          "id": "infinite_series.system_05_arbitrary_terms.operation_guard",
          "macroId": "infinite_series.system_05_arbitrary_terms",
          "type": "trigger",
          "title": "保留抵消与破坏抵消",
          "description": "能判断分组、尾项平移、取绝对值、平方或改符号是否必然保留收敛，并给出反例。",
          "training": {
            "goal": "判断操作是否保留原抵消结构。",
            "entryTrigger": "选择题给出由已知收敛级数变形得到的新级数时。",
            "masteryCriteria": "能区分线性/分组/尾项平移与取绝对值、平方、改符号，并用反例。",
            "repairTargetNodeId": "infinite_series.system_05_arbitrary_terms.operation_guard",
            "questionId": "infinite_series.system_05_arbitrary_terms.operation_guard.core_q01",
            "kind": "confusion_compare",
            "difficulty": "advanced",
            "targetDimensions": [
              "trigger",
              "concept",
              "migration"
            ],
            "stem": "已知 $\\sum u_n$ 收敛。判断下列结论是否必然成立：\nA. $\\sum(u_{2n-1}+u_{2n})$；\nB. $\\sum(u_{2n-1}-u_{2n})$；\nC. $\\sum(u_n+u_{n+1})$；\nD. $\\sum\\lvert u_n\\rvert$。",
            "expectedAnswer": "A必然：只是相邻分组，不改项序与符号。B不必然：可能翻转偶数项符号，例如交错调和变成正项调和型。C必然：等于原级数与尾项平移之和。D不必然：条件收敛级数给出反例。",
            "variant": {
              "questionId": "infinite_series.system_05_arbitrary_terms.operation_guard.transfer_v01",
              "relation": "加入平方操作检验反例构造。",
              "stem": "已知 $\\sum u_n$ 收敛，$\\sum u_n^2$ 是否必然收敛？",
              "expectedAnswer": "不必然。取 $u_n=(-1)^{n-1}/\\sqrt n$，原级数由莱布尼茨收敛，但 $u_n^2=1/n$，平方级数发散。",
              "masteryEvidence": "能主动构造“消符号后暴露调和尺度”的反例。"
            }
          }
        }
      ]
    },
    {
      "id": "infinite_series.system_06_power_domain",
      "macroNodeId": "infinite_series.system_06_power_domain",
      "title": "函数项级数与幂级数收敛域",
      "coreQuestion": "怎样把函数项级数逐点落地，并将幂级数的无穷多个点压缩成中心、半径和端点问题？",
      "learningOrder": 6,
      "visualPriority": "high",
      "recommendedDepth": "middle",
      "preferredSector": "lower_left",
      "prerequisiteSystemIds": [
        "infinite_series.system_02_geometric_tests",
        "infinite_series.system_03_integral_test",
        "infinite_series.system_05_arbitrary_terms"
      ],
      "bossContribution": "提供逐点判敛、收敛半径计算、阿贝尔内部外部结构和端点单独验收。",
      "spacingReason": "这是从数项级数进入函数级数的结构跃迁，应与前五个数项星系留出明显层级间隔。",
      "sourceEvidence": "材料C《16讲 07-08幂级数及其收敛域_高价值学习笔记》 > 第2-5页“逐点落地、中心半径、阿贝尔”; 第6-12页“半径、端点、缺项、一般函数项与变形”",
      "planets": [
        {
          "id": "infinite_series.system_06_power_domain.pointwise_grounding",
          "macroId": "infinite_series.system_06_power_domain",
          "type": "concept",
          "title": "固定 $x$ 的逐点落地",
          "description": "能区分第 $n$ 项函数 $u_n(x)$、函数项级数及收敛点集合；常见失败是把一项当整个无穷和。",
          "training": {
            "goal": "把函数项级数固定为数项级数再判。",
            "entryTrigger": "面对 $\\sum u_n(x)$ 或含参数的无穷级数时。",
            "masteryCriteria": "能区分第n项、整个级数、收敛点与收敛域。",
            "repairTargetNodeId": "infinite_series.system_06_power_domain.pointwise_grounding",
            "questionId": "infinite_series.system_06_power_domain.pointwise_grounding.core_q01",
            "kind": "concept_judgement",
            "difficulty": "basic",
            "targetDimensions": [
              "concept",
              "trigger",
              "expression"
            ],
            "stem": "解释 $u_n(x)$、$\\sum u_n(x)$、收敛点和收敛域的区别，并说明为什么要先固定 $x=x_0$。",
            "expectedAnswer": "$u_n(x)$ 只是第 $n$ 项函数；$\\sum u_n(x)$ 是函数项级数。若固定 $x=x_0$ 后数项级数 $\\sum u_n(x_0)$ 收敛，则 $x_0$ 是收敛点；所有收敛点组成收敛域。固定 $x$ 后才能调用数项级数判别法。",
            "variant": {
              "questionId": "infinite_series.system_06_power_domain.pointwise_grounding.transfer_v01",
              "relation": "用具体函数项级数求一个点。",
              "stem": "对 $\\sum_{n=1}^{\\infty}x^n/n$，判断 $x=1/2$ 是否为收敛点。",
              "expectedAnswer": "代入后为 $\\sum(1/2)^n/n$，可与收敛几何级数 $\\sum(1/2)^n$ 比较，故收敛；$1/2$ 是收敛点。",
              "masteryEvidence": "能把抽象定义落到一次具体代入。"
            }
          }
        },
        {
          "id": "infinite_series.system_06_power_domain.center_radius",
          "macroId": "infinite_series.system_06_power_domain",
          "type": "concept",
          "title": "中心、距离与阿贝尔结构",
          "description": "能解释收敛由 $\\lvert x-x_0\\rvert$ 控制，内部绝对收敛、外部发散而端点另判。",
          "training": {
            "goal": "理解幂级数的中心距离结构与阿贝尔分区。",
            "entryTrigger": "确认对象是 $\\sum a_n(x-x_0)^n$ 后。",
            "masteryCriteria": "能解释半径是距离，内部绝对收敛、外部发散、端点另判。",
            "repairTargetNodeId": "infinite_series.system_06_power_domain.center_radius",
            "questionId": "infinite_series.system_06_power_domain.center_radius.core_q01",
            "kind": "concept_judgement",
            "difficulty": "standard",
            "targetDimensions": [
              "concept",
              "expression"
            ],
            "stem": "对幂级数 $\\sum a_n(x-3)^n$，说明“中心3、收敛半径R”各是什么意思，并写出内部、外部和端点三类。",
            "expectedAnswer": "中心是 $x_0=3$，半径 $R$ 是允许 $x$ 离中心的距离阈值。$\\lvert x-3\\rvert<R$ 时绝对收敛；$\\lvert x-3\\rvert>R$ 时发散；$x=3\\pm R$ 必须分别代回原级数判断。",
            "variant": {
              "questionId": "infinite_series.system_06_power_domain.center_radius.transfer_v01",
              "relation": "迁移到中心平移。",
              "stem": "若 $\\sum a_nx^n$ 半径为2，则 $\\sum a_n(x+5)^n$ 的中心和内部区间是什么？",
              "expectedAnswer": "中心为 $-5$，半径仍为2，内部区间为 $(-7,-3)$；端点仍需另判。",
              "masteryEvidence": "能把“距离结构”迁移到平移而非重算系数。"
            }
          }
        },
        {
          "id": "infinite_series.system_06_power_domain.radius_execution",
          "macroId": "infinite_series.system_06_power_domain",
          "type": "calculation",
          "title": "收敛半径计算",
          "description": "能对标准幂级数用系数比，也能对整个通项直接做比值或根值并解不等式。",
          "training": {
            "goal": "计算标准与一般形式的收敛半径。",
            "entryTrigger": "需要求幂级数主体收敛区间时。",
            "masteryCriteria": "能先对整个通项做比值根值并解小于1，而非口号式“令x小于1”。",
            "repairTargetNodeId": "infinite_series.system_06_power_domain.radius_execution",
            "questionId": "infinite_series.system_06_power_domain.radius_execution.core_q01",
            "kind": "calculation_execution",
            "difficulty": "standard",
            "targetDimensions": [
              "method",
              "calculation",
              "expression"
            ],
            "stem": "求 $\\sum_{n=1}^{\\infty}\\dfrac{n}{3^n}(x-2)^n$ 的收敛半径与内部区间。",
            "expectedAnswer": "通项绝对比值为\n$\\dfrac{n+1}{n}\\dfrac{\\lvert x-2\\rvert}{3}\\to\\lvert x-2\\rvert/3$。\n令比值极限小于1，得 $\\lvert x-2\\rvert<3$，所以 $R=3$，内部区间 $(-1,5)$。端点另判。",
            "variant": {
              "questionId": "infinite_series.system_06_power_domain.radius_execution.transfer_v01",
              "relation": "改成根值更自然的系数。",
              "stem": "求 $\\sum_{n=1}^{\\infty}((n+1)/(2n+1))^n(x+1)^n$ 的半径。",
              "expectedAnswer": "根值为 $[(n+1)/(2n+1)]\\lvert x+1\\rvert\\to\\lvert x+1\\rvert/2$，故内部 $\\lvert x+1\\rvert<2$，$R=2$。",
              "masteryEvidence": "能根据整体n次幂切换根值法。"
            }
          }
        },
        {
          "id": "infinite_series.system_06_power_domain.endpoint_judgement",
          "macroId": "infinite_series.system_06_power_domain",
          "type": "method",
          "title": "端点代回与收敛域合并",
          "description": "能把两个端点分别代回原数项级数判别，再用正确开闭端点写收敛域。",
          "training": {
            "goal": "分别代回端点并合并开闭区间。",
            "entryTrigger": "已得到 $\\lvert x-x_0\\rvert<R$ 后。",
            "masteryCriteria": "能在每个端点生成数项级数、判敛散并写最终收敛域。",
            "repairTargetNodeId": "infinite_series.system_06_power_domain.endpoint_judgement",
            "questionId": "infinite_series.system_06_power_domain.endpoint_judgement.core_q01",
            "kind": "calculation_execution",
            "difficulty": "standard",
            "targetDimensions": [
              "method",
              "calculation",
              "final_answer"
            ],
            "stem": "求 $\\sum_{n=1}^{\\infty}x^n/n$ 的收敛域。",
            "expectedAnswer": "比值法给 $\\lvert x\\rvert<1$。端点 $x=1$ 时为调和级数，发散；$x=-1$ 时为交错调和级数，收敛。因此收敛域为 $[-1,1)$。",
            "variant": {
              "questionId": "infinite_series.system_06_power_domain.endpoint_judgement.transfer_v01",
              "relation": "改变端点行为而半径不变。",
              "stem": "求 $\\sum_{n=1}^{\\infty}x^n/n^2$ 的收敛域。",
              "expectedAnswer": "半径仍为1。$x=1$ 时 $\\sum1/n^2$ 收敛；$x=-1$ 时绝对收敛。因此收敛域为 $[-1,1]$。",
              "masteryEvidence": "能理解半径相同不代表端点相同。"
            }
          }
        },
        {
          "id": "infinite_series.system_06_power_domain.nonstandard_transform",
          "macroId": "infinite_series.system_06_power_domain",
          "type": "transformation",
          "title": "缺项、一般函数项与操作变形",
          "description": "能处理 $x^{2n}$、中心平移、逐项求导积分及非幂函数项级数，并区分半径继承与端点变化。",
          "training": {
            "goal": "处理缺项、一般函数项及求导积分后的端点。",
            "entryTrigger": "幂次不是n、对象非幂级数或级数被求导积分时。",
            "masteryCriteria": "能对整个通项判别，继承半径但重新检查端点。",
            "repairTargetNodeId": "infinite_series.system_06_power_domain.nonstandard_transform",
            "questionId": "infinite_series.system_06_power_domain.nonstandard_transform.core_q01",
            "kind": "condition_transformation",
            "difficulty": "advanced",
            "targetDimensions": [
              "transformation",
              "method",
              "migration"
            ],
            "stem": "求 $\\sum_{n=1}^{\\infty}x^{2n}/n$ 的收敛域，并说明为什么不能把端点符号想当然。",
            "expectedAnswer": "把 $y=x^2$，主体要求 $\\lvert x^2\\rvert<1$，即 $\\lvert x\\rvert<1$。当 $x=1$ 或 $x=-1$ 时，$x^{2n}=1$，两端都变成 $\\sum1/n$，均发散。因此收敛域为 $(-1,1)$。",
            "variant": {
              "questionId": "infinite_series.system_06_power_domain.nonstandard_transform.transfer_v01",
              "relation": "从缺项迁移到非幂函数项级数。",
              "stem": "求 $\\sum_{n=1}^{\\infty}e^{-nx}$ 的收敛域，并说明是否存在收敛半径。",
              "expectedAnswer": "固定x后是公比 $e^{-x}$ 的几何级数。收敛需 $e^{-x}<1$，即 $x>0$。它不是幂级数，因此只有收敛域 $(0,\\infty)$，不定义“中心+半径”。",
              "masteryEvidence": "能处理一般函数项级数而不滥用半径语言。"
            }
          }
        }
      ]
    },
    {
      "id": "infinite_series.system_07_sum_basics",
      "macroNodeId": "infinite_series.system_07_sum_basics",
      "title": "幂级数求和函数的基础转换工具",
      "coreQuestion": "怎样把陌生幂级数整理成已知基础函数，并始终保留原级数的有效定义域？",
      "learningOrder": 7,
      "visualPriority": "high",
      "recommendedDepth": "near",
      "preferredSector": "upper",
      "prerequisiteSystemIds": [
        "infinite_series.system_06_power_domain"
      ],
      "bossContribution": "提供定义域优先、下标次数对齐、已知展开识别、逐项微积分与柯西乘积能力。",
      "spacingReason": "该星系是“判敛散”到“求具体和”的升级，应靠近Boss但与高级构造保持独立。",
      "sourceEvidence": "材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第2页“和函数=表达式+收敛域”; 第3-6页“变形、柯西乘积、展开式、先导后积与先积后导”",
      "planets": [
        {
          "id": "infinite_series.system_07_sum_basics.domain_first",
          "macroId": "infinite_series.system_07_sum_basics",
          "type": "concept",
          "title": "和函数定义域优先",
          "description": "能把和函数写成“表达式加收敛域”，并拒绝用化简后函数的自然定义域替代原级数收敛域。",
          "training": {
            "goal": "把和函数写成表达式与原级数收敛域的组合。",
            "entryTrigger": "题目要求幂级数和函数或用基础展开式时。",
            "masteryCriteria": "能先求或继承原级数收敛域，并拒绝用化简式自然定义域替代。",
            "repairTargetNodeId": "infinite_series.system_07_sum_basics.domain_first",
            "questionId": "infinite_series.system_07_sum_basics.domain_first.core_q01",
            "kind": "expression_standard",
            "difficulty": "basic",
            "targetDimensions": [
              "concept",
              "expression",
              "final_answer"
            ],
            "stem": "写出几何级数 $\\sum_{n=0}^{\\infty}x^n$ 的和函数，并解释为什么不能只写 $1/(1-x)$ 或条件 $x\\ne1$。",
            "expectedAnswer": "$S(x)=1/(1-x)$，但只在原级数收敛域 $\\lvert x\\rvert<1$ 成立。$x=2$ 时右侧有值而原级数发散，说明化简式的自然定义域不是和函数定义域。",
            "variant": {
              "questionId": "infinite_series.system_07_sum_basics.domain_first.transfer_v01",
              "relation": "把基础式替换变量并追踪定义域。",
              "stem": "求 $\\sum_{n=0}^{\\infty}(2x-1)^n$ 的和函数。",
              "expectedAnswer": "当 $\\lvert2x-1\\rvert<1$，即 $0<x<1$ 时，和为 $1/[1-(2x-1)]=1/[2(1-x)]$。",
              "masteryEvidence": "能同步变换表达式与收敛域。"
            }
          }
        },
        {
          "id": "infinite_series.system_07_sum_basics.index_alignment",
          "macroId": "infinite_series.system_07_sum_basics",
          "type": "transformation",
          "title": "下标与次数对齐",
          "description": "能区分换编号、拆前项、提出 $x$ 的幂，并在合并前确认下标起点和次数一致。",
          "training": {
            "goal": "在合并前统一下标起点和幂次。",
            "entryTrigger": "多个级数需要相加、相减、求导积分或套原型时。",
            "masteryCriteria": "能说明每次变形是换编号、拆前项还是提出幂，并验证项未改变。",
            "repairTargetNodeId": "infinite_series.system_07_sum_basics.index_alignment",
            "questionId": "infinite_series.system_07_sum_basics.index_alignment.core_q01",
            "kind": "condition_transformation",
            "difficulty": "standard",
            "targetDimensions": [
              "transformation",
              "process",
              "expression"
            ],
            "stem": "把 $\\sum_{n=1}^{\\infty}a_{n-1}x^{n-1}$ 改写成从 $n=0$ 开始的形式，并说明为什么这是换编号而非删项。",
            "expectedAnswer": "令 $m=n-1$，当 $n=1$ 时 $m=0$，故级数为 $\\sum_{m=0}^{\\infty}a_mx^m$。每个原项一一对应，只改变编号，没有删项或增项。",
            "variant": {
              "questionId": "infinite_series.system_07_sum_basics.index_alignment.transfer_v01",
              "relation": "检验拆前项与提出幂的组合。",
              "stem": "将 $\\sum_{n=0}^{\\infty}a_nx^{n+1}$ 与 $a_0+\\sum_{n=1}^{\\infty}a_nx^n$ 分别整理。",
              "expectedAnswer": "第一式为 $x\\sum_{n=0}^{\\infty}a_nx^n$；第二式正好等于 $\\sum_{n=0}^{\\infty}a_nx^n$。前者提出幂，后者把缺失的第0项补回。",
              "masteryEvidence": "能区分“通项次数变形”与“下标起点补项”。"
            }
          }
        },
        {
          "id": "infinite_series.system_07_sum_basics.known_expansion",
          "macroId": "infinite_series.system_07_sum_basics",
          "type": "trigger",
          "title": "基础展开式反向识别",
          "description": "能从 $1/n$、$n$、$n!$、交错符号或奇数次幂识别对数、导数型、指数或反三角原型。",
          "training": {
            "goal": "根据系数障碍反向识别基础展开。",
            "entryTrigger": "通项出现 $1/n$、$n$、$n!$、交错或奇数次幂时。",
            "masteryCriteria": "能指出由几何级数经过何种替换、求导或积分得到目标。",
            "repairTargetNodeId": "infinite_series.system_07_sum_basics.known_expansion",
            "questionId": "infinite_series.system_07_sum_basics.known_expansion.core_q01",
            "kind": "method_selection",
            "difficulty": "standard",
            "targetDimensions": [
              "trigger",
              "method",
              "migration"
            ],
            "stem": "求 $\\sum_{n=1}^{\\infty}(-1)^{n-1}x^n/n$ 的和函数及内部收敛区间。",
            "expectedAnswer": "由 $-\\ln(1-t)=\\sum t^n/n$，令 $t=-x$ 或直接对几何级数积分，得到\n$\\sum_{n=1}^{\\infty}(-1)^{n-1}x^n/n=\\ln(1+x)$，内部 $\\lvert x\\rvert<1$；端点需另判。",
            "variant": {
              "questionId": "infinite_series.system_07_sum_basics.known_expansion.transfer_v01",
              "relation": "换成阶乘结构。",
              "stem": "求 $\\sum_{n=0}^{\\infty}x^n/n!$。",
              "expectedAnswer": "这是 $e^x$ 的泰勒展开，对所有实数 $x$ 收敛，和函数为 $e^x$。",
              "masteryEvidence": "能从系数结构切换到另一基础模型。"
            }
          }
        },
        {
          "id": "infinite_series.system_07_sum_basics.calculus_transform",
          "macroId": "infinite_series.system_07_sum_basics",
          "type": "method",
          "title": "逐项求导积分消障碍",
          "description": "能根据 $n$ 在分子或分母选择求导或积分，并用 $S(0)$ 恢复常数及保留收敛域。",
          "training": {
            "goal": "通过求导或积分消除系数n，并恢复常数。",
            "entryTrigger": "分母或分子含 $n$，直接原型不明显时。",
            "masteryCriteria": "能说明选择原因、逐项运算、$S(0)$ 与收敛域。",
            "repairTargetNodeId": "infinite_series.system_07_sum_basics.calculus_transform",
            "questionId": "infinite_series.system_07_sum_basics.calculus_transform.core_q01",
            "kind": "calculation_execution",
            "difficulty": "standard",
            "targetDimensions": [
              "method",
              "transformation",
              "calculation",
              "expression"
            ],
            "stem": "从几何级数出发求 $S(x)=\\sum_{n=1}^{\\infty}x^n/n$。必须说明为什么求导后还要积分以及 $S(0)$ 的作用。",
            "expectedAnswer": "求导得 $S'(x)=\\sum_{n=1}^{\\infty}x^{n-1}=1/(1-x)$，$\\lvert x\\rvert<1$。因此\n$S(x)=S(0)+\\int_0^xdt/(1-t)=-\\ln(1-x)$。这里 $S(0)=0$ 固定了积分常数；收敛域由原级数决定。",
            "variant": {
              "questionId": "infinite_series.system_07_sum_basics.calculus_transform.transfer_v01",
              "relation": "改为分子有n的逆向操作。",
              "stem": "求 $\\sum_{n=1}^{\\infty}nx^n$。",
              "expectedAnswer": "由 $\\sum_{n=0}^{\\infty}x^n=1/(1-x)$ 求导得 $\\sum_{n=1}^{\\infty}nx^{n-1}=1/(1-x)^2$，再乘x：$\\sum nx^n=x/(1-x)^2$，$\\lvert x\\rvert<1$。",
              "masteryEvidence": "能根据障碍位置决定求导并处理幂次。"
            }
          }
        },
        {
          "id": "infinite_series.system_07_sum_basics.cauchy_product",
          "macroId": "infinite_series.system_07_sum_basics",
          "type": "method",
          "title": "柯西乘积系数卷积",
          "description": "能解释 $x^n$ 系数来自所有次数和为 $n$ 的组合，并在共同绝对收敛区间内使用。",
          "training": {
            "goal": "理解卷积系数并在合法域内相乘。",
            "entryTrigger": "系数形如 $\\sum_{i=0}^na_ib_{n-i}$ 时。",
            "masteryCriteria": "能从次数组合解释系数，而非死背公式；能声明在共同绝对收敛域内。",
            "repairTargetNodeId": "infinite_series.system_07_sum_basics.cauchy_product",
            "questionId": "infinite_series.system_07_sum_basics.cauchy_product.core_q01",
            "kind": "calculation_execution",
            "difficulty": "advanced",
            "targetDimensions": [
              "concept",
              "method",
              "calculation"
            ],
            "stem": "设 $A(x)=\\sum_{n=0}^{\\infty}a_nx^n$，$B(x)=\\sum_{n=0}^{\\infty}b_nx^n$ 在 $\\lvert x\\rvert<R$ 内绝对收敛。写出 $A(x)B(x)$ 中 $x^3$ 的系数并解释来源。",
            "expectedAnswer": "次数和为3的组合是 $(0,3),(1,2),(2,1),(3,0)$，所以系数为 $a_0b_3+a_1b_2+a_2b_1+a_3b_0$。一般系数为 $\\sum_{i=0}^na_ib_{n-i}$。",
            "variant": {
              "questionId": "infinite_series.system_07_sum_basics.cauchy_product.transfer_v01",
              "relation": "用几何级数平方得到可识别系数。",
              "stem": "利用 $(\\sum_{n=0}^{\\infty}x^n)^2$ 求 $\\sum_{n=0}^{\\infty}(n+1)x^n$。",
              "expectedAnswer": "每个 $x^n$ 有 $n+1$ 组次数组合，所以左侧平方为 $\\sum(n+1)x^n$；右侧为 $1/(1-x)^2$，$\\lvert x\\rvert<1$。",
              "masteryEvidence": "能从卷积组合数反向识别系数。"
            }
          }
        }
      ]
    },
    {
      "id": "infinite_series.system_08_sum_advanced",
      "macroNodeId": "infinite_series.system_08_sum_advanced",
      "title": "递推、隐藏系数与构造和函数",
      "coreQuestion": "当系数没有显式公式或原题没有变量时，怎样把隐藏关系升级为函数关系并恢复目标数值？",
      "learningOrder": 8,
      "visualPriority": "high",
      "recommendedDepth": "near",
      "preferredSector": "lower",
      "prerequisiteSystemIds": [
        "infinite_series.system_06_power_domain",
        "infinite_series.system_07_sum_basics"
      ],
      "bossContribution": "提供递推转微分方程、积分系数化简、人工引入变量和特殊点回收的综合转换能力。",
      "spacingReason": "该星系包含高级构造与综合链，应靠近Boss并与基础工具星系保持清晰先后关系。",
      "sourceEvidence": "材料D《16讲 09-10幂级数求和函数0_极高价值复盘笔记_智慧版》 > 第7页“递推转微分方程”; 第8-9页“16.34隐藏系数、点火公式与构造S(x)”; 第10-11页综合地图",
      "planets": [
        {
          "id": "infinite_series.system_08_sum_advanced.recurrence_translation",
          "macroId": "infinite_series.system_08_sum_advanced",
          "type": "transformation",
          "title": "系数递推转函数方程",
          "description": "能把 $a_n$、$na_n$、$(n+1)a_{n+1}$ 的关系翻译为 $S(x)$、$S'(x)$ 的方程，并正确移动下标。",
          "training": {
            "goal": "把系数递推翻译成 $S$ 与 $S'$ 的关系。",
            "entryTrigger": "只给 $a_{n+1}$ 与 $a_n$ 的关系而无显式公式时。",
            "masteryCriteria": "能展开前三项核对下标，并正确识别 $na_nx^{n-1}$ 与导数。",
            "repairTargetNodeId": "infinite_series.system_08_sum_advanced.recurrence_translation",
            "questionId": "infinite_series.system_08_sum_advanced.recurrence_translation.core_q01",
            "kind": "condition_transformation",
            "difficulty": "advanced",
            "targetDimensions": [
              "transformation",
              "process",
              "calculation"
            ],
            "stem": "设 $a_0=1$，$(n+1)a_{n+1}=2a_n$。令 $S(x)=\\sum_{n=0}^{\\infty}a_nx^n$，求 $S$ 满足的微分方程并求 $S(x)$。",
            "expectedAnswer": "两边乘 $x^n$ 并从 $n=0$ 求和：左侧 $\\sum(n+1)a_{n+1}x^n=S'(x)$，右侧 $2\\sum a_nx^n=2S(x)$。故 $S'=2S$，且 $S(0)=a_0=1$，所以 $S(x)=e^{2x}$。",
            "variant": {
              "questionId": "infinite_series.system_08_sum_advanced.recurrence_translation.transfer_v01",
              "relation": "让递推同时出现n与常数项。",
              "stem": "设 $na_n=a_{n-1}$ 对 $n\\ge1$，$a_0=1$。用和函数法求 $S(x)$。",
              "expectedAnswer": "乘 $x^{n-1}$ 求和得 $S'(x)=S(x)$，初值1，所以 $S=e^x$。",
              "masteryEvidence": "能调整乘幂使两边对齐。"
            }
          }
        },
        {
          "id": "infinite_series.system_08_sum_advanced.hidden_coefficient",
          "macroId": "infinite_series.system_08_sum_advanced",
          "type": "method",
          "title": "隐藏积分系数化简",
          "description": "能用三角换元把 $a_n$ 写成相邻积分量之差，再用递推比值消去未知积分。",
          "training": {
            "goal": "通过换元与递推比值消除积分定义系数。",
            "entryTrigger": "系数由一族相邻幂次积分定义时。",
            "masteryCriteria": "能识别目标是求相邻积分比值，而不是逐个算积分。",
            "repairTargetNodeId": "infinite_series.system_08_sum_advanced.hidden_coefficient",
            "questionId": "infinite_series.system_08_sum_advanced.hidden_coefficient.core_q01",
            "kind": "condition_transformation",
            "difficulty": "advanced",
            "targetDimensions": [
              "transformation",
              "method",
              "calculation"
            ],
            "stem": "设 $b_n=\\int_0^{\\pi/2}\\sin^nt\\,dt$，且 $a_n=\\int_0^1x^n\\sqrt{1-x^2}\\,dx$。证明 $a_n/b_n=1/(n+2)$。",
            "expectedAnswer": "令 $x=\\sin t$，则 $dx=\\cos tdt$、$\\sqrt{1-x^2}=\\cos t$，故\n$a_n=\\int_0^{\\pi/2}\\sin^nt\\cos^2t\\,dt=b_n-b_{n+2}$。\n点火递推给 $b_{n+2}=(n+1)b_n/(n+2)$，所以 $a_n/b_n=1-(n+1)/(n+2)=1/(n+2)$。",
            "variant": {
              "questionId": "infinite_series.system_08_sum_advanced.hidden_coefficient.transfer_v01",
              "relation": "将根号结构改写但仍要求相邻积分。",
              "stem": "若积分中出现 $x^n(1-x^2)^{3/2}$，说明三角换元后应优先寻找什么结构。",
              "expectedAnswer": "令 $x=\\sin t$ 后得到 $\\sin^nt\\cos^4t$。应把 $\\cos^4t=(1-\\sin^2t)^2$ 展开为 $b_n-2b_{n+2}+b_{n+4}$，再用相邻递推比值化简。",
              "masteryEvidence": "能把“相邻积分线性组合”迁移到更高次余因子。"
            }
          }
        },
        {
          "id": "infinite_series.system_08_sum_advanced.construct_sum_function",
          "macroId": "infinite_series.system_08_sum_advanced",
          "type": "method",
          "title": "人工构造 $S(x)$",
          "description": "能识别数项级数像某幂级数特殊点值，选择合适幂次引入 $x$，消掉分母后积分还原。",
          "training": {
            "goal": "为特殊点数项和选择幂次并构造 $S(x)$。",
            "entryTrigger": "原题无x但通项含 $1/(n+r)$、交错或像某幂级数在特殊点的值时。",
            "masteryCriteria": "能根据求导后消分母来选择 $x$ 的指数，并写从构造到积分的链。",
            "repairTargetNodeId": "infinite_series.system_08_sum_advanced.construct_sum_function",
            "questionId": "infinite_series.system_08_sum_advanced.construct_sum_function.core_q01",
            "kind": "method_selection",
            "difficulty": "advanced",
            "targetDimensions": [
              "trigger",
              "method",
              "transformation"
            ],
            "stem": "为 $\\sum_{n=1}^{\\infty}(-1)^n/(n+2)$ 构造一个幂级数，使求导能消掉分母，并求其和。",
            "expectedAnswer": "构造 $S(x)=\\sum_{n=1}^{\\infty}(-1)^nx^{n+2}/(n+2)$。则\n$S'(x)=\\sum_{n=1}^{\\infty}(-1)^nx^{n+1}=x\\sum_{n=1}^{\\infty}(-1)^nx^n=-x^2/(1+x)$，$\\lvert x\\rvert<1$。\n由 $S(0)=0$，积分得 $S(x)=x-x^2/2-\\ln(1+x)$。取 $x=1$ 的收敛端点，原和为 $S(1)=1/2-\\ln2$。",
            "variant": {
              "questionId": "infinite_series.system_08_sum_advanced.construct_sum_function.transfer_v01",
              "relation": "改变偏移量。",
              "stem": "为 $\\sum_{n=0}^{\\infty}(-1)^n/(n+3)$ 说明应构造何种 $S(x)$，无需完整积分。",
              "expectedAnswer": "构造 $S(x)=\\sum_{n=0}^{\\infty}(-1)^nx^{n+3}/(n+3)$，则 $S'(x)=x^2/(1+x)$，目标和为 $S(1)$。",
              "masteryEvidence": "能依据分母偏移同步选择幂次。"
            }
          }
        },
        {
          "id": "infinite_series.system_08_sum_advanced.special_value_recovery",
          "macroId": "infinite_series.system_08_sum_advanced",
          "type": "method",
          "title": "特殊点回收目标数值",
          "description": "能在求得 $S(x)$ 后验证端点可代性并代入特殊值，形成完整“化简-构造-求和-回收”链。",
          "training": {
            "goal": "验证特殊点代入并完成综合回收。",
            "entryTrigger": "已求出和函数，需要回到原无变量数项级数时。",
            "masteryCriteria": "能检查特殊点是否在收敛域或端点可收敛，写出最终数值与完整链。",
            "repairTargetNodeId": "infinite_series.system_08_sum_advanced.special_value_recovery",
            "questionId": "infinite_series.system_08_sum_advanced.special_value_recovery.core_q01",
            "kind": "synthesis_decomposition",
            "difficulty": "advanced",
            "targetDimensions": [
              "synthesis",
              "expression",
              "final_answer"
            ],
            "stem": "复述例16.34的完整逻辑链：为什么原题 $\\sum_{n=1}^{\\infty}(-1)^na_n/b_n$ 最终等于 $1/2-\\ln2$？",
            "expectedAnswer": "先由三角换元和点火递推得 $a_n/b_n=1/(n+2)$。原题化为 $\\sum(-1)^n/(n+2)$。构造 $S(x)=\\sum(-1)^nx^{n+2}/(n+2)$，求得 $S(x)=x-x^2/2-\\ln(1+x)$。原级数在 $x=1$ 为收敛端点，因此代入得 $S(1)=1/2-\\ln2$。",
            "variant": {
              "questionId": "infinite_series.system_08_sum_advanced.special_value_recovery.transfer_v01",
              "relation": "改用幂级数内部点而非端点。",
              "stem": "若目标和为 $\\sum_{n=1}^{\\infty}(-1)^n/[2^{n+2}(n+2)]$，如何从同一 $S(x)$ 回收？",
              "expectedAnswer": "它等于 $S(1/2)$，直接代入 $x=1/2$；该点位于 $\\lvert x\\rvert<1$ 内，无需端点额外判别。",
              "masteryEvidence": "能识别不同数项和对应不同特殊点。"
            }
          }
        }
      ]
    },
    {
      "id": "infinite_series.system_09_fourier_representation",
      "macroNodeId": "infinite_series.system_09_fourier_representation",
      "title": "傅里叶表示、系数提取与半区间延拓",
      "coreQuestion": "怎样把周期函数分解为兼容周期的三角波，并利用正交、奇偶与延拓高效得到系数？",
      "learningOrder": 9,
      "visualPriority": "high",
      "recommendedDepth": "near",
      "preferredSector": "upper_left",
      "prerequisiteSystemIds": [
        "infinite_series.system_01_foundations"
      ],
      "bossContribution": "提供周期与频率含义、系数积分提取、奇偶消项和半区间补全能力。",
      "spacingReason": "傅里叶使用三角基底而非幂基底，应与幂级数星系保留视觉断层，同时在应用层与Boss汇合。",
      "sourceEvidence": "材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第2-4页“主线、符号、系数提取”; 第6-8页“奇偶、半区间延拓与公式系统”",
      "planets": [
        {
          "id": "infinite_series.system_09_fourier_representation.period_frequency",
          "macroId": "infinite_series.system_09_fourier_representation",
          "type": "concept",
          "title": "周期、角度与频率",
          "description": "能区分 $2l$、$l$、$2\\pi$、$\\pi/l$ 与 $n$，并解释第 $n$ 个波在长度 $2l$ 内振动 $n$ 次。",
          "training": {
            "goal": "区分横轴周期、内部角度与频率编号。",
            "entryTrigger": "面对周期 $2l$ 的傅里叶公式或更换区间时。",
            "masteryCriteria": "能解释 $\\pi/l$ 的换算和第n波最小周期 $2l/n$。",
            "repairTargetNodeId": "infinite_series.system_09_fourier_representation.period_frequency",
            "questionId": "infinite_series.system_09_fourier_representation.period_frequency.core_q01",
            "kind": "concept_judgement",
            "difficulty": "standard",
            "targetDimensions": [
              "concept",
              "expression"
            ],
            "stem": "周期为 $2l$ 的傅里叶项为何写成 $\\sin(n\\pi x/l)$？解释 $2l,l,2\\pi,\\pi/l,n$ 的不同角色。",
            "expectedAnswer": "$2l$ 是原函数横轴上的完整周期，$l$ 是半周期；$2\\pi$ 是三角角度一圈。$\\pi/l$ 把横轴距离换算成角度：$x$ 增加 $2l$ 时角度增加 $2\\pi$。$n$ 表示在一个总周期内振动n次，第n波最小周期为 $2l/n$。",
            "variant": {
              "questionId": "infinite_series.system_09_fourier_representation.period_frequency.transfer_v01",
              "relation": "代入具体半周期。",
              "stem": "当 $l=\\pi$ 时，为什么三角项化为 $\\sin nx,\\cos nx$？",
              "expectedAnswer": "因 $n\\pi x/l=n\\pi x/\\pi=nx$。此处是换算率简化，不是说原函数周期变成 $\\pi$；完整周期仍为 $2\\pi$。",
              "masteryEvidence": "能在具体公式中保持周期与角度的区分。"
            }
          }
        },
        {
          "id": "infinite_series.system_09_fourier_representation.coefficient_extraction",
          "macroId": "infinite_series.system_09_fourier_representation",
          "type": "method",
          "title": "正交积分提取系数",
          "description": "能写出 $a_0,a_n,b_n$ 并解释“乘对应波再积一个完整周期”是频率检测。",
          "training": {
            "goal": "用正交积分提取对应频率含量。",
            "entryTrigger": "需要计算 $a_n,b_n$ 或解释系数意义时。",
            "masteryCriteria": "能写公式并说明不同频率在完整周期积分抵消。",
            "repairTargetNodeId": "infinite_series.system_09_fourier_representation.coefficient_extraction",
            "questionId": "infinite_series.system_09_fourier_representation.coefficient_extraction.core_q01",
            "kind": "expression_standard",
            "difficulty": "standard",
            "targetDimensions": [
              "concept",
              "method",
              "expression"
            ],
            "stem": "设 $f(x)=3\\cos(\\pi x/l)+2\\sin(2\\pi x/l)$。不用完整积分计算，说明为什么第一余弦系数 $a_1=3$。",
            "expectedAnswer": "计算 $a_1$ 时把f乘 $\\cos(\\pi x/l)$ 并在 $[-l,l]$ 积分。$3\\cos^2(\\pi x/l)$ 留下；$2\\sin(2\\pi x/l)\\cos(\\pi x/l)$ 与目标频率正交，完整周期积分为0。除以l后读出3。",
            "variant": {
              "questionId": "infinite_series.system_09_fourier_representation.coefficient_extraction.transfer_v01",
              "relation": "改成不存在的频率。",
              "stem": "对同一f，解释为什么 $a_3=0$。",
              "expectedAnswer": "原函数没有第三余弦频率；乘 $\\cos(3\\pi x/l)$ 后，所有项都与之正交，完整周期积分为0。",
              "masteryEvidence": "能把零系数解释为“对应频率成分不存在”。"
            }
          }
        },
        {
          "id": "infinite_series.system_09_fourier_representation.parity_simplification",
          "macroId": "infinite_series.system_09_fourier_representation",
          "type": "trigger",
          "title": "奇偶性消系数",
          "description": "能通过奇偶乘积与对称积分判断奇函数只剩正弦、偶函数只剩余弦。",
          "training": {
            "goal": "由奇偶乘积和对称积分消去系数。",
            "entryTrigger": "函数在对称区间已知奇偶性时。",
            "masteryCriteria": "能从乘积奇偶性推导系数为零，而非仅背口诀。",
            "repairTargetNodeId": "infinite_series.system_09_fourier_representation.parity_simplification",
            "questionId": "infinite_series.system_09_fourier_representation.parity_simplification.core_q01",
            "kind": "condition_transformation",
            "difficulty": "standard",
            "targetDimensions": [
              "trigger",
              "concept",
              "expression"
            ],
            "stem": "若 $f$ 是 $[-l,l]$ 上的奇函数，证明其傅里叶级数只含正弦项。",
            "expectedAnswer": "$a_0$ 的被积函数f为奇函数，对称积分为0。对任意n，余弦为偶函数，所以 $f(x)\\cos(n\\pi x/l)$ 为奇函数，对称积分为0，故 $a_n=0$。正弦项可能保留，因此只含正弦项。",
            "variant": {
              "questionId": "infinite_series.system_09_fourier_representation.parity_simplification.transfer_v01",
              "relation": "迁移到偶函数。",
              "stem": "若f是偶函数，哪些系数为0？为什么半区间积分出现 $2/l$？",
              "expectedAnswer": "正弦为奇函数，偶乘奇为奇，对称积分0，所以 $b_n=0$。保留的偶被积函数在左右两半积分相等，故 $\\int_{-l}^lg=2\\int_0^lg$，系数前出现 $2/l$。",
              "masteryEvidence": "能从同一机制推出偶余弦与半区间因子。"
            }
          }
        },
        {
          "id": "infinite_series.system_09_fourier_representation.half_range_extension",
          "macroId": "infinite_series.system_09_fourier_representation",
          "type": "transformation",
          "title": "半区间奇偶延拓",
          "description": "能从 $[0,l]$ 构造奇延拓或偶延拓，区分补左半边与周期复制，并写对应半区间系数。",
          "training": {
            "goal": "从半区间构造奇或偶周期延拓。",
            "entryTrigger": "题目只给 $[0,l]$ 并要求正弦或余弦展开时。",
            "masteryCriteria": "能先补左半边再周期延拓，区分两种延拓代表不同全局函数。",
            "repairTargetNodeId": "infinite_series.system_09_fourier_representation.half_range_extension",
            "questionId": "infinite_series.system_09_fourier_representation.half_range_extension.core_q01",
            "kind": "condition_transformation",
            "difficulty": "standard",
            "targetDimensions": [
              "transformation",
              "concept",
              "expression"
            ],
            "stem": "已知 $f(x)=x$ 在 $[0,l]$。分别写出奇延拓与偶延拓在 $[-l,l]$ 的表达，并说明为什么两种展开不矛盾。",
            "expectedAnswer": "奇延拓为 $F_o(x)=x$，满足 $F_o(-x)=-F_o(x)$，产生正弦级数；偶延拓为 $F_e(x)=\\lvert x\\rvert$，满足 $F_e(-x)=F_e(x)$，产生余弦级数。二者在 $[0,l]$ 都等于原f，但在负半轴及周期复制后是不同函数，因此不矛盾。",
            "variant": {
              "questionId": "infinite_series.system_09_fourier_representation.half_range_extension.transfer_v01",
              "relation": "要求从目标展开类型反向选择延拓。",
              "stem": "只给 $[0,2]$ 上函数，题目要求余弦级数。应如何补全和确定周期？",
              "expectedAnswer": "先在 $[-2,2]$ 做偶延拓 $F(-x)=F(x)$，再以 $2l=4$ 为周期复制到全轴；系数使用半区间余弦公式。",
              "masteryEvidence": "能从题目要求反向决定延拓与周期。"
            }
          }
        }
      ]
    },
    {
      "id": "infinite_series.system_10_fourier_application",
      "macroNodeId": "infinite_series.system_10_fourier_application",
      "title": "傅里叶逐点收敛与特殊点应用",
      "coreQuestion": "怎样在连续点、跳跃点和周期拼接点确定和函数值，并利用展开式提取数项级数？",
      "learningOrder": 10,
      "visualPriority": "high",
      "recommendedDepth": "near",
      "preferredSector": "flexible",
      "prerequisiteSystemIds": [
        "infinite_series.system_09_fourier_representation"
      ],
      "bossContribution": "提供狄利克雷逐点取值、周期奇偶移点、分部积分求系数和特殊点提取数项和。",
      "spacingReason": "这是傅里叶星系的验收与全章应用出口，应靠近Boss但与表示星系保持先修箭头。",
      "sourceEvidence": "材料E《傅里叶级数_高价值章节笔记_蒋俊豪》 > 第5页“狄利克雷”; 第9页“直接求和函数值”; 第10-11页“余弦展开与反求数项级数”",
      "planets": [
        {
          "id": "infinite_series.system_10_fourier_application.dirichlet_value",
          "macroId": "infinite_series.system_10_fourier_application",
          "type": "concept",
          "title": "狄利克雷逐点取值",
          "description": "能在连续点取原函数值，在跳跃或周期拼接点取左右极限平均，并忽略孤立点的人为值。",
          "training": {
            "goal": "根据左右极限确定傅里叶和函数逐点值。",
            "entryTrigger": "求 $S(x_0)$ 或讨论跳跃、端点、孤立点修改时。",
            "masteryCriteria": "能分连续点、跳跃点和周期拼接端点，并写平均值。",
            "repairTargetNodeId": "infinite_series.system_10_fourier_application.dirichlet_value",
            "questionId": "infinite_series.system_10_fourier_application.dirichlet_value.core_q01",
            "kind": "concept_judgement",
            "difficulty": "standard",
            "targetDimensions": [
              "concept",
              "trigger",
              "expression"
            ],
            "stem": "某周期函数在 $x_0$ 左极限为2、右极限为6，但人为定义 $f(x_0)=100$。其傅里叶和函数在 $x_0$ 的值是多少？为什么？",
            "expectedAnswer": "$S(x_0)=[2+6]/2=4$。逐点收敛值由左右极限决定，不由孤立点的人为值决定；修改有限个孤立点也不改变系数积分。",
            "variant": {
              "questionId": "infinite_series.system_10_fourier_application.dirichlet_value.transfer_v01",
              "relation": "迁移到周期拼接端点。",
              "stem": "在基本区间右端点，左极限来自本周期、右极限来自哪里？应怎样取值？",
              "expectedAnswer": "右极限来自下一周期复制后的起点值；仍取拼接两侧极限的平均。",
              "masteryEvidence": "能把跳跃规则迁移到周期端点。"
            }
          }
        },
        {
          "id": "infinite_series.system_10_fourier_application.point_mapping",
          "macroId": "infinite_series.system_10_fourier_application",
          "type": "method",
          "title": "周期与奇偶移点",
          "description": "能先用周期性和奇偶性把目标点搬到基本区间，再用左右极限决定数值；常见失败是移点后直接代函数值。",
          "training": {
            "goal": "先移点再用狄利克雷取值。",
            "entryTrigger": "求远离基本区间的S(x)且已知周期与奇偶性时。",
            "masteryCriteria": "能严格区分周期/奇偶只负责搬点，最终取值由左右极限决定。",
            "repairTargetNodeId": "infinite_series.system_10_fourier_application.point_mapping",
            "questionId": "infinite_series.system_10_fourier_application.point_mapping.core_q01",
            "kind": "calculation_execution",
            "difficulty": "advanced",
            "targetDimensions": [
              "method",
              "process",
              "final_answer"
            ],
            "stem": "设题中余弦展开对应偶周期函数，周期为2，且在 $[0,1]$ 上\n$f(x)=x$ 对 $0\\le x\\le1/2$，$f(x)=2-2x$ 对 $1/2<x\\le1$。求 $S(-5/2)$。",
            "expectedAnswer": "周期性给 $S(-5/2)=S(-1/2)$；偶性给 $S(-1/2)=S(1/2)$。在 $1/2$ 处左极限为 $1/2$，右极限为1，所以 $S(1/2)=(1/2+1)/2=3/4$。",
            "variant": {
              "questionId": "infinite_series.system_10_fourier_application.point_mapping.transfer_v01",
              "relation": "改变目标点但保持同一函数。",
              "stem": "求 $S(5/2)$。",
              "expectedAnswer": "周期性 $S(5/2)=S(1/2)$，同样是跳跃平均，结果 $3/4$。",
              "masteryEvidence": "能自主选择最短周期移点，不机械照抄负号步骤。"
            }
          }
        },
        {
          "id": "infinite_series.system_10_fourier_application.coefficient_calculation",
          "macroId": "infinite_series.system_10_fourier_application",
          "type": "calculation",
          "title": "分部积分计算傅里叶系数",
          "description": "能对多项式余弦系数完成两次分部积分，处理边界项和 $(-1)^n$ 符号。",
          "training": {
            "goal": "用分部积分求多项式余弦系数。",
            "entryTrigger": "半区间多项式要求余弦展开时。",
            "masteryCriteria": "能正确计算a0和an，处理两次分部积分及边界符号。",
            "repairTargetNodeId": "infinite_series.system_10_fourier_application.coefficient_calculation",
            "questionId": "infinite_series.system_10_fourier_application.coefficient_calculation.core_q01",
            "kind": "calculation_execution",
            "difficulty": "advanced",
            "targetDimensions": [
              "calculation",
              "process",
              "expression"
            ],
            "stem": "对 $f(x)=1-x^2$，$0\\le x\\le\\pi$，求其余弦级数的 $a_0$ 与 $a_n$。",
            "expectedAnswer": "偶延拓且 $l=\\pi$。\n$a_0=(2/\\pi)\\int_0^\\pi(1-x^2)dx=2-2\\pi^2/3$。\n$a_n=(2/\\pi)\\int_0^\\pi(1-x^2)\\cos nx\\,dx=-(2/\\pi)I$，其中 $I=\\int_0^\\pi x^2\\cos nx\\,dx=2\\pi(-1)^n/n^2$，故 $a_n=4(-1)^{n+1}/n^2$。",
            "variant": {
              "questionId": "infinite_series.system_10_fourier_application.coefficient_calculation.transfer_v01",
              "relation": "改为奇延拓的一次分部积分。",
              "stem": "对 $f(x)=x$，$0<x<\\pi$，做正弦展开时求 $b_n$。",
              "expectedAnswer": "$b_n=(2/\\pi)\\int_0^\\pi x\\sin nx\\,dx=2(-1)^{n+1}/n$。",
              "masteryEvidence": "能迁移半区间公式与分部积分到正弦系数。"
            }
          }
        },
        {
          "id": "infinite_series.system_10_fourier_application.special_point_sum",
          "macroId": "infinite_series.system_10_fourier_application",
          "type": "method",
          "title": "特殊点提取数项和",
          "description": "能选择使三角因子统一为 $0,1,-1$ 的点，并先判断该点连续性，再解出目标数项级数。",
          "training": {
            "goal": "从傅里叶恒等式选择特殊点提取数项级数。",
            "entryTrigger": "已知傅里叶展开且目标和不含三角因子时。",
            "masteryCriteria": "能选择点使三角因子统一，先判连续性，再解出目标和。",
            "repairTargetNodeId": "infinite_series.system_10_fourier_application.special_point_sum",
            "questionId": "infinite_series.system_10_fourier_application.special_point_sum.core_q01",
            "kind": "method_selection",
            "difficulty": "advanced",
            "targetDimensions": [
              "trigger",
              "method",
              "calculation",
              "final_answer"
            ],
            "stem": "由\n$1-x^2=1-\\pi^2/3+4\\sum_{n=1}^{\\infty}(-1)^{n+1}\\cos(nx)/n^2$\n求 $\\sum_{n=1}^{\\infty}(-1)^{n+1}/n^2$。",
            "expectedAnswer": "取 $x=0$，因为 $\\cos(n\\cdot0)=1$，且0是偶延拓后的连续点，左边取 $f(0)=1$。于是\n$1=1-\\pi^2/3+4S$，得 $S=\\pi^2/12$。",
            "variant": {
              "questionId": "infinite_series.system_10_fourier_application.special_point_sum.transfer_v01",
              "relation": "选择另一个点提取非交错平方倒数和。",
              "stem": "在同一展开式中取 $x=\\pi$，可得到哪个级数和？给出结果。",
              "expectedAnswer": "$\\cos(n\\pi)=(-1)^n$，乘原系数 $(-1)^{n+1}$ 后恒为-1。左边 $1-\\pi^2$，所以\n$1-\\pi^2=1-\\pi^2/3-4\\sum1/n^2$，解得 $\\sum1/n^2=\\pi^2/6$。",
              "masteryEvidence": "能根据目标符号选择不同特殊点并处理端点连续/拼接值。"
            }
          }
        }
      ]
    }
  ],
  "boss": {
    "id": "infinite_series.boss",
    "title": "黑洞验收：从敛散分类到函数展开与特殊和",
    "coversSystemIds": [
      "infinite_series.system_01_foundations",
      "infinite_series.system_02_geometric_tests",
      "infinite_series.system_03_integral_test",
      "infinite_series.system_04_alternating_series",
      "infinite_series.system_05_arbitrary_terms",
      "infinite_series.system_06_power_domain",
      "infinite_series.system_07_sum_basics",
      "infinite_series.system_08_sum_advanced",
      "infinite_series.system_09_fourier_representation",
      "infinite_series.system_10_fourier_application"
    ],
    "integratedLearningGoal": "在同一任务中识别对象、选择并组合判别方法，求幂级数收敛域与和函数，完成傅里叶展开和逐点取值，并给出可评分的条件、过程与结论。",
    "challengeBrief": "三阶段综合任务：判定含扰动交错级数的收敛类型；求对数型幂级数的收敛域与和函数；计算半区间余弦级数并用特殊点提取平方倒数和。",
    "successEvidence": "所有方法触发正确，成立条件完整，关键变形与计算可复查，最终表达含收敛域或逐点取值规则，任一失败可精确路由到MicroNode。",
    "failureRouting": "通项门槛或结构路由错误 -> infinite_series.system_01_foundations.term_gate; 比值根值方法或边界错误 -> infinite_series.system_02_geometric_tests.geometric_proof_boundary; 积分条件或对数积分错误 -> infinite_series.system_03_integral_test.condition_check; 交错条件或拆项错误 -> infinite_series.system_04_alternating_series.failure_repair; 绝对条件分类错误 -> infinite_series.system_05_arbitrary_terms.convergence_classification; 半径或端点错误 -> infinite_series.system_06_power_domain.endpoint_judgement; 求和式漏定义域或变形错位 -> infinite_series.system_07_sum_basics.domain_first; 构造S或特殊值回收失败 -> infinite_series.system_08_sum_advanced.construct_sum_function; 傅里叶系数或延拓错误 -> infinite_series.system_09_fourier_representation.coefficient_extraction; 傅里叶逐点值或特殊点错误 -> infinite_series.system_10_fourier_application.dirichlet_value",
    "sourceEvidence": "五份材料全章主线；重点见材料A第2-11页、材料B第3-9页、材料C第2-12页、材料D第2-10页、材料E第2-11页。",
    "training": {
      "bossId": "infinite_series.boss",
      "kind": "boss_acceptance",
      "title": "黑洞验收：三种无穷展开的一体化调用",
      "coversSystemIds": [
        "infinite_series.system_01_foundations",
        "infinite_series.system_02_geometric_tests",
        "infinite_series.system_03_integral_test",
        "infinite_series.system_04_alternating_series",
        "infinite_series.system_05_arbitrary_terms",
        "infinite_series.system_06_power_domain",
        "infinite_series.system_07_sum_basics",
        "infinite_series.system_08_sum_advanced",
        "infinite_series.system_09_fourier_representation",
        "infinite_series.system_10_fourier_application"
      ],
      "coversMicroNodes": [
        "infinite_series.system_01_foundations.term_gate",
        "infinite_series.system_02_geometric_tests.root_method",
        "infinite_series.system_04_alternating_series.failure_repair",
        "infinite_series.system_05_arbitrary_terms.convergence_classification",
        "infinite_series.system_06_power_domain.endpoint_judgement",
        "infinite_series.system_07_sum_basics.known_expansion",
        "infinite_series.system_08_sum_advanced.construct_sum_function",
        "infinite_series.system_09_fourier_representation.half_range_extension",
        "infinite_series.system_10_fourier_application.coefficient_calculation",
        "infinite_series.system_10_fourier_application.special_point_sum"
      ],
      "stem": "完成以下三个相互关联的阶段，所有结论必须写成立条件和过程证据。\n\n**阶段A：数项级数分类**\n1. 判断 $\\sum_{n=1}^{\\infty}\\left(\\dfrac{2n+1}{3n+2}\\right)^n$。\n2. 判断并分类 $\\sum_{n=2}^{\\infty}\\dfrac{(-1)^{n-1}}{n+\\sin n}$。\n\n**阶段B：幂级数收敛域与和函数**\n求 $F(x)=\\sum_{n=1}^{\\infty}(-1)^{n-1}x^n/n$ 的完整收敛域与和函数。\n\n**阶段C：傅里叶展开与特殊数项和**\n对 $f(x)=1-x^2$，$0\\le x\\le\\pi$ 作余弦级数展开，并由该展开求\n$\\sum_{n=1}^{\\infty}(-1)^{n+1}/n^2$。",
      "expectedAnswer": "**阶段A-1**：取n次根，极限为 $2/3<1$，故正项级数收敛。\n\n**阶段A-2**：\n$1/(n+\\sin n)=1/n-\\sin n/[n(n+\\sin n)]$。原级数等于交错调和级数减去一个绝对收敛误差级数，因此收敛。绝对值级数与 $\\sum1/n$ 极限比较同敛而发散，所以原级数条件收敛。\n\n**阶段B**：比值或根值给 $\\lvert x\\rvert<1$。$x=1$ 时为交错调和级数，收敛；$x=-1$ 时为负调和级数，发散，故收敛域为 $(-1,1]$。在 $\\lvert x\\rvert<1$ 内对几何级数积分得 $F(x)=\\ln(1+x)$，并由端点收敛延伸到 $x=1$，$F(1)=\\ln2$。\n\n**阶段C**：偶延拓，$l=\\pi$。\n$a_0=(2/\\pi)\\int_0^\\pi(1-x^2)dx=2-2\\pi^2/3$；\n$a_n=(2/\\pi)\\int_0^\\pi(1-x^2)\\cos nx\\,dx=4(-1)^{n+1}/n^2$。\n因此\n$1-x^2=1-\\pi^2/3+4\\sum_{n=1}^{\\infty}(-1)^{n+1}\\cos(nx)/n^2$。\n取连续点 $x=0$，所有余弦等于1，得目标和 $\\pi^2/12$。",
      "sourceEvidence": "材料A第2-11页; 材料B第3-9页; 材料C第3-7页; 材料D第2-9页; 材料E第5-11页"
    }
  },
  "metrics": {
    "systemCount": 10,
    "planetCount": 43,
    "bossCount": 1
  }
};
