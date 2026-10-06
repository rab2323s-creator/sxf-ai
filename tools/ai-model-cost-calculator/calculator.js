(() => {
  const root = document.querySelector(".cost-calculator-page");
  if (!root) return;

  const modelSelect = document.getElementById("costModel");
  const compareSelect = document.getElementById("compareModel");
  const billingDate = document.getElementById("billingDate");
  const inputTokens = document.getElementById("inputTokens");
  const cachedTokens = document.getElementById("cachedTokens");
  const outputTokens = document.getElementById("outputTokens");
  const requestsPerDay = document.getElementById("requestsPerDay");
  const requestsPerMonth = document.getElementById("requestsPerMonth");
  const dailyVolumeField = document.getElementById("dailyVolumeField");
  const monthlyVolumeField = document.getElementById("monthlyVolumeField");
  const volumeDaily = document.getElementById("volumeDaily");
  const volumeMonthly = document.getElementById("volumeMonthly");
  const tokenPresets = [...document.querySelectorAll("[data-token-preset]")];
  const workloadPresets = [...document.querySelectorAll("[data-workload-preset]")];
  const workloadAssumption = document.getElementById("workloadAssumption");

  const statusNode = document.getElementById("catalogStatus");
  const resultModelName = document.getElementById("resultModelName");
  const officialPricingLink = document.getElementById("officialPricingLink");
  const perRequestNode = document.getElementById("costPerRequest");
  const perDayNode = document.getElementById("costPerDay");
  const perMonthNode = document.getElementById("costPerMonth");
  const perThousandNode = document.getElementById("costPerThousand");
  const dailyRequestsNode = document.getElementById("dailyRequests");
  const requestShapeNode = document.getElementById("requestShape");
  const inputCostNode = document.getElementById("inputCost");
  const cachedCostNode = document.getElementById("cachedCost");
  const outputCostNode = document.getElementById("outputCost");
  const rateProfileNode = document.getElementById("rateProfile");
  const warningNode = document.getElementById("calculatorWarning");

  const comparisonPanel = document.getElementById("comparisonPanel");
  const comparisonPrimaryProvider = document.getElementById("comparisonPrimaryProvider");
  const comparisonPrimaryName = document.getElementById("comparisonPrimaryName");
  const comparisonPrimaryCost = document.getElementById("comparisonPrimaryCost");
  const comparisonSecondaryProvider = document.getElementById("comparisonSecondaryProvider");
  const comparisonSecondaryName = document.getElementById("comparisonSecondaryName");
  const comparisonSecondaryCost = document.getElementById("comparisonSecondaryCost");
  const comparisonDeltaLabel = document.getElementById("comparisonDeltaLabel");
  const comparisonDelta = document.getElementById("comparisonDelta");
  const comparisonMonthlyDelta = document.getElementById("comparisonMonthlyDelta");

  const compareAllToggle = document.getElementById("compareAllToggle");
  const allModelsPanel = document.getElementById("allModelsPanel");
  const allModelsRows = document.getElementById("allModelsRows");
  const allModelsVolumeHeading = document.getElementById("allModelsVolumeHeading");
  const lowestCostModel = document.getElementById("lowestCostModel");
  const lowestCostValue = document.getElementById("lowestCostValue");

  const modelCountNode = document.getElementById("modelCount");
  const providerCountNode = document.getElementById("providerCount");
  const verifiedDateNode = document.getElementById("verifiedDate");

  if (!modelSelect || !billingDate || !perRequestNode) return;

  let catalog = null;
  let byId = new Map();
  let volumeMode = "daily";

  const clampNumber = (value, max) => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed <= 0) return 0;
    return Math.min(Math.floor(parsed), max);
  };

  const tokenValue = input => clampNumber(input?.value, 10_000_000_000);
  const requestValue = (input, max = 30_000_000_000) => clampNumber(input?.value, max);

  const money = value => {
    if (!Number.isFinite(value)) return "—";
    const abs = Math.abs(value);
    let digits = 2;
    if (abs < 1) digits = 4;
    if (abs < 0.01) digits = 6;
    return "$" + value.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: digits});
  };

  const rateMoney = value => {
    if (!Number.isFinite(Number(value))) return "—";
    const n = Number(value);
    return "$" + n.toLocaleString(undefined, {minimumFractionDigits: n >= 1 ? 2 : 0, maximumFractionDigits: 4});
  };

  const compactNumber = value => Number(value).toLocaleString(undefined, {maximumFractionDigits: 0});

  const isTokenCalculatorModel = model =>
    model?.pricing_basis?.meter === "tokens" &&
    model?.pricing_status === "official-paid" &&
    model?.calculator_eligible === true;

  const pricingQuantity = model => Number(model?.pricing_basis?.quantity || 1_000_000);
  const pricingDisplayUnit = model => model?.pricing_basis?.display_unit || "per 1 million tokens";

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

  const estimate = (model, date, input, cached, output) => {
    const effective = effectiveRates(model, date, input + cached);
    if (!effective) return null;
    const {rates, long, longRule} = effective;
    if (!isTokenCalculatorModel(model)) return null;
    const quantity = pricingQuantity(model);
    const inputRate = Number(rates.input || 0);
    const cachedRate = Number(rates.cached_input ?? rates.input ?? 0);
    const outputRate = Number(rates.output || 0);
    const inputCost = input / quantity * inputRate;
    const cachedCost = cached / quantity * cachedRate;
    const outputCost = output / quantity * outputRate;
    return {rates, long, longRule, inputCost, cachedCost, outputCost, total: inputCost + cachedCost + outputCost};
  };

  const appendModelGroups = (select, includeEmpty = false) => {
    select.replaceChildren();
    if (includeEmpty) {
      const empty = document.createElement("option");
      empty.value = "";
      empty.textContent = "No comparison";
      select.appendChild(empty);
    }
    const groups = new Map();
    for (const model of catalog.models || []) {
      if (!isTokenCalculatorModel(model)) continue;
      if (!groups.has(model.provider)) groups.set(model.provider, []);
      groups.get(model.provider).push(model);
    }
    for (const [provider, models] of groups) {
      const group = document.createElement("optgroup");
      group.label = provider;
      for (const model of models) {
        const option = document.createElement("option");
        option.value = model.model_id;
        option.textContent = model.model;
        group.appendChild(option);
      }
      select.appendChild(group);
    }
  };

  const syncCompareOptions = () => {
    const selected = modelSelect.value;
    [...compareSelect.options].forEach(option => {
      option.disabled = Boolean(option.value && option.value === selected);
    });
    if (compareSelect.value === selected) compareSelect.value = "";
  };

  const sourceForModel = model => {
    const sources = model?.official_sources || [];
    return sources.find(url => /pricing/i.test(url)) || sources[0] || "/models/pricing/";
  };

  const warningsFor = (model, estimateResult, input, cached, output) => {
    const warnings = [];
    const totalInput = input + cached;
    if (estimateResult?.long) {
      warnings.push("Long-context pricing is active because total input exceeds " + Number(estimateResult.longRule.threshold_input_tokens).toLocaleString() + " tokens. The stored multiplier applies to the request.");
    }
    if (totalInput > Number(model.context_window)) {
      warnings.push("Total input exceeds the model's published context window of " + Number(model.context_window).toLocaleString() + " tokens.");
    }
    if (output > Number(model.max_output)) {
      warnings.push("Output exceeds the model's published maximum output of " + Number(model.max_output).toLocaleString() + " tokens.");
    }
    return warnings;
  };

  const volume = () => {
    if (volumeMode === "monthly") {
      const monthly = requestValue(requestsPerMonth);
      return {monthly, daily: monthly / 30};
    }
    const daily = requestValue(requestsPerDay, 1_000_000_000);
    return {daily, monthly: daily * 30};
  };

  const setVolumeMode = (mode, preserveTotal = true) => {
    if (!["daily", "monthly"].includes(mode) || mode === volumeMode) return;
    const previous = volume();
    volumeMode = mode;

    if (preserveTotal) {
      if (mode === "monthly") {
        requestsPerMonth.value = String(Math.round(previous.monthly));
      } else {
        requestsPerDay.value = String(Math.round(previous.monthly / 30));
      }
    }

    dailyVolumeField.hidden = mode !== "daily";
    monthlyVolumeField.hidden = mode !== "monthly";
    volumeDaily.classList.toggle("is-active", mode === "daily");
    volumeMonthly.classList.toggle("is-active", mode === "monthly");
    volumeDaily.setAttribute("aria-pressed", String(mode === "daily"));
    volumeMonthly.setAttribute("aria-pressed", String(mode === "monthly"));
    render();
  };

  const renderComparison = (primaryModel, primaryEstimate, date, input, cached, output, monthlyRequests) => {
    const secondaryId = compareSelect.value;
    if (!secondaryId) {
      comparisonPanel.hidden = true;
      return;
    }
    const secondaryModel = byId.get(secondaryId);
    const secondaryEstimate = secondaryModel ? estimate(secondaryModel, date, input, cached, output) : null;
    comparisonPanel.hidden = false;

    comparisonPrimaryProvider.textContent = primaryModel.provider || "Provider";
    comparisonPrimaryName.textContent = primaryModel.model || "Model";
    comparisonPrimaryCost.textContent = money(primaryEstimate?.total);
    comparisonSecondaryProvider.textContent = secondaryModel?.provider || "Provider";
    comparisonSecondaryName.textContent = secondaryModel?.model || "Model";
    comparisonSecondaryCost.textContent = money(secondaryEstimate?.total);

    if (!primaryEstimate || !secondaryEstimate) {
      comparisonDeltaLabel.textContent = "No comparable rate";
      comparisonDelta.textContent = "—";
      comparisonMonthlyDelta.textContent = "No Standard pricing period is stored for one of the selected models on this date.";
      return;
    }

    const difference = secondaryEstimate.total - primaryEstimate.total;
    const absolute = Math.abs(difference);
    const monthly = absolute * monthlyRequests;

    if (Math.abs(difference) < 1e-12) {
      comparisonDeltaLabel.textContent = "Same direct token cost";
      comparisonDelta.textContent = "$0";
      comparisonMonthlyDelta.textContent = "No cost difference for this workload.";
    } else if (difference > 0) {
      comparisonDeltaLabel.textContent = primaryModel.model + " costs less";
      comparisonDelta.textContent = money(absolute) + " / request";
      comparisonMonthlyDelta.textContent = money(monthly) + " difference at this monthly volume.";
    } else {
      comparisonDeltaLabel.textContent = secondaryModel.model + " costs less";
      comparisonDelta.textContent = money(absolute) + " / request";
      comparisonMonthlyDelta.textContent = money(monthly) + " difference at this monthly volume.";
    }
  };

  const renderAllModels = (date, input, cached, output, monthlyRequests) => {
    if (!catalog || !allModelsRows) return;
    const rows = (catalog.models || []).map(model => {
      const result = estimate(model, date, input, cached, output);
      const tooMuchInput = input + cached > Number(model.context_window);
      const tooMuchOutput = output > Number(model.max_output);
      const eligible = Boolean(result && !tooMuchInput && !tooMuchOutput);
      let status = "Comparable";
      if (!result) status = "No rate for date";
      else if (tooMuchInput && tooMuchOutput) status = "Input + output exceed limits";
      else if (tooMuchInput) status = "Input exceeds context";
      else if (tooMuchOutput) status = "Output exceeds max";
      else if (result.long) status = "Long-context rate";
      return {model, result, eligible, status};
    });

    rows.sort((a, b) => {
      if (a.eligible !== b.eligible) return a.eligible ? -1 : 1;
      if (!a.result && !b.result) return a.model.model.localeCompare(b.model.model);
      if (!a.result) return 1;
      if (!b.result) return -1;
      return a.result.total - b.result.total || a.model.model.localeCompare(b.model.model);
    });

    allModelsRows.replaceChildren();
    for (const row of rows) {
      const tr = document.createElement("tr");
      if (!row.eligible) tr.classList.add("is-ineligible");
      if (row.model.model_id === modelSelect.value) tr.classList.add("is-selected");

      const modelCell = document.createElement("th");
      modelCell.scope = "row";
      const link = document.createElement("a");
      link.href = row.model.sxf_url || "/models/";
      link.textContent = row.model.model;
      modelCell.appendChild(link);

      const providerCell = document.createElement("td");
      providerCell.textContent = row.model.provider;

      const perRequestCell = document.createElement("td");
      perRequestCell.className = "all-model-price";
      perRequestCell.textContent = row.result ? money(row.result.total) : "—";

      const monthlyCell = document.createElement("td");
      monthlyCell.className = "all-model-price";
      monthlyCell.textContent = row.result ? money(row.result.total * monthlyRequests) : "—";

      const statusCell = document.createElement("td");
      statusCell.className = "all-model-status";
      statusCell.textContent = row.status;

      tr.append(modelCell, providerCell, perRequestCell, monthlyCell, statusCell);
      allModelsRows.appendChild(tr);
    }

    const cheapest = rows.find(row => row.eligible);
    if (cheapest) {
      lowestCostModel.textContent = cheapest.model.model;
      lowestCostValue.textContent = money(cheapest.result.total) + " / request · " + money(cheapest.result.total * monthlyRequests) + " at this monthly volume";
    } else {
      lowestCostModel.textContent = "No comparable model";
      lowestCostValue.textContent = "This workload exceeds the stored limits or has no valid Standard price for the selected date.";
    }
    allModelsVolumeHeading.textContent = volumeMode === "monthly" ? "Monthly cost" : "30-day cost";
  };

  const render = () => {
    if (!catalog) return;
    syncCompareOptions();
    const model = byId.get(modelSelect.value);
    if (!model) return;

    const input = tokenValue(inputTokens);
    const cached = tokenValue(cachedTokens);
    const output = tokenValue(outputTokens);
    const usage = volume();
    const date = billingDate.value || catalog.source_verified;
    const result = estimate(model, date, input, cached, output);

    resultModelName.textContent = model.model;
    officialPricingLink.href = sourceForModel(model);
    officialPricingLink.target = "_blank";
    officialPricingLink.rel = "noopener noreferrer";
    requestShapeNode.textContent = compactNumber(input + cached) + " input · " + compactNumber(output) + " output tokens";
    dailyRequestsNode.textContent = volumeMode === "monthly"
      ? compactNumber(usage.monthly) + " requests / month"
      : compactNumber(usage.daily) + " requests / day";

    if (!result) {
      perRequestNode.textContent = "—";
      perDayNode.textContent = "—";
      perMonthNode.textContent = "—";
      perThousandNode.textContent = "—";
      inputCostNode.textContent = "—";
      cachedCostNode.textContent = "—";
      outputCostNode.textContent = "—";
      rateProfileNode.textContent = "No Standard pricing period is stored for this model on the selected date.";
      warningNode.hidden = true;
      renderComparison(model, null, date, input, cached, output, usage.monthly);
      renderAllModels(date, input, cached, output, usage.monthly);
      return;
    }

    perRequestNode.textContent = money(result.total);
    perDayNode.textContent = money(result.total * usage.daily);
    perMonthNode.textContent = money(result.total * usage.monthly);
    perThousandNode.textContent = money(result.total * 1000);
    inputCostNode.textContent = money(result.inputCost);
    cachedCostNode.textContent = money(result.cachedCost);
    outputCostNode.textContent = money(result.outputCost);

    const periodLabel = result.rates.end ? result.rates.start + " → " + result.rates.end : result.rates.start + " onward";
    rateProfileNode.textContent = [
      result.long ? "Long-context Standard" : "Standard API",
      periodLabel,
      "Input " + rateMoney(result.rates.input) + " " + pricingDisplayUnit(model),
      "Cached " + rateMoney(result.rates.cached_input ?? result.rates.input) + " " + pricingDisplayUnit(model),
      "Output " + rateMoney(result.rates.output) + " " + pricingDisplayUnit(model)
    ].join(" · ");

    const warnings = warningsFor(model, result, input, cached, output);
    warningNode.hidden = warnings.length === 0;
    warningNode.textContent = warnings.join(" ");
    renderComparison(model, result, date, input, cached, output, usage.monthly);
    renderAllModels(date, input, cached, output, usage.monthly);
  };

  const clearPresetState = () => {
    tokenPresets.forEach(button => button.classList.remove("is-active"));
    workloadPresets.forEach(button => button.classList.remove("is-active"));
    if (workloadAssumption) {
      workloadAssumption.hidden = true;
      workloadAssumption.textContent = "";
    }
  };

  tokenPresets.forEach(button => button.addEventListener("click", () => {
    inputTokens.value = button.dataset.input || "0";
    cachedTokens.value = button.dataset.cached || "0";
    outputTokens.value = button.dataset.output || "0";
    clearPresetState();
    button.classList.add("is-active");
    render();
  }));

  workloadPresets.forEach(button => button.addEventListener("click", () => {
    inputTokens.value = button.dataset.input || "0";
    cachedTokens.value = button.dataset.cached || "0";
    outputTokens.value = button.dataset.output || "0";
    requestsPerMonth.value = button.dataset.monthly || "0";
    if (volumeMode !== "monthly") {
      volumeMode = "monthly";
      dailyVolumeField.hidden = true;
      monthlyVolumeField.hidden = false;
      volumeDaily.classList.remove("is-active");
      volumeMonthly.classList.add("is-active");
      volumeDaily.setAttribute("aria-pressed", "false");
      volumeMonthly.setAttribute("aria-pressed", "true");
    }
    clearPresetState();
    button.classList.add("is-active");
    workloadAssumption.hidden = false;
    workloadAssumption.textContent =
      button.textContent.trim() + ": " +
      compactNumber(Number(button.dataset.input || 0)) + " uncached input · " +
      compactNumber(Number(button.dataset.cached || 0)) + " cached input · " +
      compactNumber(Number(button.dataset.output || 0)) + " output · " +
      compactNumber(Number(button.dataset.monthly || 0)) + " requests / month.";
    render();
  }));

  [inputTokens, cachedTokens, outputTokens].forEach(node => {
    node?.addEventListener("input", () => {
      clearPresetState();
      render();
    });
  });

  [modelSelect, compareSelect, billingDate].forEach(node => {
    node?.addEventListener("input", render);
    node?.addEventListener("change", render);
  });

  requestsPerDay?.addEventListener("input", render);
  requestsPerMonth?.addEventListener("input", render);

  volumeDaily?.addEventListener("click", () => setVolumeMode("daily"));
  volumeMonthly?.addEventListener("click", () => setVolumeMode("monthly"));

  compareAllToggle?.addEventListener("click", () => {
    const willOpen = allModelsPanel.hidden;
    allModelsPanel.hidden = !willOpen;
    compareAllToggle.setAttribute("aria-expanded", String(willOpen));
    compareAllToggle.querySelector("span").textContent = willOpen ? "↑" : "↓";
    if (willOpen) render();
  });

  fetch("/data/model-pricing.json", {cache: "no-cache"})
    .then(response => {
      if (!response.ok) throw new Error("Could not load model pricing catalog");
      return response.json();
    })
    .then(data => {
      if (!Array.isArray(data.models) || data.models.length === 0) throw new Error("Pricing catalog is empty");
      catalog = data;
      byId = new Map(data.models.map(model => [model.model_id, model]));
      appendModelGroups(modelSelect);
      appendModelGroups(compareSelect, true);
      if (byId.has("gpt-6-sol")) modelSelect.value = "gpt-6-sol";
      billingDate.value = data.source_verified || new Date().toISOString().slice(0, 10);
      modelCountNode.textContent = String(data.models.length);
      providerCountNode.textContent = String(new Set(data.models.map(model => model.provider)).size);
      verifiedDateNode.textContent = data.source_verified || "Current";
      statusNode.textContent = "Catalog verified " + (data.source_verified || "");
      statusNode.classList.add("is-ready");
      render();
    })
    .catch(() => {
      statusNode.textContent = "Pricing unavailable";
      statusNode.classList.add("is-error");
      rateProfileNode.textContent = "The pricing dataset could not be loaded. Try the Model Pricing database for the current published rates.";
      warningNode.hidden = false;
      warningNode.textContent = "Calculator unavailable because the canonical pricing dataset did not load.";
      if (compareAllToggle) compareAllToggle.disabled = true;
    });
})();