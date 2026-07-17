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
                                "blocks": [
                                    {
                                        "id": "limit-intro",
                                        "kind": "prose",
                                        "data": {
                                            "markdown": "极限描述的是变量趋近时，函数值稳定接近什么。"
                                        },
                                        "detail_branches": [
                                            {
                                                "id": "limit-intro-detail",
                                                "title": "为什么不是直接代入",
                                                "blocks": [
                                                    {
                                                        "id": "limit-intro-detail-prose",
                                                        "kind": "prose",
                                                        "data": {
                                                            "markdown": "趋近研究的是邻域行为，点值可以不存在或不同。"
                                                        },
                                                    }
                                                ],
                                            }
                                        ],
                                    },
                                    {
                                        "id": "limit-formula",
                                        "kind": "formula_explanation",
                                        "data": {
                                            "latex": "\\lim_{x\\to a}f(x)=L",
                                            "explanation": "当 x 足够接近 a 时，f(x) 可以任意接近 L。",
                                        },
                                    },
                                ],
                                "segments": [
                                    {
                                        "id": "limit-example-segment",
                                        "title": "用一个可消去间断点观察极限",
                                        "blocks": [
                                            {
                                                "id": "limit-example",
                                                "kind": "worked_example",
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
                    }
                ],
            }
        ],
        "model_instances": [],
        "assets": [],
    }
