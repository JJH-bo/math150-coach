const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

function requestPath(url) {
  try {
    const parsed = new URL(url);
    return `${parsed.pathname}${parsed.search}`;
  } catch {
    return String(url);
  }
}

async function main() {
  const origin = process.argv[2];
  const assetUri = process.argv[3];
  const outputRoot = path.resolve(process.argv[4]);
  if (!origin || !assetUri || !process.argv[4]) {
    throw new Error("usage: capture_classroom_asset.cjs <origin> <asset-uri> <output-root>");
  }
  if (!/^\/api\/classroom\/v1\/assets\/a-[a-f0-9]{64}$/.test(assetUri)) {
    throw new Error("asset URI is not canonical");
  }
  fs.mkdirSync(outputRoot, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.MODEL_PREVIEW_BROWSER || undefined,
  });
  const consoleErrors = [];
  const failedRequests = [];
  try {
    const context = await browser.newContext({
      viewport: { width: 900, height: 620 },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    let assetResponse = null;
    page.on("pageerror", (error) => consoleErrors.push(String(error)));
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    page.on("requestfailed", (request) => {
      failedRequests.push({
        url: requestPath(request.url()),
        error: request.failure()?.errorText || "request failed",
      });
    });
    page.on("response", (response) => {
      if (requestPath(response.url()) === assetUri) assetResponse = response;
      if (response.status() >= 400) {
        failedRequests.push({
          url: requestPath(response.url()),
          status: response.status(),
        });
      }
    });

    await page.route(`${origin}/__asset_evidence__`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/html; charset=utf-8",
        body: `<!doctype html>
<html><head><meta charset="utf-8"><link rel="icon" href="data:,"><style>
html,body{margin:0;min-height:100%;background:#101923;display:grid;place-items:center}
img{display:block;max-width:100%;height:auto}
</style></head><body><img src="${assetUri}" alt="Verified classroom asset"></body></html>`,
      });
    });
    await page.goto(`${origin}/__asset_evidence__`, {
      waitUntil: "load",
      timeout: 20000,
    });
    await page.waitForFunction(() => {
      const image = document.querySelector("img");
      return Boolean(image?.complete && image.naturalWidth && image.naturalHeight);
    });
    const imageReport = await page.evaluate(() => {
      const image = document.querySelector("img");
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const context = canvas.getContext("2d", { willReadFrequently: true });
      context.drawImage(image, 0, 0);
      const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
      let first = null;
      let variedPixels = 0;
      let visiblePixels = 0;
      for (let offset = 0; offset < pixels.length; offset += 16) {
        const rgba = `${pixels[offset]},${pixels[offset + 1]},${pixels[offset + 2]},${pixels[offset + 3]}`;
        first ||= rgba;
        if (rgba !== first) variedPixels += 1;
        if (pixels[offset + 3] > 0) visiblePixels += 1;
      }
      return {
        natural_width: image.naturalWidth,
        natural_height: image.naturalHeight,
        nonblank: variedPixels > 64 && visiblePixels > 64,
        varied_pixels: variedPixels,
        visible_pixels: visiblePixels,
      };
    });
    await page.screenshot({
      path: path.join(outputRoot, "browser.png"),
      fullPage: true,
    });
    const responseHeaders = assetResponse ? await assetResponse.allHeaders() : {};
    const report = {
      asset_uri: assetUri,
      status: assetResponse?.status() || null,
      content_type: responseHeaders["content-type"] || null,
      cache_control: responseHeaders["cache-control"] || null,
      etag: responseHeaders.etag || null,
      ...imageReport,
      console_errors: consoleErrors,
      failed_requests: failedRequests,
    };
    fs.writeFileSync(
      path.join(outputRoot, "browser-report.json"),
      `${JSON.stringify(report, null, 2)}\n`,
      "utf8",
    );
    await context.close();
    if (
      report.status !== 200 ||
      !report.nonblank ||
      report.console_errors.length ||
      report.failed_requests.length
    ) {
      throw new Error(`asset browser verification failed: ${JSON.stringify(report)}`);
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
