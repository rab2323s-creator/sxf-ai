"use strict";

// Reproducible deterministic sensitivity experiment, NOT an agent deployment benchmark.
// Reuses the same economic model used by the interactive article.
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const {compute} = require("../guides/ai-agent-cost/study.js");

const ROOT = path.resolve(__dirname, "..");
const STUDY = "data/enterprise-agent-economics-assumptions.json";
const CATALOG = "data/model-pricing.json";
const SNAPSHOT = "data/agent-economics-stress-test.json";
const ARTICLE = "guides/ai-agent-cost/index.html";
const START = "<!-- SXF:STRESS_TEST_TABLE_START -->";
const END = "<!-- SXF:STRESS_TEST_TABLE_END -->";
const DELTAS = [-0.10, -0.05, 0, 0.05, 0.10];
const FACTORS = [
  "accepted_success_rate",
  "human_review_fraction",
  "value_realization_fraction"
];

function readJSON(rel) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, rel), "utf8"));
}
function rounded(value, digits = 1) {
  if (!Number.isFinite(value)) throw new Error("Non-finite output");
  return Number(value.toFixed(digits));
}
function clamp(x) { return Math.max(0, Math.min(1, x)); }
function modelRate(model, date) {
  assert.equal(model.pricing_status, "official-paid");
  assert.equal(model.pricing_basis.quantity, 1000000);
  const matches = model.pricing.standard.filter(row =>
    row.start <= date && (!row.end || date <= row.end)
  );
  assert.equal(matches.length, 1, "Expected exactly one effective Standard price");
  return matches[0];
}
function calculateCase(c, rate) {
  const baseline = compute(c, rate);
  const values = [];
  for (const successDelta of DELTAS) {
    for (const reviewDelta of DELTAS) {
      for (const realizationDelta of DELTAS) {
        const outcome = compute(c, rate, {
          accepted_success_rate: clamp(c.accepted_success_rate + successDelta),
          human_review_fraction: clamp(c.human_review_fraction + reviewDelta),
          value_realization_fraction: clamp(c.value_realization_fraction + realizationDelta)
        });
        values.push(outcome.roi);
      }
    }
  }
  values.sort((a, b) => a - b);
  assert.equal(values.length, 125);
  const oneFactor = {};
  for (const field of FACTORS) {
    oneFactor[field] = {
      minus_10pp_roi: rounded(compute(c, rate, {[field]: clamp(c[field] - 0.10)}).roi),
      plus_10pp_roi: rounded(compute(c, rate, {[field]: clamp(c[field] + 0.10)}).roi)
    };
  }
  const half = compute(c, rate, {monthly_tasks: c.monthly_tasks / 2});
  const double = compute(c, rate, {monthly_tasks: c.monthly_tasks * 2});
  return {
    id: c.id,
    name: c.name,
    model_id: c.model_id,
    base_roi_pct: rounded(baseline.roi),
    base_cost_per_accepted_usd: rounded(baseline.costPerAccepted, 2),
    grid: {
      combinations: values.length,
      minimum_roi_pct: rounded(values[0]),
      median_roi_pct: rounded(values[62]),
      maximum_roi_pct: rounded(values[124]),
      nonnegative_combinations: values.filter(n => n >= 0).length
    },
    one_factor_10_percentage_points: oneFactor,
    volume: {
      half_base_tasks_roi_pct: rounded(half.roi),
      double_base_tasks_roi_pct: rounded(double.roi)
    }
  };
}
function buildReport() {
  const study = readJSON(STUDY);
  const catalog = readJSON(CATALOG);
  assert.ok(study.date && Array.isArray(study.cases));
  const models = new Map(catalog.models.map(m => [m.model_id, m]));
  const cases = study.cases.map(c => {
    const m = models.get(c.model_id);
    assert.ok(m, "Missing model " + c.model_id);
    return calculateCase(c, modelRate(m, study.date));
  });
  return {
    schema_version: "1.0",
    study_id: study.study_id,
    study_as_of: study.date,
    evidence_class: "Deterministic hypothetical sensitivity analysis; not measured model accuracy, observed outcomes, deployment ROI, forecast or probability",
    protocol: {
      variables: FACTORS,
      deltas_absolute_percentage_points: [-10, -5, 0, 5, 10],
      clamp_fraction_to: [0, 1],
      combinations_per_case: 125,
      interpretation: "All grid combinations are equally enumerated, NOT sampled from a measured probability distribution.",
      volume_scenarios: [0.5, 2],
      volume_assumption: "Per-task usage scales linearly; implementation and monthly fixed costs remain unchanged.",
      prices: "Historical Standard text input/output rates effective on study_as_of; assumes no prompt caching or extra vendor tiers."
    },
    cases
  };
}
function pct(n) {
  return (n >= 0 ? "+" : "") + n.toFixed(1) + "%";
}
function escapeHtml(s) {
  return String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}
