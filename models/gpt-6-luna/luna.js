/* GPT-6 Luna Standard API cost estimator. Source rates provided by site generator. */
(() => {
  "use strict";
  const root = document.querySelector("[data-luna-calculator]");
  if (!root) return;
  let prices;
  try { prices = JSON.parse(root.getAttribute("data-rates")); } catch (_) { return; }
  const form = root.querySelector("form");
  const status = root.querySelector("[data-luna-status]");
  if (!form || !status) return;
  const fields = ["uncached","cached","write","output"];
  const format = amount => "$" + amount.toFixed(amount < .01 ? 6 : 4).replace(/0+$/, "").replace(/\.$/, "");
  const update = () => {
    let invalid = false;
    const values = {};
    for (const field of fields) {
      const input = form.elements.namedItem(field);
      if (!input) return;
      const n = Number(input.value);
      if (input.value === "" || !Number.isInteger(n) || n < 0 || !input.validity.valid) invalid = true;
      values[field] = n;
    }
    const prompt = values.uncached + values.cached + values.write;
    if (prompt > 1050000) invalid = true;
    const long = prompt > 272000;
    status.textContent = invalid ? "Input exceeds the model limits or includes an invalid token count." :
      (long ? "Long-context Standard rate: entire request" : "Short-context Standard rate") +
      " · " + prompt.toLocaleString("en-US") + " input tokens";
    for (const name of ["luna","sol","astra"]) {
      const cell = root.querySelector('[data-luna-cost="' + name + '"]');
      if (!cell) continue;
      if (invalid) { cell.textContent = "—"; continue; }
      const r = prices[name];
      const amount = (values.uncached * r.input * (long ? 2 : 1) +
        values.cached * r.cached * (long ? 2 : 1) +
        values.write * r.write * (long ? 2 : 1) +
        values.output * r.output * (long ? 1.5 : 1)) / 1000000;
      cell.textContent = format(amount);
    }
  };
  form.addEventListener("input", update);
  form.addEventListener("submit", e => e.preventDefault());
  update();
})();
