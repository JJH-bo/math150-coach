function parameterControl(spec) {
  if (spec.type === "number" || spec.type === "integer") return "range";
  if (spec.type === "choice") return "select";
  if (spec.type === "boolean") return "checkbox";
  return "text";
}

export function buildModelControlDescriptors(manifest, instance) {
  const allowed = new Set(instance?.allowed_interactions || []);
  const descriptors = [];
  if (allowed.has("parameter_change")) {
    for (const spec of manifest?.parameters || []) {
      descriptors.push({
        kind: "parameter",
        id: spec.id,
        label: spec.description || spec.id,
        control: parameterControl(spec),
        value: Object.hasOwn(instance?.parameters || {}, spec.id)
          ? instance.parameters[spec.id]
          : spec.default,
        minimum: spec.minimum,
        maximum: spec.maximum,
        choices: spec.choices || [],
        spec,
      });
    }
  }
  if (allowed.has("explicit_control")) {
    for (const action of manifest?.actions || []) {
      descriptors.push({
        kind: "action",
        id: action.id,
        label: action.title || action.id,
        control: "button",
        action,
      });
    }
  }
  return descriptors;
}

export function coerceControlValue(spec, value, checked = false) {
  if (spec.type === "integer") return Number.parseInt(value, 10);
  if (spec.type === "number") return Number(value);
  if (spec.type === "boolean") return Boolean(checked);
  return value;
}

export function mountModelControls({
  root,
  manifest,
  instance,
  onParameter,
  onAction,
}) {
  root.replaceChildren();
  const descriptors = buildModelControlDescriptors(manifest, instance);
  if (!descriptors.length) {
    root.classList.add("is-hidden");
    return { dispose() {}, values: () => ({}) };
  }
  root.classList.remove("is-hidden");
  const values = Object.fromEntries(
    descriptors
      .filter((descriptor) => descriptor.kind === "parameter")
      .map((descriptor) => [descriptor.id, descriptor.value]),
  );
  const disposers = [];
  for (const descriptor of descriptors) {
    if (descriptor.kind === "action") {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "model-action-control";
      button.textContent = descriptor.label;
      const listener = () => onAction?.(descriptor.id, {});
      button.addEventListener("click", listener);
      disposers.push(() => button.removeEventListener("click", listener));
      root.append(button);
      continue;
    }
    const label = document.createElement("label");
    label.className = "model-parameter-control";
    const copy = document.createElement("span");
    copy.textContent = descriptor.label;
    let input;
    if (descriptor.control === "select") {
      input = document.createElement("select");
      for (const choice of descriptor.choices) {
        const option = document.createElement("option");
        option.value = choice;
        option.textContent = choice;
        input.append(option);
      }
      input.value = String(descriptor.value);
    } else {
      input = document.createElement("input");
      input.type = descriptor.control;
      if (descriptor.minimum !== undefined && descriptor.minimum !== null) {
        input.min = String(descriptor.minimum);
      }
      if (descriptor.maximum !== undefined && descriptor.maximum !== null) {
        input.max = String(descriptor.maximum);
      }
      if (descriptor.control === "range") {
        input.step = descriptor.spec.type === "integer" ? "1" : "any";
      }
      if (descriptor.control === "checkbox") {
        input.checked = Boolean(descriptor.value);
      } else {
        input.value = String(descriptor.value);
      }
    }
    input.dataset.parameterId = descriptor.id;
    const output = document.createElement("output");
    output.textContent = String(descriptor.value);
    const listener = () => {
      const next = coerceControlValue(
        descriptor.spec,
        input.value,
        input.checked,
      );
      values[descriptor.id] = next;
      output.textContent = String(next);
      onParameter?.(descriptor.id, next, { ...values });
    };
    input.addEventListener("input", listener);
    input.addEventListener("change", listener);
    disposers.push(() => {
      input.removeEventListener("input", listener);
      input.removeEventListener("change", listener);
    });
    label.append(copy, input, output);
    root.append(label);
  }
  return {
    values: () => ({ ...values }),
    dispose() {
      disposers.forEach((dispose) => dispose());
      root.replaceChildren();
    },
  };
}
