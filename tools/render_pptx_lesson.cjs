"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const PptxGenJS = require("pptxgenjs");
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

const WIDTH = 1280;
const HEIGHT = 720;
const PX_PER_INCH = 96;
const COLORS = {
  surface: "0C121A",
  panel: "18202A",
  ink: "F4F7FB",
  body: "E5EBF3",
  muted: "AAB7C8",
  accent: "35C8FF",
};

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
    const html = adaptor
      .outerHTML(node)
      .replace(/\sdata-latex(?:-[\w-]+)?="[^"]*"/g, "")
      .replaceAll("currentColor", `#${COLORS.body}`);
    const start = html.indexOf("<svg");
    const end = html.lastIndexOf("</svg>");
    if (start < 0 || end < start) throw new Error("MathJax did not produce an SVG root");
    return { html, svg: html.slice(start, end + 6) };
  };
}

function inches(value) {
  return value / PX_PER_INCH;
}

function fontFor(language) {
  return String(language || "").toLowerCase().startsWith("zh")
    ? "Microsoft YaHei"
    : "Aptos";
}

function textPrimitive(role, text, x, y, w, h, fontPt, options = {}) {
  return {
    type: "text",
    role,
    text,
    x,
    y,
    w,
    h,
    fontPt,
    bold: options.bold ?? false,
    color: options.color ?? COLORS.body,
    align: options.align ?? "left",
    valign: options.valign ?? "top",
    fill: options.fill ?? null,
    radius: options.radius ?? 0,
    padding: options.padding ?? 0,
  };
}

function formulaPrimitive(rendered, latex, x, y, w, h) {
  return { type: "formula", role: "formula", html: rendered.html, svg: rendered.svg, latex, x, y, w, h };
}

function decoration(kind, x, y, w, h, options = {}) {
  return {
    type: "decoration",
    kind,
    x,
    y,
    w,
    h,
    fill: options.fill ?? COLORS.panel,
    line: options.line ?? null,
    radius: options.radius ?? 0,
  };
}

function openingLayout(slide) {
  const body = [...slide.body, ...slide.bullets].join("\n");
  return [
    decoration("rect", 0, 0, WIDTH, HEIGHT, { fill: COLORS.surface }),
    decoration("rect", 82, 48, 84, 5, { fill: COLORS.accent }),
    textPrimitive("slide-index", "01", 1180, 30, 58, 30, 16, {
      color: COLORS.muted,
      align: "right",
    }),
    textPrimitive("deck-title", slide.title, 82, 66, 1080, 180, 54, {
      bold: true,
      color: COLORS.ink,
    }),
    textPrimitive("subheading", slide.primary_claim, 82, 260, 1080, 90, 24, {
      bold: true,
      color: COLORS.accent,
    }),
    textPrimitive("body", body, 82, 370, 1080, 130, 18, { color: COLORS.body }),
  ];
}

function conceptLayout(slide, index, renderMath) {
  const primitives = [
    decoration("rect", 0, 0, WIDTH, HEIGHT, { fill: COLORS.surface }),
    textPrimitive("slide-index", String(index + 1).padStart(2, "0"), 1180, 30, 58, 30, 16, {
      color: COLORS.muted,
      align: "right",
    }),
    textPrimitive("slide-title", slide.title, 82, 56, 1080, 130, 39, {
      bold: true,
      color: COLORS.ink,
    }),
    textPrimitive("subheading", slide.primary_claim, 82, 198, 1080, 82, 24, {
      bold: true,
      color: COLORS.accent,
    }),
  ];
  const items = [...slide.body, ...slide.bullets];
  const formulaY = slide.formula ? 500 : 630;
  const available = formulaY - 292;
  const itemHeight = Math.min(64, Math.floor(available / Math.max(1, items.length)));
  items.forEach((item, itemIndex) => {
    const y = 292 + itemIndex * itemHeight;
    primitives.push(decoration("circle", 88, y + 11, 12, 12, { fill: COLORS.accent }));
    primitives.push(textPrimitive("body", item, 118, y, 1010, itemHeight - 4, 18));
  });
  if (slide.formula) {
    primitives.push(decoration("rect", 82, formulaY, 1080, 116, { fill: "20262D" }));
    primitives.push(decoration("rect", 82, formulaY, 5, 116, { fill: COLORS.accent }));
    primitives.push(formulaPrimitive(renderMath(slide.formula), slide.formula, 108, formulaY + 14, 1020, 88));
  }
  return primitives;
}

