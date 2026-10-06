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
  const results = document.getElementById("compareBuilderResults");
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

  const rate = value => {
    if (!Number.isFinite(Number(value))) return "—";
    return "$" + Number(value).toLocaleString(undefined, {maximumFractionDigits: 4});
  };

  const isTokenCalculatorModel = model =>
    model?.pricing_basis?.meter === "tokens" &&
    model?.pricing_status === "official-paid" &&
    model?.calculator_eligible === true;

  const pricingQuantity = model => Number(model?.pricing_basis?.quantity || 1_000_000);
  const pricingDisplayUnit = model => model?.pricing_basis?.display_unit || "per 1 million tokens";

  const periodForDate = (model, date) => {
    const schedule = model?.pricing?.standard || [];
    return schedule.find(period => date >= period.start && (!period.end || date <= period.end)) || null;
  };

  const effectiveRates = (model, totalInput) => {
    if (!isTokenCalculatorModel(model)) return null;
    const period = periodForDate(model, catalog.source_verified);
    if (!period) return null;
    const rates = {...period};
    const rule = model?.pricing?.long_context;
    const long = Boolean(rule && totalInput > Number(rule.threshold_input_tokens));
    if (long) {
      for (const field of ["input", "cached_input", "cache_write", "output"]) {
        if (typeof rates[field] === "number" && typeof rule.multipliers?.[field] === "number") {
          rates[field] *= rule.multipliers[field];
        }
      }
    }
    return {rates, long, rule};
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

  const outputLabel = model => {
    if (model.max_output === "unlimited") return "No separate limit";
    if (model.max_output == null) return "Not published";
    return Number(model.max_output).toLocaleString() + " tokens";
  };

  const pricingLabel = model => {
    const p = periodForDate(model, catalog.source_verified);
    if (!p || !isTokenCalculatorModel(model)) {
      return model.pricing_status || "not-published";
    }
    return rate(p.input) + " input · " + rate(p.output) + " output " + pricingDisplayUnit(model);
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
        <div><dt>Context</dt><dd>${Number(model.context_window).toLocaleString()} tokens</dd></div>
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
      results.innerHTML = '<div class="compare-builder-error">Choose two different models.</div>';
      curatedLink.hidden = true;
      return;
    }

    const input = number(inputTokens?.value);
    const cached = number(cachedTokens?.value);
    const output = number(outputTokens?.value);
    const leftCost = modelCost(left, input, cached, output);
    const rightCost = modelCost(right, input, cached, output);

    let verdict = "";
    if (leftCost && rightCost) {
      if (Math.abs(leftCost.total - rightCost.total) < 1e-12) {
        verdict = "Direct token cost is equal for this workload.";
      } else {
        const cheaper = leftCost.total < rightCost.total ? left : right;
        const lower = Math.min(leftCost.total, rightCost.total);
        const higher = Math.max(leftCost.total, rightCost.total);
        verdict = cheaper.model + " has the lower direct token cost for this workload (" +
          money(lower) + " vs " + money(higher) + ").";
      }
    } else {
      verdict = "A direct paid-token cost winner is not shown because at least one model lacks a calculator-eligible provider Standard rate.";
    }

    results.innerHTML = `<div class="compare-builder-summary"><span>WORKLOAD RESULT</span><strong>${verdict}</strong><small>Pricing is not a quality score. Compare acceptance rate, latency and tool reliability on your own workload.</small></div>
      <div class="compare-builder-grid">${card(left, leftCost)}${card(right, rightCost)}</div>`;

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
    fetch(root.dataset.catalog || "/data/model-pricing.json", {cache: "no-cache"}).then(r => {
      if (!r.ok) throw new Error("catalog");
      return r.json();
    }),
    fetch(root.dataset.registry || "/data/model-comparisons.json", {cache: "no-cache"}).then(r => {
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
  }).catch(() => {
    results.innerHTML = '<div class="compare-builder-error">The comparison datasets could not be loaded.</div>';
  });

  [modelA, modelB, inputTokens, cachedTokens, outputTokens].forEach(node => {
    node?.addEventListener("input", render);
    node?.addEventListener("change", render);
  });
})();
