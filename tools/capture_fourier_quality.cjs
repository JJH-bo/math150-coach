const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

function hash(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

async function main() {
  const baseUrl = process.argv[2];
  const outputRoot = path.resolve(process.argv[3]);
  fs.mkdirSync(outputRoot, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.MODEL_PREVIEW_BROWSER || undefined,
  });
  const report = {
    base_url: "<local-classroom-server>",
    errors: [],
    failed_responses: [],
    checks: {},
  };
  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 960 },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    page.on("pageerror", (error) => report.errors.push(String(error)));
    page.on("console", (message) => {
      if (message.type() === "error") report.errors.push(`console: ${message.text()}`);
    });
    page.on("response", (response) => {
      if (response.status() >= 400) {
        report.failed_responses.push({
          status: response.status(),
          path: new URL(response.url()).pathname,
        });
      }
    });
    await page.goto(
      `${baseUrl}/classroom/?package_id=fourier-series-class`,
      { waitUntil: "domcontentloaded" },
    );
    await page.waitForSelector(".module-destination");
    const packageResponse = await page.request.get(
      `${baseUrl}/api/classroom/v1/packages/fourier-series-class`,
    );
    if (!packageResponse.ok()) {
      throw new Error(`package inspection failed: ${packageResponse.status()}`);
    }
    const packagePayload = await packageResponse.json();
    const chapter = packagePayload.package.courses[0].chapters[0];
    const moduleBlockIds = (module) => new Set(
      module.segments.flatMap((segment) =>
        segment.blocks.flatMap((block) => [
          block.id,
          ...(block.detail_branches || []).flatMap((detail) =>
            (detail.blocks || []).map((child) => child.id)
          ),
        ])
      ),
    );
    const moduleDetails = chapter.modules.map((module) =>
      module.segments.flatMap((segment) =>
        segment.blocks.flatMap((block) => block.detail_branches || [])
      )
    );
    const bindingContentIds = new Set(
      packagePayload.package.model_bindings.map((binding) => binding.content_id),
    );
    report.checks.source_section_count = chapter.source_sections.length;
    report.checks.knowledge_point_count = chapter.knowledge_points.length;
    report.checks.coverage_is_complete =
      chapter.knowledge_points.length > 0
      && chapter.knowledge_points.length === chapter.coverage_map.length
      && chapter.coverage_audit.unresolved_items.length === 0;
    report.checks.all_modules_have_specific_core_questions =
      chapter.modules.every((module) =>
        module.core_question.length >= 20
        && !module.core_question.startsWith("如何通过“")
      );
    report.checks.all_modules_have_novice_bridges =
      chapter.modules.every((module) =>
        module.novice_bridge.known_before.length > 0
        && module.novice_bridge.missing_bridge.length >= 20
        && module.novice_bridge.concrete_anchor.length >= 20
        && module.novice_bridge.bridge_strategy.length >= 20
      );
    report.checks.all_segments_are_subject_specific =
      chapter.modules.every((module) =>
        module.segments.every((segment) =>
          segment.question_answered.length >= 18
          && !segment.question_answered.startsWith("如何理解“")
          && !segment.mechanism.includes("通过同时追踪对象、条件和结果")
        )
      );
    report.checks.all_modules_have_substantive_details =
      moduleDetails.every((details) =>
        details.length > 0
        && details.every((detail) =>
          detail.bridge_steps.length >= 2
          && detail.blocks.length >= 2
          && !detail.learning_obstacle.startsWith("第一次学习时容易只记住")
        )
      );
    report.checks.all_modules_have_model_bindings =
      chapter.modules.every((module) =>
        [...moduleBlockIds(module)].some((id) => bindingContentIds.has(id))
      );
    report.checks.core_module_count = await page.locator(".module-destination").count();
    report.checks.chapter_map_is_not_a_core_module =
      await page.locator(".module-destination[data-module-id='fourier-map']").count() === 0;
    report.checks.chapter_question_visible =
      (await page.locator("#chapterQuestion").innerText()).trim().length >= 8;
    await page.screenshot({ path: path.join(outputRoot, "fourier-atlas.png") });

    await page.locator(".module-destination").first().click();
    await page.waitForSelector("#lessonContent .baseline-step");
    await page.waitForSelector("#modelRoot canvas");
    await page.waitForSelector("#modelControls:not(.is-hidden)");
    report.checks.model_control_count =
      await page.locator("#modelControls input,#modelControls select,#modelControls button").count();
    report.checks.module_contract_visible =
      await page.locator(".module-core-question").isVisible()
      && await page.locator(".module-novice-bridge").isVisible();
    report.checks.segment_bridge_visible =
      await page.locator(".segment-bridge").first().isVisible();
    report.checks.formula_typeset =
      await page.locator("#lessonContent mjx-container").count() > 0;

    const canvas = page.locator("#modelRoot canvas");
    const initialCanvasHash = hash(await canvas.screenshot({ type: "png" }));
    const harmonicControl = page.locator(
      '#modelControls input[data-parameter-id="harmonic-count"]',
    );
    await harmonicControl.fill("13");
    await harmonicControl.dispatchEvent("input");
    await page.waitForTimeout(150);
    const changedCanvasHash = hash(await canvas.screenshot({ type: "png" }));
    report.checks.model_interaction_changes_visual =
      initialCanvasHash !== changedCanvasHash;
    report.model_visual_hashes = {
      initial: initialCanvasHash,
      changed: changedCanvasHash,
    };

    for (let index = 0; index < 12; index += 1) {
      if (await page.locator("details[data-detail-id]").count()) break;
      const reveal = page.locator("#revealNextStep");
      if (!(await reveal.isVisible())) break;
      const previousCount = await page.locator(".baseline-step").count();
      await reveal.click();
      await page.waitForFunction(
        (count) => document.querySelectorAll(".baseline-step").length > count,
        previousCount,
      );
    }
    const detail = page.locator("details[data-detail-id]").first();
    if (!(await detail.count())) {
      throw new Error("no detailed expansion became available after revealing the module");
    }
    await detail.locator("summary").click();
    report.checks.detail_has_obstacle =
      await detail.locator(".detail-obstacle").isVisible();
    report.checks.detail_has_bridge =
      await detail.locator(".detail-bridge li").count() >= 2;
    report.checks.detail_has_substantive_blocks =
      await detail.locator(".detail-content .content-block").count() >= 2;
    const comparisonCopies = await page.locator(".comparison-grid section")
      .allTextContents();
    report.checks.no_blank_comparison_cards =
      comparisonCopies.every((copy) => copy.trim().length > 0);
    report.checks.no_raw_latex_in_visible_text = !(
      await page.locator("#lessonContent").innerText()
    ).includes("\\text{");
    report.checks.desktop_horizontal_overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    await page.screenshot({
      path: path.join(outputRoot, "fourier-classroom.png"),
      fullPage: true,
    });
    await context.close();

    const mobile = await browser.newContext({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 1,
    });
    const mobilePage = await mobile.newPage();
    mobilePage.on("pageerror", (error) => report.errors.push(`mobile: ${String(error)}`));
    await mobilePage.goto(
      `${baseUrl}/classroom/?package_id=fourier-series-class`,
      { waitUntil: "domcontentloaded" },
    );
    await mobilePage.waitForSelector(".module-destination");
    await mobilePage.locator(".module-destination").first().click();
    await mobilePage.waitForSelector("#modelRoot canvas");
    report.checks.mobile_model_visible =
      await mobilePage.locator("#modelRoot canvas").isVisible();
    report.checks.mobile_controls_visible =
      await mobilePage.locator("#modelControls:not(.is-hidden)").isVisible();
    report.checks.mobile_horizontal_overflow = await mobilePage.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    await mobilePage.screenshot({
      path: path.join(outputRoot, "fourier-mobile.png"),
      fullPage: true,
    });
    await mobile.close();

    fs.writeFileSync(
      path.join(outputRoot, "fourier-browser-report.json"),
      `${JSON.stringify(report, null, 2)}\n`,
      "utf8",
    );
    process.stdout.write(JSON.stringify(report));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  process.stderr.write(error.stack || String(error));
  process.exitCode = 1;
});
