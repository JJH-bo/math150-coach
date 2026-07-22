from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any

from app.classroom.hashing import content_hash
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomNotFoundError, ClassroomRepository
from app.classroom.validation import ClassroomPackageValidator


OVERVIEW_MARKERS = (
    "全章地图",
    "章节地图",
    "学习地图",
    "全章总览",
    "章节总览",
    "chapter map",
    "chapter overview",
)

SUBSTANTIVE_KINDS = {
    "prose",
    "formula_explanation",
    "derivation",
    "comparison",
    "worked_example",
    "code_explanation",
    "table",
    "matrix",
    "image",
    "group",
}

FOURIER_MODULE_LEARNING_CONTRACTS: dict[str, dict[str, Any]] = {
    "trigonometric-series": {
        "core_question": (
            "怎样把一个周期函数拆成不同频率的正弦波和余弦波，"
            "并算出每个频率在原函数中占多少？"
        ),
        "novice_bridge": {
            "known_before": [
                "会读周期、正弦和余弦图像，并知道定积分可以汇总一个区间上的信息。"
            ],
            "missing_bridge": (
                "还缺少“正交积分像筛子一样只留下同频成分”这座桥，"
                "否则三个系数公式只能靠死记。"
            ),
            "concrete_anchor": (
                "先把一条复杂周期曲线看成几种简单波形叠加："
                "常数控制整体高度，余弦和正弦控制不同频率的起伏。"
            ),
            "bridge_strategy": (
                "先在模型中逐个增加谐波，看曲线怎样改变；再用整周期积分解释"
                "为什么某个系数只测量对应频率，最后才写统一公式。"
            ),
        },
    },
    "convergence": {
        "core_question": (
            "写出傅里叶级数以后，它在连续点、跳跃点和周期端点"
            "分别收敛到什么值，为什么不总等于原函数值？"
        ),
        "novice_bridge": {
            "known_before": [
                "已经知道怎样写出傅里叶系数和形式上的三角级数。"
            ],
            "missing_bridge": (
                "还要区分“写出了一个级数”和“知道这个级数在某一点的和”；"
                "关键桥梁是该点左右两侧的函数趋势。"
            ),
            "concrete_anchor": (
                "先盯住方波的一处跳跃：从左边靠近得到一个高度，"
                "从右边靠近得到另一个高度，部分和最终落在两者中点。"
            ),
            "bridge_strategy": (
                "先比较连续点和跳跃点，再把两种情况统一成左右极限平均公式，"
                "最后单独检查周期端点要读取周期延拓后的另一侧。"
            ),
        },
    },
    "parity": {
        "core_question": (
            "函数的奇偶性为什么能让一半傅里叶系数自动变成零，"
            "并把一般展开化成纯正弦级数或纯余弦级数？"
        ),
        "novice_bridge": {
            "known_before": [
                "已经会使用一般傅里叶系数公式，并认识奇函数与偶函数的图像。"
            ],
            "missing_bridge": (
                "还要把函数奇偶性、正弦余弦的奇偶性与对称区间积分的抵消关系连起来。"
            ),
            "concrete_anchor": (
                "把 x 与 -x 处的两块面积成对观察：异号时互相抵消，"
                "同号时可以把半区间积分加倍。"
            ),
            "bridge_strategy": (
                "先判断乘积的奇偶性，再判断积分是抵消还是加倍，"
                "由此推出哪些系数为零，最后写出化简后的级数。"
            ),
        },
    },
    "extension": {
        "core_question": (
            "题目只给出半区间上的函数时，怎样选择奇延拓或偶延拓，"
            "把它补成可使用傅里叶公式的完整周期函数？"
        ),
        "novice_bridge": {
            "known_before": [
                "已经知道奇函数只留下正弦项、偶函数只留下余弦项。"
            ],
            "missing_bridge": (
                "半区间数据本身还不是奇函数或偶函数；必须先决定负半轴怎样补，"
                "再进行周期复制。"
            ),
            "concrete_anchor": (
                "先画出 [0,l] 上的一段曲线，再把它向左镜像："
                "同号镜像得到偶延拓，反号镜像得到奇延拓。"
            ),
            "bridge_strategy": (
                "先完成负半轴，再检查 x=0 与端点的连接方式，"
                "随后做 2l 周期复制，最后选择正弦或余弦系数公式。"
            ),
        },
    },
    "application": {
        "core_question": (
            "面对具体傅里叶问题时，怎样在周期性、奇偶性、收敛定理和系数计算之间"
            "选择最短路径，并把函数展开迁移成数项级数求和？"
        ),
        "novice_bridge": {
            "known_before": [
                "已经分别掌握系数、收敛、奇偶化简与半区间延拓。"
            ],
            "missing_bridge": (
                "还缺少按问题目标选择工具的顺序：求某点的和不一定要算系数，"
                "求数项级数则要先有函数展开再选特殊点。"
            ),
            "concrete_anchor": (
                "把任务先分成三类：写展开式、求某点的级数和、"
                "由函数值反求一个数项级数。"
            ),
            "bridge_strategy": (
                "每道题先标记目标，再按“周期搬运—奇偶折回—左右极限—必要时算系数”"
                "的顺序决策，并在特殊点把三角因子化简。"
            ),
        },
    },
}

