const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

async function main() {
  const baseUrl = process.argv[2];
  const outputRoot = path.resolve(process.argv[3]);
  const studioKey = process.env.STUDIO_API_KEY;
  fs.mkdirSync(outputRoot, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.MODEL_PREVIEW_BROWSER || undefined,
  });
  const errors = [];
  const requests = [];
  const report = { base_url: baseUrl, errors, requests, failed_responses: [], checks: {} };
  try {
    const desktop = await browser.newContext({ viewport: { width: 1440, height: 960 }, deviceScaleFactor: 1 });
    const page = await desktop.newPage();
    page.on("pageerror", (error) => errors.push(String(error)));
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(`console: ${message.text()}`);
    });
    page.on("request", (request) => requests.push(request.url()));
    page.on("response", (response) => {
      if (response.status() >= 400) report.failed_responses.push({ status: response.status(), url: response.url() });
    });
    await page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
    report.checks.root_redirected_to_classroom =
      new URL(page.url()).pathname === "/classroom/";
    await page.waitForSelector(".module-destination");
    await page.screenshot({ path: path.join(outputRoot, "desktop-atlas.png") });
    report.checks.module_destinations = await page.locator(".module-destination").count();

    await page.locator(".module-destination").first().click();
    await page.waitForSelector("#lessonContent .baseline-step");
    await page.waitForSelector("#modelRoot canvas");
    report.checks.initial_revealed_steps = await page.locator(".baseline-step").count();
    await page.locator("#revealNextStep").click();
    await page.waitForFunction(() =>
      document.querySelectorAll(".baseline-step").length === 2
    );
    await page.waitForSelector("#lessonContent .formula-pair");
    await page.screenshot({ path: path.join(outputRoot, "desktop-classroom.png") });
    report.checks.formula_pair_visible = await page.locator(".formula-pair").isVisible();
    report.checks.model_visible = await page.locator("#modelRoot canvas").isVisible();
    report.checks.reveal_added_one_stable_step =
      await page.locator(".baseline-step").count() === 2;
    report.checks.formula_typeset =
      await page.locator(".formula mjx-container").count() > 0;

    const access = await page.evaluate(() => {
      const key = Object.keys(localStorage)
        .find((item) => item.startsWith("math150-learning-session-v1:"));
      return key ? JSON.parse(localStorage.getItem(key)) : null;
    });
    if (!access?.sessionId) throw new Error("learning session was not persisted");
    const studioHeaders = {
      Authorization: `Bearer ${studioKey}`,
      "Content-Type": "application/json",
    };
    const studioGet = async () => {
      const response = await fetch(
        `${baseUrl}/api/studio/v1/learning-sessions/${access.sessionId}`,
        { headers: studioHeaders },
      );
      if (!response.ok) throw new Error(`studio get failed: ${response.status}`);
      return response.json();
    };
    const studioPatch = async (body, key) => {
      const response = await fetch(
        `${baseUrl}/api/studio/v1/learning-sessions/${access.sessionId}/scene`,
        {
          method: "PATCH",
          headers: { ...studioHeaders, "Idempotency-Key": key },
          body: JSON.stringify(body),
        },
      );
      if (!response.ok) {
        throw new Error(`studio patch failed: ${response.status} ${await response.text()}`);
      }
      return response.json();
    };
    let liveSession = await studioGet();
    const parentBlock = liveSession.baseline_steps[0].blocks[0].id;
    liveSession = await studioPatch({
      expected_revision: liveSession.revision,
      pedagogical_intent: "把抽象的趋近关系改写成可直接比较的两幅局部图景",
      expansion: {
        id: "live-limit-visual",
        title: "先把“趋近”看成镜头不断拉近",
        parent_content_id: parentBlock,
        parent_expansion_id: null,
        learner_question: "这里的趋近和直接代入到底有什么区别？",
        preserved_context: ["极限研究邻域行为", "当前基础路线保持不变"],
        focus_relation: "只拆开趋近过程，不改写原来的极限结论。",
        representation: "annotated_diagram",
        blocks: [
          {
            id: "live-limit-lens",
            kind: "comparison",
            data: {
              items: [
                { title: "直接代入", body: "只看 x=a 这一点，得到的是点值。" },
                { title: "观察极限", body: "不断缩小 a 周围的邻域，看附近函数值稳定靠近哪里。" },
              ],
            },
          },
          {
            id: "live-limit-formula",
            kind: "formula_explanation",
            data: {
              title: "镜头缩小时保持不变的关系",
              formulae: [
                {
                  latex: "\\lim_{x\\to a} f(x)=L",
                  explanation: "x 可以始终不等于 a；真正被追踪的是附近的 f(x)。",
                },
              ],
            },
          },
        ],
        model_commands: [],
        return_connection: "理解邻域中的稳定趋势后，回到主线继续研究极限公式。",
      },
    }, "browser-live-expansion-1");
    await page.waitForSelector('[data-live-expansion-id="live-limit-visual"]');
    report.checks.gpt_expansion_inserted_in_place =
      await page.locator('[data-live-expansion-id="live-limit-visual"]').isVisible();
    report.checks.gpt_expansion_has_substantial_content =
      await page.locator('[data-live-expansion-id="live-limit-visual"] .content-block').count() === 2;

    liveSession = await studioPatch({
      expected_revision: liveSession.revision,
      pedagogical_intent: "继续降低抽象度，用一个具体数值邻域解释上一层公式",
      expansion: {
        id: "live-limit-number-line",
        title: "再具体一步：只看 1 附近的数",
        parent_content_id: "live-limit-formula",
        parent_expansion_id: "live-limit-visual",
        learner_question: "还是不懂，能不能给一个具体数字过程？",
        preserved_context: ["上一层区分了点值与邻域", "目标仍是理解趋近"],
        focus_relation: "用 x=0.9、0.99、1.01、1.1 代替抽象的 x→1。",
        representation: "smaller_example",
        blocks: [
          {
            id: "live-limit-numbers",
            kind: "worked_example",
            data: {
              prompt: "观察 f(x)=x+1 在 x=1 附近",
              steps: [
                "x=0.9 时 f(x)=1.9",
                "x=0.99 时 f(x)=1.99",
                "x=1.01 时 f(x)=2.01",
                "左右两边都稳定靠近 2",
              ],
            },
          },
        ],
        model_commands: [],
        return_connection: "这些具体数值说明了上一层的邻域趋势，再回到极限记号。",
      },
    }, "browser-live-expansion-2");
    await page.waitForSelector('[data-live-expansion-id="live-limit-number-line"]');
    report.checks.nested_expansion_visible =
      await page.locator('[data-live-expansion-id="live-limit-number-line"]').isVisible();
    await page.screenshot({
      path: path.join(outputRoot, "desktop-live-expansion.png"),
      fullPage: true,
    });
    await page.locator("#returnFromExpansion").click();
    await page.waitForFunction(() =>
      document.querySelector("#returnFromExpansion")?.dataset.expansionId === "live-limit-visual"
    );
    report.checks.return_restored_parent_expansion = true;

    const detail = page.locator("details[data-detail-id]").first();
    await detail.locator("summary").click();
    await page.waitForFunction(() => {
      const scene = JSON.parse(
        localStorage.getItem("math150-classroom-scene-v1") || "null",
      );
      return scene?.model_snapshot?.highlightedTarget === "target-value";
    }, null, { timeout: 2000 });
    await page.screenshot({ path: path.join(outputRoot, "desktop-detail.png") });
    let snapshot = await page.evaluate(() => JSON.parse(localStorage.getItem("math150-classroom-scene-v1")));
    report.checks.detail_open = await detail.evaluate((element) => element.open);
    report.checks.detail_model_state = snapshot.model_snapshot;

    const scrollBefore = await page.evaluate(() => window.scrollY);
    await page.locator("#fullscreenModel").click();
    report.checks.fullscreen_open = await page.locator("#modelDock").evaluate((element) => element.classList.contains("is-fullscreen"));
    await page.locator("#closeFullscreenModel").click();
    report.checks.fullscreen_return_scroll_delta = Math.abs(
      (await page.evaluate(() => window.scrollY)) - scrollBefore
    );

    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForSelector("#classroomStage:not(.is-hidden) #modelRoot canvas");
    report.checks.reload_restored_module = await page.locator("#classroomStage").isVisible();
    report.checks.reload_restored_detail = await page.locator("details[data-detail-id]").first().evaluate((element) => element.open);
    report.checks.reload_restored_model_state = await page.evaluate(() => {
      const scene = JSON.parse(
        localStorage.getItem("math150-classroom-scene-v1") || "null",
      );
      return scene?.model_snapshot?.highlightedTarget === "target-value";
    });
    report.checks.desktop_horizontal_overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    snapshot = await page.evaluate(() => JSON.parse(localStorage.getItem("math150-classroom-scene-v1")));
    report.scene_snapshot = snapshot;
    await page.locator("#backToAtlas").click();
    await page.waitForSelector("#atlasView:not(.is-hidden)");
    await page.reload({ waitUntil: "domcontentloaded" });
    report.checks.return_reload_stays_atlas =
      await page.locator("#atlasView").isVisible() &&
      !(await page.locator("#classroomStage").isVisible());
    await desktop.close();

    const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
    const mobilePage = await mobile.newPage();
    mobilePage.on("pageerror", (error) => errors.push(`mobile: ${String(error)}`));
    mobilePage.on("console", (message) => {
      if (message.type() === "error") errors.push(`mobile console: ${message.text()}`);
    });
    mobilePage.on("request", (request) => requests.push(request.url()));
    mobilePage.on("response", (response) => {
      if (response.status() >= 400) report.failed_responses.push({ status: response.status(), url: response.url() });
    });
    await mobilePage.goto(`${baseUrl}/classroom/`, { waitUntil: "domcontentloaded" });
    await mobilePage.locator(".module-destination").first().click();
    await mobilePage.waitForSelector("#modelRoot canvas");
    await mobilePage.screenshot({ path: path.join(outputRoot, "mobile-classroom.png"), fullPage: true });
    report.checks.mobile_model_visible = await mobilePage.locator("#modelRoot canvas").isVisible();
    report.checks.mobile_horizontal_overflow = await mobilePage.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    await mobile.close();

    report.checks.forbidden_product_requests = requests.filter((url) =>
      url.includes("/api/challenge")
    );
    report.base_url = "<local-classroom-server>";
    report.requests = requests.map((url) => {
      if (url.startsWith("blob:")) return "blob:<teaching-model-module>";
      return new URL(url).pathname;
    });
    report.failed_responses = report.failed_responses.map((failure) => ({
      ...failure,
      url: new URL(failure.url).pathname,
    }));
    fs.writeFileSync(path.join(outputRoot, "browser-report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
    process.stdout.write(JSON.stringify(report));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  process.stderr.write(error.stack || String(error));
  process.exitCode = 1;
});
