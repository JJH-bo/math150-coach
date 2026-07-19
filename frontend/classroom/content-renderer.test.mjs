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
