const TAU = Math.PI * 2;

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function periodicX(x) {
  return ((x + Math.PI) % TAU + TAU) % TAU - Math.PI;
}

function targetValue(view, x, amplitude) {
  const wrapped = periodicX(x);
  if (view === "square-wave") return wrapped >= 0 ? amplitude : -amplitude;
  if (view === "even-extension") return amplitude * Math.abs(wrapped) / Math.PI;
  return amplitude * wrapped / Math.PI;
}

function partialValue(view, x, count, amplitude) {
  if (view === "square-wave") {
    let total = 0;
    for (let index = 0; index < count; index += 1) {
      const harmonic = index * 2 + 1;
      total += Math.sin(harmonic * x) / harmonic;
    }
    return amplitude * 4 * total / Math.PI;
  }
  if (view === "even-extension") {
    let total = Math.PI / 2;
    for (let index = 0; index < count; index += 1) {
      const harmonic = index * 2 + 1;
      total -= 4 * Math.cos(harmonic * x) / (Math.PI * harmonic * harmonic);
    }
    return amplitude * total / Math.PI;
  }
  let total = 0;
  for (let harmonic = 1; harmonic <= count; harmonic += 1) {
    total += 2 * ((harmonic % 2 === 0) ? -1 : 1) * Math.sin(harmonic * x) / harmonic;
  }
  return amplitude * total / Math.PI;
}

export function computeFourierSnapshot(
  state = "base-interval",
  parameters = {},
  highlightedTarget = null,
) {
  return {
    state,
    harmonicCount: Number(parameters["harmonic-count"] ?? 7),
    view: parameters.view ?? "square-wave",
    amplitude: Number(parameters.amplitude ?? 1),
    highlightedTarget,
  };
}