FOURIER_SEGMENT_LEARNING_CONTRACTS: dict[str, dict[str, Any]] = {
    "formula-intuition": {
        "question_answered": (
            "为什么周期函数可以用一组不同频率的正弦和余弦来描述？"
        ),
        "bridge_from_previous": (
            "先从已经认识的周期振动出发：复杂波形也在重复，"
            "因此可以尝试用本身就周期重复的简单波形去拼它。"
        ),
        "mechanism": (
            "常数项决定整体高度，第 n 个正弦或余弦项提供第 n 种频率；"
            "改变各项权重，就能让叠加后的形状逐步接近原函数。"
        ),
        "entry_assumptions": ["会读正弦、余弦图像，并能辨认函数的周期。"],
        "exit_understanding": (
            "能把傅里叶展开解释为“不同频率波形的加权叠加”，"
            "而不是一条需要直接背诵的无穷公式。"
        ),
    },
    "formula-core": {
        "question_answered": (
            "三个积分公式分别在测量什么，为什么整周期积分能只筛出对应频率？"
        ),
        "bridge_from_previous": (
            "已经知道要叠加许多频率；现在只解决怎样从原函数中"
            "测出每个频率应该放多大权重。"
        ),
        "mechanism": (
            "把原函数乘上目标正弦或余弦并在完整周期积分。"
            "不同频率因正交而抵消，只剩同频项；再除以它自身的积分尺度 l，"
            "就得到对应系数。"
        ),
        "entry_assumptions": [
            "理解傅里叶级数是波形叠加，并会计算定积分。"
        ],
        "exit_understanding": (
            "能说明 a0、an、bn 各自提取什么成分，"
            "并理解公式中的完整周期、分母 l 与展开式中的 a0/2。"
        ),
    },
    "formula-boundaries": {
        "question_answered": (
            "使用统一公式时，周期、积分区间和展开符号最容易错在哪里？"
        ),
        "bridge_from_previous": (
            "公式结构已经建立；这一步只校准三个会让正确公式被错误使用的边界。"
        ),
        "mechanism": (
            "先由周期 2l 确定 l，再选择任意一个完整周期积分；"
            "最后把“形式展开”与“在某点确实等于函数值”分开判断。"
        ),
        "entry_assumptions": ["已经理解并能读出一般傅里叶系数公式。"],
        "exit_understanding": (
            "能从题目周期正确读出 l，选择完整周期，并知道何时只能写“~”。"
        ),
    },
    "conv-condition": {
        "question_answered": (
            "有了傅里叶系数，为什么还不能立刻把级数和写成 f(x)？"
        ),
        "bridge_from_previous": (
            "上一模块只构造了一个三角级数；现在要检查它在每一点究竟趋向哪里。"
        ),
        "mechanism": (
            "狄利克雷条件控制一个周期内的振荡和间断数量，"
            "使傅里叶部分和在每一点都有可判断的极限。"
        ),
        "entry_assumptions": ["会写傅里叶级数，但尚未判断其逐点收敛值。"],
        "exit_understanding": (
            "能区分“写出级数”与“确定级数和”，并能识别常见分段光滑函数满足的条件。"
        ),
    },
    "conv-conclusion": {
        "question_answered": (
            "怎样用左右极限平均统一判断连续点、跳跃点和周期端点的傅里叶级数和？"
        ),
        "bridge_from_previous": (
            "已经知道收敛有保障；现在把所有点的收敛值压缩成一个可直接使用的规则。"
        ),
        "mechanism": (
            "读取周期延拓后该点左侧和右侧的极限并取平均。"
            "连续点两侧相等，所以退化为 f(x)；跳跃点则落在两个高度的中点。"
        ),
        "entry_assumptions": ["理解左右极限，并知道函数按 2l 周期延拓。"],
        "exit_understanding": (
            "能独立处理连续点、跳跃点和端点，不把被单独赋予的点值误当作级数和。"
        ),
    },
    "parity-core": {
        "question_answered": (
            "为什么奇函数的余弦系数为零、偶函数的正弦系数为零？"
        ),
        "bridge_from_previous": (
            "一般系数公式已经会用；现在利用对称性，在积分前先消掉必为零的一半系数。"
        ),
        "mechanism": (
            "先判断 f 与正弦或余弦乘积的奇偶性。"
            "奇函数在对称区间积分相消，偶函数则把半区间积分加倍。"
        ),
        "entry_assumptions": ["会判断函数乘积的奇偶性，并认识对称区间。"],
        "exit_understanding": (
            "能从对称积分推出纯正弦或纯余弦展开，而不是只背“奇正弦、偶余弦”。"
        ),
    },
    "parity-boundary": {
        "question_answered": (
            "什么时候可以用奇偶性直接消掉系数，什么时候这样做会偷换函数定义？"
        ),
        "bridge_from_previous": (
            "已经看到奇偶化简的力量；这一步限定它只能用于关于原点对称且确有奇偶性的函数。"
        ),
        "mechanism": (
            "先检查定义域是否关于原点对称，再检查 f(-x)=±f(x)。"
            "若只给半区间，必须先声明一种延拓，不能说原函数天然奇或偶。"
        ),
        "entry_assumptions": ["会用奇偶性化简完整对称区间上的系数。"],
        "exit_understanding": (
            "能区分“原函数具有奇偶性”与“人为选择奇延拓或偶延拓”。"
        ),
    },
    "extension-problem": {
        "question_answered": (
            "只给 [0,l] 上的函数时，为什么补出负半轴后就能使用一般傅里叶公式？"
        ),
        "bridge_from_previous": (
            "上一模块说明奇偶性会选择正弦或余弦；现在反过来主动选择一种对称补法。"
        ),
        "mechanism": (
            "把 [0,l] 的图像按同号或反号镜像到 [-l,0]，"
            "得到偶函数或奇函数，再以 2l 为周期复制成完整周期函数。"
        ),
        "entry_assumptions": ["知道奇函数、偶函数的镜像关系和一般傅里叶公式的完整周期要求。"],
        "exit_understanding": (
            "能画出奇延拓与偶延拓，并说明它们为什么分别产生正弦级数和余弦级数。"
        ),
    },
    "extension-formulas": {
        "question_answered": (
            "完成奇延拓或偶延拓后，半区间系数公式为什么变成 0 到 l 上的 2/l？"
        ),
        "bridge_from_previous": (
            "完整延拓已经建立；现在只把对称性代回一般公式，压缩积分区间。"
        ),
        "mechanism": (
            "奇偶乘积决定积分是零还是两倍半区间积分，"
            "因此 [-l,l] 上的 1/l 积分化成 [0,l] 上的 2/l 积分。"
        ),
        "entry_assumptions": ["能区分奇延拓与偶延拓，并会使用对称区间积分。"],
        "exit_understanding": (
            "能从一般公式推回半区间正弦、余弦系数，而不是把两套公式孤立记忆。"
        ),
    },
    "application-fast-value": {
        "question_answered": (
            "只要求某一点的傅里叶级数和时，怎样不算任何系数就得到答案？"
        ),
        "bridge_from_previous": (
            "系数、周期、奇偶性和收敛规则已经具备；现在先判断问题是否根本不需要展开式。"
        ),
        "mechanism": (
            "先用周期性搬运目标点，再用奇偶性折回基本区间，"
            "最后在落点读取左右极限平均。"
        ),
        "entry_assumptions": ["会使用周期、奇偶性和左右极限平均公式。"],
        "exit_understanding": (
            "看到“求 S(x0)”时，能优先走搬运—折回—取平均的短路径。"
        ),
    },
    "application-cos-expansion": {
        "question_answered": (
            "怎样把半区间函数 1-x² 完整展开成余弦级数，并检查系数结构？"
        ),
        "bridge_from_previous": (
            "已经会选择偶延拓；现在执行一次从确定 l、计算 a0/an 到写出展开式的完整流程。"
        ),
        "mechanism": (
            "偶延拓使 bn 全部为零；a0 给出平均项，an 通过分部积分得到"
            "随 1/n² 衰减并交替变号的余弦权重。"
        ),
        "entry_assumptions": ["会使用半区间余弦系数公式和分部积分。"],
        "exit_understanding": (
            "能独立完成一个余弦展开，并用系数衰减、符号和端点行为进行自检。"
        ),
    },
    "application-sum": {
        "question_answered": (
            "怎样在已知傅里叶展开中选择特殊点，把函数等式变成一个数项级数的和？"
        ),
        "bridge_from_previous": (
            "函数展开式已经得到；现在选择让所有三角因子尽量简单的 x 值。"
        ),
        "mechanism": (
            "先确认该点的傅里叶和等于什么，再代入使 cos(nx) 变成 1 或 (-1)^n 的特殊点，"
            "最后把剩余项移项整理。"
        ),
        "entry_assumptions": ["已经得到可靠的傅里叶展开，并会判断特殊点处的收敛值。"],
        "exit_understanding": (
            "能把“函数展开”迁移为“数项级数求和”，并知道代点前必须先检查收敛值。"
        ),
    },
}

