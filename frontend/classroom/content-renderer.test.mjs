import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./content-renderer.js", import.meta.url), "utf8");
const { renderModule } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);

test("renderer connects formulas, explanations, examples, and details", () => {
  const html = renderModule({
    id: "limit-core",
    title: "极限核心",
    summary: "趋近机制",
    blocks: [
      { id: "intro", kind: "prose", data: { markdown: "先看趋近。" }, detail_branches: [{
        id: "detail-1", title: "为什么不是代入", blocks: [{
          id: "detail-text", kind: "prose", data: { markdown: "研究邻域。" },
          detail_branches: [],
        }],
      }] },
      { id: "formula", kind: "formula_explanation", data: {
        latex: "\\lim_{x\\to a}f(x)=L", explanation: "函数值趋近 L。",
      }, detail_branches: [] },
      { id: "example", kind: "worked_example", data: {
        prompt: "观察函数", steps: ["因式分解", "得到极限"],
      }, detail_branches: [] },
    ],
    segments: [],
  });

  assert.match(html, /data-content-id="formula"/);
  assert.match(html, /class="formula-pair"/);
  assert.match(html, /class="math-typeset"/);
  assert.match(html, /data-latex="\\lim_\{x\\to a\}f\(x\)=L"/);
  assert.doesNotMatch(html, /class="limit-operator"|class="math-fraction"/);
  assert.match(html, /<details[^>]+data-detail-id="detail-1"/);
  assert.match(html, /<ol class="solution-steps">/);
});

test("renderer accepts GPT-shaped comparison items and multi-formula explanations", () => {
  const html = renderModule({
    id: "gpt-shaped",
    title: "GPT 实际数据",
    blocks: [
      {
        id: "comparison-items",
        kind: "comparison",
        data: {
          items: [
            { title: "奇函数", body: "只保留正弦项" },
            { title: "偶函数", body: "只保留余弦项" },
          ],
        },
        detail_branches: [],
      },
      {
        id: "formulae",
        kind: "formula_explanation",
        data: {
          title: "半区间展开",
          text: "选择奇延拓或偶延拓，会得到不同的系数公式。",
          formulae: [
            {
              latex: String.raw`b_n=\frac{2}{l}\int_0^l f(x)\sin\frac{n\pi x}{l}\,dx`,
              explanation: "奇延拓对应正弦级数。",
            },
            {
              latex: String.raw`a_n=\frac{2}{l}\int_0^l f(x)\cos\frac{n\pi x}{l}\,dx`,
              explanation: "偶延拓对应余弦级数。",
            },
          ],
        },
        detail_branches: [],
      },
    ],
    segments: [],
  });

  assert.match(html, /奇函数/);
  assert.match(html, /偶函数/);
  assert.match(html, /只保留正弦项/);
  assert.match(html, /半区间展开/);
  assert.match(html, /奇延拓对应正弦级数/);
  assert.match(html, /偶延拓对应余弦级数/);
  assert.equal((html.match(/class="math-typeset"/g) || []).length, 2);
});

test("long formulas use a stacked readable layout", () => {
  const html = renderModule({
    id: "long-formula",
    title: "长公式",
    blocks: [{
      id: "series",
      kind: "formula_explanation",
      data: {
        latex: String.raw`f(x)\sim\frac{a_0}{2}+\sum_{n=1}^{\infty}\left(a_n\cos\frac{n\pi x}{l}+b_n\sin\frac{n\pi x}{l}\right)`,
        explanation: "长公式不能被两栏布局裁掉。",
      },
      detail_branches: [],
    }],
    segments: [],
  });

  assert.match(html, /class="formula-pair is-long"/);
});

test("legacy string comparison items remain visible instead of empty cards", () => {
  const html = renderModule({
    id: "legacy-comparison",
    title: "旧课堂也必须可读",
    blocks: [{
      id: "comparison",
      kind: "comparison",
      data: {
        title: "三个路径",
        items: ["先判断周期", "再判断奇偶性", "最后计算系数"],
      },
      detail_branches: [],
    }],
    segments: [],
  });

  assert.match(html, /先判断周期/);
  assert.match(html, /再判断奇偶性/);
  assert.match(html, /最后计算系数/);
  assert.doesNotMatch(html, /<strong><\/strong>\s*<p><\/p>/);
});

