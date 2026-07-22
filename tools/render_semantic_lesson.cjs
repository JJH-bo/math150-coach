"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");
const { mathjax } = require("@mathjax/src/js/mathjax.js");
const { TeX } = require("@mathjax/src/js/input/tex.js");
const { SVG } = require("@mathjax/src/js/output/svg.js");
const { MathJaxTexFont } = require("@mathjax/mathjax-tex-font/js/svg.js");
const { liteAdaptor } = require("@mathjax/src/js/adaptors/liteAdaptor.js");
const { RegisterHTMLHandler } = require("@mathjax/src/js/handlers/html.js");
require("@mathjax/src/js/input/tex/base/BaseConfiguration.js");
require("@mathjax/src/js/input/tex/ams/AmsConfiguration.js");
require("@mathjax/src/js/input/tex/newcommand/NewcommandConfiguration.js");

function parseArgs(argv) {
  const result = {};
  for (let index = 2; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error("arguments must be --name value pairs");
    }
    result[key.slice(2)] = value;
  }
  return result;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function mathRenderer() {
  const adaptor = liteAdaptor({ fontSize: 16 });
  RegisterHTMLHandler(adaptor);
  const document = mathjax.document("", {
    InputJax: new TeX({
      packages: ["base", "ams", "newcommand"],
      formatError(_jax, error) { throw error; },
    }),
    OutputJax: new SVG({ fontCache: "local", fontData: MathJaxTexFont }),
  });
  return (latex) => {
    const node = document.convert(latex, { display: true, em: 16, ex: 8, containerWidth: 1280 });
    return adaptor
      .outerHTML(node)
      .replace(/\sdata-latex(?:-[\w-]+)?="[^"]*"/g, "");
  };
}