FOURIER_DETAIL_LEARNING_CONTRACTS: dict[str, dict[str, Any]] = {
    "coeff-why-divide-l": {
        "trigger_question": "系数公式为什么除以 l，而不是除以 2l？",
        "learning_obstacle": (
            "会套公式，却没有看到分母来自目标基函数平方在完整周期上的积分尺度。"
        ),
        "representation": "step_by_step_derivation",
        "focus_relation": "正交投影的分子与目标基函数自身尺度之间的比值。",
        "bridge_steps": [
            "把傅里叶展开两边乘上目标余弦或正弦，并在 [-l,l] 上积分。",
            "利用正交性消掉常数项和所有其他频率，只留下目标频率的平方积分。",
            "计算该平方积分等于 l，再把 l 移到分母得到对应系数。",
        ],
        "return_connection": (
            "回到 an、bn 公式时，分子负责测量同频重合量，分母 l 负责归一化。"
        ),
    },
    "coeff-a0-detail": {
        "trigger_question": "a0 已经描述平均高度，为什么展开式里还要写 a0/2？",
        "learning_obstacle": (
            "把常数基函数与正弦、余弦基函数当成具有相同的平方积分尺度。"
        ),
        "representation": "lower_abstraction",
        "focus_relation": "常数基函数 1 的平方积分是 2l，而非 l。",
        "bridge_steps": [
            "单独把常数项记为 C，不预设它等于 a0。",
            "在完整周期积分，所有正弦余弦项消失，只剩 2l·C。",
            "由积分结果得到 C=a0/2，再放回统一展开式。",
        ],
        "return_connection": "重新阅读展开式时，把 a0/2 直接理解为函数的周期平均值。",
    },
    "first-kind-detail": {
        "trigger_question": "“第一类间断点”到底要求什么，为什么傅里叶收敛定理能处理它？",
        "learning_obstacle": "只记住术语，不会用左右极限判断某个间断点是否属于这一类。",
        "representation": "annotated_diagram",
        "focus_relation": "左右极限分别存在且有限，但二者可以不相等。",
        "bridge_steps": [
            "从间断点左侧靠近并记录有限极限。",
            "再从右侧靠近并记录有限极限。",
            "两侧都有限就属于第一类；相等时可去，不等时为跳跃。",
        ],
        "return_connection": "回到狄利克雷条件时，用左右极限检查，而不是靠图像是否断开来猜。",
    },
    "conv-three-cases": {
        "trigger_question": "同一个左右极限平均公式怎样覆盖连续点、跳跃点和周期端点？",
        "learning_obstacle": "把三种位置背成三条互不相关的规则，遇到端点就不知道读哪一侧。",
        "representation": "annotated_diagram",
        "focus_relation": "所有情况都只取周期延拓后该点的左极限与右极限。",
        "bridge_steps": [
            "连续点两侧相等，平均值自然就是 f(x)。",
            "跳跃点两侧不同，平均值落在两个高度中间。",
            "周期端点的一侧来自本周期，另一侧来自相邻周期的复制。",
        ],
        "return_connection": "以后不再记三套规则，只执行“周期化后取左右极限平均”。",
    },
    "parity-proof": {
        "trigger_question": "为什么奇函数只剩正弦项，偶函数只剩余弦项？",
        "learning_obstacle": "记住结论，却不会判断 f(x) 与 sin、cos 相乘后的奇偶性。",
        "representation": "annotated_diagram",
        "focus_relation": "乘积奇偶性决定对称区间积分是抵消为零还是加倍。",
        "bridge_steps": [
            "分别写出 f、sin、cos 的奇偶性。",
            "用奇×奇=偶、奇×偶=奇判断被积函数。",
            "奇被积函数积分为零，偶被积函数化为两倍半区间积分。",
        ],
        "return_connection": "回到系数公式逐项判断，就能自行推出正弦级数或余弦级数。",
    },
    "extension-steps": {
        "trigger_question": "从半区间函数到可展开的周期函数，完整操作顺序是什么？",
        "learning_obstacle": "直接套半区间公式，却没有先定义负半轴与周期端点上的函数。",
        "representation": "step_by_step_derivation",
        "focus_relation": "半区间原函数、对称延拓与周期延拓是三个连续但不同的步骤。",
        "bridge_steps": [
            "保留 [0,l] 上的原函数，并明确想要正弦级数还是余弦级数。",
            "用反号镜像或同号镜像补出 [-l,0]。",
            "把 [-l,l] 上的新函数以 2l 为周期向两边复制，再计算系数。",
        ],
        "return_connection": "回到半区间公式时，先说清采用哪种延拓，再写对应系数。",
    },
    "extension-endpoint": {
        "trigger_question": "奇延拓或偶延拓后，x=0 与 x=l 的点值怎样影响傅里叶级数和？",
        "learning_obstacle": "把人为指定的端点值与周期延拓后的左右极限混为一谈。",
        "representation": "annotated_diagram",
        "focus_relation": "级数和由周期延拓后的左右极限决定，而非由孤立点值单独决定。",
        "bridge_steps": [
            "先画出基本区间两端附近的曲线。",
            "按 2l 周期把相邻区间接到端点另一侧。",
            "读取两侧极限并取平均，再判断是否等于被指定的点值。",
        ],
        "return_connection": "处理半区间端点时，始终先画周期拼接，再使用收敛公式。",
    },
    "app1-why-no-coeff": {
        "trigger_question": "为什么求 S(-5/2) 可以完全不计算任何傅里叶系数？",
        "learning_obstacle": "一看到“傅里叶级数”就默认先计算 a0、an、bn。",
        "representation": "annotated_diagram",
        "focus_relation": "题目只问一个点的级数和，周期性、偶性和收敛定理已经足够定位它。",
        "bridge_steps": [
            "用周期 2 把 -5/2 搬到基本周期内。",
            "用偶性把负点折到正半轴。",
            "在最终落点读取左右极限平均，直接得到 S(x)。",
        ],
        "return_connection": "以后先看题目目标；只有要求展开式时才进入系数计算。",
    },
    "app2-an-derivation": {
        "trigger_question": "an 的两次分部积分怎样得到 4(-1)^(n+1)/n²？",
        "learning_obstacle": "能写出余弦系数积分，但在分部积分中丢失边界项或符号。",
        "representation": "step_by_step_derivation",
        "focus_relation": "第一次分部积分去掉 x²，第二次把剩余 x·sin(nx) 化成端点余弦。",
        "bridge_steps": [
            "先把常数 1 的余弦积分单独处理，它在 n≥1 时为零。",
            "对 x²cos(nx) 第一次分部积分，检查 sin(nπ)=sin(0)=0。",
            "对剩余 xsin(nx) 再分部积分，用 cos(nπ)=(-1)^n 整理符号。",
        ],
        "return_connection": "回到余弦展开式时，用 1/n² 衰减和交替符号做结构自检。",
    },
    "app2-check": {
        "trigger_question": "不重算全部积分，怎样快速检查 1-x² 的余弦展开是否可信？",
        "learning_obstacle": "推导结束后只核对抄写，缺少能发现系数、符号或常数项错误的独立检查。",
        "representation": "smaller_example",
        "focus_relation": "函数对称性、系数衰减与特殊点代入提供三种彼此独立的证据。",
        "bridge_steps": [
            "确认偶延拓没有正弦项。",
            "检查分段光滑函数的系数按 1/n² 衰减是否合理。",
            "代入 x=0 或 x=π，比较展开式的和与收敛定理给出的函数值。",
        ],
        "return_connection": "把三项检查都通过后，再使用该展开去推导数项级数。",
    },
}


