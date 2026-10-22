"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const core = require("../guides/ai-agent-use-cases/atlas-core.js");
const base = path.join(__dirname, "../guides/ai-agent-use-cases");
const cases = JSON.parse(fs.readFileSync(path.join(base, "atlas.json"), "utf8")).cases;
const html = fs.readFileSync(path.join(base, "index.html"), "utf8");
const js = fs.readFileSync(path.join(base, "atlas.js"), "utf8");
assert.equal(cases.length, 50);
assert.equal(new Set(cases.map(c => c.id)).size, 50);
for (const c of cases) {
  assert.ok(["agent", "assist", "workflow", "human"].includes(c.pattern));
  assert.ok(["low", "medium", "high"].includes(c.risk));
  assert.ok(html.includes('data-id="' + c.id + '"'), "HTML should serve " + c.id);
}
assert.equal((html.match(/class="oa-case"/g) || []).length, cases.length);
assert.ok(html.includes("atlas-core.js"));
assert.ok(html.includes('id="oa-current"'));
assert.ok(html.includes('id="oa-validation"'));
assert.ok(js.includes("core.compareCosts"));
assert.ok(html.includes("<h3>AI Agent Examples: turn a scenario into a decision</h3>"));
assert.ok(html.includes("Use these AI Agent Examples to find a task like yours"));
for (const link of ["/models/pricing/", "/compare/", "/guides/ai-agent-evaluation-checklist/"]) {
  assert.ok(html.includes('<a href="' + link + '">'), "Missing contextual SXF internal link: " + link);
}

assert.equal(core.matchesCase(cases[0], {search: "SUPPORT",category: "",pattern: "",risk: ""}), true);
assert.equal(core.matchesCase(cases[0], {search: "missing_keyword_785",category: "",pattern: "",risk: ""}), false);
assert.equal(core.parseField(""), NaN); // NaN is equal using Object.is in strictEqual
const input = {
  volume: 3000, minutes: 8, hourly: 35, accepted: 70,
  review: 20, agentCost: .12, agentPlatform: 300, setup: 3500,
  currentPerTask: .02, currentPlatform: 250, currentManual: 40
};
const result = core.compareCosts(input);
assert.equal(result.valid, true);
assert.equal(result.humanBaseline, 14000);
assert.equal(result.currentCost, 5910);
assert.equal(Math.round(result.agentCost), 6820);
assert.equal(Math.round(result.monthlyDelta), -910);
assert.equal(core.compareCosts({...input, volume: ""}).valid, false);
assert.equal(core.compareCosts({...input, accepted: 101}).valid, false);
assert.equal(core.compareCosts({...input, currentManual: -1}).valid, false);
assert.equal(core.compareCosts({...input, platform: Infinity}).valid, true); // unknown keys ignored
assert.equal(core.opportunity({repeat:5,risk:4,errors:0,access:0,savings:5}).humanGate, true);
assert.equal(core.opportunity({repeat:5,risk:1,errors:1,access:1,savings:3}).category, "workflow");
assert.equal(core.opportunity({repeat:5,risk:6,errors:1,access:1,savings:3}).valid, false);
console.log("SXF Atlas: data, static catalog, classification and financial regression checks passed.");