function exampleLayout(slide, index, renderMath) {
  const primitives = [
    decoration("rect", 0, 0, WIDTH, HEIGHT, { fill: COLORS.surface }),
    decoration("rect", 0, 0, 14, HEIGHT, { fill: COLORS.accent }),
    textPrimitive("slide-index", String(index + 1).padStart(2, "0"), 1180, 30, 58, 30, 16, {
      color: COLORS.muted,
      align: "right",
    }),
    textPrimitive("slide-title", slide.title, 82, 54, 1080, 130, 39, {
      bold: true,
      color: COLORS.ink,
    }),
    textPrimitive("subheading", slide.primary_claim, 82, 194, 1080, 82, 24, {
      bold: true,
      color: COLORS.accent,
    }),
  ];
  const items = [...slide.body, ...slide.bullets];
  const columns = items.length <= 3 ? Math.max(1, items.length) : 2;
  const gap = 18;
  const cardWidth = (1080 - gap * (columns - 1)) / columns;
  const rows = Math.ceil(items.length / columns);
  const cardHeight = Math.min(116, (190 - gap * (rows - 1)) / Math.max(1, rows));
  items.forEach((item, itemIndex) => {
    const column = itemIndex % columns;
    const row = Math.floor(itemIndex / columns);
    const x = 82 + column * (cardWidth + gap);
    const y = 294 + row * (cardHeight + gap);
    primitives.push(decoration("roundRect", x, y, cardWidth, cardHeight, { fill: COLORS.panel, radius: 12 }));
    primitives.push(textPrimitive("body", String(itemIndex + 1).padStart(2, "0"), x + 18, y + 16, 36, 26, 16, {
      bold: true,
      color: COLORS.accent,
    }));
    primitives.push(textPrimitive("body", item, x + 58, y + 16, cardWidth - 76, cardHeight - 28, 18));
  });
  if (slide.formula) {
    primitives.push(decoration("rect", 82, 518, 1080, 116, { fill: "20262D" }));
    primitives.push(decoration("rect", 82, 518, 5, 116, { fill: COLORS.accent }));
    primitives.push(formulaPrimitive(renderMath(slide.formula), slide.formula, 108, 532, 1020, 88));
  }
  return primitives;
}

function synthesisLayout(slide, index) {
  const body = [...slide.body, ...slide.bullets].join("\n");
  return [
    decoration("rect", 0, 0, WIDTH, HEIGHT, { fill: COLORS.surface }),
    decoration("roundRect", 60, 44, 1160, 622, { fill: "111923", radius: 20 }),
    textPrimitive("slide-index", String(index + 1).padStart(2, "0"), 1180, 72, 58, 30, 16, {
      color: COLORS.muted,
      align: "right",
    }),
    textPrimitive("slide-title", slide.title, 102, 84, 1040, 132, 39, {
      bold: true,
      color: COLORS.ink,
    }),
    textPrimitive("subheading", slide.primary_claim, 102, 246, 1030, 92, 24, {
      bold: true,
      color: COLORS.accent,
    }),
    textPrimitive("body", body, 102, 362, 1030, 132, 18),
    decoration("rect", 102, 548, 180, 5, { fill: COLORS.accent }),
    textPrimitive("body", "Learning objective resolved", 102, 570, 500, 36, 16, {
      bold: true,
      color: COLORS.muted,
    }),
  ];
}

function layoutSlide(slide, index, renderMath) {
  if (slide.kind === "opening") return openingLayout(slide);
  if (slide.kind === "synthesis") return synthesisLayout(slide, index);
  if (["example", "steps"].includes(slide.kind)) return exampleLayout(slide, index, renderMath);
  return conceptLayout(slide, index, renderMath);
}