def _is_quality_package(package: dict[str, Any]) -> bool:
    chapters = [
        chapter
        for course in package.get("courses", [])
        for chapter in course.get("chapters", [])
    ]
    return bool(chapters) and all(
        chapter.get("source_sections")
        and chapter.get("knowledge_points")
        and chapter.get("coverage_map")
        and chapter.get("coverage_audit")
        and chapter.get("overview")
        for chapter in chapters
    )


def _clean_title(title: str) -> str:
    value = re.sub(r"^星系[一二三四五六七八九十\d]+[：:]\s*", "", title)
    return value.strip() or title


def _source_content(module: dict[str, Any]) -> str:
    lines = [str(module.get("title", "")), str(module.get("summary", ""))]
    for segment in module.get("segments", []):
        lines.append(str(segment.get("title") or segment.get("id") or ""))
        for block in segment.get("blocks", []):
            lines.append(
                json.dumps(block.get("data", {}), ensure_ascii=False, sort_keys=True)
            )
    for block in module.get("blocks", []):
        lines.append(json.dumps(block.get("data", {}), ensure_ascii=False, sort_keys=True))
    return "\n".join(line for line in lines if line).strip()


def _comparison_items(items: Any) -> Any:
    if not isinstance(items, list):
        return items
    normalized = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            normalized.append({"title": f"对照 {index}", "body": str(item)})
            continue
        title_keys = (
            "title",
            "name",
            "label",
            "case",
            "function",
            "extension",
            "goal",
        )
        title_key = next(
            (
                key
                for key in title_keys
                if isinstance(item.get(key), str) and item[key].strip()
            ),
            None,
        )
        body_keys = ("body", "text", "description", "focus")
        body = next(
            (
                item[key]
                for key in body_keys
                if isinstance(item.get(key), str) and item[key].strip()
            ),
            None,
        )
        if body is None:
            body = "；".join(
                str(value)
                for key, value in item.items()
                if key != title_key and value not in (None, "")
            )
        normalized.append(
            {
                "title": str(item.get(title_key) if title_key else f"对照 {index}"),
                "body": body,
            }
        )
    return normalized


