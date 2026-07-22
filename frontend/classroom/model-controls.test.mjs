import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("./model-controls.js", import.meta.url),
  "utf8",
).catch(() => "export function buildModelControlDescriptors(){return []}\nexport function coerceControlValue(){return null}");
const {
  buildModelControlDescriptors,
  coerceControlValue,
} = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);

const manifest = {
  parameters: [
    { id: "harmonics", type: "integer", default: 5, minimum: 1, maximum: 30, description: "谐波项数" },
    { id: "delta", type: "number", default: 0.5, minimum: 0.05, maximum: 2, description: "邻域宽度" },
    { id: "extension", type: "choice", default: "even", choices: ["even", "odd"], description: "延拓方式" },
    { id: "show-average", type: "boolean", default: true, description: "显示平均值" },
  ],
  actions: [
    { id: "next-stage", title: "下一阶段" },
    { id: "reset-view", title: "重置" },
  ],
};

test("allowed model vocabulary becomes real learner controls", () => {
  const controls = buildModelControlDescriptors(manifest, {
    allowed_interactions: ["parameter_change", "explicit_control"],
    parameters: { harmonics: 8 },
  });

  assert.deepEqual(
    controls.map((item) => [item.id, item.control]),
    [
      ["harmonics", "range"],
      ["delta", "range"],
      ["extension", "select"],
      ["show-average", "checkbox"],
      ["next-stage", "button"],
      ["reset-view", "button"],
    ],
  );
  assert.equal(controls[0].value, 8);
  assert.equal(controls[1].value, 0.5);
});

test("undeclared interaction modes do not expose fake controls", () => {
  const controls = buildModelControlDescriptors(manifest, {
    allowed_interactions: [],
    parameters: {},
  });

  assert.deepEqual(controls, []);
});

test("control values are converted back to their declared parameter types", () => {
  assert.equal(coerceControlValue({ type: "integer" }, "12"), 12);
  assert.equal(coerceControlValue({ type: "number" }, "0.25"), 0.25);
  assert.equal(coerceControlValue({ type: "boolean" }, "", true), true);
  assert.equal(coerceControlValue({ type: "choice" }, "odd"), "odd");
});
