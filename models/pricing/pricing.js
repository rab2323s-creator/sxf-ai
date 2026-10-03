(() => {
  const tableRows = [...document.querySelectorAll("[data-pricing-row]")];
  const filters = [...document.querySelectorAll("[data-pricing-filter]")];
  const search = document.getElementById("pricingSearch");
  const empty = document.getElementById("pricingEmpty");
  const modelSelect = document.getElementById("pricingModel");
  const pricingDate = document.getElementById("pricingDate");
  const uncachedInput = document.getElementById("pricingInput");
  const cachedInput = document.getElementById("pricingCached");
  const outputTokens = document.getElementById("pricingOutput");
  const totalNode = document.getElementById("pricingTotal");
  const inputCostNode = document.getElementById("pricingInputCost");
  const cachedCostNode = document.getElementById("pricingCachedCost");
  const outputCostNode = document.getElementById("pricingOutputCost");
  const rateProfileNode = document.getElementById("pricingRateProfile");
  const warningNode = document.getElementById("pricingWarning");
  const presets = [...document.querySelectorAll("[data-pricing-preset]")];

  if (!modelSelect || !pricingDate || !totalNode) return;

  let activeProvider = "all";
  let catalog = null;
  let byId = new Map();

  const number = value => {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed >= 0 ? Math.floor(parsed) : 0;
  };

  const money = value => {
    const abs = Math.abs(value);
    const digits = abs >= 100 ? 2 : abs >= 1 ? 4 : 6;
    return "$" + value.toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: digits
    });
  };

  const rateMoney = value => "$" + Number(value).toLocaleString(undefined, {
    minimumFractionDigits: Number(value) >= 1 ? 2 : 0,
    maximumFractionDigits: 4
  });

  const periodForDate = (model, date) => {
    const schedule = model?.pricing?.standard || [];
    return schedule.find(period => {
      const afterStart = date >= period.start;
      const beforeEnd = !period.end || date <= period.end;
      return afterStart && beforeEnd;
    }) || null;
  };

  const effectiveRates = (model, date, totalInput) => {
    const period = periodForDate(model, date);
    if (!period) return null;

    const rates = {...period};
    const longRule = model?.pricing?.long_context;
    const long = Boolean(longRule && totalInput > Number(longRule.threshold_input_tokens));
    if (long) {
      for (const field of ["input", "cached_input", "cache_write", "output"]) {
        if (typeof rates[field] === "number" && typeof longRule.multipliers?.[field] === "number") {
          rates[field] *= longRule.multipliers[field];
        }
      }
    }
    return {rates, long, longRule};
  };

  const updateFilters = () => {
    const query = (search?.value || "").trim().toLowerCase();
    let visible = 0;
    for (const row of tableRows) {
      const providerMatch = activeProvider === "all" || row.dataset.provider === activeProvider;
      const haystack = (row.dataset.search || "").toLowerCase();
      const searchMatch = !query || haystack.includes(query);
      const show = providerMatch && searchMatch;
      row.hidden = !show;
      if (show) visible += 1;
    }
    if (empty) empty.hidden = visible !== 0;
  };

  const populateModels = models => {
    modelSelect.replaceChildren();
    const groups = new Map();
    for (const model of models) {
      if (model.pricing_status !== "official-paid" || model.calculator_eligible !== true) continue;
      if (!groups.has(model.provider)) groups.set(model.provider, []);
      groups.get(model.provider).push(model);
    }

    for (const [provider, modelsForProvider] of groups) {
      const group = document.createElement("optgroup");
      group.label = provider;
      for (const model of modelsForProvider) {
        const option = document.createElement("option");
        option.value = model.model_id;
        option.textContent = model.model;
        group.appendChild(option);
      }
      modelSelect.appendChild(group);
    }

    if (byId.has("gpt-6-sol")) modelSelect.value = "gpt-6-sol";
  };

  const updateCalculator = () => {
    if (!catalog) return;
    const model = byId.get(modelSelect.value);
    if (!model) return;
    if (model.pricing_status !== "official-paid" || model.calculator_eligible !== true) {
      totalNode.textContent = "—";
      inputCostNode.textContent = "—";
      cachedCostNode.textContent = "—";
      outputCostNode.textContent = "—";
      rateProfileNode.textContent = "This model has no provider-published Standard paid token rate eligible for the calculator.";
      warningNode.hidden = true;
      return;
    }

    const input = number(uncachedInput?.value);
    const cached = number(cachedInput?.value);
    const output = number(outputTokens?.value);
    const totalInput = input + cached;
    const date = pricingDate.value || catalog.source_verified;
    const effective = effectiveRates(model, date, totalInput);

    if (!effective) {
      totalNode.textContent = "—";
      inputCostNode.textContent = "—";
      cachedCostNode.textContent = "—";
      outputCostNode.textContent = "—";
      rateProfileNode.textContent = "No Standard pricing period is stored for this date.";
      warningNode.hidden = true;
      return;
    }

    const {rates, long, longRule} = effective;
    const inputCost = input / 1_000_000 * rates.input;
    const cachedCost = cached / 1_000_000 * rates.cached_input;
    const outputCost = output / 1_000_000 * rates.output;
    const total = inputCost + cachedCost + outputCost;

    totalNode.textContent = money(total);
    inputCostNode.textContent = money(inputCost);
    cachedCostNode.textContent = money(cachedCost);
    outputCostNode.textContent = money(outputCost);

    const periodLabel = rates.end ? rates.start + " → " + rates.end : rates.start + " onward";
    const profile = [
      long ? "Long-context Standard" : "Standard",
      periodLabel,
      "Input " + rateMoney(rates.input) + " / MTok",
      "Cached " + rateMoney(rates.cached_input) + " / MTok",
      "Output " + rateMoney(rates.output) + " / MTok"
    ];
    rateProfileNode.textContent = profile.join(" · ");

    const warnings = [];
    if (long) {
      warnings.push("Long-context pricing is active because total input exceeds " +
        Number(longRule.threshold_input_tokens).toLocaleString() +
        " tokens. The published multiplier applies to the entire request.");
    }
    if (totalInput > Number(model.context_window)) {
      warnings.push("Total input exceeds this model's published context window of " +
        Number(model.context_window).toLocaleString() + " tokens.");
    }
    if (model.max_output !== "unlimited" && output > Number(model.max_output)) {
      warnings.push("Output tokens exceed this model's published maximum output of " +
        Number(model.max_output).toLocaleString() + " tokens.");
    }

    warningNode.hidden = warnings.length === 0;
    warningNode.textContent = warnings.join(" ");
  };

  filters.forEach(button => button.addEventListener("click", () => {
    filters.forEach(item => item.classList.remove("is-active"));
    button.classList.add("is-active");
    activeProvider = button.dataset.pricingFilter || "all";
    updateFilters();
  }));

  search?.addEventListener("input", updateFilters);
  [modelSelect, pricingDate, uncachedInput, cachedInput, outputTokens].forEach(node => {
    node?.addEventListener("input", updateCalculator);
    node?.addEventListener("change", updateCalculator);
  });

  presets.forEach(button => button.addEventListener("click", () => {
    uncachedInput.value = button.dataset.input || "0";
    cachedInput.value = button.dataset.cached || "0";
    outputTokens.value = button.dataset.output || "0";
    updateCalculator();
  }));

  fetch("/data/model-pricing.json", {cache: "no-cache"})
    .then(response => {
      if (!response.ok) throw new Error("Could not load model pricing catalog");
      return response.json();
    })
    .then(data => {
      catalog = data;
      byId = new Map((data.models || []).map(model => [model.model_id, model]));
      pricingDate.value = data.source_verified || new Date().toISOString().slice(0, 10);
      populateModels(data.models || []);
      updateCalculator();
      updateFilters();
    })
    .catch(() => {
      rateProfileNode.textContent = "The pricing dataset could not be loaded.";
      warningNode.hidden = false;
      warningNode.textContent = "Calculator unavailable. The server-rendered pricing table remains available above.";
    });
})();
