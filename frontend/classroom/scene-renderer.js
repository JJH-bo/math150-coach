import { escapeHtml, renderBlock } from "./content-renderer.js";

function text(value) {
  return escapeHtml(value ?? "").replaceAll("\n", "<br>");
}

function childrenFor(session, contentId) {
  return (session.expansions || []).filter(
    (expansion) => expansion.parent_content_id === contentId,
  );
}

function renderExpansion(expansion, session, depth) {
  const active = (session.expansion_stack || []).includes(expansion.id);
  const representation = String(expansion.representation || "")
    .replaceAll("_", " ");
  return `
    <details class="live-expansion" data-live-expansion-id="${escapeHtml(expansion.id)}"
      data-depth="${depth}" ${active ? "open" : ""}>
      <summary>
        <span class="expansion-label">GPT 针对这里重新设计</span>
        <strong>${text(expansion.title)}</strong>
        <small>${text(expansion.learner_question)}</small>
      </summary>
      <div class="live-expansion-body">
        <div class="expansion-focus">
          <span>${text(representation)}</span>
          <p>${text(expansion.focus_relation)}</p>
        </div>
        ${(expansion.blocks || []).map((block) =>
          renderBlockWithExpansions(block, session, depth + 1)
        ).join("")}
        <div class="return-connection">
          <span>重新接回完整模型</span>
          <p>${text(expansion.return_connection)}</p>
        </div>
      </div>
    </details>
  `;
}

function renderBlockWithExpansions(block, session, depth = 0) {
  const expansions = childrenFor(session, block.id)
    .map((item) => renderExpansion(item, session, depth))
    .join("");
  return `${renderBlock(block)}${expansions}`;
}

function revealedSteps(session) {
  const revealed = new Set(session.revealed_step_ids || []);
  return (session.baseline_steps || []).filter((step) => revealed.has(step.id));
}

export function renderLearningSession(session, module) {
  const steps = revealedSteps(session);
  const total = session.baseline_steps?.length || 0;
  const hasNext = steps.length < total;
  const activeExpansionId = session.expansion_stack?.at(-1);
  return `
    <header class="module-introduction" data-content-id="${escapeHtml(module.id || session.module_id)}">
      <p class="eyebrow">Core module / stable baseline</p>
      <h1>${text(module.title)}</h1>
      ${module.summary ? `<p>${text(module.summary)}</p>` : ""}
      <div class="session-progress" aria-label="基础学习路线进度">
        <span>当前只展开到这里</span>
        <strong>${steps.length} / ${total}</strong>
      </div>
    </header>
    <div class="baseline-route">
      ${steps.map((step, index) => `
        <section class="baseline-step" data-baseline-step-id="${escapeHtml(step.id)}">
          <header>
            <span>${String(index + 1).padStart(2, "0")}</span>
            <div>
              <small>基础学习路线</small>
              <h2>${text(step.title)}</h2>
            </div>
          </header>
          ${(step.blocks || []).map((block) =>
            renderBlockWithExpansions(block, session)
          ).join("")}
        </section>
      `).join("")}
    </div>
    <footer class="learning-controls">
      ${hasNext ? `
        <button id="revealNextStep" class="primary-learning-action" type="button">
          继续展开基础路线
        </button>
        <p>这里只显示已经发布的下一步，不会临时生成新内容。</p>
      ` : `
        <div class="baseline-complete">
          <span>基础路线已经完整展开</span>
          <strong>现在可以回看整个核心模型</strong>
        </div>
      `}
      ${activeExpansionId ? `
        <button id="returnFromExpansion" type="button"
          data-expansion-id="${escapeHtml(activeExpansionId)}">
          返回上一层解释
        </button>
      ` : ""}
      <aside class="gpt-learning-handoff">
        <span>某一步没有学懂？</span>
        <strong>回到自定义 GPT 直接说“这里没懂”</strong>
        <p>GPT 会读取当前高亮位置，并把新的详细解释插入这里。</p>
      </aside>
    </footer>
  `;
}