function addPrimitiveToPptx(slide, pptx, primitive, fontFace) {
  const position = {
    x: inches(primitive.x),
    y: inches(primitive.y),
    w: inches(primitive.w),
    h: inches(primitive.h),
  };
  if (primitive.type === "decoration") {
    slide.addShape(pptx.ShapeType[primitive.kind] || pptx.ShapeType.rect, {
      ...position,
      fill: { color: primitive.fill },
      line: primitive.line ? { color: primitive.line, width: 1 } : { color: primitive.fill, transparency: 100 },
      radius: primitive.radius,
    });
    return;
  }
  if (primitive.type === "text") {
    if (primitive.fill) {
      slide.addShape(pptx.ShapeType.roundRect, {
        ...position,
        fill: { color: primitive.fill },
        line: { color: primitive.fill, transparency: 100 },
        radius: primitive.radius,
      });
    }
    slide.addText(primitive.text, {
      ...position,
      fontFace,
      fontSize: primitive.fontPt,
      bold: primitive.bold,
      color: primitive.color,
      align: primitive.align,
      valign: primitive.valign,
      margin: primitive.padding,
      breakLine: false,
      objectName: `lesson-${primitive.role}`,
      paraSpaceAfterPt: 0,
      lineSpacingMultiple: 0.92,
    });
    return;
  }
  if (primitive.type === "formula") {
    const data = `data:image/svg+xml;base64,${Buffer.from(primitive.svg, "utf8").toString("base64")}`;
    slide.addImage({ ...position, data, transparency: 0 });
  }
}

function primitiveHtml(primitive) {
  const common = `left:${primitive.x}px;top:${primitive.y}px;width:${primitive.w}px;height:${primitive.h}px;`;
  if (primitive.type === "decoration") {
    const radius = primitive.kind === "circle" ? "50%" : `${primitive.radius || 0}px`;
    return `<div class="decoration" style="${common}background:#${primitive.fill};border-radius:${radius}"></div>`;
  }
  if (primitive.type === "formula") {
    return `<div class="content formula" data-role="formula" aria-label="${escapeHtml(primitive.latex)}" style="${common}">${primitive.html}</div>`;
  }
  const background = primitive.fill ? `background:#${primitive.fill};border-radius:${primitive.radius}px;` : "";
  return `<div class="content text role-${primitive.role}" data-role="${primitive.role}" style="${common}${background}font-size:${primitive.fontPt * 4 / 3}px;font-weight:${primitive.bold ? 700 : 400};color:#${primitive.color};text-align:${primitive.align};padding:${primitive.padding}px;align-items:${primitive.valign === "middle" ? "center" : "flex-start"}">${escapeHtml(primitive.text)}</div>`;
}

function previewHtml(layouts, fontFace) {
  const slides = layouts.map((layout, index) => `<section class="ppt-slide" data-index="${index}">${layout.map(primitiveHtml).join("\n")}</section>`).join("\n");
  return `<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;width:1280px;height:720px;overflow:hidden;background:#081018}
body{font-family:${JSON.stringify(fontFace)},"Segoe UI",Arial,sans-serif}
.ppt-slide{display:none;position:relative;width:1280px;height:720px;overflow:hidden;background:#${COLORS.surface}}
.ppt-slide.active{display:block}.ppt-slide>div{position:absolute}.text{display:flex;white-space:pre-wrap;line-height:1.16;overflow:hidden}
.formula{display:flex;align-items:center;overflow:hidden;padding:6px 12px;font-size:32px}.formula mjx-container{margin:0!important;width:100%;height:100%}.formula svg{width:100%!important;height:100%!important;max-width:100%;max-height:100%}
</style></head><body>${slides}</body></html>`;
}

