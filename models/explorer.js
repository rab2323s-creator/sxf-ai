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
        <button type="button" class="model-filter-chip" data-capability="vision" aria-pressed="false">Image</button>
        <button type="button" class="model-filter-chip" data-capability="video" aria-pressed="false">Video</button>
        <button type="button" class="model-filter-chip" data-capability="audio" aria-pressed="false">Audio</button>
      </div>
    </div>
    <label class="model-advanced-select"><span>Task</span><select id="modelTaskFilter">
      <option value="all">Any task</option>
      <option value="coding">Coding</option>
      <option value="agents">Agents</option>
      <option value="tool-use">Tool use</option>
    </select></label>
    <label class="model-advanced-select"><span>Context</span><select id="modelContextFilter">
      <option value="0">Any context</option>
      <option value="500000">500K+</option>
      <option value="1000000">1M+</option>
      <option value="2000000">2M+</option>
    </select></label>
    <label class="model-advanced-select"><span>Access</span><select id="modelAccessFilter">
      <option value="all">Any access</option>
      <option value="paid-api">Paid API</option>
      <option value="free-api">Free API</option>
      <option value="open-weight">Open weights</option>
      <option value="self-hostable">Self-hostable</option>
      <option value="calculator">Calculator eligible</option>
    </select></label>
    <label class="model-advanced-select"><span>Lifecycle</span><select id="modelLifecycleFilter">
      <option value="all">Any lifecycle</option>
      <option value="current">Current</option>
      <option value="preview">Preview</option>
      <option value="legacy">Legacy</option>
      <option value="deprecated">Deprecated</option>
    </select></label>
    <label class="model-advanced-select"><span>Verification</span><select id="modelVerificationFilter">
      <option value="all">Any verification date</option>
      <option value="14">Verified ≤14d</option>
      <option value="30">Verified ≤30d</option>
    </select></label>
    <button type="button" class="model-filter-reset" id="modelFilterReset">Reset filters</button>
  `;
  toolbar?.appendChild(filters);

  const taskFilter = filters.querySelector("#modelTaskFilter");
  const contextFilter = filters.querySelector("#modelContextFilter");
  const accessFilter = filters.querySelector("#modelAccessFilter");
  const lifecycleFilter = filters.querySelector("#modelLifecycleFilter");
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
      const key = button.dataset.capability;
      const active = params.get(key) === "1";
      button.setAttribute("aria-pressed", String(active));
      button.classList.toggle("is-active", active);
    });

    if (search) search.value = params.get("q") || "";
    if (sort) sort.value = validValues(sort).has(params.get("sort")) ? params.get("sort") : "default";
    if (taskFilter) taskFilter.value = validValues(taskFilter).has(params.get("task")) ? params.get("task") : "all";
    if (contextFilter) contextFilter.value = validValues(contextFilter).has(params.get("context")) ? params.get("context") : "0";
    if (accessFilter) accessFilter.value = validValues(accessFilter).has(params.get("access")) ? params.get("access") : "all";
    if (lifecycleFilter) lifecycleFilter.value = validValues(lifecycleFilter).has(params.get("lifecycle")) ? params.get("lifecycle") : "all";
    if (verificationFilter) verificationFilter.value = validValues(verificationFilter).has(params.get("verified")) ? params.get("verified") : "all";
  };

  const writeUrlState = (historyMode = "replace") => {
    const params = new URLSearchParams();
    const caps = activeCapabilities();
    const query = search?.value.trim() || "";
    const mode = sort?.value || "default";
    const task = taskFilter?.value || "all";
    const context = contextFilter?.value || "0";
    const access = accessFilter?.value || "all";
    const lifecycle = lifecycleFilter?.value || "all";
    const verified = verificationFilter?.value || "all";

    if (provider !== "all") params.set("provider", normalize(provider));
    capabilityButtons.forEach(button => {
      if (caps.has(button.dataset.capability)) params.set(button.dataset.capability, "1");
    });
    if (task !== "all") params.set("task", task);
    if (context !== "0") params.set("context", context);
    if (access !== "all") params.set("access", access);
    if (lifecycle !== "all") params.set("lifecycle", lifecycle);
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
  const capabilitySet = model => new Set((model?.capabilities || []).map(normalize));
  const supports = (model, capability) => capabilitySet(model).has(capability);
  const isOpenWeight = model => model?.access?.open_weight === true;
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
        const caps = capabilitySet(model);
        if (caps.has("reasoning")) tags.push("Reasoning");
        if (caps.has("vision")) tags.push("Image");
        if (caps.has("video")) tags.push("Video");
        if (caps.has("audio")) tags.push("Audio");
        if (caps.has("coding")) tags.push("Coding");
        if (caps.has("agents")) tags.push("Agents");
        if (isOpenWeight(model)) tags.push("Open weights");
        line.textContent = tags.slice(0, 4).join(" · ");
        modelCell.appendChild(line);
      }
    });
  };

  const apply = (historyMode = "replace") => {
    const query = normalize(search?.value);
    const mode = sort?.value || "default";
    const caps = activeCapabilities();
    const task = taskFilter?.value || "all";
    const minContext = Number(contextFilter?.value || 0);
    const access = accessFilter?.value || "all";
    const lifecycle = lifecycleFilter?.value || "all";
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
      const taskMatch = task === "all" || supports(model, task);
      const contextMatch = Number(model?.context_window || row.dataset.context || 0) >= minContext;
      const accessMatch =
        access === "all" ||
        (access === "paid-api" && model?.access?.official_api === true && model?.pricing_status === "official-paid") ||
        (access === "free-api" && model?.access?.official_api === true && model?.pricing_status === "free-preview") ||
        (access === "calculator" && model?.calculator_eligible === true) ||
        (access === "open-weight" && model?.access?.open_weight === true) ||
        (access === "self-hostable" && model?.access?.self_hostable === true);
      const lifecycleMatch = lifecycle === "all" || model?.lifecycle?.status === lifecycle;
      const verificationMatch = maxAge == null || verificationAge(model) <= maxAge;
      const show = providerMatch && queryMatch && capabilityMatch && taskMatch && contextMatch && accessMatch && lifecycleMatch && verificationMatch;
      row.hidden = !show;
      if (show) visible += 1;
    });

    if (count) count.textContent = visible + (visible === 1 ? " model shown" : " models shown");
    if (empty) empty.hidden = visible !== 0;
    root.classList.toggle("has-active-filters",
      provider !== "all" || Boolean(query) || caps.size > 0 || task !== "all" || minContext > 0 ||
      access !== "all" || lifecycle !== "all" || maxAge != null
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
  taskFilter?.addEventListener("change", () => apply("push"));
  contextFilter?.addEventListener("change", () => apply("push"));
  accessFilter?.addEventListener("change", () => apply("push"));
  lifecycleFilter?.addEventListener("change", () => apply("push"));
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
    if (taskFilter) taskFilter.value = "all";
    if (contextFilter) contextFilter.value = "0";
    if (accessFilter) accessFilter.value = "all";
    if (lifecycleFilter) lifecycleFilter.value = "all";
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