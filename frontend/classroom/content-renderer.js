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
  return /^\/api\/classroom\/v1\/assets\/a-[a-f0-9]{64}$/.test(uri)
    ? escapeHtml(uri)
    : "";
}

export function formatMath(latex, { display = true } = {}) {
  const source = String(latex || "").trim();
  return `<span class="math-typeset" data-latex="${escapeHtml(source)}" data-display="${display}">${escapeHtml(source)}</span>`;
}

export async function typesetMath(root, mathJax = globalThis.MathJax) {
  const targets = [...(root?.querySelectorAll?.(".math-typeset[data-latex]") || [])];
  if (!targets.length || typeof mathJax?.tex2chtmlPromise !== "function") {
    return { rendered: 0, fallback: targets.length };
  }
  let rendered = 0;
  for (const target of targets) {
    try {
      const node = await mathJax.tex2chtmlPromise(target.dataset.latex, {
        display: target.dataset.display !== "false",
      });
      target.replaceChildren(node);
      target.classList.add("is-typeset");
      rendered += 1;
    } catch {
      target.classList.add("math-render-fallback");
    }
  }
  mathJax.startup?.document?.clear?.();
  mathJax.startup?.document?.updateDocument?.();
  return { rendered, fallback: targets.length - rendered };
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
      <div class="detail-content">
        ${branch.trigger_question ? `<section class="detail-question"><span>触发问题</span><p>${text(branch.trigger_question)}</p></section>` : ""}
        ${branch.learning_obstacle ? `<section class="detail-obstacle"><span>当前障碍</span><p>${text(branch.learning_obstacle)}</p></section>` : ""}
        ${branch.focus_relation ? `<section class="detail-focus"><span>这次换一个表示方式</span><p>${text(branch.focus_relation)}</p></section>` : ""}
        ${(branch.bridge_steps || []).length ? `<section class="detail-bridge"><span>重新搭桥</span>${steps(branch.bridge_steps)}</section>` : ""}
        ${(branch.blocks || []).map(renderBlock).join("")}
        ${branch.return_connection ? `<section class="detail-return"><span>接回主线</span><p>${text(branch.return_connection)}</p></section>` : ""}
      </div>
    </details>
  `).join("");
}

function formulaEntries(data) {
  if (Array.isArray(data.formulae)) {
    return data.formulae.map((entry) => (
      typeof entry === "string"
        ? { latex: entry, explanation: "" }
        : {
            latex: entry.latex || entry.formula || "",
            explanation: entry.explanation || entry.text || "",
          }
    ));
  }
  return [{
    latex: data.latex || data.formula || "",
    explanation: data.explanation || data.text || "",
  }];
}

function renderFormulaExplanation(data) {
  const entries = formulaEntries(data);
  const title = data.title ? `<h3>${text(data.title)}</h3>` : "";
  const introduction = data.text && data.explanation === undefined
    ? `<p class="formula-introduction">${text(data.text)}</p>`
    : "";
  return `<section class="formula-explanation-set">${title}${introduction}${
    entries.map((entry) => {
      const layoutClass = entry.latex.length > 56 ? " is-long" : "";
      return `
      <div class="formula-pair${layoutClass}">
        <div class="formula" role="math">${formatMath(entry.latex)}</div>
        <div class="formula-explanation">${text(entry.explanation)}</div>
      </div>
    `;
    }).join("")
  }</section>`;
}

function renderComparison(data) {
  const entries = Array.isArray(data.items)
    ? data.items
    : [data.left, data.right].filter(Boolean);
  return `<div class="comparison-grid">${entries.map((entry, index) => {
    const normalized = typeof entry === "string"
      ? { title: `要点 ${index + 1}`, body: entry }
      : {
          title: entry?.title || entry?.name || entry?.label || `要点 ${index + 1}`,
          body: entry?.body || entry?.text || entry?.description || entry?.focus || entry?.value || "",
        };
    return `
    <section>
      <strong>${text(normalized.title)}</strong>
      <p>${text(normalized.body)}</p>
    </section>
  `;
  }).join("")}</div>`;
}

function renderBody(block) {
  const data = block.data || {};
  if (block.kind === "prose") return `<div class="prose">${text(data.markdown || data.text)}</div>`;
  if (block.kind === "heading") {
    const level = Math.min(4, Math.max(2, Number(data.level || 2)));
    return `<h${level}>${text(data.text || data.title)}</h${level}>`;
  }
  if (block.kind === "callout") return `<aside class="callout"><strong>${text(data.title || "核心结论")}</strong><div>${text(data.markdown || data.text)}</div></aside>`;
  if (block.kind === "math") return `<div class="display-math" role="math">${formatMath(data.latex || data.formula)}</div>`;
  if (block.kind === "formula_explanation") return renderFormulaExplanation(data);
  if (block.kind === "derivation") return `<section class="derivation"><h3>${text(data.title || "推导")}</h3>${steps(data.steps)}</section>`;
  if (block.kind === "comparison") return renderComparison(data);
  if (block.kind === "worked_example") return `<section class="worked-example"><p class="example-label">完整例子</p><h3>${text(data.prompt || data.title)}</h3>${steps(data.steps, "solution-steps")}</section>`;
  if (block.kind === "code_explanation") return `<div class="code-pair"><pre><code data-language="${escapeHtml(data.language || "")}">${escapeHtml(data.code)}</code></pre>${steps(data.lines || [], "code-lines")}</div>`;
  if (block.kind === "table") return table(data.headers || [], data.rows || []);
  if (block.kind === "matrix") return table([], data.values || [], "matrix-table");
  if (block.kind === "image") return `<figure><img src="${safeUri(data.uri)}" alt="${escapeHtml(data.alt || "")}"><figcaption>${text(data.caption)}</figcaption></figure>`;
  if (block.kind === "model_reference") {
    const instanceId = data.instance_id || data.model_id || "";
    return `<button class="model-reference" type="button" data-model-instance-id="${escapeHtml(instanceId)}">${text(data.label || data.description || "观察教学模型")}</button>`;
  }
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
      ${segment.question_answered ? `<section class="segment-question"><span>这一步解决</span><p>${text(segment.question_answered)}</p></section>` : ""}
      ${segment.bridge_from_previous ? `<section class="segment-bridge"><span>从上一理解走到这里</span><p>${text(segment.bridge_from_previous)}</p></section>` : ""}
      ${segment.mechanism ? `<section class="segment-mechanism"><span>核心机制</span><p>${text(segment.mechanism)}</p></section>` : ""}
      ${(segment.blocks || []).map(renderBlock).join("")}
      ${segment.exit_understanding ? `<section class="segment-exit"><span>学完应当看见</span><p>${text(segment.exit_understanding)}</p></section>` : ""}
    </section>
  `).join("");
  const bridge = module.novice_bridge;
  return `
    <header class="module-introduction" data-content-id="${escapeHtml(module.id)}">
      <p class="eyebrow">Core module</p>
      <h1>${text(module.title)}</h1>
      ${module.summary ? `<p>${text(module.summary)}</p>` : ""}
      ${module.core_question ? `<section class="module-contract module-core-question"><span>核心问题</span><strong>${text(module.core_question)}</strong></section>` : ""}
      ${module.chapter_role ? `<section class="module-contract"><span>本章作用</span><p>${text(module.chapter_role)}</p></section>` : ""}
      ${module.why_indispensable ? `<section class="module-contract"><span>为什么不可删除</span><p>${text(module.why_indispensable)}</p></section>` : ""}
      ${bridge ? `<section class="module-contract module-novice-bridge"><span>进入这一步前的桥梁</span><p>${text(bridge.missing_bridge)}</p><p><strong>从这里开始：</strong>${text(bridge.concrete_anchor)}</p></section>` : ""}
    </header>
    ${continuous}
    ${segments}
  `;
}
