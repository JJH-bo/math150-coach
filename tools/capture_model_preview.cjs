const fs = require("node:fs");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

async function main() {
  const request = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  let browser;
  let context;
  try {
    browser = await chromium.launch({
      headless: true,
      executablePath: process.env.MODEL_PREVIEW_BROWSER || undefined,
      args: ["--allow-file-access-from-files"],
    });
    context = await browser.newContext({
      viewport: {
        width: request.viewport.width,
        height: request.viewport.height,
      },
      deviceScaleFactor: request.viewport.device_scale_factor || 1,
    });
    const page = await context.newPage();
    const consoleMessages = [];
    const uncaughtErrors = [];
    page.on("console", (message) => consoleMessages.push({
      type: message.type(),
      text: message.text(),
    }));
    page.on("pageerror", (error) => uncaughtErrors.push(String(error)));
    await page.route(/^https?:/, (route) => route.abort("blockedbyclient"));
    await page.goto(pathToFileURL(request.preview_html).href, { waitUntil: "load" });
    await page.waitForFunction(
      () => window.__teachingPreviewReady !== undefined,
      null,
      { timeout: 15000 },
    );
    const ready = await page.evaluate(() => window.__teachingPreviewReady);
    if (!ready.ready) throw new Error(ready.error || "model preview did not become ready");
    const visualEvidence = await page.evaluate(() => {
      const root = document.querySelector("#modelRoot");
      if (!root) return {
        visible_element_count: 0,
        painted_bounds: { x: 0, y: 0, width: 0, height: 0, area: 0 },
      };
      const visible = [...root.querySelectorAll("*")].filter((element) => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return (
          style.display !== "none"
          && style.visibility !== "hidden"
          && Number(style.opacity || 1) > 0
          && rect.width >= 2
          && rect.height >= 2
        );
      });
      if (!visible.length) return {
        visible_element_count: 0,
        painted_bounds: { x: 0, y: 0, width: 0, height: 0, area: 0 },
      };
      const rects = visible.map((element) => element.getBoundingClientRect());
      const x = Math.max(0, Math.min(...rects.map((rect) => rect.left)));
      const y = Math.max(0, Math.min(...rects.map((rect) => rect.top)));
      const right = Math.min(innerWidth, Math.max(...rects.map((rect) => rect.right)));
      const bottom = Math.min(innerHeight, Math.max(...rects.map((rect) => rect.bottom)));
      const width = Math.max(0, right - x);
      const height = Math.max(0, bottom - y);
      return {
        visible_element_count: visible.length,
        painted_bounds: { x, y, width, height, area: width * height },
      };
    });
    await page.screenshot({ path: request.screenshot_path, type: "png" });
    const disposed = await page.evaluate(() => window.__disposeTeachingPreview());
    const report = {
      job_id: request.job_id,
      model_id: request.model_id,
      draft_id: request.draft_id,
      draft_revision: request.draft_revision,
      draft_content_hash: request.draft_content_hash,
      scenario_id: request.scenario_id,
      viewport: request.viewport,
      snapshot: ready.snapshot,
      model_logs: ready.logs,
      console_messages: consoleMessages,
      uncaught_errors: uncaughtErrors,
      resources_before_dispose: ready.resources_before_dispose,
      resources_after_dispose: disposed.resources_after_dispose,
      ...visualEvidence,
    };
    process.stdout.write(JSON.stringify(report));
  } finally {
    if (context) await context.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
  }
}

main().catch((error) => {
  process.stderr.write(error.stack || String(error));
  process.exitCode = 1;
});
