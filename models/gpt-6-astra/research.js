"use strict";
/* SXF deterministic pricing model: no API access, usage transmission or hidden fees. */
(() => {
  const lab = document.querySelector("#astra-calculator");
  if (!lab) return;
  const inputs = Object.fromEntries(
    ["input", "cached", "write", "output"].map(key => [
      key, lab.querySelector('[data-tokens="' + key + '"]')
    ])
  );
  const cacheDuration = lab.querySelector("[data-cache-ttl]");
  const result = key => lab.querySelector('[data-result="' + key + '"]');
  const rate = key => Number(lab.dataset[key]);
  const costs = (model, amounts, long, ttl) => {
    const writeRate = rate(model + (ttl === "12h" ? "Write12h" : "Write"));
    const inputTotal =
      amounts.input * rate(model + "Input") +
      amounts.cached * rate(model + "Cached") +
      amounts.write * writeRate;
    const outputTotal = amounts.output * rate(model + "Output");
    return (inputTotal * (long ? 2 : 1) +
      outputTotal * (long ? 1.5 : 1)) / 1_000_000;
  };
  function refresh() {
    const amounts = Object.fromEntries(Object.entries(inputs).map(([key, el]) => [
      key, el.value.trim() === "" ? NaN : Number(el.value)
    ]));
    const ttl = cacheDuration.value;
    const total = amounts.input + amounts.cached + amounts.write;
    const invalid =
      Object.values(amounts).some(value =>
        !Number.isFinite(value) || value < 0 || !Number.isInteger(value)
      ) ||
      total > 1050000 || amounts.output > 128000 ||
      !["30m", "12h"].includes(ttl);
    if (invalid) {
      result("tier").textContent = "Invalid token counts";
      result("astra").textContent = "—";
      result("sol").textContent = "—";
      result("warning").textContent =
        "Use non-negative whole tokens; total input ≤1,050,000 and output ≤128,000.";
      return;
    }
    const long = total > 272000;
    result("tier").textContent = long ? "Long >272K" : "Short ≤272K";
    result("astra").textContent = "$" + costs("astra", amounts, long, ttl).toFixed(5);
    result("sol").textContent = "$" + costs("sol", amounts, long, ttl).toFixed(5);
    result("warning").textContent =
      "Estimated Standard API list prices (" +
      (ttl === "12h" ? "12-hour" : "30-minute") +
      " cache writes). Actual cache hits, tools, processing modes and usage can change bills.";
  }
  [...Object.values(inputs), cacheDuration].forEach(el =>
    el.addEventListener("input", refresh)
  );
  refresh();
})();