test("legacy named comparison cards keep both their label and explanation", () => {
  const html = renderModule({
    id: "legacy-named-comparison",
    title: "旧命名结构",
    blocks: [{
      id: "comparison",
      kind: "comparison",
      data: {
        items: [
          {name: "奇函数", focus: "只保留正弦项"},
          {name: "偶函数", focus: "只保留常数项与余弦项"},
        ],
      },
      detail_branches: [],
    }],
    segments: [],
  });

  assert.match(html, /奇函数/);
  assert.match(html, /只保留正弦项/);
  assert.match(html, /偶函数/);
  assert.match(html, /只保留常数项与余弦项/);
});

test("module and detailed expansion render their learning relationships", () => {
  const html = renderModule({
    id: "limit-core",
    title: "极限机制",
    core_question: "点值不存在时为什么仍然可以有极限？",
    chapter_role: "建立后续连续与导数需要的邻域观点。",
    why_indispensable: "删除它以后，极限会退化成代入技巧。",
    novice_bridge: {
      known_before: ["会读取函数值"],
      missing_bridge: "从单点转向邻域",
      concrete_anchor: "沿图像走向 x=1",
      bridge_strategy: "先看图，再写记号",
    },
    blocks: [{
      id: "intro",
      kind: "prose",
      data: { text: "观察邻域。" },
      detail_branches: [{
        id: "detail",
        title: "换一种方式",
        trigger_question: "为什么不是直接代入？",
        learning_obstacle: "混淆点值和邻域趋势。",
        representation: "counterexample",
        focus_relation: "单点改变不改变周围趋势。",
        bridge_steps: ["遮住单点", "改变单点后重新比较"],
        return_connection: "回到 x→a，它不要求 x=a。",
        blocks: [
          { id: "d1", kind: "prose", data: { text: "先看周围。" }, detail_branches: [] },
          { id: "d2", kind: "prose", data: { text: "再改单点。" }, detail_branches: [] },
        ],
      }],
    }],
    segments: [],
  });

  assert.match(html, /核心问题/);
  assert.match(html, /点值不存在时为什么仍然可以有极限/);
  assert.match(html, /本章作用/);
  assert.match(html, /进入这一步前的桥梁/);
  assert.match(html, /当前障碍/);
  assert.match(html, /遮住单点/);
  assert.match(html, /接回主线/);
});

test("renderer supports the complete layout vocabulary", () => {
  const kinds = [
    ["heading", { text: "标题", level: 3 }],
    ["callout", { title: "结论", markdown: "核心结论" }],
    ["math", { latex: "x^2" }],
    ["derivation", { title: "推导", steps: ["第一步", "第二步"] }],
    ["comparison", { left: { title: "A", body: "左" }, right: { title: "B", body: "右" } }],
    ["code_explanation", { language: "js", code: "let x=1;", lines: ["初始化"] }],
    ["table", { headers: ["A"], rows: [["1"]] }],
    ["matrix", { values: [[1, 2], [3, 4]] }],
    ["image", { uri: "/image.png", alt: "示意图", caption: "图注" }],
    ["model_reference", { instance_id: "limit-view", label: "观察模型" }],
    ["group", { title: "组合", blocks: [{ id: "nested", kind: "prose", data: { markdown: "内部" } }] }],
  ];
  const html = renderModule({
    id: "all",
    title: "全部组件",
    blocks: kinds.map(([kind, data], index) => ({
      id: `b-${index}`, kind, data, detail_branches: [],
    })),
    segments: [],
  });

  for (const kind of kinds.map(([value]) => value)) {
    assert.match(html, new RegExp(`block-${kind.replace("_", "-")}`));
  }
});

test("renderer escapes authored text and keeps unknown blocks readable", () => {
  const html = renderModule({
    id: "safe",
    title: "<script>alert(1)</script>",
    blocks: [{
      id: "unknown",
      kind: "future_kind",
      data: { text: "<img src=x onerror=alert(1)>" },
      detail_branches: [],
    }],
    segments: [],
  });

  assert.doesNotMatch(html, /<script>|<img/);
  assert.match(html, /&lt;script&gt;/);
  assert.match(html, /暂不支持的内容类型/);
});
