import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./scene-runtime.js", import.meta.url), "utf8");
const {
  activeExpansion,
  expansionChildren,
  projectRevealedSteps,
  sessionProgress,
} = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);

function session() {
  return {
    revision: 4,
    baseline_steps: [
      { id: "intuition", title: "直觉", blocks: [{ id: "intuition-text" }] },
      { id: "mechanism", title: "机制", blocks: [{ id: "mechanism-formula" }] },
      { id: "return", title: "回到模型", blocks: [{ id: "return-model" }] },
    ],
    revealed_step_ids: ["intuition", "mechanism"],
    active_content_id: "cancel-bridge",
    expansions: [
      {
        id: "cancel",
        parent_content_id: "mechanism-formula",
        blocks: [{ id: "cancel-bridge" }],
      },
      {
        id: "paired",
        parent_content_id: "cancel-bridge",
        parent_expansion_id: "cancel",
        blocks: [{ id: "paired-intervals" }],
      },
    ],
    expansion_stack: ["cancel"],
  };
}

test("baseline projection reveals only fixed published steps", () => {
  const projected = projectRevealedSteps(session());

  assert.deepEqual(projected.map((step) => step.id), ["intuition", "mechanism"]);
  assert.equal(sessionProgress(session()).revealed, 2);
  assert.equal(sessionProgress(session()).total, 3);
  assert.equal(sessionProgress(session()).hasNext, true);
});

test("detailed expansions stay attached to their exact content target", () => {
  const current = session();

  assert.deepEqual(
    expansionChildren(current, "mechanism-formula").map((item) => item.id),
    ["cancel"],
  );
  assert.deepEqual(
    expansionChildren(current, "cancel-bridge").map((item) => item.id),
    ["paired"],
  );
});

test("active expansion follows the server expansion stack", () => {
  assert.equal(activeExpansion(session()).id, "cancel");
  assert.equal(activeExpansion({ ...session(), expansion_stack: [] }), null);
});

test("scene renderer inserts a detailed branch directly under its parent", async () => {
  const contentSource = await readFile(
    new URL("./content-renderer.js", import.meta.url),
    "utf8",
  );
  const contentUrl = `data:text/javascript;base64,${
    Buffer.from(contentSource).toString("base64")
  }`;
  const rendererSource = (
    await readFile(new URL("./scene-renderer.js", import.meta.url), "utf8")
  ).replace("./content-renderer.js", contentUrl);
  const { renderLearningSession } = await import(
    `data:text/javascript;base64,${Buffer.from(rendererSource).toString("base64")}`
  );
  const current = session();
  current.baseline_steps[0].blocks[0] = {
    id: "intuition-text",
    kind: "prose",
    data: { markdown: "基础直觉" },
  };
  current.baseline_steps[1].blocks[0] = {
    id: "mechanism-formula",
    kind: "prose",
    data: { markdown: "抵消机制" },
  };
  current.baseline_steps[1] = {
    ...current.baseline_steps[1],
    question_answered: "不同频率为什么能彼此分离？",
    bridge_from_previous: "已经看见频率不同，现在比较完整周期上的乘积面积。",
    mechanism: "异频乘积的正负面积在完整周期上成对抵消。",
    entry_assumptions: ["理解正负面积", "会读取周期"],
    exit_understanding: "能把正交积分为零解释成面积抵消。",
  };
  current.expansions[0] = {
    ...current.expansions[0],
    title: "为什么抵消",
    learner_question: "为什么？",
    focus_relation: "正负面积配对",
    learning_obstacle: "只记住积分等于零，没有看见抵消过程。",
    bridge_steps: ["切开完整周期", "把正负小区间配对"],
    understanding_target: "看见每块正面积对应一块负面积。",
    representation: "animated_visual",
    return_connection: "重新接回正交性",
    blocks: [{
      id: "cancel-bridge",
      kind: "prose",
      data: { markdown: "详细动画解释" },
    }],
  };
  current.expansions[1] = {
    ...current.expansions[1],
    title: "为什么成对",
    learner_question: "为什么成对？",
    focus_relation: "区间平移",
    representation: "smaller_example",
    return_connection: "回到面积抵消",
    blocks: [{
      id: "paired-intervals",
      kind: "prose",
      data: { markdown: "更小区间解释" },
    }],
  };

  const html = renderLearningSession(current, {
    title: "傅里叶系数",
    summary: "从频率检测理解系数。",
    core_question: "系数怎样从混合信号中只检出一个频率？",
    chapter_role: "建立后续收敛与应用所需的系数机制。",
    novice_bridge: {
      missing_bridge: "从图像相似转向完整周期上的乘积面积。",
      concrete_anchor: "先比较同频和异频波形。",
    },
  });

  assert.doesNotMatch(html, /return-model/);
  assert.ok(html.indexOf("抵消机制") < html.indexOf("为什么抵消"));
  assert.ok(html.indexOf("为什么抵消") < html.indexOf("为什么成对"));
  assert.match(html, /继续展开基础路线/);
  assert.match(html, /2 \/ 3/);
  assert.match(html, /系数怎样从混合信号中只检出一个频率/);
  assert.match(html, /不同频率为什么能彼此分离/);
  assert.match(html, /从上一理解走到这里/);
  assert.match(html, /异频乘积的正负面积/);
  assert.match(html, /当前障碍/);
  assert.match(html, /切开完整周期/);
});

test("session client restores access and sends revision-safe reveal", async () => {
  const clientSource = await readFile(
    new URL("./session-client.js", import.meta.url),
    "utf8",
  );
  const { createSessionClient } = await import(
    `data:text/javascript;base64,${Buffer.from(clientSource).toString("base64")}`
  );
  const calls = [];
  const fetch = async (url, options = {}) => {
    calls.push({ url, options });
    return {
      ok: true,
      json: async () => (
        url.endsWith("/return")
          ? { session_id: "ls-123", revision: 3 }
          : url.endsWith("/reveal")
          ? { session_id: "ls-123", revision: 2 }
          : {
              session: { session_id: "ls-123", revision: 1 },
              access_token: "secret-token",
            }
      ),
    };
  };
  const client = createSessionClient({ apiBase: "/api/classroom/v1", fetch });
  const access = await client.create({
    packageId: "fourier",
    moduleId: "coefficients",
  });
  const revealed = await client.reveal(access, 1);
  const returned = await client.returnToParent(access, 2, "return-1");

  assert.equal(access.accessToken, "secret-token");
  assert.equal(revealed.revision, 2);
  assert.equal(returned.revision, 3);
  assert.equal(calls[1].url, "/api/classroom/v1/learning-sessions/ls-123/reveal");
  assert.deepEqual(JSON.parse(calls[1].options.body), {
    access_token: "secret-token",
    expected_revision: 1,
  });
  assert.deepEqual(JSON.parse(calls[2].options.body), {
    access_token: "secret-token",
    expected_revision: 2,
    idempotency_key: "return-1",
  });
});
