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
  const tableWrap = root.querySelector(".model-explorer-table-wrap");
  const cardByRow = new Map();

  const mobileBar = document.createElement("div");
  mobileBar.className = "model-mobile-bar";
  mobileBar.innerHTML = `
    <div class="model-mobile-summary">
      <span>MODEL CATALOG</span>
      <strong id="modelMobileCount">Loading models…</strong>
    </div>
    <button type="button" class="model-mobile-filter-button" id="modelMobileFilterButton" aria-expanded="false" aria-controls="modelExplorerFacets">
      Filters <span id="modelMobileFilterCount" aria-hidden="true"></span>
    </button>
  `;
  toolbar?.before(mobileBar);

  const mobileActiveFilters = document.createElement("div");
  mobileActiveFilters.className = "model-mobile-active-filters";
  mobileActiveFilters.hidden = true;
  mobileBar.after(mobileActiveFilters);

  const mobileCards = document.createElement("div");
  mobileCards.className = "model-mobile-cards";
  mobileCards.setAttribute("aria-label", "AI model results");
  tableWrap?.after(mobileCards);

  const mobileBackdrop = document.createElement("button");
  mobileBackdrop.type = "button";
  mobileBackdrop.className = "model-filter-backdrop";
  mobileBackdrop.setAttribute("aria-label", "Close filters");
  mobileBackdrop.hidden = true;
  root.appendChild(mobileBackdrop);

  let provider = "all";
  let catalog = null;
  let modelByRow = new Map();
  let selected = new Set();
  const PAGE_SIZE = 25;
  let visibleLimit = PAGE_SIZE;

  const normalize = value => String(value || "").trim().toLowerCase();
  const numeric = (row, key) => {
    if ((key === "input" || key === "output") && row.dataset.pricingStatus !== "official-paid") {
      return Number.POSITIVE_INFINITY;
    }
    const value = Number(row.dataset[key] || 0);
    return Number.isFinite(value) ? value : Number.POSITIVE_INFINITY;
  };

  const filters = document.createElement("div");
  filters.className = "model-explorer-facets";
  filters.id = "modelExplorerFacets";
  filters.innerHTML = `
    <div class="model-mobile-sheet-head">
      <div><span>FILTER MODELS</span><strong>Refine the catalog</strong></div>
      <button type="button" id="modelMobileFilterClose" aria-label="Close filters">×</button>
    </div>
    <div class="model-facet-primary">
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
        <option value="ocr">OCR</option>
        <option value="transcription">Transcription</option>
        <option value="rerank">Reranking</option>
        <option value="embeddings">Embeddings</option>
      </select></label>
      <label class="model-advanced-select"><span>Access</span><select id="modelAccessFilter">
        <option value="all">Any access</option>
        <option value="paid-api">Paid API</option>
        <option value="free-api">Free API</option>
        <option value="open-weight">Open weights</option>
        <option value="self-hostable">Self-hostable</option>
        <option value="calculator">Calculator eligible</option>
      </select></label>
      <button type="button" class="model-more-filters" id="modelMoreFilters" aria-expanded="false" aria-controls="modelSecondaryFilters">
        More filters <span id="modelMoreFilterCount" aria-hidden="true"></span>
      </button>
    </div>
    <div class="model-facet-secondary" id="modelSecondaryFilters" hidden>
      <label class="model-advanced-select"><span>Context</span><select id="modelContextFilter">
        <option value="0">Any context</option>
        <option value="500000">500K+</option>
        <option value="1000000">1M+</option>
        <option value="2000000">2M+</option>
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
      <button type="button" class="model-filter-reset" id="modelFilterReset">Clear filters</button>
    </div>
    <div class="model-active-filters" id="modelActiveFilters" aria-live="polite" hidden></div>
  `;
  toolbar?.appendChild(filters);

  const taskFilter = filters.querySelector("#modelTaskFilter");
  const contextFilter = filters.querySelector("#modelContextFilter");
  const accessFilter = filters.querySelector("#modelAccessFilter");
  const lifecycleFilter = filters.querySelector("#modelLifecycleFilter");
  const verificationFilter = filters.querySelector("#modelVerificationFilter");
  const resetButton = filters.querySelector("#modelFilterReset");
  const moreFiltersButton = filters.querySelector("#modelMoreFilters");
  const moreFilterCount = filters.querySelector("#modelMoreFilterCount");
  const secondaryFilters = filters.querySelector("#modelSecondaryFilters");
  const activeFilters = filters.querySelector("#modelActiveFilters");
  const capabilityButtons = [...filters.querySelectorAll("[data-capability]")];
  const mobileFilterButton = mobileBar.querySelector("#modelMobileFilterButton");
  const mobileFilterCount = mobileBar.querySelector("#modelMobileFilterCount");
  const mobileCount = mobileBar.querySelector("#modelMobileCount");
  const mobileFilterClose = filters.querySelector("#modelMobileFilterClose");

  const setMobileFiltersOpen = open => {
    root.classList.toggle("mobile-filters-open", open);
    mobileBackdrop.hidden = !open;
    mobileFilterButton?.setAttribute("aria-expanded", String(open));
    if (open) {
      document.documentElement.classList.add("model-filters-lock");
      window.setTimeout(() => filters.querySelector("button,select,input")?.focus(), 0);
    } else {
      document.documentElement.classList.remove("model-filters-lock");
    }
  };

  const quickProviderNames = new Set(["all", "OpenAI", "Anthropic", "Google", "xAI"]);
  const providerWrap = root.querySelector(".model-provider-filters");
  const sortWrap = sort?.closest(".model-sort") || null;
  const providerSlot = document.createComment("model-provider-slot");
  const sortSlot = document.createComment("model-sort-slot");
  providerWrap?.after(providerSlot);
  sortWrap?.after(sortSlot);
  const providerMoreButton = document.createElement("button");
  providerMoreButton.type = "button";
  providerMoreButton.className = "model-filter model-provider-more";
  providerMoreButton.setAttribute("aria-expanded", "false");
  providerMoreButton.setAttribute("aria-controls", "modelProviderPicker");
  providerMoreButton.textContent = "More providers";

  const providerPicker = document.createElement("div");
  providerPicker.className = "model-provider-picker";
  providerPicker.id = "modelProviderPicker";
  providerPicker.hidden = true;
  providerPicker.innerHTML = `
    <label class="model-provider-search">
      <span class="sr-only">Search providers</span>
      <input type="search" id="modelProviderSearch" placeholder="Search providers…" autocomplete="off">
    </label>
    <div class="model-provider-options" role="listbox" aria-label="All model providers"></div>
  `;
  providerWrap?.appendChild(providerMoreButton);
  providerWrap?.appendChild(providerPicker);
  const providerSearch = providerPicker.querySelector("#modelProviderSearch");
  const providerOptions = providerPicker.querySelector(".model-provider-options");

  providerButtons.forEach(button => {
    if (!quickProviderNames.has(button.dataset.modelProvider || "")) button.hidden = true;
    if ((button.dataset.modelProvider || "") !== "all") {
      const option = document.createElement("button");
      option.type = "button";
      option.className = "model-provider-option";
      option.dataset.providerOption = button.dataset.modelProvider || "";
      option.setAttribute("role", "option");
      option.textContent = button.textContent?.trim() || button.dataset.modelProvider || "";
      providerOptions?.appendChild(option);
    }
  });
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

  const resultsControl = document.createElement("div");
  resultsControl.className = "model-results-control";
  resultsControl.hidden = true;
  resultsControl.innerHTML = `
    <button type="button" class="model-show-more" id="modelShowMore">
      Show 25 more
    </button>
  `;
  root.querySelector(".model-explorer-foot")?.before(resultsControl);
  const showMoreButton = resultsControl.querySelector("#modelShowMore");

  const activeCapabilities = () => new Set(
    capabilityButtons.filter(button => button.getAttribute("aria-pressed") === "true")
      .map(button => button.dataset.capability)
  );

  const validValues = (select) => new Set([...select.options].map(option => option.value));
  const validProviders = new Map(providerButtons.map(button => [normalize(button.dataset.modelProvider), button.dataset.modelProvider || "all"]));

  const secondaryFilterCount = () => {
    let total = 0;
    if ((contextFilter?.value || "0") !== "0") total += 1;
    if ((lifecycleFilter?.value || "all") !== "all") total += 1;
    if ((verificationFilter?.value || "all") !== "all") total += 1;
    return total;
  };

  const setSecondaryOpen = open => {
    if (!secondaryFilters || !moreFiltersButton) return;
    secondaryFilters.hidden = !open;
    moreFiltersButton.setAttribute("aria-expanded", String(open));
  };

  const syncProviderUi = () => {
    providerButtons.forEach(button => {
      const active = button.dataset.modelProvider === provider;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    providerOptions?.querySelectorAll("[data-provider-option]").forEach(button => {
      const active = button.dataset.providerOption === provider;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    });
    const hiddenProviderActive = provider !== "all" && !quickProviderNames.has(provider);
    providerMoreButton.classList.toggle("is-active", hiddenProviderActive);
    providerMoreButton.textContent = hiddenProviderActive ? provider : "More providers";
  };

  const closeProviderPicker = () => {
    providerPicker.hidden = true;
    providerMoreButton.setAttribute("aria-expanded", "false");
  };

  const filterProviderOptions = () => {
    const query = normalize(providerSearch?.value);
    providerOptions?.querySelectorAll("[data-provider-option]").forEach(button => {
      button.hidden = Boolean(query) && !normalize(button.textContent).includes(query);
    });
  };

  const activeFilterEntries = () => {
    const entries = [];
    if (provider !== "all") entries.push({key: "provider", label: provider});
    activeCapabilities().forEach(capability => {
      const labels = {reasoning: "Reasoning", vision: "Image", video: "Video", audio: "Audio"};
      entries.push({key: "capability:" + capability, label: labels[capability] || capability});
    });
    if ((taskFilter?.value || "all") !== "all") entries.push({key: "task", label: taskFilter.options[taskFilter.selectedIndex]?.text || taskFilter.value});
    if ((accessFilter?.value || "all") !== "all") entries.push({key: "access", label: accessFilter.options[accessFilter.selectedIndex]?.text || accessFilter.value});
    if ((contextFilter?.value || "0") !== "0") entries.push({key: "context", label: contextFilter.options[contextFilter.selectedIndex]?.text || contextFilter.value});
    if ((lifecycleFilter?.value || "all") !== "all") entries.push({key: "lifecycle", label: lifecycleFilter.options[lifecycleFilter.selectedIndex]?.text || lifecycleFilter.value});
    if ((verificationFilter?.value || "all") !== "all") entries.push({key: "verified", label: verificationFilter.options[verificationFilter.selectedIndex]?.text || verificationFilter.value});
    return entries;
  };

  const renderActiveFilters = () => {
    if (!activeFilters) return;
    const entries = activeFilterEntries();
    const markup = entries.map(entry =>
      '<button type="button" class="model-active-filter" data-remove-filter="' + entry.key + '">' +
      entry.label + ' <span aria-hidden="true">×</span></button>'
    ).join("") + (entries.length > 1 ? '<button type="button" class="model-active-clear" data-clear-all>Clear all</button>' : "");
    activeFilters.hidden = entries.length === 0;
    activeFilters.innerHTML = markup;
    mobileActiveFilters.hidden = entries.length === 0;
    mobileActiveFilters.innerHTML = markup;
    const totalActive = entries.length;
    if (mobileFilterCount) mobileFilterCount.textContent = totalActive ? String(totalActive) : "";
    if (moreFilterCount) {
      const total = secondaryFilterCount();
      moreFilterCount.textContent = total ? String(total) : "";
    }
  };

  const readUrlState = () => {
    const params = new URLSearchParams(window.location.search);
    const urlProvider = normalize(params.get("provider") || "all");
    provider = validProviders.get(urlProvider) || "all";
    syncProviderUi();

    capabilityButtons.forEach(button => {
      const key = button.dataset.capability;
      const legacyKey = key === "vision" ? "image" : key;
      const active = params.get(key) === "1" || params.get(legacyKey) === "1";
      button.setAttribute("aria-pressed", String(active));
      button.classList.toggle("is-active", active);
    });

    if (search) search.value = params.get("q") || "";
    if (sort) sort.value = validValues(sort).has(params.get("sort")) ? params.get("sort") : "default";
    if (taskFilter) taskFilter.value = validValues(taskFilter).has(params.get("task")) ? params.get("task") : "all";
    if (contextFilter) contextFilter.value = validValues(contextFilter).has(params.get("context")) ? params.get("context") : "0";
    if (accessFilter) {
      const rawAccess = params.get("access");
      const accessAlias = rawAccess === "official-paid" ? "paid-api" : rawAccess;
      accessFilter.value = validValues(accessFilter).has(accessAlias) ? accessAlias : "all";
    }
    if (lifecycleFilter) lifecycleFilter.value = validValues(lifecycleFilter).has(params.get("lifecycle")) ? params.get("lifecycle") : "all";
    if (verificationFilter) verificationFilter.value = validValues(verificationFilter).has(params.get("verified")) ? params.get("verified") : "all";
    setSecondaryOpen(secondaryFilterCount() > 0);
    renderActiveFilters();
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
    if (!catalog?.source_verified || !model?.verified_at) return Number.POSITIVE_INFINITY;
    const anchor = new Date(catalog.source_verified + "T00:00:00Z");
    const verified = new Date(model.verified_at + "T00:00:00Z");
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

  const syncSelectionUi = (row, checked) => {
    row.classList.toggle("is-selected", checked);
    const rowInput = row.querySelector(".model-compare-check");
    if (rowInput) rowInput.checked = checked;
    const card = cardByRow.get(row);
    card?.classList.toggle("is-selected", checked);
    const cardInput = card?.querySelector(".model-card-compare-check");
    if (cardInput) cardInput.checked = checked;
  };

  const setSelected = (row, checked) => {
    const model = modelForRow(row);
    if (!model) return;
    if (checked && selected.size >= 2 && !selected.has(model.model_id)) {
      const first = selected.values().next().value;
      selected.delete(first);
      const previous = rows.find(item => modelForRow(item)?.model_id === first);
      if (previous) syncSelectionUi(previous, false);
    }
    if (checked) selected.add(model.model_id);
    else selected.delete(model.model_id);
    syncSelectionUi(row, selected.has(model.model_id));
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
        if (caps.has("ocr")) tags.push("OCR");
        if (caps.has("transcription")) tags.push("Transcription");
        if (caps.has("rerank")) tags.push("Rerank");
        if (caps.has("embeddings")) tags.push("Embeddings");
        if (isOpenWeight(model)) tags.push("Open weights");
        line.textContent = tags.slice(0, 4).join(" · ");
        modelCell.appendChild(line);
      }

      if (!cardByRow.has(row)) {
        const priceCells = [...row.querySelectorAll("td.model-price")];
        const primaryRate = priceCells[0]?.childNodes[0]?.textContent?.trim() || "Not published";
        const outputRate = priceCells[2]?.textContent?.trim() || "—";
        const context = model.context_window
          ? Number(model.context_window).toLocaleString() + " tokens"
          : "Not published";
        const caps = capabilitySet(model);
        const tags = [];
        if (caps.has("reasoning")) tags.push("Reasoning");
        if (caps.has("vision")) tags.push("Image");
        if (caps.has("video")) tags.push("Video");
        if (caps.has("audio")) tags.push("Audio");
        if (caps.has("coding")) tags.push("Coding");
        if (caps.has("agents")) tags.push("Agents");
        if (caps.has("embeddings")) tags.push("Embeddings");
        if (caps.has("transcription")) tags.push("Transcription");
        if (caps.has("ocr")) tags.push("OCR");
        if (isOpenWeight(model)) tags.push("Open weights");

        const card = document.createElement("article");
        card.className = "model-mobile-card";
        card.dataset.modelCard = model.model_id;
        card.innerHTML = `
          <div class="model-card-topline">
            <div class="model-card-provider"><span>${model.provider}</span><small>${model.family || ""}</small></div>
            <label class="model-card-compare">
              <input type="checkbox" class="model-card-compare-check" aria-label="Select ${model.model} for comparison">
              <span>Compare</span>
            </label>
          </div>
          <a class="model-card-title" href="${row.querySelector("th[scope='row'] a")?.getAttribute("href") || "#"}">
            <strong>${model.model}</strong>
            <small>${model.model_id}</small>
          </a>
          <div class="model-card-facts">
            <div><span>Context</span><strong>${context}</strong></div>
            <div><span>Input</span><strong>${primaryRate}</strong></div>
            <div><span>Output</span><strong>${outputRate}</strong></div>
          </div>
          <div class="model-card-tags">${tags.slice(0, 4).map(tag => "<span>" + tag + "</span>").join("")}</div>
          <div class="model-card-actions">
            <a href="${row.querySelector("th[scope='row'] a")?.getAttribute("href") || "#"}">View model <b>↗</b></a>
            <span>Verified ${model.verified_at || ""}</span>
          </div>
        `;
        const cardInput = card.querySelector(".model-card-compare-check");
        cardInput?.addEventListener("change", () => setSelected(row, cardInput.checked));
        cardByRow.set(row, card);
        mobileCards.appendChild(card);
      }
    });
    if (cardByRow.size) root.classList.add("mobile-cards-ready");
  };

  const apply = (historyMode = "replace", resetWindow = true) => {
    if (resetWindow) visibleLimit = PAGE_SIZE;

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

    const matches = ordered.filter(row => {
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
      return providerMatch && queryMatch && capabilityMatch && taskMatch && contextMatch &&
        accessMatch && lifecycleMatch && verificationMatch;
    });

    const renderedRows = new Set(matches.slice(0, visibleLimit));

    ordered.forEach(row => {
      body?.appendChild(row);
      row.hidden = !renderedRows.has(row);
      const card = cardByRow.get(row);
      if (card) {
        mobileCards.appendChild(card);
        card.hidden = !renderedRows.has(row);
      }
    });

    const totalMatches = matches.length;
    const shown = Math.min(visibleLimit, totalMatches);
    const countText = shown < totalMatches
      ? shown + " of " + totalMatches + " models shown"
      : totalMatches + (totalMatches === 1 ? " model shown" : " models shown");
    if (count) count.textContent = countText;
    if (mobileCount) mobileCount.textContent = countText;
    if (empty) empty.hidden = totalMatches !== 0;
    if (resultsControl) resultsControl.hidden = shown >= totalMatches;
    if (showMoreButton) {
      const remaining = Math.max(0, totalMatches - shown);
      const increment = Math.min(PAGE_SIZE, remaining);
      showMoreButton.textContent = increment ? "Show " + increment + " more" : "All models shown";
      showMoreButton.setAttribute("aria-label", increment
        ? "Show " + increment + " more of " + totalMatches + " matching models"
        : "All matching models shown");
    }

    root.dataset.matchCount = String(totalMatches);
    root.dataset.renderedCount = String(shown);
    root.classList.toggle("has-active-filters",
      provider !== "all" || Boolean(query) || caps.size > 0 || task !== "all" || minContext > 0 ||
      access !== "all" || lifecycle !== "all" || maxAge != null
    );
    renderActiveFilters();
    if (historyMode) writeUrlState(historyMode);
  };

  readUrlState();

  window.addEventListener("popstate", () => {
    readUrlState();
    apply(null, true);
  });

  const setProvider = nextProvider => {
    provider = nextProvider || "all";
    syncProviderUi();
    closeProviderPicker();
    apply("push");
  };

  providerButtons.forEach(button => button.addEventListener("click", () => {
    setProvider(button.dataset.modelProvider || "all");
  }));
  providerOptions?.addEventListener("click", event => {
    const button = event.target.closest("[data-provider-option]");
    if (!button) return;
    setProvider(button.dataset.providerOption || "all");
  });
  providerMoreButton.addEventListener("click", () => {
    const open = providerPicker.hidden;
    providerPicker.hidden = !open;
    providerMoreButton.setAttribute("aria-expanded", String(open));
    if (open) {
      if (providerSearch) providerSearch.value = "";
      filterProviderOptions();
      providerSearch?.focus();
    }
  });
  providerSearch?.addEventListener("input", filterProviderOptions);
  capabilityButtons.forEach(button => button.addEventListener("click", () => {
    const next = button.getAttribute("aria-pressed") !== "true";
    button.setAttribute("aria-pressed", String(next));
    button.classList.toggle("is-active", next);
    apply("push");
  }));
  moreFiltersButton?.addEventListener("click", () => {
    setSecondaryOpen(secondaryFilters?.hidden === true);
  });

  const handleActiveFilterClick = event => {
    const clearAll = event.target.closest("[data-clear-all]");
    if (clearAll) {
      resetButton?.click();
      return;
    }
    const button = event.target.closest("[data-remove-filter]");
    if (!button) return;
    const key = button.dataset.removeFilter || "";
    if (key === "provider") provider = "all";
    else if (key.startsWith("capability:")) {
      const capability = key.split(":")[1];
      const target = capabilityButtons.find(item => item.dataset.capability === capability);
      if (target) {
        target.setAttribute("aria-pressed", "false");
        target.classList.remove("is-active");
      }
    } else if (key === "task" && taskFilter) taskFilter.value = "all";
    else if (key === "access" && accessFilter) accessFilter.value = "all";
    else if (key === "context" && contextFilter) contextFilter.value = "0";
    else if (key === "lifecycle" && lifecycleFilter) lifecycleFilter.value = "all";
    else if (key === "verified" && verificationFilter) verificationFilter.value = "all";
    syncProviderUi();
    apply("push");
  };
  activeFilters?.addEventListener("click", handleActiveFilterClick);
  mobileActiveFilters.addEventListener("click", handleActiveFilterClick);

  mobileFilterButton?.addEventListener("click", () => setMobileFiltersOpen(true));
  mobileFilterClose?.addEventListener("click", () => setMobileFiltersOpen(false));
  mobileBackdrop.addEventListener("click", () => setMobileFiltersOpen(false));

  document.addEventListener("click", event => {
    if (!providerPicker.hidden && !providerPicker.contains(event.target) && event.target !== providerMoreButton) {
      closeProviderPicker();
    }
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      setMobileFiltersOpen(false);
      closeProviderPicker();
      if (!secondaryFilters?.hidden && secondaryFilterCount() === 0) setSecondaryOpen(false);
    }
  });

  let searchFrame = null;
  search?.addEventListener("input", () => {
    if (searchFrame) window.cancelAnimationFrame(searchFrame);
    searchFrame = window.requestAnimationFrame(() => {
      searchFrame = null;
      apply("replace", true);
    });
  });
  sort?.addEventListener("change", () => apply("push"));
  taskFilter?.addEventListener("change", () => apply("push"));
  contextFilter?.addEventListener("change", () => {
    if (contextFilter.value !== "0") setSecondaryOpen(true);
    apply("push");
  });
  accessFilter?.addEventListener("change", () => apply("push"));
  lifecycleFilter?.addEventListener("change", () => {
    if (lifecycleFilter.value !== "all") setSecondaryOpen(true);
    apply("push");
  });
  verificationFilter?.addEventListener("change", () => {
    if (verificationFilter.value !== "all") setSecondaryOpen(true);
    apply("push");
  });

  resetButton?.addEventListener("click", () => {
    provider = "all";
    syncProviderUi();
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
    setSecondaryOpen(false);
    apply("push");
  });

  showMoreButton?.addEventListener("click", () => {
    visibleLimit += PAGE_SIZE;
    apply(null, false);
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

  const mobileQuery = window.matchMedia("(max-width: 680px)");
  const syncMobileMode = () => {
    if (mobileQuery.matches) {
      if (providerWrap && providerWrap.parentElement !== filters) {
        filters.querySelector(".model-mobile-sheet-head")?.after(providerWrap);
      }
      if (sortWrap && sortWrap.parentElement !== filters) {
        providerWrap?.after(sortWrap);
      }
    } else {
      setMobileFiltersOpen(false);
      if (providerWrap && providerSlot.parentNode) providerSlot.parentNode.insertBefore(providerWrap, providerSlot);
      if (sortWrap && sortSlot.parentNode) sortSlot.parentNode.insertBefore(sortWrap, sortSlot);
    }
  };
  mobileQuery.addEventListener?.("change", syncMobileMode);
  syncMobileMode();

  fetch("/data/model-index.json", {cache: "no-cache"})
    .then(response => {
      if (!response.ok) throw new Error("model-index");
      return response.json();
    })
    .then(data => {
      catalog = data;
      const byId = new Map((data.models || []).map(model => [model.model_id, model]));
      rows.forEach(row => {
        const model = byId.get(row.dataset.modelId || "");
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
        const input = Number(model?.standard_rate?.input);
        return model.pricing_status === "official-paid" && model.calculator_eligible === true && Number.isFinite(input)
          ? {model, input}
          : null;
      }).filter(Boolean);

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
      apply(null, true);
    })
    .catch(() => {
      root.classList.add("catalog-fallback");
      apply(null, true);
    });
})();