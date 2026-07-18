const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

async function main() {
  const baseUrl = process.argv[2];
  const outputRoot = path.resolve(process.argv[3]);
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
    await page.goto(`${baseUrl}/`, { waitUntil: "networkidle" });
    report.checks.root_redirected_to_classroom =
      new URL(page.url()).pathname === "/classroom/";
    await page.waitForSelector(".module-destination");
    await page.screenshot({ path: path.join(outputRoot, "desktop-atlas.png") });
    report.checks.module_destinations = await page.locator(".module-destination").count();

    await page.locator(".module-destination").first().click();
    await page.waitForSelector("#lessonContent .formula-pair");
    await page.waitForSelector("#modelRoot canvas");
    await page.screenshot({ path: path.join(outputRoot, "desktop-classroom.png") });
    report.checks.formula_pair_visible = await page.locator(".formula-pair").isVisible();
    report.checks.model_visible = await page.locator("#modelRoot canvas").isVisible();

    const detail = page.locator("details[data-detail-id]").first();
    await detail.locator("summary").click();
    await page.waitForTimeout(100);
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

    await page.reload({ waitUntil: "networkidle" });
    await page.waitForSelector("#classroomStage:not(.is-hidden) #modelRoot canvas");
    report.checks.reload_restored_module = await page.locator("#classroomStage").isVisible();
    report.checks.reload_restored_detail = await page.locator("details[data-detail-id]").first().evaluate((element) => element.open);
    report.checks.desktop_horizontal_overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    snapshot = await page.evaluate(() => JSON.parse(localStorage.getItem("math150-classroom-scene-v1")));
    report.scene_snapshot = snapshot;
    await page.locator("#backToAtlas").click();
    await page.waitForSelector("#atlasView:not(.is-hidden)");
    await page.reload({ waitUntil: "networkidle" });
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
    await mobilePage.goto(`${baseUrl}/classroom/`, { waitUntil: "networkidle" });
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
