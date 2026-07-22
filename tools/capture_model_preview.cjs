const fs = require("node:fs");
const crypto = require("node:crypto");
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
        semantic_visual_signal: {
          has_meaningful_content: false,
          visible_text_characters: 0,
          svg_graphic_count: 0,
          canvas_distinct_colors: 0,
        },
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
        semantic_visual_signal: {
          has_meaningful_content: false,
          visible_text_characters: 0,
          svg_graphic_count: 0,
          canvas_distinct_colors: 0,
        },
      };
      const rects = visible.map((element) => element.getBoundingClientRect());
      const x = Math.max(0, Math.min(...rects.map((rect) => rect.left)));
      const y = Math.max(0, Math.min(...rects.map((rect) => rect.top)));
      const right = Math.min(innerWidth, Math.max(...rects.map((rect) => rect.right)));
      const bottom = Math.min(innerHeight, Math.max(...rects.map((rect) => rect.bottom)));
      const width = Math.max(0, right - x);
      const height = Math.max(0, bottom - y);
      const visibleTextCharacters = (root.innerText || "").replace(/\s/g, "").length;
      const svgGraphicCount = root.querySelectorAll(
        "svg path,svg line,svg circle,svg ellipse,svg rect,svg polygon,svg polyline,svg text",
      ).length;
      let canvasDistinctColors = 0;
      for (const canvas of root.querySelectorAll("canvas")) {
        try {
          const context = canvas.getContext("2d", { willReadFrequently: true });
          if (!context || !canvas.width || !canvas.height) continue;
          const colors = new Set();
          const columns = Math.min(32, canvas.width);
          const rows = Math.min(32, canvas.height);
          for (let row = 0; row < rows; row += 1) {
            for (let column = 0; column < columns; column += 1) {
              const px = Math.floor((column + 0.5) * canvas.width / columns);
              const py = Math.floor((row + 0.5) * canvas.height / rows);
              const rgba = context.getImageData(px, py, 1, 1).data;
              colors.add(`${rgba[0]},${rgba[1]},${rgba[2]},${rgba[3]}`);
              if (colors.size >= 16) break;
            }
            if (colors.size >= 16) break;
          }
          canvasDistinctColors = Math.max(canvasDistinctColors, colors.size);
        } catch {
          // A tainted canvas is not accepted as semantic evidence on its own.
        }
      }
      const hasMeaningfulContent = (
        visibleTextCharacters >= 12
        || svgGraphicCount >= 2
        || canvasDistinctColors >= 3
      );
      return {
        visible_element_count: visible.length,
        painted_bounds: { x, y, width, height, area: width * height },
        semantic_visual_signal: {
          has_meaningful_content: hasMeaningfulContent,
          visible_text_characters: visibleTextCharacters,
          svg_graphic_count: svgGraphicCount,
          canvas_distinct_colors: canvasDistinctColors,
        },
      };
    });
    const modelRoot = page.locator("#modelRoot");
    const initialImage = await modelRoot.screenshot({ type: "png" });
    const interaction = await page.evaluate(() => window.__exerciseTeachingPreview());
    await page.waitForTimeout(100);
    const finalImage = await modelRoot.screenshot({ type: "png" });
    const initialVisualHash = crypto.createHash("sha256").update(initialImage).digest("hex");
    const finalVisualHash = crypto.createHash("sha256").update(finalImage).digest("hex");
    const snapshotChanged = JSON.stringify(interaction.snapshot_before)
      !== JSON.stringify(interaction.snapshot_after);
    const interactionExercised = interaction.performed.length > 0;
    const interactionChanged = interactionExercised
      && (snapshotChanged || initialVisualHash !== finalVisualHash);
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
      interaction_evidence: interaction,
      interaction_exercised: interactionExercised,
      interaction_changed: interactionChanged,
      initial_visual_hash: initialVisualHash,
      final_visual_hash: finalVisualHash,
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
