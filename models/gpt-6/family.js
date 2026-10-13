/* Self-contained, dependency-free GPT-6 Standard API pricing estimator. */
(() => {
  "use strict";
  const root = document.querySelector("[data-gpt6-calc]");
  if (!root) return;
  let rates;
  try { rates = JSON.parse(root.getAttribute("data-rates")); } catch (_) { return; }
  const form = root.querySelector("form");
  const status = root.querySelector("[data-gpt6-tier]");
  if (!form || !status) return;
  const names = ["input","cached","writes","output"];
  const output = value => value === 0 ? "$0" :
    "$" + value.toFixed(value < 0.01 ? 5 : 4).replace(/0+$/, "").replace(/\.$/, "");
  const update = () => {
    const values = {};
    let invalid = false;
    for (const name of names) {
      const field = form.elements.namedItem(name);
      if (!field) return;
      const n = Number(field.value);
      if (field.value === "" || !Number.isInteger(n) || n < 0 || !field.validity.valid) invalid = true;
      values[name] = n;
    }
    const prompt = values.input + values.cached + values.writes;
    if (prompt > 1050000) invalid = true;
    status.textContent = invalid
      ? "Enter valid token counts within the published model limits."
      : (prompt > 272000 ? "Long-context Standard rates · entire request" : "Short-context Standard rates") +
        " · " + prompt.toLocaleString("en-US") + " prompt tokens";
    for (const key of ["astra","sol","luna"]) {
      const cell = root.querySelector('[data-cost="' + key + '"]');
      if (!cell) continue;
      if (invalid) { cell.textContent = "—"; continue; }
      const r = rates[key], long = prompt > 272000;
      const total = (values.input * r.input * (long ? 2 : 1) +
        values.cached * r.cached * (long ? 2 : 1) +
        values.writes * r.writes * (long ? 2 : 1) +
        values.output * r.output * (long ? 1.5 : 1)) / 1000000;
      cell.textContent = output(total);
    }
  };
  form.addEventListener("input", update);
  form.addEventListener("submit", event => event.preventDefault());
  update();
})();