function rectanglesOverlap(a, b) {
  const width = Math.min(a.right, b.right) - Math.max(a.left, b.left);
  const height = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
  return width > 2 && height > 2;
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.input || !args.output) throw new Error("--input and --output are required");
  const payload = JSON.parse(fs.readFileSync(args.input, "utf8"));
  fs.mkdirSync(args.output, { recursive: true });
  const renderMath = mathRenderer();
  const layouts = payload.lesson.slides.map((slide, index) => layoutSlide(slide, index, renderMath));
  const fontFace = fontFor(payload.lesson.language);

  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Math150 Coach";
  pptx.company = "Math150 Coach";
  pptx.subject = payload.content_hash;
  pptx.title = payload.lesson.title;
  pptx.lang = payload.lesson.language || "en-US";
  pptx.theme = {
    headFontFace: fontFace,
    bodyFontFace: fontFace,
    lang: payload.lesson.language || "en-US",
  };
  payload.lesson.slides.forEach((lessonSlide, index) => {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.surface };
    layouts[index].forEach((primitive) => addPrimitiveToPptx(slide, pptx, primitive, fontFace));
    slide.addNotes(lessonSlide.speaker_notes || lessonSlide.narrative_job);
  });
  const pptxPath = path.join(args.output, "lesson.pptx");
  await pptx.writeFile({ fileName: pptxPath, compression: true });

  const previewPath = path.join(args.output, "pptx-preview.html");
  fs.writeFileSync(previewPath, previewHtml(layouts, fontFace), "utf8");
  const browser = await chromium.launch({ executablePath: args.browser || undefined, headless: true });
  const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 1 });
  const consoleErrors = [];
  const failedRequests = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text().slice(0, 1000));
  });
  page.on("requestfailed", (request) => {
    failedRequests.push({ url: request.url(), error: request.failure()?.errorText || "unknown" });
  });
  await page.goto(pathToFileURL(previewPath).href, { waitUntil: "load" });
  const slides = [];
  const overflowFindings = [];
  const overlapFindings = [];
  for (let index = 0; index < layouts.length; index += 1) {
    const report = await page.evaluate((slideIndex) => {
      document.querySelectorAll(".ppt-slide").forEach((slide, index) => slide.classList.toggle("active", index === slideIndex));
      const slide = document.querySelector(".ppt-slide.active");
      const elements = [...slide.querySelectorAll(".content")];
      return {
        elements: elements.map((element) => {
          const rect = element.getBoundingClientRect();
          return {
            role: element.dataset.role,
            left: rect.left,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom,
            scroll_width: element.scrollWidth,
            client_width: element.clientWidth,
            scroll_height: element.scrollHeight,
            client_height: element.clientHeight,
            font_pt: Number.parseFloat(getComputedStyle(element).fontSize || "0") * 0.75,
          };
        }),
      };
    }, index);
    report.elements.forEach((element) => {
      if (element.scroll_width > element.client_width + 1 || element.scroll_height > element.client_height + 1) {
        overflowFindings.push({ slide_index: index + 1, role: element.role, code: "element_overflow" });
      }
      const minimum = element.role === "deck-title" ? 50 : element.role === "slide-title" ? 35 : element.role === "subheading" ? 24 : element.role === "formula" ? 0 : 16;
      if (element.font_pt && element.font_pt + 0.01 < minimum) {
        overflowFindings.push({ slide_index: index + 1, role: element.role, code: "font_below_minimum" });
      }
    });
    for (let first = 0; first < report.elements.length; first += 1) {
      for (let second = first + 1; second < report.elements.length; second += 1) {
        if (rectanglesOverlap(report.elements[first], report.elements[second])) {
          overlapFindings.push({ slide_index: index + 1, roles: [report.elements[first].role, report.elements[second].role], code: "content_overlap" });
        }
      }
    }
    slides.push({ slide_id: payload.lesson.slides[index].slide_id, kind: payload.lesson.slides[index].kind, elements: report.elements });
    await page.screenshot({ path: path.join(args.output, `slide-${String(index + 1).padStart(3, "0")}.png`) });
  }
  await browser.close();
  fs.rmSync(previewPath, { force: true });
  const layoutReport = {
    passed: overflowFindings.length === 0 && overlapFindings.length === 0 && consoleErrors.length === 0 && failedRequests.length === 0,
    slide_count: layouts.length,
    viewport: { width: WIDTH, height: HEIGHT },
    minimum_font_sizes: { deck_title: 50, slide_title: 35, subheading: 24, body: 16 },
    slides,
    overflow_findings: overflowFindings,
    overlap_findings: overlapFindings,
    console_errors: consoleErrors,
    failed_requests: failedRequests,
  };
  fs.writeFileSync(path.join(args.output, "layout-report.json"), `${JSON.stringify(layoutReport, null, 2)}\n`, "utf8");
  if (!layoutReport.passed) throw new Error(`PPTX layout quality gates failed: ${JSON.stringify(layoutReport)}`);
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
