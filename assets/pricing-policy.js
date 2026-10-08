/* SXF Standard API pricing: date-policy implementation for browser consumers.
   Source of amounts: /data/model-pricing.json. Dates are inclusive UTC calendar days.
   Keep parity with scripts/update_news.py:active_standard_price; tested in CI. */
(function (root) {
  "use strict";
  const utcToday = () => new Date().toISOString().slice(0, 10);
  const isoDate = value => typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
  const periodForDate = (model, date) => {
    if (!isoDate(date)) throw new Error("Effective pricing date must be YYYY-MM-DD");
    const ordered = [...(model?.pricing?.standard || [])].sort((a, b) => a.start.localeCompare(b.start));
    let previousEnd = null;
    ordered.forEach((period, index) => {
      if (!isoDate(period.start) || (period.end != null && !isoDate(period.end))) {
        throw new Error("Malformed pricing period for " + (model?.model_id || "unknown"));
      }
      if (period.end != null && period.end < period.start) {
        throw new Error("Reversed pricing period for " + (model?.model_id || "unknown"));
      }
      if (index && (previousEnd === null || period.start <= previousEnd)) {
        throw new Error("Overlapping pricing periods for " + (model?.model_id || "unknown"));
      }
      previousEnd = period.end ?? null;
    });
    return ordered.find(period => date >= period.start && (!period.end || date <= period.end)) || null;
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
  root.SXFPricing = Object.freeze({utcToday, periodForDate, effectiveRates});
})(window);
