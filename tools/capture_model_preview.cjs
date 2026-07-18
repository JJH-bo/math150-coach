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
