/* SXF Compare decision engine.
 * Pure shared calculations; no global winners or inferred benchmark scores.
 * Both the browser and Node tests use this implementation.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.SxfCompareEngine = api;
})(typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : null), function () {
  "use strict";
  const MAX_TOKENS = 10000000;
  const MAX_REQUESTS = 100000000;

  function integer(value, max, allowZero) {
    if (value === "" || value == null || typeof value === "boolean") return null;
    const n = Number(value);
    return Number.isSafeInteger(n) && n >= (allowZero ? 0 : 1) && n <= max ? n : null;
  }

  function workload(fields) {
    const input = integer(fields.input, MAX_TOKENS, true);
    const cached = integer(fields.cached, MAX_TOKENS, true);
    const output = integer(fields.output, MAX_TOKENS, true);
    const requests = integer(fields.requests, MAX_REQUESTS, false);
    if ([input, cached, output, requests].some(v => v === null)) {
      return {ok: false, error: "Enter whole, non-negative token counts (up to 10 million each) and 1–100 million monthly requests."};
    }
    if (input + cached > MAX_TOKENS) return {ok: false, error: "Total input tokens cannot exceed 10 million per request."};
    if (input + cached + output === 0) return {ok: false, error: "Add at least one input or output token."};
    return {ok: true, input, cached, output, requests};
  }

  function activePeriod(model, date) {
    if (!date || !model || !Array.isArray(model.pricing?.standard)) return null;
    const policy = typeof window !== "undefined"
      ? window.SXFPricing
      : (typeof module === "object" && module.exports ? require("../assets/pricing-policy.js") : null);
    if (!policy) throw new Error("Shared SXF pricing policy is not loaded");
    return policy.periodForDate(model, date);
  }

  function validRate(n) {
    return typeof n === "number" && Number.isFinite(n) && n >= 0;
  }

  function pricing(model, task, date) {
    if (!task?.ok || !model || model.pricing_basis?.meter !== "tokens" ||
        model.pricing_status !== "official-paid" || model.calculator_eligible !== true) {
      return {available: false, reason: "No directly comparable official Standard token pricing."};
    }
    const period = activePeriod(model, date);
    if (!period) return {available: false, reason: "No applicable verified Standard price period."};
    if ((task.input && !validRate(period.input)) ||
        (task.cached && !validRate(period.cached_input)) ||
        (task.output && !validRate(period.output))) {
      return {available: false, reason: "A required token rate is unpublished; no substitute rate is assumed."};
    }
    const unit = Number(model.pricing_basis.quantity);
    if (!Number.isFinite(unit) || unit <= 0) return {available: false, reason: "Invalid pricing unit."};

    const threshold = Number(model.pricing?.long_context?.threshold_input_tokens);
    const rule = model.pricing?.long_context;
    const long = Number.isFinite(threshold) && threshold > 0 && task.input + task.cached > threshold;
    const factor = field => long && validRate(rule?.multipliers?.[field]) ? rule.multipliers[field] : 1;
    const inputCost = (task.input / unit) * (period.input || 0) * factor("input");
    const cachedCost = (task.cached / unit) * (period.cached_input || 0) * factor("cached_input");
    const outputCost = (task.output / unit) * (period.output || 0) * factor("output");
    const total = inputCost + cachedCost + outputCost;
    if (!Number.isFinite(total)) return {available: false, reason: "Unable to compute this workload safely."};
    return {available: true, total, monthly: total * task.requests, long,
      breakdown: {input: inputCost, cached: cachedCost, output: outputCost},
      notes: long ? "Long-context multipliers applied from the published catalog." : "Standard rates applied."};
  }

  function capacityWarnings(model, task) {
    if (!task?.ok || !model) return [];
    const warnings = [];
    const context = Number(model.context_window);
    if (model.context_window != null && Number.isFinite(context) && context > 0 &&
        task.input + task.cached > context)
      warnings.push("Input exceeds the model's published context window.");
    const output = Number(model.max_output);
    if (model.max_output != null && model.max_output !== "unlimited" &&
        Number.isFinite(output) && output > 0 && task.output > output)
      warnings.push("Output exceeds the model's published output limit.");
    return warnings;
  }

  function benchmarkPairs(data, left, right) {
    if (!Array.isArray(data?.benchmarks) || !Array.isArray(data?.observations)) return [];
    const benchmarks = new Map(data.benchmarks.map(x => [x.benchmark_id, x]));
    const observations = data.observations.filter(x =>
      (x.model_id === left || x.model_id === right) && x.evidence_type === "independent" &&
      typeof x.benchmark_id === "string" && typeof x.comparable_group === "string" &&
      validRate(x.score) && typeof x.source_url === "string" && /^https:\/\//.test(x.source_url));
    const result = [];
    const seen = new Set();
    for (const first of observations.filter(x => x.model_id === left)) {
      const key = first.benchmark_id + "|" + first.comparable_group;
      if (seen.has(key)) continue;
      const counterpart = observations.find(x => x.model_id === right &&
        x.benchmark_id === first.benchmark_id && x.comparable_group === first.comparable_group);
      const b = benchmarks.get(first.benchmark_id);
      if (!counterpart || !b) continue;
      seen.add(key);
      result.push({benchmark: b, left: first, right: counterpart,
        configurationDiffers: JSON.stringify(first.model_configuration || {}) !==
          JSON.stringify(counterpart.model_configuration || {})});
    }
    return result;
  }

  function fit(model, required) {
    const capabilities = Array.isArray(model?.capabilities) ? model.capabilities : [];
    const listed = required.filter(x => capabilities.includes(x));
    return {listed, missing: required.filter(x => !capabilities.includes(x))};
  }

  return {integer, workload, activePeriod, pricing, capacityWarnings, benchmarkPairs, fit};
});
