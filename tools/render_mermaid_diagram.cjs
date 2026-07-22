const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

function parseArguments(argv) {
  const parsed = {};
  for (let index = 2; index < argv.length; index += 2) {
    const name = argv[index];
    const value = argv[index + 1];
    if (!name?.startsWith("--") || value === undefined) {
      throw new Error("worker arguments must be --name value pairs");
    }
    parsed[name.slice(2)] = value;
  }
  for (const required of ["spec", "source", "svg", "png", "report"]) {
    if (!parsed[required]) throw new Error(`missing --${required}`);
  }
  return parsed;
}

function mermaidBrowserBundle() {
  const packagePath = require.resolve("mermaid/package.json");
  return path.join(path.dirname(packagePath), "dist", "mermaid.min.js");
}

async function main() {
  const options = parseArguments(process.argv);
  const specification = JSON.parse(fs.readFileSync(options.spec, "utf8"));
  const source = fs.readFileSync(options.source, "utf8");
  const packageMetadata = JSON.parse(
    fs.readFileSync(require.resolve("mermaid/package.json"), "utf8"),
  );
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
      failedRequests.push({
        url: request.url().replace(/^file:\/\/\/.*?([^/\\]+)$/, "file:///<local>/$1"),
        error: request.failure()?.errorText || "request failed",
      });
    });
    const background = specification.theme === "dark" ? "#0B1119" : "#F7F9FC";
    await page.setContent(
      `<!doctype html><html><head><meta charset="utf-8"><style>
      html,body{margin:0;width:100%;height:100%;overflow:hidden;background:${background};}
      body{display:grid;grid-template-rows:auto 1fr;gap:22px;padding:34px 30px;box-sizing:border-box;
        color:${specification.theme === "dark" ? "#F4F7FB" : "#132033"};font-family:Inter,Arial,sans-serif;}
      header{display:grid;gap:8px;} .kicker{color:#33C3FF;font-size:13px;font-weight:800;letter-spacing:.14em;}
      h1{margin:0;font-size:30px;line-height:1.12;letter-spacing:-.025em;}
      #mount{min-width:0;min-height:0;width:100%;height:100%;display:grid;place-items:center;
        border:1px solid ${specification.theme === "dark" ? "#273545" : "#D7E0EA"};border-radius:18px;
        background:${specification.theme === "dark" ? "#101923" : "#FFFFFF"};padding:8px;box-sizing:border-box;}
      #mount svg{display:block;max-width:100%;max-height:100%;width:auto;height:auto;}
      </style></head><body><header><div class="kicker">CONCEPT DIAGRAM</div><h1 id="title"></h1></header><main id="mount"></main></body></html>`,
      { waitUntil: "load" },
    );
    await page.addScriptTag({ path: mermaidBrowserBundle() });
    const rendered = await page.evaluate(
      async ({ sourceText, theme, title, altText }) => {
        window.mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme,
          htmlLabels: false,
          deterministicIds: true,
          deterministicIDSeed: "math150-studio-diagram-v1",
          handDrawnSeed: 150,
          flowchart: {
            htmlLabels: false,
            curve: "basis",
            useMaxWidth: true,
            nodeSpacing: 24,
            rankSpacing: 20,
            diagramPadding: 4,
          },
        });
        document.getElementById("title").textContent = title;
        const result = await window.mermaid.render("studio-diagram", sourceText);
        const mount = document.getElementById("mount");
        mount.innerHTML = result.svg;
        const svg = mount.querySelector("svg");
        svg.setAttribute("role", "img");
        svg.setAttribute("aria-label", altText);
        const titleNode = document.createElementNS("http://www.w3.org/2000/svg", "title");
        titleNode.textContent = title;
        svg.prepend(titleNode);
        const mountBounds = mount.getBoundingClientRect();
        const svgBounds = svg.getBoundingClientRect();
        const nodeCount = svg.querySelectorAll("g.node").length;
        const edgeCount = svg.querySelectorAll("g.edgePath, path.flowchart-link").length;
        const textCount = svg.querySelectorAll("text").length;
        const viewBox = svg.viewBox.baseVal;
        const scale = Math.min(
          svgBounds.width / Math.max(viewBox.width, 1),
          svgBounds.height / Math.max(viewBox.height, 1),
        );
        const effectiveFontPx = Math.min(
          ...Array.from(svg.querySelectorAll("text")).map((node) =>
            Number.parseFloat(getComputedStyle(node).fontSize) * scale,
          ),
        );
        return {
          svg: svg.outerHTML,
          mountBounds: {
            left: mountBounds.left,
            top: mountBounds.top,
            right: mountBounds.right,
            bottom: mountBounds.bottom,
          },
          svgBounds: {
            left: svgBounds.left,
            top: svgBounds.top,
            right: svgBounds.right,
            bottom: svgBounds.bottom,
            width: svgBounds.width,
            height: svgBounds.height,
          },
          nodeCount,
          edgeCount,
          textCount,
          effectiveFontPx,
        };
      },
      {
        sourceText: source,
        theme: specification.theme === "dark" ? "dark" : "default",
        title: specification.title,
        altText: specification.alt_text,
      },
    );
    const tolerance = 1;
    const clipped =
      rendered.svgBounds.left < rendered.mountBounds.left - tolerance ||
      rendered.svgBounds.top < rendered.mountBounds.top - tolerance ||
      rendered.svgBounds.right > rendered.mountBounds.right + tolerance ||
      rendered.svgBounds.bottom > rendered.mountBounds.bottom + tolerance;
    fs.writeFileSync(options.svg, `${rendered.svg}\n`, "utf8");
    await page.screenshot({ path: options.png, fullPage: false });
    const report = {
      passed:
        consoleErrors.length === 0 &&
        pageErrors.length === 0 &&
        failedRequests.length === 0 &&
        !clipped &&
        rendered.nodeCount === specification.nodes.length &&
        rendered.textCount >= specification.nodes.length &&
        rendered.effectiveFontPx >= 14,
      renderer: `Mermaid ${packageMetadata.version}`,
      viewport: { width: specification.width, height: specification.height },
      svg_bounds: rendered.svgBounds,
      node_count: rendered.nodeCount,
      rendered_edge_path_count: rendered.edgeCount,
      text_count: rendered.textCount,
      minimum_effective_font_px: rendered.effectiveFontPx,
      clipped,
      console_errors: consoleErrors,
      page_errors: pageErrors,
      failed_requests: failedRequests,
    };
    fs.writeFileSync(options.report, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    if (!report.passed) throw new Error(`diagram quality report failed: ${JSON.stringify(report)}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
