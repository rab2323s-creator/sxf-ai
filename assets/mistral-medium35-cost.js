/* SXF / AI — deterministic Mistral Medium 3.5 standard API cost model.
   No network calls. Values reflect documented USD per 1M tokens. */
(function () {
  "use strict";
  const root = document.querySelector("[data-mm35-calculator]");
  if (!root) return;

  const PRICE = Object.freeze({ input: 1.5, cached: 0.15, output: 7.5 });
  const field = (key) => root.querySelector("[data-mm35-" + key + "]");
  const inputs = ["input", "cached", "output", "requests"].map(field);
  const onceEl = field("once");
  const totalEl = field("total");
  const yearlyEl = field("yearly");
  const breakdownEl = field("breakdown");
  if (inputs.some((node) => !node) || !onceEl || !totalEl || !yearlyEl || !breakdownEl) return;

  function tokens(node) {
    const value = Number(node.value);
    return Number.isFinite(value) && value >= 0 ? Math.min(value, 1000000000) : 0;
  }
  function usd(value, small) {
    return value.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: small ? 4 : 2,
      maximumFractionDigits: small ? 6 : 2
    });
  }
  function update() {
    const [input, cached, output, requests] = inputs.map(tokens);
    // Each token class is exclusive; do not count cached input twice.
    const inputUsd = input * PRICE.input / 1000000;
    const cachedUsd = cached * PRICE.cached / 1000000;
    const outputUsd = output * PRICE.output / 1000000;
    const perRequest = inputUsd + cachedUsd + outputUsd;
    const volume = perRequest * requests;
    onceEl.textContent = usd(perRequest, true);
    totalEl.textContent = usd(volume, false);
    yearlyEl.textContent = usd(volume * 12, false);
    breakdownEl.textContent = "Uncached input " + usd(inputUsd, true) +
      " + cached input " + usd(cachedUsd, true) +
      " + output " + usd(outputUsd, true) + " per request.";
  }
  inputs.forEach((input) => input.addEventListener("input", update));
  update();
})();
