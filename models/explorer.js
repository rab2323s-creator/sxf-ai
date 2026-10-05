(() => {
  const root = document.querySelector("[data-model-explorer]");
  if (!root) return;

  const rows = [...root.querySelectorAll("[data-model-row]")];
  const body = document.getElementById("modelExplorerBody");
  const search = document.getElementById("modelExplorerSearch");
  const sort = document.getElementById("modelExplorerSort");
  const count = document.getElementById("modelExplorerCount");
  const empty = document.getElementById("modelExplorerEmpty");
  const providerButtons = [...root.querySelectorAll("[data-model-provider]")];
  const toolbar = root.querySelector(".model-explorer-toolbar");

  let provider = "all";
  let catalog = null;
  let modelByRow = new Map();
  let selected = new Set();

  const normalize = value => String(value || "").trim().toLowerCase();
  const numeric = (row, key) => {
    if ((key === "input" || key === "output") && row.dataset.pricingStatus !== "official-paid") {
      return Number.POSITIVE_INFINITY;
    }
    const value = Number(row.dataset[key] || 0);
    return Number.isFinite(value) ? value : Number.POSITIVE_INFINITY;
  };

  const filters = document.createElement("div");
  filters.className = "model-explorer-advanced";
  filters.innerHTML = `
    <div class="model-filter-group" aria-label="Capabilities">
      <span class="model-filter-label">Capabilities</span>
      <div class="model-capability-filters">
        <button type="button" class="model-filter-chip" data-capability="reasoning" aria-pressed="false">Reasoning</button>
        <button type="button" class="model-filter-chip" data-capability="image" aria-pressed="false">Image</button>
        <button type="button" class="model-filter-chip" data-capability="audio-video" aria-pressed="false">Audio / video</button>
      </div>
    </div>
    <label class="model-advanced-select"><span>Context</span><select id="modelContextFilter">
      <option value="0">Any context</option>
      <option value="500000">500K+</option>
      <option value="1000000">1M+</option>
      <option value="2000000">2M+</option>
    </select></label>
    <label class="model-advanced-select"><span>Access</span><select id="modelAccessFilter">
      <option value="all">Any access</option>
      <option value="official-paid">Official paid API</option>
      <option value="open-weight">Open weights</option>
      <option value="calculator">Calculator eligible</option>
    </select></label>
    <label class="model-advanced-select"><span>Verification</span><select id="modelVerificationFilter">
      <option value="all">Any verification date</option>
      <option value="14">Verified ≤14d</option>
      <option value="30">Verified ≤30d</option>
    </select></label>
    <button type="button" class="model-filter-reset" id="modelFilterReset">Reset filters</button>
  `;
  toolbar?.appendChild(filters);

  const contextFilter = filters.querySelector("#modelContextFilter");
  const accessFilter = filters.querySelector("#modelAccessFilter");
  const verificationFilter = filters.querySelector("#modelVerificationFilter");
  const resetButton = filters.querySelector("#modelFilterReset");
  const capabilityButtons = [...filters.querySelectorAll("[data-capability]")];

  const dock = document.createElement("div");
  dock.className = "model-compare-dock";
  dock.hidden = true;
  dock.setAttribute("aria-live", "polite");
  dock.innerHTML = `
    <div class="model-compare-copy">
      <span>COMPARE SELECTION</span>
      <strong id="modelCompareNames">Choose two models</strong>
    </div>
    <div class="model-compare-actions">
      <button type="button" id="modelCompareClear">Clear</button>
      <a id="modelCompareLaunch" href="/compare/" aria-disabled="true">Compare selected <b>↗</b></a>
    </div>
  `;
  root.appendChild(dock);
  const compareNames = dock.querySelector("#modelCompareNames");
  const compareLaunch = dock.querySelector("#modelCompareLaunch");
  const compareClear = dock.querySelector("#modelCompareClear");

  const activeCapabilities = () => new Set(
    capabilityButtons.filter(button => button.getAttribute("aria-pressed") === "true")
      .map(button => button.dataset.capability)
  );

  const validValues = (select) => new Set([...select.options].map(option => option.value));
  const validProviders = new Map(providerButtons.map(button => [normalize(button.dataset.modelProvider), button.dataset.modelProvider || "all"]));

  const readUrlState = () => {
    const params = new URLSearchParams(window.location.search);
    const urlProvider = normalize(params.get("provider") || "all");
    provider = validProviders.get(urlProvider) || "all";
    providerButtons.forEach(button => button.classList.toggle("is-active", button.dataset.modelProvider === provider));

    capabilityButtons.forEach(button => {
      const key = button.dataset.capability === "audio-video" ? "av" : button.dataset.capability;
      const active = params.get(key) === "1";
      button.setAttribute("aria-pressed", String(active));
      button.classList.toggle("is-active", active);
    });

    if (search) search.value = params.get("q") || "";
    if (sort && validValues(sort).has(params.get("sort"))) sort.value = params.get("sort");
    if (contextFilter && validValues(contextFilter).has(params.get("context"))) contextFilter.value = params.get("context");
    if (accessFilter && validValues(accessFilter).has(params.get("access"))) accessFilter.value = params.get("access");
    if (verificationFilter && validValues(verificationFilter).has(params.get("verified"))) verificationFilter.value = params.get("verified");
  };

  const writeUrlState = (historyMode = "replace") => {
    const params = new URLSearchParams();
    const caps = activeCapabilities();
    const query = search?.value.trim() || "";
    const mode = sort?.value || "default";
    const context = contextFilter?.value || "0";
    const access = accessFilter?.value || "all";
    const verified = verificationFilter?.value || "all";

    if (provider !== "all") params.set("provider", normalize(provider));
    if (caps.has("reasoning")) params.set("reasoning", "1");
    if (caps.has("image")) params.set("image", "1");
    if (caps.has("audio-video")) params.set("av", "1");
    if (context !== "0") params.set("context", context);
    if (access !== "all") params.set("access", access);
    if (verified !== "all") params.set("verified", verified);
    if (mode !== "default") params.set("sort", mode);
    if (query) params.set("q", query);

    const next = window.location.pathname + (params.toString() ? "?" + params.toString() : "") + window.location.hash;
    const current = window.location.pathname + window.location.search + window.location.hash;
    if (next === current) return;
    const method = historyMode === "push" ? "pushState" : "replaceState";
    window.history[method]({modelExplorer: true}, "", next);
  };

  const modelForRow = row => modelByRow.get(row) || null;
  const supports = (model, capability) => {
    if (!model) return false;
    const inputs = (model.modalities?.input || []).map(normalize);
    if (capability === "reasoning") return Boolean(model.reasoning);
    if (capability === "image") return inputs.includes("image");
    if (capability === "audio-video") return inputs.includes("audio") || inputs.includes("video");
    return true;
  };
  const isOpenWeight = model => /open[- ]weight/i.test(model?.positioning || "") || model?.provider === "Meta";
  const verificationAge = model => {
    if (!catalog?.source_verified || !model?.provenance?.verified_at) return Number.POSITIVE_INFINITY;
    const anchor = new Date(catalog.source_verified + "T00:00:00Z");
    const verified = new Date(model.provenance.verified_at + "T00:00:00Z");
    return Math.max(0, Math.round((anchor - verified) / 86400000));
  };

  const updateDock = () => {
    const models = [...selected].map(id => (catalog?.models || []).find(model => model.model_id === id)).filter(Boolean);
    dock.hidden = models.length === 0;
    compareNames.textContent = models.length ? models.map(model => model.model).join(" + ") : "Choose two models";
    const ready = models.length === 2;
    compareLaunch.setAttribute("aria-disabled", ready ? "false" : "true");
    compareLaunch.classList.toggle("is-disabled", !ready);
    compareLaunch.href = ready
      ? "/compare/?a=" + encodeURIComponent(models[0].model_id) + "&b=" + encodeURIComponent(models[1].model_id)
      : "/compare/";
  };

  const setSelected = (row, checked) => {
    const model = modelForRow(row);
    if (!model) return;
    if (checked && selected.size >= 2 && !selected.has(model.model_id)) {
      const first = selected.values().next().value;
      selected.delete(first);
      const previous = rows.find(item => modelForRow(item)?.model_id === first);
      previous?.querySelector(".model-compare-check")?.removeAttribute("checked");
      const previousInput = previous?.querySelector(".model-compare-check");
      if (previousInput) previousInput.checked = false;
    }
    if (checked) selected.add(model.model_id);
    else selected.delete(model.model_id);
    row.classList.toggle("is-selected", selected.has(model.model_id));
    updateDock();
  };

  const enhanceRows = () => {
    const head = root.querySelector(".model-explorer-table thead tr");
    if (head && !head.querySelector(".model-compare-heading")) {
      const th = document.createElement("th");
      th.className = "model-compare-heading";
      th.scope = "col";
      th.innerHTML = '<span class="sr-only">Select for comparison</span>';
      head.prepend(th);
    }
    rows.forEach(row => {
      if (row.querySelector(".model-compare-cell")) return;
      const model = modelForRow(row);
      if (!model) return;
      const cell = document.createElement("td");
      cell.className = "model-compare-cell";
      const input = document.createElement("input");
      input.type = "checkbox";
      input.className = "model-compare-check";
      input.setAttribute("aria-label", "Select " + model.model + " for comparison");
      input.addEventListener("change", () => setSelected(row, input.checked));
      cell.appendChild(input);
      row.prepend(cell);

      const modelCell = row.querySelector("th[scope='row']");
      if (modelCell && !modelCell.querySelector(".model-capability-line")) {
        const line = document.createElement("span");
        line.className = "model-capability-line";
        const tags = [];
        if (model.reasoning) tags.push("Reasoning");
        const inputs = (model.modalities?.input || []).map(normalize);
        if (inputs.includes("image")) tags.push("Image");
        if (inputs.includes("audio") || inputs.includes("video")) tags.push("A/V");
        if (isOpenWeight(model)) tags.push("Open weights");
        line.textContent = tags.join(" · ");
        modelCell.appendChild(line);
      }
    });
  };

  const apply = (historyMode = "replace") => {
    const query = normalize(search?.value);
    const mode = sort?.value || "default";
    const caps = activeCapabilities();
    const minContext = Number(contextFilter?.value || 0);
    const access = accessFilter?.value || "all";
    const maxAge = verificationFilter?.value === "all" ? null : Number(verificationFilter?.value);

    const ordered = [...rows].sort((a, b) => {
      if (mode === "input-asc") return numeric(a, "input") - numeric(b, "input");
      if (mode === "output-asc") return numeric(a, "output") - numeric(b, "output");
      if (mode === "context-desc") return numeric(b, "context") - numeric(a, "context");
      return numeric(a, "order") - numeric(b, "order");
    });
    ordered.forEach(row => body?.appendChild(row));

    let visible = 0;
    ordered.forEach(row => {
      const model = modelForRow(row);
      const providerMatch = provider === "all" || row.dataset.provider === provider;
      const queryMatch = !query || (row.dataset.search || "").includes(query);
      const capabilityMatch = [...caps].every(capability => supports(model, capability));
      const contextMatch = Number(model?.context_window || row.dataset.context || 0) >= minContext;
      const accessMatch =
        access === "all" ||
        (access === "official-paid" && model?.pricing_status === "official-paid") ||
        (access === "calculator" && model?.calculator_eligible === true) ||
        (access === "open-weight" && isOpenWeight(model));
      const verificationMatch = maxAge == null || verificationAge(model) <= maxAge;
      const show = providerMatch && queryMatch && capabilityMatch && contextMatch && accessMatch && verificationMatch;
      row.hidden = !show;
      if (show) visible += 1;
    });

    if (count) count.textContent = visible + (visible === 1 ? " model shown" : " models shown");
    if (empty) empty.hidden = visible !== 0;
    root.classList.toggle("has-active-filters",
      provider !== "all" || Boolean(query) || caps.size > 0 || minContext > 0 || access !== "all" || maxAge != null
    );
    if (historyMode) writeUrlState(historyMode);
  };

  readUrlState();

  window.addEventListener("popstate", () => {
    readUrlState();
    apply(null);
  });

  providerButtons.forEach(button => button.addEventListener("click", () => {
    providerButtons.forEach(item => item.classList.remove("is-active"));
    button.classList.add("is-active");
    provider = button.dataset.modelProvider || "all";
    apply("push");
  }));
  capabilityButtons.forEach(button => button.addEventListener("click", () => {
    const next = button.getAttribute("aria-pressed") !== "true";
    button.setAttribute("aria-pressed", String(next));
    button.classList.toggle("is-active", next);
    apply("push");
  }));
  search?.addEventListener("input", () => apply("replace"));
  sort?.addEventListener("change", () => apply("push"));
  contextFilter?.addEventListener("change", () => apply("push"));
  accessFilter?.addEventListener("change", () => apply("push"));
  verificationFilter?.addEventListener("change", () => apply("push"));

  resetButton?.addEventListener("click", () => {
    provider = "all";
    providerButtons.forEach(button => button.classList.toggle("is-active", button.dataset.modelProvider === "all"));
    capabilityButtons.forEach(button => {
      button.setAttribute("aria-pressed", "false");
      button.classList.remove("is-active");
    });
    if (search) search.value = "";
    if (sort) sort.value = "default";
    if (contextFilter) contextFilter.value = "0";
    if (accessFilter) accessFilter.value = "all";
    if (verificationFilter) verificationFilter.value = "all";
    apply("push");
  });

  compareClear?.addEventListener("click", () => {
    selected.clear();
    rows.forEach(row => {
      row.classList.remove("is-selected");
      const input = row.querySelector(".model-compare-check");
      if (input) input.checked = false;
    });
    updateDock();
  });

  fetch("/data/model-pricing.json", {cache: "no-cache"})
    .then(response => {
      if (!response.ok) throw new Error("catalog");
      return response.json();
    })
    .then(data => {
      catalog = data;
      const byName = new Map((data.models || []).map(model => [normalize(model.model), model]));
      rows.forEach(row => {
        const name = row.querySelector("th[scope='row'] > a")?.textContent;
        const model = byName.get(normalize(name));
        if (model) modelByRow.set(row, model);
      });
      enhanceRows();
      const badge = root.querySelector(".model-verification-badge strong");
      const meta = root.querySelector(".model-verification-badge small");
      if (badge && data.source_verified) badge.textContent = data.source_verified;
      const models = data.models || [];
      const providers = new Set(models.map(model => model.provider));
      if (meta) {
        meta.textContent = models.length + " models · " + providers.size + " providers";
      }

      const metricModels = document.getElementById("metricModels");
      const metricProviders = document.getElementById("metricProviders");
      const metricContext = document.getElementById("metricContext");
      const metricContextModel = document.getElementById("metricContextModel");
      const metricPrice = document.getElementById("metricPrice");
      const metricPriceModel = document.getElementById("metricPriceModel");

      const formatContext = value => {
        const n = Number(value);
        if (!Number.isFinite(n)) return "—";
        if (n >= 1000000) return (n / 1000000).toLocaleString(undefined, {maximumFractionDigits: 2}) + "M";
        if (n >= 1000) return (n / 1000).toLocaleString(undefined, {maximumFractionDigits: 0}) + "K";
        return n.toLocaleString();
      };
      const verifiedRates = models.map(model => {
        const periods = model?.pricing?.standard || [];
        const current = periods.find(period =>
          data.source_verified >= period.start && (!period.end || data.source_verified <= period.end)
        );
        return current && model.pricing_status === "official-paid" && model.calculator_eligible === true
          ? {model, input: Number(current.input)}
          : null;
      }).filter(item => item && Number.isFinite(item.input));

      const largestContextModel = models.reduce((best, model) =>
        Number(model.context_window || 0) > Number(best?.context_window || 0) ? model : best, null
      );
      const lowestInput = verifiedRates.reduce((best, item) =>
        !best || item.input < best.input ? item : best, null
      );

      if (metricModels) metricModels.textContent = models.length.toLocaleString();
      if (metricProviders) metricProviders.textContent = providers.size.toLocaleString();
      if (metricContext && largestContextModel) metricContext.textContent = formatContext(largestContextModel.context_window);
      if (metricContextModel && largestContextModel) metricContextModel.textContent = largestContextModel.model;
      if (metricPrice && lowestInput) metricPrice.textContent = "$" + lowestInput.input.toLocaleString(undefined, {maximumFractionDigits: 4});
      if (metricPriceModel && lowestInput) metricPriceModel.textContent = lowestInput.model + " / MTok";
      apply(null);
    })
    .catch(() => {
      root.classList.add("catalog-fallback");
      apply(null);
    });
})();