export function computeLimitSnapshot(state = "overview", parameters = {}, highlightedTarget = null) {
  const delta = Number(parameters.delta ?? 0.5);
  return {
    state,
    delta,
    epsilon: Number((delta * 0.7).toFixed(3)),
    targetX: 1,
    targetY: 2,
    theme: parameters.theme ?? "cyan",
    highlightedTarget,
  };
}

export function createTeachingModel(context) {
  let state = "overview";
  let parameters = { delta: 0.5, theme: "cyan" };
  let highlightedTarget = null;
  let canvas;
  let ctx;

  function draw() {
    if (!ctx) return;
    const width = canvas.width = Math.max(640, context.root.clientWidth || 800);
    const height = canvas.height = Math.max(420, context.root.clientHeight || 520);
    const cyan = parameters.theme === "amber" ? "#f3b76a" : "#63e6ff";
    ctx.fillStyle = "#061019";
    ctx.fillRect(0, 0, width, height);
    const ox = width * 0.46;
    const oy = height * 0.62;
    const sx = width * 0.16;
    const sy = height * 0.16;
    ctx.strokeStyle = "rgba(190,220,232,.28)";
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(50, oy); ctx.lineTo(width - 50, oy);
    ctx.moveTo(ox, 45); ctx.lineTo(ox, height - 45); ctx.stroke();
    const map = (x, y) => [ox + (x - 1) * sx, oy - (y - 2) * sy];
    const left = map(1 - parameters.delta, 2);
    const right = map(1 + parameters.delta, 2);
    ctx.fillStyle = "rgba(99,230,255,.09)";
    ctx.fillRect(left[0], 45, right[0] - left[0], height - 90);
    ctx.strokeStyle = cyan; ctx.lineWidth = 4; ctx.beginPath();
    for (let x = -1; x <= 3; x += 0.025) {
      const [px, py] = map(x, x + 1);
      if (x === -1) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.stroke();
    const [hx, hy] = map(1, 2);
    ctx.fillStyle = "#061019"; ctx.strokeStyle = "#f7fbff"; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.arc(hx, hy, state === "hole" ? 12 : 8, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.setLineDash([8, 8]); ctx.strokeStyle = highlightedTarget ? "#fff0a8" : "rgba(99,230,255,.65)";
    ctx.beginPath(); ctx.moveTo(50, hy); ctx.lineTo(width - 50, hy); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = "#eaf7fb"; ctx.font = "600 22px system-ui";
    ctx.fillText("x → 1 时，f(x) → 2", 54, 72);
    ctx.fillStyle = "#9db7c2"; ctx.font = "15px system-ui";
    ctx.fillText(`δ = ${parameters.delta.toFixed(2)}    ε = ${(parameters.delta * 0.7).toFixed(2)}`, 54, 102);
  }

  return {
    mount(initial) {
      state = initial.state || state;
      parameters = { ...parameters, ...(initial.parameters || {}) };
      canvas = document.createElement("canvas");
      canvas.setAttribute("aria-label", "极限邻域二维模型");
      context.root.replaceChildren(canvas);
      ctx = canvas.getContext("2d");
      draw();
    },
    update(next) {
      if (next.state) state = next.state;
      if (next.parameters) parameters = { ...parameters, ...next.parameters };
      draw();
    },
    perform(action) {
      if (action === "highlight-target") highlightedTarget = "target-value";
      if (action === "clear-highlight") highlightedTarget = null;
      draw();
    },
    pause() {},
    resume() { draw(); },
    reset() { state = "overview"; highlightedTarget = null; draw(); },
    snapshot() { return computeLimitSnapshot(state, parameters, highlightedTarget); },
    dispose() { context.root.replaceChildren(); canvas = null; ctx = null; },
  };
}
