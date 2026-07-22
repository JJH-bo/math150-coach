const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

function parseArguments(argv) {
  const parsed = {};
  for (let index = 2; index < argv.length; index += 2) {
    const name = argv[index];
    const value = argv[index + 1];
    if (!name?.startsWith("--") || value === undefined) throw new Error("invalid worker arguments");
    parsed[name.slice(2)] = value;
  }
  for (const required of ["spec", "html", "svg", "png", "report", "output"]) {
    if (!parsed[required]) throw new Error(`missing --${required}`);
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
    const page = await browser.newPage({
      viewport: { width: specification.width, height: specification.height },
      deviceScaleFactor: 1,
    });
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    page.on("pageerror", (error) => pageErrors.push(String(error)));
    page.on("requestfailed", (request) => {
      failedRequests.push({ url: request.url().replace(/^file:.*$/, "file:///<local>"), error: request.failure()?.errorText || "request failed" });
    });
    await page.goto(pathToFileURL(path.resolve(options.html)).href, { waitUntil: "load" });
    await page.waitForFunction(() => Boolean(window.geometryStudio?.snapshot));
    const baseline = await page.evaluate(() => window.geometryStudio.snapshot());
    await page.screenshot({ path: options.png, fullPage: false });
    const interactionReports = [];
    for (let index = 0; index < specification.parameters.length; index += 1) {
      const parameter = specification.parameters[index];
      const target = parameter.value === parameter.maximum ? parameter.minimum : parameter.maximum;
      await page.evaluate(
        ({ id, value }) => window.geometryStudio.setParameter(id, value),
        { id: parameter.id, value: target },
      );
      const changed = await page.evaluate((before) => window.geometryStudio.snapshot() !== before, baseline);
      const screenshot = path.join(options.output, `interaction-${String(index + 1).padStart(3, "0")}.png`);
      await page.screenshot({ path: screenshot, fullPage: false });
      interactionReports.push({ parameter_id: parameter.id, target_value: target, changed });
      await page.evaluate(() => window.geometryStudio.restore());
    }
    const restored = await page.evaluate(() => window.geometryStudio.snapshot());
    const inspection = await page.evaluate(() => {
      const svg = document.getElementById("geometry-canvas");
      const view = svg.viewBox.baseVal;
      const findings = [];
      for (const group of svg.querySelectorAll("[data-object-id]")) {
        const box = group.getBBox();
        if (box.x < -1 || box.y < -1 || box.x + box.width > view.width + 1 || box.y + box.height > view.height + 1) {
          findings.push({ id: group.dataset.objectId, x: box.x, y: box.y, width: box.width, height: box.height });
        }
      }
      return {
        svg: svg.outerHTML,
        visible_object_count: svg.querySelectorAll("[data-object-id]").length,
        clipped_findings: findings,
      };
    });
    fs.writeFileSync(options.svg, `${inspection.svg}\n`, "utf8");
    const interactionChanged = interactionReports.every((item) => item.changed);
    const report = {
      passed:
        consoleErrors.length === 0 &&
        pageErrors.length === 0 &&
        failedRequests.length === 0 &&
        inspection.visible_object_count === specification.objects.length &&
        inspection.clipped_findings.length === 0 &&
        restored === baseline &&
        interactionChanged,
      renderer: "browser-native SVG geometry runtime v1",
      viewport: { width: specification.width, height: specification.height },
      visible_object_count: inspection.visible_object_count,
      parameter_count: specification.parameters.length,
      interaction_exercised: specification.parameters.length > 0,
      interaction_changed: interactionChanged,
      interactions: interactionReports,
      restored_to_baseline: restored === baseline,
      clipped: inspection.clipped_findings.length > 0,
      clipped_findings: inspection.clipped_findings,
      console_errors: consoleErrors,
      page_errors: pageErrors,
      failed_requests: failedRequests,
    };
    fs.writeFileSync(options.report, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    if (!report.passed) throw new Error(`geometry quality report failed: ${JSON.stringify(report)}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
