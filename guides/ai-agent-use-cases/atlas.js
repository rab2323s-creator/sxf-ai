/* Progressive enhancement: the 50 editorial cases are already in HTML.
 * Filtering, comparison, and scoring work without an API or third-party analytics. */
(function () {
  "use strict";
  const core = window.SXFAtlasCore;
  const $ = id => document.getElementById(id);
  const fmt = n => new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", maximumFractionDigits: 2
  }).format(n);
  const cards = Array.from(document.querySelectorAll("#oa-atlas .oa-case"));
  const controls = ["oa-search", "oa-category", "oa-pattern", "oa-risk"].map($);
  const count = $("oa-count");
  const empty = $("oa-empty");
  if (!core || !cards.length || !count || controls.some(x => !x)) {
    if (count) count.textContent = "All case studies are available below. Interactive tools could not start.";
    return;
  }
  const items = cards.map(node => ({
    node,
    id: node.dataset.id,
    category: node.dataset.category,
    pattern: node.dataset.pattern,
    risk: node.dataset.risk,
    title: node.querySelector("h3").textContent,
    description: node.querySelector(".oa-case-description").textContent,
    kpi: node.querySelector(".oa-case-kpi").textContent,
    guardrail: node.querySelector(".oa-case-guardrail").textContent
  }));
  const category = $("oa-category");
  [...new Set(items.map(item => item.category))].sort().forEach(name => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    category.append(option);
  });
  function readFilters() {
    return {
      search: $("oa-search").value,
      category: category.value,
      pattern: $("oa-pattern").value,
      risk: $("oa-risk").value
    };
  }
  function filterCases() {
    const filters = readFilters();
    let shown = 0;
    for (const item of items) {
      item.node.hidden = !core.matchesCase(item, filters);
      if (!item.node.hidden) shown++;
    }
    count.textContent = shown + " of " + items.length + " cases";
    empty.hidden = shown !== 0;
    $("oa-clear").hidden = !Object.values(filters).some(Boolean);
  }
  controls.forEach(control => control.addEventListener("input", filterCases));
  function clearFilters() {
    controls.forEach(control => { control.value = ""; });
    filterCases();
    $("oa-search").focus();
  }
  $("oa-clear").addEventListener("click", clearFilters);
  $("oa-reset").addEventListener("click", clearFilters);
  filterCases();

  // Case choice gives users context; it intentionally does not fabricate numeric inputs.
  $("oa-atlas").addEventListener("click", event => {
    const button = event.target.closest(".oa-evaluate");
    if (!button) return;
    const item = items.find(entry => entry.id === button.dataset.case);
    if (!item) return;
    $("oa-selected").textContent = item.title + " (" + core.LABELS[item.pattern] +
      ", " + item.risk + " risk). Enter your own company data below.";
    const target = $("framework");
    target.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth"
    });
    target.querySelector("h2").focus({ preventScroll: true });
  });

  const scoreIds = ["oa-repeat", "oa-risk-level", "oa-errors", "oa-access", "oa-savings-high"];
  const scoring = () => {
    const [repeat, risk, errors, access, savings] = scoreIds.map(id => core.parseField($(id).value));
    scoreIds.forEach(id => {
      const display = $(id + "-value");
      if (display) display.textContent = $(id).value + " / 5";
    });
    const result = core.opportunity({ repeat, risk, errors, access, savings });
    $("oa-index").textContent = result.valid ? result.score + "/100" : "—";
    $("oa-index-class").textContent = result.valid ? result.explanation : result.error;
    $("oa-index-notice").textContent = "SXF screening heuristic, not a validated prediction or permission to automate. Safety gates take precedence over this score.";
  };
  scoreIds.forEach(id => $(id).addEventListener("input", scoring));
  scoring();

  const fieldIds = {
    volume: "oa-volume", minutes: "oa-minutes", hourly: "oa-hourly",
    accepted: "oa-accept", review: "oa-review", agentCost: "oa-agent",
    agentPlatform: "oa-platform", setup: "oa-setup",
    currentPerTask: "oa-current-task", currentPlatform: "oa-current-platform",
    currentManual: "oa-current-manual"
  };
  const outputIds = ["oa-baseline", "oa-current", "oa-monthly", "oa-savings", "oa-year"];
  function calculate() {
    const input = Object.fromEntries(Object.entries(fieldIds).map(
      ([key, id]) => [key, core.parseField($(id).value)]
    ));
    const outcome = core.compareCosts(input);
    const validation = $("oa-validation");
    validation.hidden = outcome.valid;
    if (!outcome.valid) {
      validation.textContent = outcome.error;
      outputIds.forEach(id => { $(id).textContent = "—"; });
      $("oa-recommendation").textContent = "Complete all inputs to compare the two approaches.";
      $("oa-note").textContent = "No results are displayed for invalid inputs.";
      return;
    }
    validation.textContent = "";
    $("oa-baseline").textContent = fmt(outcome.humanBaseline);
    $("oa-current").textContent = fmt(outcome.currentCost);
    $("oa-monthly").textContent = fmt(outcome.agentCost);
    $("oa-savings").textContent = fmt(outcome.monthlyDelta);
    $("oa-year").textContent = fmt(outcome.firstYearDelta);
    $("oa-recommendation").textContent = outcome.recommendation;
    $("oa-note").textContent = "Hypothetical USD scenario. Monthly difference = current workflow minus proposed agent. Year one subtracts setup. " +
      "Model per-task costs must include retries. Excludes error losses, taxes, downtime, rework, migration and opportunity cost. " +
      "Validate acceptance and exceptions using actual data before acting.";
  }
  Object.values(fieldIds).forEach(id => $(id).addEventListener("input", calculate));
  calculate();
})();