function renderTable(report) {
  const lines = [
    '<div class="econ-table-scroll"><table class="econ-table"><thead><tr><th>Workflow</th><th data-numeric>Base ROI</th><th data-numeric>125-case ROI range</th><th data-numeric>Grid cases at or above 0% ROI</th><th data-numeric>Half / double workload ROI</th></tr></thead><tbody>'
  ];
  for (const c of report.cases) {
    lines.push(
      '<tr><td>' + escapeHtml(c.name) + '</td><td data-numeric>' + pct(c.base_roi_pct) +
      '</td><td data-numeric>' + pct(c.grid.minimum_roi_pct) + ' to ' + pct(c.grid.maximum_roi_pct) +
      '</td><td data-numeric>' + c.grid.nonnegative_combinations + ' / ' + c.grid.combinations +
      '</td><td data-numeric>' + pct(c.volume.half_base_tasks_roi_pct) + ' / ' +
      pct(c.volume.double_base_tasks_roi_pct) + '</td></tr>'
    );
  }
  lines.push("</tbody></table></div>");
  return lines.join("\n");
}
function updateArticle(table, write) {
  const filepath = path.join(ROOT, ARTICLE);
  const source = fs.readFileSync(filepath, "utf8");
  assert.equal(source.split(START).length, 2, "Missing/duplicated START marker");
  assert.equal(source.split(END).length, 2, "Missing/duplicated END marker");
  const begin = source.indexOf(START) + START.length;
  const end = source.indexOf(END, begin);
  const actual = source.slice(begin, end).trim();
  if (write) {
    const result = source.slice(0, begin) + "\n" + table + "\n" + source.slice(end);
    if (result !== source) fs.writeFileSync(filepath, result, "utf8");
  } else {
    assert.equal(actual, table, "Article table has drifted: run node scripts/agent_economics_stress_test.cjs --write");
  }
}
function main() {
  const args = process.argv.slice(2);
  assert.ok(args.length <= 1 && (!args.length || ["--check", "--write"].includes(args[0])));
  const report = buildReport();
  const snapshotText = JSON.stringify(report, null, 2) + "\n";
  const snapshotPath = path.join(ROOT, SNAPSHOT);
  if (args[0] === "--write") {
    fs.writeFileSync(snapshotPath, snapshotText, "utf8");
    updateArticle(renderTable(report), true);
    console.log("Generated deterministic sensitivity snapshot and article table.");
  } else if (args[0] === "--check") {
    assert.equal(fs.readFileSync(snapshotPath, "utf8"), snapshotText, "Snapshot drift: run generator --write");
    updateArticle(renderTable(report), false);
    console.log("PASS: 3 cases, 375 reproducible sensitivity combinations, snapshot + article parity.");
  } else {
    process.stdout.write(snapshotText);
  }
}
if (require.main === module) main();
module.exports = {buildReport, renderTable};
