/* SXF Gemini Flash calculator. No network access or third-party dependencies. */
(() => {
  "use strict";
  const root = document.querySelector("[data-gf-cost-lab]");
  if (!root) return;
  const $ = selector => root.querySelector(selector);
  const period = $("[data-gf-period]"), requests = $("[data-gf-requests]");
  const input = $("[data-gf-input]"), output37 = $("[data-gf-out37]"), output38 = $("[data-gf-out38]");
  const result37 = $("[data-gf-total37]"), result38 = $("[data-gf-total38]"), diff = $("[data-gf-diff]");
  function amount(value, max) {
    const number = Number(value);
    return Number.isFinite(number) ? Math.max(0, Math.min(max, number)) : 0;
  }
  const format = value => (value < 0 ? "-$" : "$") + Math.abs(value).toFixed(4);
  function update() {
    const [inputRate, outputRate] = period.value === "2027" ? [1.5, 7.5] : [.75, 3.75];
    const count = amount(requests.value, 1e8);
    const base = amount(input.value, 1e8) * inputRate;
    const cost37 = (base + amount(output37.value, 1e8) * outputRate) * count / 1e6;
    const cost38 = (base + amount(output38.value, 1e8) * outputRate) * count / 1e6;
    result37.textContent = format(cost37);
    result38.textContent = format(cost38);
    diff.textContent = format(cost38 - cost37);
  }
  [period, requests, input, output37, output38].forEach(field => {
    field.addEventListener("input", update);
    field.addEventListener("change", update);
  });
  update();
})();
