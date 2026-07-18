export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function text(value) {
  return escapeHtml(value).replaceAll("\n", "<br>");
}

function safeUri(value) {
  const uri = String(value || "");
  return /^(https?:\/\/|\/(?!\/)|data:image\/)/.test(uri) ? escapeHtml(uri) : "";
}

function steps(values, className = "derivation-steps") {
  return `<ol class="${className}">${(values || []).map((item) =>
    `<li>${text(typeof item === "string" ? item : item.explanation || item.text || JSON.stringify(item))}</li>`
  ).join("")}</ol>`;
}

function table(headers, rows, className = "content-table") {
  const head = headers?.length
    ? `<thead><tr>${headers.map((item) => `<th>${text(item)}</th>`).join("")}</tr></thead>`
    : "";
  return `<div class="table-scroll"><table class="${className}">${head}<tbody>${
    (rows || []).map((row) => `<tr>${row.map((item) => `<td>${text(item)}</td>`).join("")}</tr>`).join("")
  }</tbody></table></div>`;
}

function renderDetails(block) {
  return (block.detail_branches || []).map((branch) => `
    <details class="detail-branch" data-detail-id="${escapeHtml(branch.id)}" data-parent-content-id="${escapeHtml(block.id)}">
      <summary><span>详细展开</span><strong>${text(branch.title)}</strong></summary>
      <div class="detail-content">${(branch.blocks || []).map(renderBlock).join("")}</div>
    </details>
  `).join("");
}

function renderBody(block) {
  const data = block.data || {};
  if (block.kind === "prose") return `<div class="prose">${text(data.markdown || data.text)}</div>`;
  if (block.kind === "heading") {
    const level = Math.min(4, Math.max(2, Number(data.level || 2)));
    return `<h${level}>${text(data.text || data.title)}</h${level}>`;
  }
  if (block.kind === "callout") return `<aside class="callout"><strong>${text(data.title || "核心结论")}</strong><div>${text(data.markdown || data.text)}</div></aside>`;
  if (block.kind === "math") return `<div class="display-math" role="math">${text(data.latex)}</div>`;
  if (block.kind === "formula_explanation") return `<div class="formula-pair"><div class="formula" role="math">${text(data.latex)}</div><div class="formula-explanation">${text(data.explanation)}</div></div>`;
  if (block.kind === "derivation") return `<section class="derivation"><h3>${text(data.title || "推导")}</h3>${steps(data.steps)}</section>`;
  if (block.kind === "comparison") return `<div class="comparison-grid"><section><strong>${text(data.left?.title)}</strong><p>${text(data.left?.body)}</p></section><section><strong>${text(data.right?.title)}</strong><p>${text(data.right?.body)}</p></section></div>`;
  if (block.kind === "worked_example") return `<section class="worked-example"><p class="example-label">完整例子</p><h3>${text(data.prompt || data.title)}</h3>${steps(data.steps, "solution-steps")}</section>`;
  if (block.kind === "code_explanation") return `<div class="code-pair"><pre><code data-language="${escapeHtml(data.language || "")}">${escapeHtml(data.code)}</code></pre>${steps(data.lines || [], "code-lines")}</div>`;
  if (block.kind === "table") return table(data.headers || [], data.rows || []);
  if (block.kind === "matrix") return table([], data.values || [], "matrix-table");
  if (block.kind === "image") return `<figure><img src="${safeUri(data.uri)}" alt="${escapeHtml(data.alt || "")}"><figcaption>${text(data.caption)}</figcaption></figure>`;
  if (block.kind === "model_reference") return `<button class="model-reference" type="button" data-model-instance-id="${escapeHtml(data.instance_id)}">${text(data.label || "观察教学模型")}</button>`;
  if (block.kind === "group") return `<section class="content-group"><h3>${text(data.title)}</h3>${(data.blocks || []).map((child) => renderBlock({ detail_branches: [], ...child })).join("")}</section>`;
  return `<aside class="unknown-block"><strong>暂不支持的内容类型</strong><p>${text(block.kind)}</p></aside>`;
}

export function renderBlock(block) {
  const className = String(block.kind || "unknown").replaceAll("_", "-");
  return `
    <article class="content-block block-${escapeHtml(className)}" data-content-id="${escapeHtml(block.id)}">
      ${renderBody(block)}
      ${renderDetails(block)}
    </article>
  `;
}

export function renderModule(module) {
  const continuous = (module.blocks || []).map(renderBlock).join("");
  const segments = (module.segments || []).map((segment, index) => `
    <section class="learning-segment" data-segment-id="${escapeHtml(segment.id)}">
      <header><span>${String(index + 1).padStart(2, "0")}</span><h2>${text(segment.title || "")}</h2></header>
      ${(segment.blocks || []).map(renderBlock).join("")}
    </section>
  `).join("");
  return `
    <header class="module-introduction" data-content-id="${escapeHtml(module.id)}">
      <p class="eyebrow">Core module</p>
      <h1>${text(module.title)}</h1>
      ${module.summary ? `<p>${text(module.summary)}</p>` : ""}
    </header>
    ${continuous}
    ${segments}
  `;
}
