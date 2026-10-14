/* Local calculator only: no network calls, storage or tracking. */
(() => {
  "use strict";
  const tokens = document.getElementById("ge001-tokens");
  const tier = document.getElementById("ge001-tier");
  const result = document.getElementById("ge001-cost-result");
  const form = document.getElementById("ge001-cost-tool");
  if (!tokens || !tier || !result || !form) return;
  form.addEventListener("submit", (event) => event.preventDefault());
  function update() {
    const quantity = Number(tokens.value);
    const rate = Number(tier.value);
    if (!Number.isFinite(quantity) || !Number.isInteger(quantity) ||
        quantity < 1 || quantity > 1000000000000 ||
        ![0.15, 0.075].includes(rate)) {
      result.textContent = "Enter valid input";
      return;
    }
    const estimate = quantity / 1000000 * rate;
    result.textContent = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: estimate < 0.01 ? 6 : 4,
      maximumFractionDigits: 6
    }).format(estimate);
  }
  tokens.addEventListener("input", update);
  tier.addEventListener("change", update);
  update();
})();
