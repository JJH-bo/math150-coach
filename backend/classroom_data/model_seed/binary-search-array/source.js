export function createSearchState(values, target) {
  return { values: [...values], target, low: 0, high: values.length - 1, mid: null, status: "ready", steps: 0 };
}

export function advanceSearch(input) {
  const state = { ...input, values: [...input.values] };
  if (state.status === "found" || state.low > state.high) return state;
  state.mid = Math.floor((state.low + state.high) / 2);
  state.steps += 1;
  const value = state.values[state.mid];
  if (value === state.target) state.status = "found";
  else if (value < state.target) { state.low = state.mid + 1; state.status = "searching"; }
  else { state.high = state.mid - 1; state.status = "searching"; }
  return state;
}

export function createTeachingModel(context) {
  const values = [2, 5, 8, 12, 16, 23, 38];
  let search = createSearchState(values, 23);
  let canvas;
  let ctx;
  function draw() {
    if (!ctx) return;
    const width = canvas.width = Math.max(680, context.root.clientWidth || 820);
    const height = canvas.height = Math.max(380, context.root.clientHeight || 480);
    ctx.fillStyle = "#071019"; ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = "#edf8fb"; ctx.font = "600 24px system-ui";
    ctx.fillText(`二分查找 target = ${search.target}`, 48, 62);
    const gap = 10, cell = Math.min(86, (width - 100 - gap * 6) / 7), y = height * 0.42;
    search.values.forEach((value, index) => {
      const x = 48 + index * (cell + gap);
      const active = index >= search.low && index <= search.high;
      ctx.fillStyle = index === search.mid ? "#f5bd62" : active ? "#12384a" : "#101a21";
      ctx.strokeStyle = index === search.mid ? "#fff0b2" : active ? "#5fdbff" : "#33434b";
      ctx.lineWidth = 2; ctx.fillRect(x, y, cell, cell); ctx.strokeRect(x, y, cell, cell);
      ctx.fillStyle = index === search.mid ? "#071019" : "#eef8fb"; ctx.font = "700 22px system-ui";
      ctx.textAlign = "center"; ctx.fillText(String(value), x + cell / 2, y + cell / 2 + 8);
      ctx.fillStyle = "#8fa8b2"; ctx.font = "13px system-ui"; ctx.fillText(String(index), x + cell / 2, y + cell + 24);
    });
    ctx.textAlign = "left"; ctx.fillStyle = "#a9c0c8"; ctx.font = "16px system-ui";
    ctx.fillText(`low=${search.low}   high=${search.high}   mid=${search.mid ?? "—"}   ${search.status}`, 48, height - 54);
  }
  return {
    mount(initial) { search = createSearchState(values, Number(initial.parameters?.target ?? 23)); canvas = document.createElement("canvas"); context.root.replaceChildren(canvas); ctx = canvas.getContext("2d"); draw(); },
    update(next) { if (next.parameters?.target !== undefined) search = createSearchState(values, Number(next.parameters.target)); draw(); },
    perform(action) { if (action === "step") search = advanceSearch(search); if (action === "reset-search") search = createSearchState(values, search.target); draw(); },
    pause() {}, resume() { draw(); }, reset() { search = createSearchState(values, search.target); draw(); },
    snapshot() { return { ...search, values: [...search.values] }; },
    dispose() { context.root.replaceChildren(); canvas = null; ctx = null; },
  };
}
