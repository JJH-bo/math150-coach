const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

function option(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}

function requestPath(url) {
  try {
    const parsed = new URL(url);
    return `${parsed.pathname}${parsed.search}`;
  } catch {
    return String(url);
  }
}

async function visible(locator) {
  return (await locator.count()) > 0 && await locator.first().isVisible();
}

async function inspectPage(page, request, viewport, screenshotPath) {
  const consoleErrors = [];
  const failedRequests = [];
  page.on("pageerror", (error) => consoleErrors.push(String(error)));
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("requestfailed", (failed) => {
    const error = failed.failure()?.errorText || "request failed";
    if (!error.includes("ERR_ABORTED")) {
      failedRequests.push({ url: requestPath(failed.url()), error });
    }
  });
  page.on("response", (response) => {
    if (response.status() >= 400) {
      failedRequests.push({
        url: requestPath(response.url()),
        status: response.status(),
      });
    }
  });

  const target = new URL("/classroom/", option("--origin"));
  target.searchParams.set("package_id", request.package_id);
  await page.goto(target.href, { waitUntil: "domcontentloaded", timeout: 30000 });
  const moduleButton = page.locator(
    `.module-destination[data-module-id="${request.module_id}"]`,
  );
  await moduleButton.waitFor({ state: "visible", timeout: 15000 });
  await moduleButton.click();
  await page.locator("#classroomStage:not(.is-hidden) .baseline-step").first()
    .waitFor({ state: "visible", timeout: 15000 });
  if (request.model_expected) {
    await page.locator("#modelRoot canvas").waitFor({ state: "visible", timeout: 15000 });
  }

  for (let step = 0; step < request.reveal_steps; step += 1) {
    const reveal = page.locator("#revealNextStep");
    if (!(await visible(reveal)) || await reveal.isDisabled()) break;
    const before = await page.locator("#lessonContent .baseline-step").count();
    await reveal.click();
    await page.waitForFunction(
      (count) => document.querySelectorAll("#lessonContent .baseline-step").length > count,
      before,
      { timeout: 10000 },
    );
  }
  if (request.open_first_detail) {
    const summary = page.locator("#lessonContent details[data-detail-id] summary").first();
    if (await visible(summary)) {
      await summary.click();
      await page.waitForFunction(() => {
        const detail = document.querySelector("#lessonContent details[data-detail-id]");
        return !detail || detail.open;
      });
    }
  }
  await page.evaluate(() => new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  }));
  await page.waitForTimeout(150);

  const domReport = await page.evaluate(() => {
    const accessibilityIssues = [];
    for (const image of document.querySelectorAll("img")) {
      if (image.getClientRects().length && (image.alt || "").trim().length < 4) {
        accessibilityIssues.push("visible image lacks meaningful alt text");
      }
    }
    for (const button of document.querySelectorAll("button")) {
      if (!button.getClientRects().length) continue;
      const name = button.getAttribute("aria-label") || button.textContent || button.title;
      if (!(name || "").trim()) accessibilityIssues.push("visible button lacks a name");
    }
    for (const input of document.querySelectorAll("input,select,textarea")) {
      if (!input.getClientRects().length) continue;
      const labelled = input.getAttribute("aria-label")
        || input.getAttribute("aria-labelledby")
        || (input.id && document.querySelector(`label[for="${CSS.escape(input.id)}"]`)?.textContent)
        || input.closest("label")?.textContent;
      if (!(labelled || "").trim()) accessibilityIssues.push("visible input lacks a label");
    }

    const clippedText = [];
    const candidates = document.querySelectorAll(
      "#classroomStage h1,#classroomStage h2,#classroomStage h3,#classroomStage p," +
      "#classroomStage li,#classroomStage td,#classroomStage th,#classroomStage .content-block",
    );
    for (const element of candidates) {
      if (!element.getClientRects().length || !(element.innerText || "").trim()) continue;
      const style = getComputedStyle(element);
      const verticalClip = ["hidden", "clip"].includes(style.overflowY)
        && element.scrollHeight > element.clientHeight + 2;
      const horizontalClip = ["hidden", "clip"].includes(style.overflowX)
        && element.scrollWidth > element.clientWidth + 2;
      if (verticalClip || horizontalClip) {
        clippedText.push((element.innerText || "").trim().slice(0, 120));
      }
    }
    return {
      module_title: document.querySelector("#breadcrumbs")?.textContent?.trim() || "",
      baseline_steps: document.querySelectorAll("#lessonContent .baseline-step").length,
      formula_count: document.querySelectorAll("#lessonContent mjx-container").length,
      unrendered_math: document.querySelectorAll(
        "#lessonContent .math-typeset:not(.is-typeset)",
      ).length,
      horizontal_overflow: Math.max(
        0,
        document.documentElement.scrollWidth - document.documentElement.clientWidth,
      ),
      clipped_text: [...new Set(clippedText)].slice(0, 20),
      accessibility_issues: [...new Set(accessibilityIssues)].slice(0, 20),
    };
  });
  const modelCanvasVisible = await visible(page.locator("#modelRoot canvas"));
  await page.screenshot({ path: screenshotPath, fullPage: false });
  return {
    name: viewport.name,
    viewport_width: viewport.width,
    viewport_height: viewport.height,
    screenshot: path.basename(screenshotPath),
    ...domReport,
    model_expected: request.model_expected,
    model_canvas_visible: modelCanvasVisible,
    console_errors: [...consoleErrors],
    failed_requests: [...failedRequests],
  };
}

async function main() {
  const origin = option("--origin");
  const requestPathValue = option("--request");
  const reportPath = option("--report");
  const outputRoot = option("--output");
  const browserPath = option("--browser") || process.env.MODEL_PREVIEW_BROWSER;
  if (!origin || !requestPathValue || !reportPath || !outputRoot) {
    throw new Error("missing required page preview worker option");
  }
  const request = JSON.parse(fs.readFileSync(requestPathValue, "utf8"));
  fs.mkdirSync(outputRoot, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: browserPath || undefined,
  });
  const viewportReports = [];
  try {
    for (const viewport of request.viewports) {
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height },
        deviceScaleFactor: request.quality_profile === "high" ? 2 : 1,
        reducedMotion: "reduce",
      });
      const page = await context.newPage();
      const screenshot = path.join(outputRoot, `${viewport.name}.png`);
      viewportReports.push(await inspectPage(page, request, viewport, screenshot));
      await context.close();
    }
  } finally {
    await browser.close();
  }
  const failed = viewportReports.some((viewport) =>
    viewport.baseline_steps < 1
    || viewport.unrendered_math !== 0
    || viewport.horizontal_overflow > 1
    || viewport.clipped_text.length > 0
    || viewport.accessibility_issues.length > 0
    || viewport.console_errors.length > 0
    || viewport.failed_requests.length > 0
    || (viewport.model_expected && !viewport.model_canvas_visible)
  );
  const report = {
    passed: !failed,
    runtime: "classroom_runtime_v1",
    package_id: request.package_id,
    module_id: request.module_id,
    release_version: request.release_version,
    viewports: viewportReports,
  };
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  if (failed) throw new Error(`page preview quality gates failed: ${JSON.stringify(report)}`);
}

main().catch((error) => {
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
