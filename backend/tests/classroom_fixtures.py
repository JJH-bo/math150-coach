from __future__ import annotations

from typing import Any


def classroom_package_payload() -> dict[str, Any]:
    return {
        "schema_version": "classroom_package_v1",
        "package_id": "calculus-foundations",
        "title": "微积分基础课堂",
        "courses": [
            {
                "id": "math-1",
                "title": "高等数学",
                "chapters": [
                    {
                        "id": "limits",
                        "title": "极限",
                        "modules": [
                            {
                                "id": "limit-core",
                                "title": "极限的核心机制",
                                "summary": "从趋近过程理解极限，而不是把它当成代入规则。",
                                "core_question": "函数在点上未定义时，为什么仍然可以有极限？",
                                "chapter_role": "建立极限的邻域观点，为连续、导数和积分提供共同语言。",
                                "why_indispensable": "没有邻域观点，后续极限运算会退化成容易失效的代入技巧。",
                                "depends_on_module_ids": [],
                                "novice_bridge": {
                                    "known_before": [
                                        "会读取函数值",
                                        "理解自变量可以不断接近某个数",
                                    ],
                                    "missing_bridge": "把关注点从 x=a 的单个点转向 a 周围的一整段邻域。",
                                    "concrete_anchor": "沿着 y=x+1 的图像从左右两侧走向 x=1。",
                                    "bridge_strategy": "先观察具体图像，再把稳定接近的过程压缩成极限记号。",
                                },
                                "knowledge_point_ids": [
                                    "kp-limit-neighborhood",
                                    "kp-limit-definition",
                                    "kp-removable-example",
                                ],
                                "blocks": [],
                                "segments": [
                                    {
                                        "id": "limit-neighborhood-segment",
                                        "title": "先把视线从点值移到邻域",
                                        "question_answered": "极限究竟观察一个点，还是观察点附近的过程？",
                                        "bridge_from_previous": "过去读取函数时总是直接看 f(a)，现在需要观察 x 在 a 周围移动时发生什么。",
                                        "mechanism": "极限忽略单个点的偶然取值，比较左右邻域中的函数值是否共同稳定接近同一目标。",
                                        "entry_assumptions": [
                                            "会读取函数图像",
                                            "理解接近与相等不同",
                                        ],
                                        "exit_understanding": "能够区分点值与邻域趋势。",
                                        "knowledge_point_ids": [
                                            "kp-limit-neighborhood"
                                        ],
                                        "blocks": [
                                            {
                                                "id": "limit-intro",
                                                "kind": "prose",
                                                "knowledge_point_ids": [
                                                    "kp-limit-neighborhood"
                                                ],
                                                "data": {
                                                    "markdown": "极限描述的是变量趋近时，函数值稳定接近什么，而不是只读取一个孤立点。"
                                                },
                                                "detail_branches": [
                                                    {
                                                        "bridge_steps": [
                                                            "先遮住图像上 x=a 的单个点，只观察两侧曲线。",
                                                            "再任意改变这个点的取值，比较两侧趋近趋势是否变化。",
                                                        ],
                                                        "id": "limit-intro-detail",
                                                        "focus_relation": "点值属于单个位置，极限属于去心邻域中的共同趋势。",
                                                        "learning_obstacle": "把极限误认为把 a 直接代入函数后得到的点值。",
                                                        "representation": "counterexample",
                                                        "return_connection": "回到极限记号时，x→a 表示接近但不要求 x=a。",
                                                        "title": "为什么不是直接代入",
                                                        "trigger_question": "为什么函数在 x=a 处没有值，极限却仍然存在？",
                                                        "blocks": [
                                                            {
                                                                "id": "limit-intro-detail-prose",
                                                                "kind": "prose",
                                                                "knowledge_point_ids": [
                                                                    "kp-limit-neighborhood"
                                                                ],
                                                                "data": {
                                                                    "markdown": "趋近研究的是邻域行为：即使点值不存在或被单独改掉，周围的共同趋势仍然可能保持不变。"
                                                                },
                                                            },
                                                            {
                                                                "id": "limit-intro-detail-example",
                                                                "kind": "worked_example",
                                                                "knowledge_point_ids": [
                                                                    "kp-limit-neighborhood"
                                                                ],
                                                                "data": {
                                                                    "prompt": "把 x=1 处的点值依次改成 2、100 和不存在，比较极限。",
                                                                    "steps": [
                                                                        "先只观察 x≠1 时的曲线 y=x+1",
                                                                        "三种改法都没有改变 1 附近的曲线",
                                                                        "所以三种函数在 x→1 时都趋近 2",
                                                                    ],
                                                                },
                                                            }
                                                        ],
                                                    }
                                                ],
                                            }
                                        ],
                                    },
                                    {
                                        "id": "limit-definition-segment",
                                        "title": "把邻域中的稳定接近写成极限记号",
                                        "question_answered": "极限记号怎样压缩刚才观察到的趋近过程？",
                                        "bridge_from_previous": "已经能口头描述邻域趋势，现在需要一个不会与点值混淆的数学记号。",
                                        "mechanism": "x→a 指定自变量的运动方向，f(x)→L 指定函数值共同稳定接近的目标。",
                                        "entry_assumptions": [
                                            "理解点值与邻域趋势不同",
                                            "认识函数记号 f(x)",
                                        ],
                                        "exit_understanding": "能够逐个解释极限式中的对象和关系。",
                                        "knowledge_point_ids": [
                                            "kp-limit-definition"
                                        ],
                                        "blocks": [
                                            {
                                                "id": "limit-formula",
                                                "kind": "formula_explanation",
                                                "knowledge_point_ids": [
                                                    "kp-limit-definition"
                                                ],
                                                "data": {
                                                    "latex": "\\lim_{x\\to a}f(x)=L",
                                                    "explanation": "当 x 足够接近 a 时，f(x) 可以任意接近 L；这里描述的是邻域中的对应关系。",
                                                },
                                            }
                                        ],
                                    },
                                    {
                                        "id": "limit-example-segment",
                                        "title": "用一个可消去间断点观察极限",
                                        "question_answered": "可去间断点为什么不妨碍极限存在？",
                                        "bridge_from_previous": "已经把极限看成邻域行为，现在用一个点上有洞的函数检验这个观点。",
                                        "mechanism": "约去只在 x=1 处为零的公共因子后，去心邻域内的函数与 x+1 完全相同。",
                                        "entry_assumptions": [
                                            "理解趋近不等于取到",
                                            "会做因式分解",
                                        ],
                                        "exit_understanding": "能够解释点值与极限为什么可以不同。",
                                        "knowledge_point_ids": [
                                            "kp-removable-example"
                                        ],
                                        "blocks": [
                                            {
                                                "id": "limit-example",
                                                "kind": "worked_example",
                                                "knowledge_point_ids": [
                                                    "kp-removable-example"
                                                ],
                                                "data": {
                                                    "prompt": "观察 (x²-1)/(x-1) 在 x→1 时的行为。",
                                                    "steps": [
                                                        "因式分解 x²-1=(x-1)(x+1)",
                                                        "在 x≠1 的邻域中化简为 x+1",
                                                        "因此趋近值为 2",
                                                    ],
                                                },
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                        "relations": [],
                        "source_sections": [
                            {
                                "id": "source-limit-chapter",
                                "asset_id": "lecture-limit",
                                "filename": "极限讲义.pdf",
                                "order": 1,
                                "page": "1-2",
                                "heading": "极限的定义与可去间断点",
                                "content": (
                                    "极限研究自变量趋近时函数值的邻域行为。"
                                    "当 x 趋近 a 时，如果 f(x) 任意接近 L，"
                                    "就称 L 为函数在 a 处的极限。"
                                    "例如 (x²-1)/(x-1) 在 x 趋近 1 时的极限为 2。"
                                ),
                                "content_hash": "sha256:source-limit-chapter",
                            }
                        ],
                        "knowledge_points": [
                            {
                                "id": "kp-limit-neighborhood",
                                "statement": "极限描述自变量趋近时函数值的邻域行为。",
                                "kind": "concept",
                                "importance": "core",
                                "source_section_ids": ["source-limit-chapter"],
                                "source_quotes": [
                                    {
                                        "source_section_id": "source-limit-chapter",
                                        "quote": "极限研究自变量趋近时函数值的邻域行为",
                                    }
                                ],
                            },
                            {
                                "id": "kp-limit-definition",
                                "statement": "当 x 趋近 a 时，f(x) 任意接近 L。",
                                "kind": "definition",
                                "importance": "core",
                                "source_section_ids": ["source-limit-chapter"],
                                "source_quotes": [
                                    {
                                        "source_section_id": "source-limit-chapter",
                                        "quote": "当 x 趋近 a 时，如果 f(x) 任意接近 L",
                                    }
                                ],
                            },
                            {
                                "id": "kp-removable-example",
                                "statement": "可去间断点的点值不妨碍邻域极限存在。",
                                "kind": "example",
                                "importance": "supporting",
                                "source_section_ids": ["source-limit-chapter"],
                                "source_quotes": [
                                    {
                                        "source_section_id": "source-limit-chapter",
                                        "quote": "(x²-1)/(x-1) 在 x 趋近 1 时的极限为 2",
                                    }
                                ],
                            },
                        ],
                        "coverage_map": [
                            {
                                "knowledge_point_id": "kp-limit-neighborhood",
                                "module_id": "limit-core",
                                "baseline_content_ids": ["limit-intro"],
                                "detail_content_ids": [
                                    "limit-intro-detail-prose",
                                    "limit-intro-detail-example"
                                ],
                                "model_instance_ids": [],
                            },
                            {
                                "knowledge_point_id": "kp-limit-definition",
                                "module_id": "limit-core",
                                "baseline_content_ids": ["limit-formula"],
                                "detail_content_ids": [],
                                "model_instance_ids": [],
                            },
                            {
                                "knowledge_point_id": "kp-removable-example",
                                "module_id": "limit-core",
                                "baseline_content_ids": ["limit-example"],
                                "detail_content_ids": [],
                                "model_instance_ids": [],
                            },
                        ],
                        "coverage_audit": {
                            "source_section_ids": ["source-limit-chapter"],
                            "knowledge_point_ids": [
                                "kp-limit-neighborhood",
                                "kp-limit-definition",
                                "kp-removable-example",
                            ],
                            "unresolved_items": [],
                            "auditor_summary": "来源、知识点与基础学习内容已经逐项核对。",
                        },
                        "overview": {
                            "essential_question": "函数不断接近某一点时，怎样描述稳定的目标值？",
                            "learning_route_summary": "先区分点值与邻域行为，再建立极限记号，最后用可去间断点落地。",
                            "module_order": ["limit-core"],
                        },
                    }
                ],
            }
        ],
        "model_instances": [],
        "assets": [],
    }
