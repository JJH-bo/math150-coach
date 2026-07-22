(() => {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const spec = JSON.parse(document.getElementById("geometry-spec").textContent);
  const svg = document.getElementById("geometry-canvas");
  const controls = document.getElementById("geometry-controls");
  const values = Object.fromEntries(spec.parameters.map((item) => [item.id, item.value]));
  const baseline = { ...values };
  const plot = { left: 64, right: 24, top: 28, bottom: 52, width: 900, height: 430 };

  const element = (name, attributes = {}, text = null) => {
    const node = document.createElementNS(NS, name);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
    if (text !== null) node.textContent = text;
    return node;
  };
  const scalar = (value) =>
    typeof value === "number"
      ? value
      : value.offset + value.scale * values[value.parameter];
  const xPixel = (value) =>
    plot.left + ((value - spec.viewport.x_min) / (spec.viewport.x_max - spec.viewport.x_min)) *
      (plot.width - plot.left - plot.right);
  const yPixel = (value) =>
    plot.top + ((spec.viewport.y_max - value) / (spec.viewport.y_max - spec.viewport.y_min)) *
      (plot.height - plot.top - plot.bottom);
  const radiusPixel = (value) => {
    const sx = (plot.width - plot.left - plot.right) / (spec.viewport.x_max - spec.viewport.x_min);
    const sy = (plot.height - plot.top - plot.bottom) / (spec.viewport.y_max - spec.viewport.y_min);
    return Math.abs(value) * Math.min(sx, sy);
  };
  const tickStep = (span) => {
    const rough = span / 8;
    const power = 10 ** Math.floor(Math.log10(rough));
    const scaled = rough / power;
    return (scaled <= 1 ? 1 : scaled <= 2 ? 2 : scaled <= 5 ? 5 : 10) * power;
  };
  const ticks = (minimum, maximum) => {
    const step = tickStep(maximum - minimum);
    const first = Math.ceil(minimum / step) * step;
    const result = [];
    for (let value = first; value <= maximum + step * 1e-8; value += step) {
      result.push(Number(value.toPrecision(12)));
    }
    return result;
  };
  const addLabel = (group, label, x, y, color, anchor = "start") => {
    if (!label) return;
    group.append(
      element(
        "text",
        { x, y, fill: color, "font-size": 15, "font-weight": 700, "text-anchor": anchor },
        label,
      ),
    );
  };

  function drawGrid(root) {
    const grid = element("g", { class: "grid", "aria-hidden": "true" });
    for (const x of ticks(spec.viewport.x_min, spec.viewport.x_max)) {
      const px = xPixel(x);
      grid.append(element("line", { x1: px, y1: plot.top, x2: px, y2: plot.height - plot.bottom }));
      grid.append(
        element(
          "text",
          { x: px, y: plot.height - plot.bottom + 24, "text-anchor": "middle" },
          String(x),
        ),
      );
    }
    for (const y of ticks(spec.viewport.y_min, spec.viewport.y_max)) {
      const py = yPixel(y);
      grid.append(element("line", { x1: plot.left, y1: py, x2: plot.width - plot.right, y2: py }));
      grid.append(
        element("text", { x: plot.left - 12, y: py + 5, "text-anchor": "end" }, String(y)),
      );
    }
    root.append(grid);
    if (spec.viewport.y_min <= 0 && spec.viewport.y_max >= 0) {
      root.append(
        element("line", {
          class: "axis",
          x1: plot.left,
          y1: yPixel(0),
          x2: plot.width - plot.right,
          y2: yPixel(0),
        }),
      );
    }
    if (spec.viewport.x_min <= 0 && spec.viewport.x_max >= 0) {
      root.append(
        element("line", {
          class: "axis",
          x1: xPixel(0),
          y1: plot.top,
          x2: xPixel(0),
          y2: plot.height - plot.bottom,
        }),
      );
    }
  }

  function resolvedObject(object) {
    const resolved = { id: object.id, type: object.type };
    for (const key of ["x", "y", "x1", "y1", "x2", "y2", "dx", "dy", "cx", "cy", "r"]) {
      if (key in object) resolved[key] = scalar(object[key]);
    }
    if (object.points) {
      resolved.points = object.points.map((point) => ({ x: scalar(point.x), y: scalar(point.y) }));
    }
    return resolved;
  }

  function drawObject(root, object) {
    const value = resolvedObject(object);
    const group = element("g", { "data-object-id": object.id, role: "group", "aria-label": object.label });
    if (object.type === "point") {
      const x = xPixel(value.x);
      const y = yPixel(value.y);
      group.append(element("circle", { cx: x, cy: y, r: 7, fill: object.color }));
      addLabel(group, object.label, x + 12, y - 12, object.color);
    } else if (object.type === "segment" || object.type === "vector") {
      const x1 = xPixel(value.x ?? value.x1);
      const y1 = yPixel(value.y ?? value.y1);
      const x2 = xPixel(object.type === "vector" ? value.x + value.dx : value.x2);
      const y2 = yPixel(object.type === "vector" ? value.y + value.dy : value.y2);
      group.append(
        element("line", {
          x1,
          y1,
          x2,
          y2,
          stroke: object.color,
          "stroke-width": 4,
          "stroke-linecap": "round",
          ...(object.type === "vector" ? { "marker-end": "url(#geometry-arrow)" } : {}),
        }),
      );
      addLabel(group, object.label, (x1 + x2) / 2, (y1 + y2) / 2 - 14, object.color, "middle");
    } else if (object.type === "circle") {
      const x = xPixel(value.cx);
      const y = yPixel(value.cy);
      const radius = radiusPixel(value.r);
      group.append(
        element("circle", {
          cx: x,
          cy: y,
          r: radius,
          fill: "none",
          stroke: object.color,
          "stroke-width": 4,
        }),
      );
      addLabel(group, object.label, x + radius + 10, y, object.color);
    } else if (object.type === "polyline" || object.type === "polygon") {
      const points = value.points.map((point) => `${xPixel(point.x)},${yPixel(point.y)}`).join(" ");
      group.append(
        element(object.type, {
          points,
          fill: object.type === "polygon" ? `${object.color}22` : "none",
          stroke: object.color,
          "stroke-width": 4,
          "stroke-linejoin": "round",
          "stroke-linecap": "round",
        }),
      );
      const last = value.points[value.points.length - 1];
      addLabel(group, object.label, xPixel(last.x) - 6, yPixel(last.y) - 14, object.color, "end");
    }
    root.append(group);
    return value;
  }

  function render() {
    svg.replaceChildren();
    const defs = element("defs");
    const marker = element("marker", {
      id: "geometry-arrow",
      viewBox: "0 0 10 10",
      refX: 9,
      refY: 5,
      markerWidth: 8,
      markerHeight: 8,
      orient: "auto-start-reverse",
    });
    marker.append(element("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "#FF6B8A" }));
    defs.append(marker);
    svg.append(defs);
    drawGrid(svg);
    const resolved = spec.objects.map((object) => drawObject(svg, object));
    svg.dataset.state = JSON.stringify({ parameters: values, objects: resolved });
    for (const parameter of spec.parameters) {
      document.querySelector(`[data-value-for="${parameter.id}"]`).textContent = String(values[parameter.id]);
    }
    return resolved;
  }

  for (const parameter of spec.parameters) {
    const wrapper = document.createElement("label");
    wrapper.className = "control";
    const heading = document.createElement("span");
    heading.className = "control-heading";
    const name = document.createElement("strong");
    name.textContent = parameter.label;
    const value = document.createElement("output");
    value.dataset.valueFor = parameter.id;
    value.textContent = String(parameter.value);
    heading.append(name, value);
    const input = document.createElement("input");
    input.type = "range";
    input.min = String(parameter.minimum);
    input.max = String(parameter.maximum);
    input.step = String(parameter.step);
    input.value = String(parameter.value);
    input.dataset.parameterId = parameter.id;
    input.setAttribute("aria-label", parameter.label);
    input.addEventListener("input", () => {
      values[parameter.id] = Number(input.value);
      render();
    });
    wrapper.append(heading, input);
    controls.append(wrapper);
  }

  render();
  window.geometryStudio = {
    snapshot: () => svg.dataset.state,
    setParameter: (id, value) => {
      const input = document.querySelector(`[data-parameter-id="${id}"]`);
      if (!input) throw new Error(`unknown parameter ${id}`);
      input.value = String(value);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    },
    restore: () => {
      for (const [id, value] of Object.entries(baseline)) {
        const input = document.querySelector(`[data-parameter-id="${id}"]`);
        input.value = String(value);
        values[id] = value;
      }
      render();
    },
  };
})();
