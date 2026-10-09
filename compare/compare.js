(() => {
  const root = document.querySelector("[data-compare-builder]");
  const cards = [...document.querySelectorAll("[data-compare-card]")];
  const search = document.getElementById("compare-search");
  const filters = [...document.querySelectorAll("[data-compare-filter]")];
  const empty = document.getElementById("compare-empty");
  let activeFilter = "all";

  const applyLibraryFilter = () => {
    const query = (search?.value || "").trim().toLowerCase();
    let visible = 0;
    for (const card of cards) {
      const tags = (card.dataset.tags || "").toLowerCase();
      const haystack = (card.dataset.search || "").toLowerCase();
      const providerMatch = activeFilter === "all" || tags.includes(activeFilter);
      const queryMatch = !query || haystack.includes(query);
      card.hidden = !(providerMatch && queryMatch);
      if (!card.hidden) visible += 1;
    }
    if (empty) empty.hidden = visible !== 0;
  };

  filters.forEach(button => button.addEventListener("click", () => {
    filters.forEach(item => item.classList.remove("is-active"));
    button.classList.add("is-active");
    activeFilter = button.dataset.compareFilter || "all";
    applyLibraryFilter();
  }));
  search?.addEventListener("input", applyLibraryFilter);
  applyLibraryFilter();

  if (!root) return;

  const modelA = document.getElementById("compareModelA");
  const modelB = document.getElementById("compareModelB");
  const inputTokens = document.getElementById("compareInputTokens");
  const cachedTokens = document.getElementById("compareCachedTokens");
  const outputTokens = document.getElementById("compareOutputTokens");
  const monthlyRequests = document.getElementById("compareMonthlyRequests");
  const presetButtons = [...document.querySelectorAll("[data-compare-preset]")];
  const presets = Object.freeze({
    chat: {input: 2000, cached: 0, output: 600},
    coding: {input: 20000, cached: 10000, output: 4000},
    research: {input: 120000, cached: 30000, output: 8000}
  });
  const results = document.getElementById("compareBuilderResults");
  const errors = document.getElementById("compareBuilderError");
  const evidence = document.getElementById("compareEvidence");
  const engine = window.SxfCompareEngine;
  let evaluations = null;
  const esc = value => String(value ?? "").replace(/[&<>"']/g, char =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));

  const curatedLink = document.getElementById("compareCuratedLink");

  let catalog = null;
  let registry = null;
  let byId = new Map();

  const number = value => {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed >= 0 ? Math.floor(parsed) : 0;
  };

  const money = value => {
    if (!Number.isFinite(value)) return "—";
    const digits = Math.abs(value) >= 100 ? 2 : Math.abs(value) >= 1 ? 4 : 6;
    return "$" + value.toLocaleString(undefined, {maximumFractionDigits: digits});
  };

  const rate = value => window.SXFPricing.formatRate(value);

  const isTokenCalculatorModel = model =>
    model?.pricing_basis?.meter === "tokens" &&
    model?.pricing_status === "official-paid" &&
    model?.calculator_eligible === true;

  const pricingQuantity = model => Number(model?.pricing_basis?.quantity || 1_000_000);
  const pricingDisplayUnit = model => model?.pricing_basis?.display_unit || "per 1 million tokens";

  const {utcToday, periodForDate} = window.SXFPricing;
  const effectiveRates = (model, totalInput) => {
    if (!isTokenCalculatorModel(model)) return null;
    return window.SXFPricing.effectiveRates(model, utcToday(), totalInput);
  };

  const modelCost = (model, input, cached, output) => {
    const effective = effectiveRates(model, input + cached);
    if (!effective) return null;
    const r = effective.rates;
    const quantity = pricingQuantity(model);
    const cachedRate = r.cached_input ?? r.input;
    return {
      total: input / quantity * r.input +
        cached / quantity * cachedRate +
        output / quantity * r.output,
      effective
    };
  };

  const contextLabel = model => {
    if (!Number.isFinite(Number(model.context_window)) || model.context_window == null) return "Not published";
    return Number(model.context_window).toLocaleString() + " tokens";
  };

  const outputLabel = model => {
    if (model.max_output === "unlimited") return "No separate limit";
    if (model.max_output == null) return "Not published";
    return Number(model.max_output).toLocaleString() + " tokens";
  };

  const pricingLabel = model => {
    const p = periodForDate(model, utcToday());
    if (!p) return model.pricing_status || "not-published";
    const basis = model.pricing_basis || {};
    if (basis.meter !== "tokens") {
      const rates = p.rates || {};
      const parts = (basis.dimensions || []).map(key => {
        const label = key.replaceAll("_", " ");
        return Number.isFinite(Number(rates[key])) ? rate(rates[key]) + " " + label : null;
      }).filter(Boolean);
      return parts.length ? parts.join(" · ") + " " + (basis.display_unit || "") : (model.pricing_status || "not-published");
    }
    const parts = [];
    if (Number.isFinite(Number(p.input))) parts.push(rate(p.input) + " input");
    if (Number.isFinite(Number(p.cached_input))) parts.push(rate(p.cached_input) + " cached");
    if (Number.isFinite(Number(p.output))) parts.push(rate(p.output) + " output");
    return parts.length ? parts.join(" · ") + " " + pricingDisplayUnit(model) : (model.pricing_status || "not-published");
  };

  const reasoningLabel = model => {
    const reasoning = model.reasoning;
    if (!reasoning || !Array.isArray(reasoning.levels) || !reasoning.levels.length) return "Not published";
    const levels = reasoning.levels.join(" · ");
    return reasoning.default ? levels + " · default " + reasoning.default : levels;
  };

  const card = (model, cost) => {
    const inputs = (model.modalities?.input || []).join(" + ") || "Not published";
    const longLabel = cost?.effective?.long ? "Long-context pricing active" : "Standard pricing";
    return `<article class="compare-builder-model">
      <div class="compare-builder-model-meta"><span>${model.provider}</span><small>${model.pricing_status}</small></div>
      <h3>${model.model}</h3>
      <dl>
        <div><dt>Context</dt><dd>${contextLabel(model)}</dd></div>
        <div><dt>Max output</dt><dd>${outputLabel(model)}</dd></div>
        <div><dt>Inputs</dt><dd>${inputs}</dd></div>
        <div><dt>Reasoning</dt><dd>${reasoningLabel(model)}</dd></div>
        <div><dt>Pricing</dt><dd>${pricingLabel(model)}</dd></div>
        <div><dt>Workload cost</dt><dd>${cost ? money(cost.total) : "Not directly comparable"}</dd></div>
      </dl>
      <p class="compare-builder-rate-note">${cost ? longLabel : "Excluded from direct paid-token arithmetic"}</p>
      <a href="${model.sxf_url}">Open model reference ↗</a>
    </article>`;
  };

  const render = () => {
    if (!catalog || !registry || !modelA || !modelB || !results) return;
    const left = byId.get(modelA.value);
    const right = byId.get(modelB.value);
    if (!left || !right) return;
    if (left.model_id === right.model_id) {
      errors.hidden = false; errors.textContent = "Choose two different models."; results.replaceChildren(); evidence.replaceChildren();
      curatedLink.hidden = true;
      return;
    }

    const task = engine?.workload({
      input: inputTokens?.value, cached: cachedTokens?.value,
      output: outputTokens?.value, requests: monthlyRequests?.value
    });
    if (!task?.ok) {
      errors.hidden = false;
      errors.textContent = task?.error || "Comparison engine could not load.";
      results.replaceChildren();
      evidence.replaceChildren();
      curatedLink.hidden = true;
      return;
    }
    errors.hidden = true;
    const leftWarnings = engine.capacityWarnings(left, task);
    const rightWarnings = engine.capacityWarnings(right, task);
    const leftCost = leftWarnings.length ? null : engine.pricing(left, task, utcToday());
    const rightCost = rightWarnings.length ? null : engine.pricing(right, task, utcToday());
    const lc = leftCost?.available ? {total:leftCost.total,effective:{long:leftCost.long}} : null;
    const rc = rightCost?.available ? {total:rightCost.total,effective:{long:rightCost.long}} : null;
    let verdict = "No direct cost conclusion: one or both prices are unavailable or this workload exceeds published limits.";
    if (lc && rc) {
      const delta = Math.abs(lc.total - rc.total);
      verdict = delta < 1e-12
        ? "Direct token costs are equal for this workload."
        : (lc.total < rc.total ? left.model : right.model) +
          " has lower estimated direct token cost for this workload.";
    }
    const monthlyNote = lc && rc
      ? "For " + task.requests.toLocaleString() + " requests/month: " +
        esc(left.model) + " " + money(leftCost.monthly) + " vs " +
        esc(right.model) + " " + money(rightCost.monthly) + "."
      : "Monthly cost unavailable until comparable rates and valid model limits are confirmed.";
    results.innerHTML = `<div class="compare-builder-summary"><span>WORKLOAD RESULT</span><strong>${esc(verdict)}</strong><small>${monthlyNote}</small><small>Estimates use official catalog rates and illustrative token budgets; not quality, speed, or total ownership cost.</small></div>
      <div class="compare-builder-grid">${card(left,lc)}${card(right,rc)}</div>
      <div class="compare-engine-cautions">${leftWarnings.map(x=>"<p>"+esc(left.model)+": "+esc(x)+"</p>").join("")}${rightWarnings.map(x=>"<p>"+esc(right.model)+": "+esc(x)+"</p>").join("")}</div>`;
    const pairs = engine.benchmarkPairs(evaluations, left.model_id, right.model_id);
    const benchmarks = pairs.length ? pairs.map(p => {
      const l = p.left, r = p.right, b = p.benchmark;
      const qualifier = p.configurationDiffers
        ? "Different evaluated configurations; scores are descriptive, not a controlled head-to-head result."
        : "Matching evaluation group and configuration.";
      return `<article class="compare-evidence-card"><h4>${esc(b.name)} <small>${esc(b.version)}</small></h4>
        <p>${esc(left.model)}: <strong>${esc(l.score)} ${esc(b.unit || "")}</strong> · ${esc(right.model)}: <strong>${esc(r.score)} ${esc(b.unit || "")}</strong></p>
        <p class="compare-evidence-note">${esc(qualifier)} Scores are specific to this benchmark, not a universal model rating.</p>
        <p class="compare-evidence-note">Configurations: ${esc(l.model_configuration?.reasoning_effort || "undisclosed")} vs ${esc(r.model_configuration?.reasoning_effort || "undisclosed")}. Verified data: ${esc(evaluations.source_verified || "undated")}.</p>
        <a href="${esc(l.source_url)}" target="_blank" rel="noopener noreferrer">Source A ↗</a> · <a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Source B ↗</a></article>`;
    }).join("") : '<p>No directly comparable independent evaluation observations are available for this matchup.</p>';
    const aFit = engine.fit(left, ["coding","agents"]);
    const bFit = engine.fit(right, ["coding","agents"]);
    evidence.innerHTML = `<div class="compare-evidence-head"><span>INDEPENDENT EVIDENCE</span><h3>Task-specific performance, with sources</h3><p>Benchmark coverage is not a universal recommendation. Missing information stays missing.</p></div>
      <div class="compare-evidence-list">${benchmarks}</div>
      <div class="compare-evidence-head"><h3>Decision guidance</h3><p>For a cost-sensitive workload, choose the lower-cost model only after testing answer quality and latency on your own prompts. Catalog capabilities: ${esc(left.model)} lists ${esc(aFit.listed.join(", ") || "no coding/agent tags")}; ${esc(right.model)} lists ${esc(bFit.listed.join(", ") || "no coding/agent tags")}. These tags are not proven performance.</p></div>`;

    const pair = (registry.comparisons || []).find(entry => {
      if (!entry.indexable || entry.model_ids?.length !== 2) return false;
      const ids = new Set(entry.model_ids);
      return ids.has(left.model_id) && ids.has(right.model_id);
    });
    if (pair) {
      curatedLink.hidden = false;
      curatedLink.innerHTML = `<span>DEEP COMPARISON AVAILABLE</span><a href="/compare/${pair.slug}/"><strong>${pair.title}</strong><b>Open decision page ↗</b></a>`;
    } else {
      curatedLink.hidden = false;
      curatedLink.innerHTML = '<span>BUILDER-ONLY MATCHUP</span><p>This pair stays interactive-only until it has enough distinct decision value for a dedicated indexable page.</p>';
    }
  };

  Promise.all([
    fetch(root.dataset.catalog || "/data/model-pricing.json", {cache: "no-store"}).then(r => {
      if (!r.ok) throw new Error("catalog");
      return r.json();
    }),
    fetch(root.dataset.registry || "/data/model-comparisons.json", {cache: "no-store"}).then(r => {
      if (!r.ok) throw new Error("registry");
      return r.json();
    })
  ]).then(([catalogData, registryData]) => {
    catalog = catalogData;
    registry = registryData;
    byId = new Map((catalog.models || []).map(model => [model.model_id, model]));
    const params = new URLSearchParams(window.location.search);
    const requestedA = params.get("a");
    const requestedB = params.get("b");
    if (requestedA && byId.has(requestedA)) modelA.value = requestedA;
    else if (byId.has("gpt-6-sol")) modelA.value = "gpt-6-sol";
    if (requestedB && byId.has(requestedB) && requestedB !== modelA.value) modelB.value = requestedB;
    else if (byId.has("grok-4.7") && modelA.value !== "grok-4.7") modelB.value = "grok-4.7";
    render();
    // Model selections are assigned programmatically: notify optional enhancements.
    root.dispatchEvent(new Event("compare:ready"));
  }).catch(() => {
    results.innerHTML = '<div class="compare-builder-error">The comparison datasets could not be loaded.</div>';
  });

  presetButtons.forEach(button => button.addEventListener("click", () => {
    const preset = presets[button.dataset.comparePreset];
    if (!preset) return;
    inputTokens.value = String(preset.input);
    cachedTokens.value = String(preset.cached);
    outputTokens.value = String(preset.output);
    presetButtons.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    render();
  }));
  [inputTokens, cachedTokens, outputTokens].forEach(node => node?.addEventListener("input", () => {
    presetButtons.forEach(item => item.setAttribute("aria-pressed", "false"));
  }));
  fetch("/data/model-evaluations.json", {cache:"no-store"})
    .then(r => { if (!r.ok) throw new Error("evaluations"); return r.json(); })
    .then(data => { evaluations = data; render(); })
    .catch(() => { evaluations = null; render(); });
  [modelA, modelB, inputTokens, cachedTokens, outputTokens, monthlyRequests].forEach(node => {
    node?.addEventListener("input", render);
    node?.addEventListener("change", render);
  });
})();
