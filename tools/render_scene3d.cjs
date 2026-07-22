const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

function parseArguments(argv) {
  const parsed = {};
  for (let index = 2; index < argv.length; index += 2) {
    if (!argv[index]?.startsWith("--") || argv[index + 1] === undefined) throw new Error("invalid worker arguments");
    parsed[argv[index].slice(2)] = argv[index + 1];
  }
  for (const name of ["spec", "html", "poster", "interaction", "report"]) {
    if (!parsed[name]) throw new Error(`missing --${name}`);
  }
  return parsed;
}

async function main() {
  const options = parseArguments(process.argv);
  const specification = JSON.parse(fs.readFileSync(options.spec, "utf8"));
  const launchOptions = { headless: true };
  if (options.browser) launchOptions.executablePath = options.browser;
  const browser = await chromium.launch(launchOptions);
  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];
  try {
    const page = await browser.newPage({ viewport: { width: specification.width, height: specification.height }, deviceScaleFactor: 1 });
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    page.on("pageerror", (error) => pageErrors.push(String(error)));
    page.on("requestfailed", (request) => failedRequests.push({ url: request.url().replace(/^file:.*$/, "file:///<local>"), error: request.failure()?.errorText || "request failed" }));
    await page.goto(pathToFileURL(path.resolve(options.html)).href, { waitUntil: "load" });
    try {
      await page.waitForFunction(() => window.sceneStudio?.ready === true, null, { timeout: 8000 });
    } catch (error) {
      throw new Error(
        `scene runtime did not become ready; console=${JSON.stringify(consoleErrors)} page=${JSON.stringify(pageErrors)} failed=${JSON.stringify(failedRequests)} cause=${error}`,
      );
    }
    await page.waitForTimeout(100);
    const baseline = await page.evaluate(() => window.sceneStudio.snapshot());
    const runtime = await page.evaluate(() => window.sceneStudio.report());
    await page.screenshot({ path: options.poster, fullPage: false });
    const targetAzimuth = specification.camera.azimuth > 100 ? specification.camera.azimuth - 70 : specification.camera.azimuth + 70;
    await page.evaluate((value) => window.sceneStudio.setAzimuth(value), targetAzimuth);
    await page.waitForTimeout(50);
    const changed = await page.evaluate((before) => window.sceneStudio.snapshot() !== before, baseline);
    await page.screenshot({ path: options.interaction, fullPage: false });
    await page.evaluate(() => window.sceneStudio.restore());
    const restored = await page.evaluate(() => window.sceneStudio.snapshot());
    const report = {
      passed:
        consoleErrors.length === 0 &&
        pageErrors.length === 0 &&
        failedRequests.length === 0 &&
        runtime.renderedObjectCount === specification.objects.length &&
        runtime.triangles > 0 &&
        !runtime.frustumClipped &&
        changed &&
        restored === baseline,
      renderer: "Three.js 0.185.1 structured scene runtime",
      webgl_renderer: runtime.webglRenderer,
      rendered_object_count: runtime.renderedObjectCount,
      triangle_count: runtime.triangles,
      draw_calls: runtime.calls,
      frustum_clipped: runtime.frustumClipped,
      projected_bounds: runtime.projectedBounds,
      interaction_exercised: true,
      interaction_changed: changed,
      target_azimuth: targetAzimuth,
      restored_to_baseline: restored === baseline,
      console_errors: consoleErrors,
      page_errors: pageErrors,
      failed_requests: failedRequests,
      viewport: { width: specification.width, height: specification.height },
    };
    fs.writeFileSync(options.report, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    if (!report.passed) throw new Error(`3D quality report failed: ${JSON.stringify(report)}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
