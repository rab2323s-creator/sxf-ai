/* SXF Agent Opportunity Atlas — pure, testable scenario logic.
 * Estimates are user-supplied hypotheses, not measured outcomes or deployment approval.
 */
(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.SXFAtlasCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const LIMITS = Object.freeze({
    volume: [0, 1e7], minutes: [0, 1440], hourly: [0, 1e5],
    accepted: [0, 100], review: [0, 100],
    agentCost: [0, 1e5], agentPlatform: [0, 1e8], setup: [0, 1e9],
    currentPerTask: [0, 1e5], currentPlatform: [0, 1e8], currentManual: [0, 100]
  });
  const LABELS = Object.freeze({
    agent: "Agent candidate", workflow: "Deterministic workflow",
    assist: "AI-assisted", human: "Human decision required"
  });
  function parseField(value) {
    if (typeof value === "string" && value.trim() === "") return NaN;
    if (value === null || value === undefined) return NaN;
    return Number(value);
  }
  function compareCosts(input) {
    const p = {};
    for (const [key, range] of Object.entries(LIMITS)) {
      const n = parseField(input[key]);
      if (!Number.isFinite(n) || n < range[0] || n > range[1])
        return { valid: false, error: "Enter a valid value for " + key + " (between " + range.join(" and ") + ")." };
      p[key] = n;
    }
    const taskLabor = p.minutes / 60 * p.hourly;
    const humanBaseline = p.volume * taskLabor;
    // Incumbent workflow: per-task running costs + fixed costs + fully manual exceptions.
    const currentCost = p.volume * p.currentPerTask + p.currentPlatform +
      p.volume * p.currentManual / 100 * taskLabor;
    // Proposed agent: model/tools for every attempt + fixed operations + rejected work
    // + human review of accepted tasks. Retry and rework overhead must be budgeted in agentCost.
    const accepted = p.accepted / 100;
    const agentCost = p.volume * p.agentCost + p.agentPlatform +
      p.volume * (1 - accepted) * taskLabor +
      p.volume * accepted * p.review / 100 * taskLabor;
    const monthlyDelta = currentCost - agentCost;
    const firstYearDelta = monthlyDelta * 12 - p.setup;
    let recommendation;
    if (firstYearDelta > 0 && monthlyDelta > 0)
      recommendation = "Agent scenario is cheaper on these assumptions; validate quality, safety, and real acceptance in a controlled pilot before switching.";
    else if (monthlyDelta > 0 && firstYearDelta <= 0)
      recommendation = "Agent scenario reduces monthly cost, but setup is not recovered in year one; keep the workflow until the payback and quality are validated.";
    else if (monthlyDelta < 0)
      recommendation = "Existing automation is cheaper on these assumptions. Do not replace it without verified gains in capability or quality.";
    else
      recommendation = "Neither option shows a monthly saving on these assumptions; verify business outcomes before changing systems.";
    return {
      valid: true, humanBaseline, currentCost, agentCost,
      monthlyDelta, firstYearDelta, recommendation,
      savingRate: currentCost > 0 ? monthlyDelta / currentCost : null
    };
  }
  function opportunity(input) {
    const p = {};
    for (const key of ["repeat", "risk", "errors", "access", "savings"]) {
      const n = parseField(input[key]);
      if (!Number.isFinite(n) || n < 0 || n > 5)
        return { valid: false, error: "Opportunity inputs must be between 0 and 5." };
      p[key] = n;
    }
    const score = Math.round(
      (p.repeat * 4 + p.savings * 3 + (5 - p.errors) * 4 +
       (5 - p.access) * 3 + (5 - p.risk) * 4) / 90 * 100
    );
    const humanGate = p.risk >= 4 || p.access >= 4 || p.errors >= 4;
    const category = humanGate ? "human" :
      p.repeat >= 4 && p.risk <= 2 && p.errors <= 2 && p.access <= 2 ? "workflow" : "assist";
    const explanation = category === "human"
      ? "High impact, error sensitivity, or permissions: keep consequential decisions under authorized human control."
      : category === "workflow"
      ? "Clear repeatable tasks favor deterministic automation first; use an agent only if a measured pilot proves extra value."
      : "Evaluate bounded AI assistance or an agent pilot against the existing workflow using real acceptance and cost data.";
    return { valid: true, score, category, explanation, humanGate };
  }
  function matchesCase(item, filters) {
    const search = String(filters.search || "").trim().toLocaleLowerCase("en");
    const haystack = [item.title, item.description, item.kpi, item.guardrail, item.category, item.id]
      .join(" ").toLocaleLowerCase("en");
    return (!search || haystack.includes(search)) &&
      (!filters.category || item.category === filters.category) &&
      (!filters.pattern || item.pattern === filters.pattern) &&
      (!filters.risk || item.risk === filters.risk);
  }
  return Object.freeze({ LABELS, LIMITS, parseField, compareCosts, opportunity, matchesCase });
});
