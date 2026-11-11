/* SXF Gemini cost lab: no network calls, no dependencies, transparent rate math. */
(() => {
  "use strict";
  const root = document.querySelector("[data-gemini-cost-lab]");
  if (!root) return;
  const model = root.querySelector("[data-gemini-model]");
  const period = root.querySelector("[data-gemini-period]");
  const input = root.querySelector("[data-gemini-input]");
  const output = root.querySelector("[data-gemini-output]");
  const total = root.querySelector("[data-gemini-total]");
  const breakdown = root.querySelector("[data-gemini-breakdown]");
  const rates = {
    "gemini-3.8-flash": { earlier: [0.75, 3.75], later: [1.50, 7.50], switchDate: "2027-01" },
    "gemini-4-argon": { earlier: [2, 10], later: [4, 20], switchDate: "2026-12" },
    "gemini-4-carbon": { earlier: [2, 10], later: [4, 20], switchDate: "2026-12" },
    "gemini-3.5-flash-lite": { earlier: [0.30, 2.50], later: [0.30, 2.50], switchDate: "9999-12" }
  };
  function count(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.max(0, Math.min(1e9, parsed)) : 0;
  }
  const dollar = value => "$" + value.toFixed(4);
  function refresh() {
    const rate = rates[model.value];
    if (!rate) return;
    const [inRate, outRate] = period.value >= rate.switchDate ? rate.later : rate.earlier;
    const inTokens = count(input.value);
    const outTokens = count(output.value);
    const result = (inTokens * inRate + outTokens * outRate) / 1000000;
    total.textContent = dollar(result);
    breakdown.textContent =
      inTokens.toLocaleString("en-US") + " input × $" + inRate.toFixed(2) +
      "/M + " + outTokens.toLocaleString("en-US") + " output × $" +
      outRate.toFixed(2) + "/M";
  }
  for (const field of [model, period, input, output]) {
    field.addEventListener("input", refresh);
    field.addEventListener("change", refresh);
  }
  refresh();
})();