function renderSlide(slide, index, renderMath) {
  const titleTag = slide.kind === "opening" ? "h1" : "h2";
  const body = slide.body.map((item) => `<p>${escapeHtml(item)}</p>`).join("");
  const bullets = slide.bullets.length
    ? `<ul>${slide.bullets.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
    : "";
  const formula = slide.formula
    ? `<div class="formula" role="img" aria-label="${escapeHtml(slide.formula)}">${renderMath(slide.formula)}</div>`
    : "";
  const notes = slide.speaker_notes
    ? `<aside class="notes">${escapeHtml(slide.speaker_notes)}</aside>`
    : "";
  return `<section data-slide-id="${escapeHtml(slide.slide_id)}" data-kind="${slide.kind}">
    <div class="slide-index">${String(index + 1).padStart(2, "0")}</div>
    <${titleTag}>${escapeHtml(slide.title)}</${titleTag}>
    <p class="primary-claim">${escapeHtml(slide.primary_claim)}</p>
    <div class="lesson-copy">${body}${bullets}${formula}</div>
    ${notes}
  </section>`;
}

function buildHtml(payload) {
  const revealCss = fs.readFileSync(require.resolve("reveal.js/reveal.css"), "utf8");
  const themeCss = fs.readFileSync(require.resolve("reveal.js/theme/black.css"), "utf8");
  const revealJs = fs.readFileSync(require.resolve("reveal.js"), "utf8");
  const renderMath = mathRenderer();
  const lesson = payload.lesson;
  const slides = lesson.slides.map((slide, index) => renderSlide(slide, index, renderMath)).join("\n");
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="semantic-lesson-version" content="semantic_lesson_v1">
<meta name="lesson-content-hash" content="${escapeHtml(payload.content_hash)}">
<title>${escapeHtml(lesson.title)}</title>
<style>${revealCss}\n${themeCss}</style>
<style>
:root { --accent: #35c8ff; --ink: #f4f7fb; --muted: #aab7c8; --surface: #0c121a; }
html, body { background: var(--surface); }
.reveal { font-family: "Noto Sans CJK SC", "Segoe UI", Arial, sans-serif; color: var(--ink); }
.reveal .slides { text-align: left; }
.reveal .slides section { box-sizing: border-box; height: 720px; padding: 58px 82px 52px; overflow: hidden; }
.reveal h1, .reveal h2 { color: var(--ink); margin: 0; text-transform: none; letter-spacing: -0.025em; line-height: 1.08; }
.reveal h1 { max-width: 1050px; font-size: 72px; font-weight: 720; }
.reveal h2 { max-width: 1100px; font-size: 52px; font-weight: 700; }
.reveal .primary-claim { max-width: 1050px; margin: 30px 0 22px; color: var(--accent); font-size: 32px; font-weight: 650; line-height: 1.24; }
.reveal .lesson-copy { max-width: 1080px; font-size: 24px; line-height: 1.42; color: #e5ebf3; }
.reveal .lesson-copy p { margin: 0 0 16px; }
.reveal ul { margin: 8px 0 0 1.1em; }
.reveal li { margin: 0 0 10px; padding-left: 0.2em; }
.reveal .formula { display: flex; align-items: center; min-height: 92px; margin-top: 22px; padding: 12px 22px; border-left: 5px solid var(--accent); background: rgba(255,255,255,0.055); overflow: hidden; }
.reveal .formula mjx-container { margin: 0 !important; font-size: 125% !important; }
.reveal .formula svg { max-width: 100%; max-height: 100px; }
.reveal .slide-index { position: absolute; top: 30px; right: 42px; color: var(--muted); font-size: 18px; letter-spacing: 0.15em; }
.reveal .controls { color: var(--accent); }
.reveal .progress { color: var(--accent); height: 4px; }
@media print {
  html.reveal-print .reveal .slides section { padding: 58px 82px 52px !important; }
}
@media (max-width: 760px) {
  .reveal .slides section { padding: 42px 48px; }
}
</style>
</head>
<body class="template-${escapeHtml(lesson.template)}">
<div class="reveal" aria-label="${escapeHtml(lesson.title)}">
  <div class="slides">${slides}</div>
</div>
<script>${revealJs}</script>
<script>
Reveal.initialize({ hash: true, controls: true, progress: true, center: false,
  transition: "none", backgroundTransition: "none", width: 1280, height: 720,
  margin: 0, minScale: 0.2, maxScale: 2.0 });
</script>
</body>
</html>\n`;
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.input || !args.output) throw new Error("--input and --output are required");
  const payload = JSON.parse(fs.readFileSync(args.input, "utf8"));
  fs.mkdirSync(args.output, { recursive: true });
  const htmlPath = path.join(args.output, "lesson.html");
  const pdfPath = path.join(args.output, "lesson.pdf");
  fs.writeFileSync(htmlPath, buildHtml(payload), "utf8");

  const browser = await chromium.launch({
    executablePath: args.browser || undefined,
    headless: true,
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const consoleErrors = [];
  const failedRequests = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text().slice(0, 1000));
  });
  page.on("requestfailed", (request) => {
    failedRequests.push({ url: request.url(), error: request.failure()?.errorText || "unknown" });
  });
  const fileUrl = pathToFileURL(htmlPath).href;
  await page.goto(fileUrl, { waitUntil: "load" });
  await page.waitForFunction(() => globalThis.Reveal?.isReady?.() === true);
  const slideCount = payload.lesson.slides.length;
  const slideReports = [];
  const overflowFindings = [];
  for (let index = 0; index < slideCount; index += 1) {
    await page.evaluate((slideIndex) => globalThis.Reveal.slide(slideIndex), index);
    await page.waitForTimeout(30);
    const report = await page.evaluate((slideIndex) => {
      const slide = document.querySelectorAll(".slides > section")[slideIndex];
      const title = slide.querySelector("h1,h2");
      const claim = slide.querySelector(".primary-claim");
      const body = slide.querySelector(".lesson-copy");
      const pt = (element) => Number.parseFloat(getComputedStyle(element).fontSize) * 0.75;
      return {
        slide_id: slide.dataset.slideId,
        kind: slide.dataset.kind,
        scroll_width: slide.scrollWidth,
        client_width: slide.clientWidth,
        scroll_height: slide.scrollHeight,
        client_height: slide.clientHeight,
        title_font_pt: pt(title),
        subheading_font_pt: pt(claim),
        body_font_pt: pt(body),
      };
    }, index);
    slideReports.push(report);
    if (report.scroll_width > report.client_width + 1 || report.scroll_height > report.client_height + 1) {
      overflowFindings.push({ slide_id: report.slide_id, code: "slide_overflow" });
    }
    const minimumTitle = report.kind === "opening" ? 50 : 35;
    if (report.title_font_pt < minimumTitle || report.subheading_font_pt < 24 || report.body_font_pt < 16) {
      overflowFindings.push({ slide_id: report.slide_id, code: "font_below_minimum" });
    }
    await page.screenshot({ path: path.join(args.output, `slide-${String(index + 1).padStart(3, "0")}.png`) });
  }

  const printPage = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await printPage.goto(`${fileUrl}?print-pdf`, { waitUntil: "load" });
  await printPage.waitForFunction(() => globalThis.Reveal?.isReady?.() === true);
  await printPage.emulateMedia({ media: "print" });
  await printPage.pdf({
    path: pdfPath,
    width: "13.333333in",
    height: "7.5in",
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: "0", right: "0", bottom: "0", left: "0" },
  });
  await browser.close();
  const report = {
    passed: consoleErrors.length === 0 && failedRequests.length === 0 && overflowFindings.length === 0,
    slide_count: slideCount,
    viewport: { width: 1280, height: 720 },
    minimum_font_sizes: { deck_title: 50, slide_title: 35, subheading: 24, body: 16 },
    slides: slideReports,
    overflow_findings: overflowFindings,
    console_errors: consoleErrors,
    failed_requests: failedRequests,
  };
  fs.writeFileSync(path.join(args.output, "render-report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
  if (!report.passed) throw new Error(`render quality gates failed: ${JSON.stringify(report)}`);
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