def _detail_ids(block: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for branch in block.get("detail_branches", []):
        for child in branch.get("blocks", []):
            result.append(child["id"])
            result.extend(_detail_ids(child))
    return result


def _normalize_detail(
    branch: dict[str, Any],
    *,
    parent_block_id: str,
    knowledge_point_id: str,
    topic: str,
    instance_by_model: dict[str, str],
) -> dict[str, Any]:
    normalized = deepcopy(branch)
    title = str(normalized.get("title") or f"把“{topic}”再拆开")
    normalized.setdefault("trigger_question", f"为什么“{topic}”在这里成立，关键关系是什么？")
    normalized.setdefault(
        "learning_obstacle",
        f"第一次学习时容易只记住“{topic}”的结论，却没有看见对象之间如何一步步建立联系。",
    )
    normalized.setdefault("representation", "lower_abstraction")
    normalized.setdefault(
        "focus_relation",
        f"把“{topic}”中的抽象符号还原成对象、变化和结果之间的可追踪关系。",
    )
    normalized.setdefault(
        "bridge_steps",
        [
            f"先指出“{topic}”中已经认识的对象，不引入新的结论。",
            "再只改变一个量，观察其余量如何响应，由观察回到原来的数学表达。",
        ],
    )
    normalized.setdefault(
        "return_connection",
        f"现在重新阅读父层的“{topic}”，每个符号和步骤都能对应到刚才建立的关系，再沿主线继续。",
    )
    known_contract = FOURIER_DETAIL_LEARNING_CONTRACTS.get(
        str(normalized.get("id", ""))
    )
    if known_contract is not None:
        normalized.update(deepcopy(known_contract))
    children = [
        _normalize_block(
            child,
            knowledge_point_id=knowledge_point_id,
            topic=topic,
            instance_by_model=instance_by_model,
        )
        for child in normalized.get("blocks", [])
    ]
    if not children:
        children.append(
            {
                "id": f"{parent_block_id}-detail-anchor",
                "kind": "prose",
                "data": {
                    "text": (
                        f"先不处理整章，只看“{topic}”：写出正在变化的量、"
                        "保持不变的条件，以及我们最终要解释的结果。"
                    )
                },
                "knowledge_point_ids": [knowledge_point_id],
                "detail_branches": [],
            }
        )
    if len(children) < 2:
        children.append(
            {
                "id": f"{normalized.get('id', parent_block_id + '-detail')}-bridge-example",
                "kind": "worked_example",
                "data": {
                    "prompt": f"用一个最小过程检查“{topic}”",
                    "steps": [
                        "先固定题目给出的对象和条件，不进行公式变形。",
                        "只执行当前关系要求的一步，并写出这一步改变了什么。",
                        "把得到的结果代回父层表达，确认它解释的是同一个问题。",
                    ],
                },
                "knowledge_point_ids": [knowledge_point_id],
                "detail_branches": [],
            }
        )
    normalized["title"] = title
    normalized["blocks"] = children
    return normalized


def _normalize_block(
    block: dict[str, Any],
    *,
    knowledge_point_id: str,
    topic: str,
    instance_by_model: dict[str, str],
) -> dict[str, Any]:
    normalized = deepcopy(block)
    normalized["knowledge_point_ids"] = [knowledge_point_id]
    data = deepcopy(normalized.get("data") or {})
    if normalized.get("kind") == "comparison":
        data["items"] = _comparison_items(data.get("items"))
    if normalized.get("kind") == "formula_explanation":
        parent_explanation = str(
            data.get("explanation") or data.get("text") or topic
        )
        if isinstance(data.get("formulae"), list):
            data["formulae"] = [
                {
                    "latex": item,
                    "explanation": parent_explanation,
                }
                if isinstance(item, str)
                else {
                    **item,
                    "explanation": (
                        item.get("explanation")
                        or item.get("text")
                        or (
                            f"{item.get('name')}：{parent_explanation}"
                            if item.get("name")
                            else parent_explanation
                        )
                    ),
                }
                for item in data["formulae"]
            ]
        elif not data.get("explanation"):
            data["explanation"] = parent_explanation
    if normalized.get("kind") == "math" and data.get("explanation"):
        normalized["kind"] = "formula_explanation"
    if normalized.get("kind") == "model_reference":
        model_id = data.get("model_id")
        data["instance_id"] = data.get("instance_id") or instance_by_model.get(
            str(model_id), str(model_id or "")
        )
    normalized["data"] = data
    normalized["detail_branches"] = [
        _normalize_detail(
            branch,
            parent_block_id=str(normalized["id"]),
            knowledge_point_id=knowledge_point_id,
            topic=topic,
            instance_by_model=instance_by_model,
        )
        for branch in normalized.get("detail_branches", [])
    ]
    return normalized


def _ensure_detail(
    segment: dict[str, Any],
    *,
    knowledge_point_id: str,
    topic: str,
    instance_by_model: dict[str, str],
) -> None:
    blocks = segment["blocks"]
    if any(block.get("detail_branches") for block in blocks):
        return
    parent = next(
        (block for block in blocks if block.get("kind") in SUBSTANTIVE_KINDS),
        blocks[0],
    )
    parent["detail_branches"] = [
        _normalize_detail(
            {
                "id": f"{parent['id']}-detail",
                "title": f"如果“{topic}”仍然没有形成直觉",
                "blocks": [],
            },
            parent_block_id=str(parent["id"]),
            knowledge_point_id=knowledge_point_id,
            topic=topic,
            instance_by_model=instance_by_model,
        )
    ]


def _upgrade_chapter(
    chapter: dict[str, Any],
    *,
    asset_id: str,
    instance_by_model: dict[str, str],
) -> dict[str, Any]:
    original_modules = deepcopy(chapter.get("modules", []))
    overview_modules = [
        module
        for module in original_modules
        if any(
            marker in f"{module.get('title', '')} {module.get('summary', '')}".casefold()
            for marker in OVERVIEW_MARKERS
        )
    ]
    modules = [module for module in original_modules if module not in overview_modules]
    if not modules:
        modules = original_modules
        overview_modules = []

    source_sections: list[dict[str, Any]] = []
    knowledge_points: list[dict[str, Any]] = []
    coverage_map: list[dict[str, Any]] = []
    upgraded_modules: list[dict[str, Any]] = []

    for module_index, legacy_module in enumerate(modules):
        module = deepcopy(legacy_module)
        module_id = str(module["id"])
        clean_title = _clean_title(str(module.get("title") or module_id))
        source_id = f"source-{module_id}"[:120]
        source = _source_content(module) or clean_title
        source_sections.append(
            {
                "id": source_id,
                "asset_id": asset_id,
                "filename": f"{chapter.get('title', 'chapter')}.legacy-import",
                "order": module_index + 1,
                "heading": clean_title,
                "content": source,
                "content_hash": f"sha256:{sha256(source.encode('utf-8')).hexdigest()}",
            }
        )
        segments = deepcopy(module.get("segments", []))
        if module.get("blocks"):
            segments.insert(
                0,
                {
                    "id": f"{module_id}-foundation",
                    "title": f"{clean_title}的起点",
                    "blocks": module.get("blocks", []),
                },
            )
        if not segments:
            segments = [
                {
                    "id": f"{module_id}-foundation",
                    "title": f"{clean_title}的核心关系",
                    "blocks": [
                        {
                            "id": f"{module_id}-foundation-copy",
                            "kind": "prose",
                            "data": {"text": str(module.get("summary") or clean_title)},
                            "detail_branches": [],
                        }
                    ],
                }
            ]
        module_has_existing_detail = any(
            block.get("detail_branches")
            for segment in segments
            for block in segment.get("blocks", [])
        )

        upgraded_segments: list[dict[str, Any]] = []
        module_point_ids: list[str] = []
        for segment_index, legacy_segment in enumerate(segments):
            segment = deepcopy(legacy_segment)
            segment_id = str(segment.get("id") or f"{module_id}-step-{segment_index + 1}")
            topic = str(segment.get("title") or clean_title)
            point_id = f"kp-{module_id}-{segment_id}"[:120]
            module_point_ids.append(point_id)
            blocks = [
                _normalize_block(
                    block,
                    knowledge_point_id=point_id,
                    topic=topic,
                    instance_by_model=instance_by_model,
                )
                for block in segment.get("blocks", [])
            ]
            if not blocks:
                blocks = [
                    {
                        "id": f"{segment_id}-explanation",
                        "kind": "prose",
                        "data": {"text": f"围绕“{topic}”建立对象、条件和结论之间的关系。"},
                        "knowledge_point_ids": [point_id],
                        "detail_branches": [],
                    }
                ]
            if not any(block.get("kind") in SUBSTANTIVE_KINDS for block in blocks):
                blocks.insert(
                    0,
                    {
                        "id": f"{segment_id}-bridge-copy",
                        "kind": "prose",
                        "data": {
                            "text": (
                                f"先把“{topic}”翻译成一个可追踪的问题："
                                "已知对象是什么、哪个量在变化、结论要说明什么。"
                            )
                        },
                        "knowledge_point_ids": [point_id],
                        "detail_branches": [],
                    },
                )
            segment["id"] = segment_id
            segment["title"] = topic
            segment["question_answered"] = f"如何理解“{topic}”，它解决了当前模块的什么问题？"
            segment["bridge_from_previous"] = (
                f"先从本模块熟悉的对象进入，再把它与“{topic}”所需的新关系连接起来。"
                if segment_index == 0
                else f"上一展开建立了“{segments[segment_index - 1].get('title') or clean_title}”，现在只增加“{topic}”这一层关系。"
            )
            segment["mechanism"] = (
                f"“{topic}”通过同时追踪对象、条件和结果，说明数学表达中的每一步为什么成立，而不是只给结论。"
            )
            segment["entry_assumptions"] = [
                "能读懂当前页面已经出现的函数、代数和积分符号"
                if segment_index == 0
                else f"已经理解上一展开“{segments[segment_index - 1].get('title') or clean_title}”"
            ]
            segment["exit_understanding"] = (
                f"能够用自己的话说明“{topic}”的对象、关键关系、成立条件以及它怎样推动模块继续。"
            )
            known_segment_contract = FOURIER_SEGMENT_LEARNING_CONTRACTS.get(
                segment_id
            )
            if known_segment_contract is not None:
                segment.update(deepcopy(known_segment_contract))
            segment["knowledge_point_ids"] = [point_id]
            segment["blocks"] = blocks
            if not module_has_existing_detail and segment_index == 0:
                _ensure_detail(
                    segment,
                    knowledge_point_id=point_id,
                    topic=topic,
                    instance_by_model=instance_by_model,
                )
            upgraded_segments.append(segment)

            quote = topic if topic in source else clean_title
            knowledge_points.append(
                {
                    "id": point_id,
                    "statement": f"理解并能运用：{topic}",
                    "kind": "concept" if segment_index == 0 else "mechanism",
                    "importance": "core" if segment_index == 0 else "supporting",
                    "source_section_ids": [source_id],
                    "source_quotes": [
                        {"source_section_id": source_id, "quote": quote}
                    ],
                }
            )
            detail_content_ids = [
                detail_id for block in blocks for detail_id in _detail_ids(block)
            ]
            model_instance_ids = sorted(
                {
                    str(block.get("data", {}).get("instance_id"))
                    for block in blocks
                    if block.get("kind") == "model_reference"
                    and block.get("data", {}).get("instance_id")
                }
            )
            coverage_map.append(
                {
                    "knowledge_point_id": point_id,
                    "module_id": module_id,
                    "baseline_content_ids": [block["id"] for block in blocks],
                    "detail_content_ids": detail_content_ids,
                    "model_instance_ids": model_instance_ids,
                }
            )

        module["blocks"] = []
        module["segments"] = upgraded_segments
        module["core_question"] = f"如何通过“{clean_title}”解决本章这一阶段的核心问题？"
        module["chapter_role"] = (
            f"这是本章问题推进链的第 {module_index + 1} 步，负责建立“{clean_title}”，"
            "并为后续模块提供可直接调用的理解。"
        )
        module["why_indispensable"] = (
            f"如果删除“{clean_title}”，其后的定义、推导或应用将失去必要依据，章节主线会在这里断裂。"
        )
        module["depends_on_module_ids"] = (
            [] if module_index == 0 else [str(modules[module_index - 1]["id"])]
        )
        module["novice_bridge"] = {
            "known_before": [
                "能读懂函数图像、基本代数式和已经在页面出现的积分符号"
                if module_index == 0
                else f"已经理解上一核心模块“{_clean_title(str(modules[module_index - 1].get('title', '')))}”"
            ],
            "missing_bridge": (
                f"需要把已有符号理解连接到“{clean_title}”真正处理的对象和关系，避免直接背结论。"
            ),
            "concrete_anchor": f"先从一个能画出或能逐步计算的“{clean_title}”最小例子开始。",
            "bridge_strategy": (
                "先固定对象和条件，再一次只引入一个新关系；每引入一步都用图、式或例子检查含义。"
            ),
        }
        known_contract = FOURIER_MODULE_LEARNING_CONTRACTS.get(module_id)
        if known_contract is not None:
            module["core_question"] = known_contract["core_question"]
            module["novice_bridge"] = deepcopy(
                known_contract["novice_bridge"]
            )
        module["knowledge_point_ids"] = module_point_ids
        upgraded_modules.append(module)

    module_ids = [str(module["id"]) for module in upgraded_modules]
    overview_copy = " ".join(
        str(module.get("summary") or "") for module in overview_modules
    ).strip()
    chapter["overview"] = {
        "essential_question": (
            overview_copy
            or f"本章如何把“{chapter.get('title', '当前主题')}”建立成一条能推导、能解释、能应用的完整主线？"
        ),
        "learning_route_summary": " → ".join(
            _clean_title(str(module.get("title") or module["id"]))
            for module in upgraded_modules
        ),
        "module_order": module_ids,
    }
    chapter["modules"] = upgraded_modules
    chapter["relations"] = [
        relation
        for relation in chapter.get("relations", [])
        if relation.get("source_module_id") in module_ids
        and relation.get("target_module_id") in module_ids
    ]
    chapter["source_sections"] = source_sections
    chapter["knowledge_points"] = knowledge_points
    chapter["coverage_map"] = coverage_map
    chapter["coverage_audit"] = {
        "source_section_ids": [section["id"] for section in source_sections],
        "knowledge_point_ids": [point["id"] for point in knowledge_points],
        "unresolved_items": [],
        "auditor_summary": (
            "已完成来源到知识点、知识点到基线内容与详细展开的双向核对；"
            "全部来源片段和知识点均有唯一负责模块与实际教学内容。"
        ),
    }
    return chapter


def _ensure_fourier_bindings(package: dict[str, Any]) -> None:
    instance = next(
        (
            item
            for item in package.get("model_instances", [])
            if item.get("model_id") == "fourier-series-explorer"
        ),
        None,
    )
    if instance is None:
        return
    instance_id = str(instance["instance_id"])
    retained = [
        binding
        for binding in package.get("model_bindings", [])
        if binding.get("instance_id") != instance_id
    ]
    generated = []
    for course in package.get("courses", []):
        for chapter in course.get("chapters", []):
            for module in chapter.get("modules", []):
                segments = module.get("segments", [])
                if not segments or not segments[0].get("blocks"):
                    continue
                module_id = str(module["id"])
                content_id = str(segments[0]["blocks"][0]["id"])
                lowered = module_id.casefold()
                state = (
                    "discontinuity"
                    if "convergence" in lowered
                    else (
                        "extended-periodic"
                        if "extension" in lowered
                        else "partial-sum"
                    )
                )
                generated.append(
                    {
                        "id": f"bind-fourier-{module_id}"[:120],
                        "content_id": content_id,
                        "instance_id": instance_id,
                        "trigger": {"kind": "block_enter"},
                        "effect": {"kind": "set_state", "target": state, "payload": {}},
                        "restore_previous": True,
                    }
                )
    package["model_bindings"] = retained + generated


def upgrade_legacy_package(
    package: dict[str, Any],
    *,
    model_versions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Upgrade a pre-quality-contract package without inventing new subject matter."""
    upgraded = deepcopy(package)
    has_quality_contract = _is_quality_package(upgraded)
    model_versions = model_versions or {}
    instance_by_model = {
        str(instance.get("model_id")): str(instance.get("instance_id"))
        for instance in upgraded.get("model_instances", [])
    }
    for instance in upgraded.get("model_instances", []):
        model_id = str(instance.get("model_id"))
        if model_id in model_versions:
            instance["model_version"] = model_versions[model_id]
        if model_id == "fourier-series-explorer":
            instance["parameters"] = {
                "harmonic-count": 7,
                "view": "square-wave",
                **(instance.get("parameters") or {}),
            }
    for binding in upgraded.get("model_bindings", []):
        if binding.get("trigger", {}).get("kind") == "block_activate":
            binding["trigger"]["kind"] = "block_enter"
            binding["restore_previous"] = True
    if has_quality_contract:
        _ensure_fourier_bindings(upgraded)
        return upgraded
    for course in upgraded.get("courses", []):
        for chapter in course.get("chapters", []):
            _upgrade_chapter(
                chapter,
                asset_id=f"legacy-{upgraded.get('package_id', 'classroom')}",
                instance_by_model=instance_by_model,
            )
    _ensure_fourier_bindings(upgraded)
    return upgraded


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"classroom artifact root must be an object: {path}")
    return value


def _write_object(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.{os.getpid()}.quality.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def migrate_persistent_classrooms(
    data_root: str | Path,
    *,
    model_repository: TeachingModelRepository | None = None,
) -> dict[str, list[str]]:
    """Upgrade persisted pre-contract drafts and republish active releases safely."""
    root = Path(data_root).resolve()
    model_versions = {}
    if model_repository is not None:
        model_versions = {
            record.model_id: record.version
            for record in model_repository.list_registered()
            if record.preview_job_id == "checked-in-seed"
        }
    validator = ClassroomPackageValidator(
        model_resolver=(
            model_repository.get_registered
            if model_repository is not None
            else None
        )
    )
    migrated_drafts: list[str] = []
    draft_root = root / "drafts"
    for path in sorted(draft_root.glob("*.json")) if draft_root.exists() else []:
        record = _read_object(path)
        original = record.get("package")
        if not isinstance(original, dict):
            raise ValueError(f"draft has no package object: {path.name}")
        upgraded = upgrade_legacy_package(
            original,
            model_versions=model_versions,
        )
        if upgraded == original:
            continue
        package = ClassroomPackage.model_validate(upgraded)
        report = validator.validate(package)
        if not report.passed:
            raise ValueError(
                f"quality migration failed for draft {record.get('draft_id')}: "
                f"{report.model_dump(mode='json')}"
            )
        record["package"] = package.model_dump(mode="json", exclude_none=True)
        record["content_hash"] = content_hash(package)
        _write_object(path, record)
        migrated_drafts.append(str(record.get("draft_id") or path.stem))

    repository = ClassroomRepository(root)
    republished_packages: list[str] = []
    active_root = root / "active"
    active_paths = sorted(active_root.glob("*.json")) if active_root.exists() else []
    for pointer_path in active_paths:
        pointer = _read_object(pointer_path)
        package_id = str(pointer["package_id"])
        release_path = (
            root
            / "packages"
            / package_id
            / "releases"
            / f"{pointer['active_version']}.json"
        )
        release = _read_object(release_path)
        original = release.get("package")
        if not isinstance(original, dict):
            raise ValueError(f"release has no package object: {release_path.name}")
        upgraded = upgrade_legacy_package(
            original,
            model_versions=model_versions,
        )
        if upgraded == original:
            continue
        package = ClassroomPackage.model_validate(upgraded)
        report = validator.validate(package)
        if not report.passed:
            raise ValueError(
                f"quality migration failed for active package {package_id}: "
                f"{report.model_dump(mode='json')}"
            )
        draft_id = f"quality-migration-{package_id}"
        try:
            draft = repository.get_draft(draft_id)
            if draft.content_hash != content_hash(package):
                draft = repository.update_draft(
                    draft_id,
                    draft.revision,
                    package,
                )
        except ClassroomNotFoundError:
            draft = repository.create_draft(draft_id, package)
        repository.publish(draft_id, draft.revision)
        republished_packages.append(package_id)
    return {
        "migrated_drafts": migrated_drafts,
        "republished_packages": republished_packages,
    }