export function createTeachingModel(context) {
  let state = "base-interval";
  let parameters = {
    "harmonic-count": 7,
    view: "square-wave",
    amplitude: 1,
  };
  let highlightedTarget = null;
  let canvas = null;
  let drawing = null;

  function drawCurve(mapX, mapY, valueAt, color, width, dashed = false) {
    drawing.save();
    drawing.strokeStyle = color;
    drawing.lineWidth = width;
    drawing.setLineDash(dashed ? [8, 7] : []);
    drawing.beginPath();
    let started = false;
    let previous = null;
    for (let index = 0; index <= 900; index += 1) {
      const x = -3 * Math.PI + index * 6 * Math.PI / 900;
      const y = valueAt(x);
      const point = [mapX(x), mapY(y)];
      if (
        !started
        || (previous !== null && Math.abs(y - previous) > parameters.amplitude * 1.4)
      ) {
        drawing.moveTo(point[0], point[1]);
        started = true;
      } else {
        drawing.lineTo(point[0], point[1]);
      }
      previous = y;
    }
    drawing.stroke();
    drawing.restore();
  }

  function draw() {
    if (!canvas || !drawing) return;
    const width = canvas.width = Math.max(640, context.root.clientWidth || 860);
    const height = canvas.height = Math.max(440, context.root.clientHeight || 560);
    const left = 58;
    const right = width - 28;
    const top = 48;
    const bottom = height - 64;
    const plotWidth = right - left;
    const plotHeight = bottom - top;
    const amplitude = clamp(Number(parameters.amplitude || 1), 0.5, 2);
    const count = clamp(Number(parameters["harmonic-count"] || 7), 1, 25);
    const view = parameters.view || "square-wave";
    const mapX = (x) => left + (x + 3 * Math.PI) * plotWidth / (6 * Math.PI);
    const mapY = (y) => top + plotHeight / 2 - y * plotHeight / (amplitude * 3.2);

    drawing.fillStyle = "#061019";
    drawing.fillRect(0, 0, width, height);
    const gradient = drawing.createLinearGradient(0, top, 0, bottom);
    gradient.addColorStop(0, "rgba(35, 111, 139, .15)");
    gradient.addColorStop(1, "rgba(3, 15, 23, .02)");
    drawing.fillStyle = gradient;
    drawing.fillRect(left, top, plotWidth, plotHeight);

    drawing.strokeStyle = "rgba(166, 220, 233, .18)";
    drawing.lineWidth = 1;
    for (let multiple = -3; multiple <= 3; multiple += 1) {
      const px = mapX(multiple * Math.PI);
      drawing.beginPath();
      drawing.moveTo(px, top);
      drawing.lineTo(px, bottom);
      drawing.stroke();
    }
    drawing.beginPath();
    drawing.moveTo(left, mapY(0));
    drawing.lineTo(right, mapY(0));
    drawing.stroke();

    if (state === "base-interval") {
      drawing.fillStyle = "rgba(101, 222, 247, .08)";
      drawing.fillRect(mapX(-Math.PI), top, mapX(Math.PI) - mapX(-Math.PI), plotHeight);
      drawing.strokeStyle = "rgba(101, 222, 247, .65)";
      drawing.setLineDash([7, 6]);
      for (const endpoint of [-Math.PI, Math.PI]) {
        drawing.beginPath();
        drawing.moveTo(mapX(endpoint), top);
        drawing.lineTo(mapX(endpoint), bottom);
        drawing.stroke();
      }
      drawing.setLineDash([]);
    }

    const targetStart = state === "base-interval" ? -Math.PI : -3 * Math.PI;
    const targetEnd = state === "base-interval" ? Math.PI : 3 * Math.PI;
    drawing.save();
    drawing.beginPath();
    drawing.rect(mapX(targetStart), top, mapX(targetEnd) - mapX(targetStart), plotHeight);
    drawing.clip();
    drawCurve(
      mapX,
      mapY,
      (x) => targetValue(view, x, amplitude),
      "rgba(101, 222, 247, .75)",
      2.5,
      true,
    );
    drawing.restore();

    if (state === "partial-sum" || state === "discontinuity") {
      drawCurve(
        mapX,
        mapY,
        (x) => partialValue(view, x, count, amplitude),
        "#f0c47b",
        3.5,
      );
    }

    if (
      state === "discontinuity"
      || highlightedTarget === "jump-average"
    ) {
      const jumpX = 0;
      const average = 0;
      drawing.strokeStyle = "#fff1aa";
      drawing.lineWidth = 2;
      drawing.setLineDash([5, 5]);
      drawing.beginPath();
      drawing.moveTo(mapX(jumpX), top);
      drawing.lineTo(mapX(jumpX), bottom);
      drawing.stroke();
      drawing.setLineDash([]);
      drawing.fillStyle = "#061019";
      drawing.beginPath();
      drawing.arc(mapX(jumpX), mapY(average), 8, 0, TAU);
      drawing.fill();
      drawing.strokeStyle = "#fff1aa";
      drawing.lineWidth = 3;
      drawing.stroke();
      drawing.fillStyle = "#fff1aa";
      drawing.font = "600 14px system-ui";
      drawing.fillText("级数和 = (左极限 + 右极限) / 2", mapX(jumpX) + 14, mapY(average) - 14);
    }

    drawing.fillStyle = "#edf8fa";
    drawing.font = "600 20px system-ui";
    const viewNames = {
      "square-wave": "方波",
      sawtooth: "锯齿波",
      "even-extension": "半区间偶延拓",
      "odd-extension": "半区间奇延拓",
    };
    drawing.fillText(`${viewNames[view]}：原函数与傅里叶部分和`, left, 28);
    drawing.fillStyle = "#91a9b2";
    drawing.font = "14px system-ui";
    drawing.fillText(`谐波数量 N = ${count}`, left, height - 28);
    drawing.fillStyle = "#65def7";
    drawing.fillRect(width - 286, 18, 22, 3);
    drawing.fillStyle = "#bcd7de";
    drawing.fillText("原函数 / 周期延拓", width - 256, 25);
    drawing.fillStyle = "#f0c47b";
    drawing.fillRect(width - 132, 18, 22, 3);
    drawing.fillStyle = "#bcd7de";
    drawing.fillText("部分和", width - 102, 25);
  }

  return {
    mount(initial) {
      state = initial.state || state;
      parameters = { ...parameters, ...(initial.parameters || {}) };
      canvas = document.createElement("canvas");
      canvas.setAttribute("aria-label", "傅里叶级数原函数与有限部分和交互图");
      context.root.replaceChildren(canvas);
      drawing = canvas.getContext("2d");
      draw();
    },
    update(next) {
      if (next.state) state = next.state;
      if (next.parameters) parameters = { ...parameters, ...next.parameters };
      draw();
    },
    perform(action) {
      if (action === "highlight-jump") highlightedTarget = "jump-average";
      if (action === "clear-highlight") highlightedTarget = null;
      draw();
    },
    pause() {},
    resume() { draw(); },
    reset() {
      state = "base-interval";
      highlightedTarget = null;
      parameters = {"harmonic-count": 7, view: "square-wave", amplitude: 1};
      draw();
    },
    snapshot() {
      return computeFourierSnapshot(state, parameters, highlightedTarget);
    },
    dispose() {
      context.root.replaceChildren();
      canvas = null;
      drawing = null;
    },
  };
}
