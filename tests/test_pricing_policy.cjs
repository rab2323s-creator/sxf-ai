const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("assets/pricing-policy.js", "utf8");
const context = {window: {}, Date};
vm.runInNewContext(source, context, {filename: "assets/pricing-policy.js"});
const {periodForDate, effectiveRates, utcToday} = context.window.SXFPricing;
const fixture = {model_id:"gemini-test", pricing:{standard:[
  {start:"2026-08-13",end:"2026-12-31",input:0.75,cached_input:0.075,output:3.75},
  {start:"2027-01-01",end:null,input:1.5,cached_input:0.15,output:7.5}
]}};
for (const d of ["2026-08-13","2026-10-09","2026-12-31"]) {
  assert.equal(periodForDate(fixture,d).input,0.75);
  assert.equal(periodForDate(fixture,d).output,3.75);
}
assert.equal(periodForDate(fixture,"2027-01-01").input,1.5);
assert.equal(periodForDate(fixture,"2027-01-01").output,7.5);
assert.equal(periodForDate(fixture,"2026-08-12"),null);
assert.equal(effectiveRates(fixture,"2026-10-09",100000).rates.cached_input,0.075);
const missing={model_id:"missing",pricing:{standard:[]}};
assert.equal(periodForDate(missing,"2026-10-09"),null);
assert.throws(()=>periodForDate(fixture,"9/10/2026"),/date/);
const overlapping={model_id:"overlap",pricing:{standard:[
 {start:"2026-01-01",end:"2026-12-31",input:1,output:1},
 {start:"2026-12-31",end:null,input:2,output:2}
]}};
assert.throws(()=>periodForDate(overlapping,"2026-12-31"),/Overlapping/);
const catalog=JSON.parse(fs.readFileSync("data/model-pricing.json","utf8"));
assert.equal(catalog.currency,"USD");
const gemini=catalog.models.find(m=>m.model_id==="gemini-3.7-flash");
assert.ok(gemini);
for(const date of ["2026-10-09","2026-12-31","2027-01-01"]) {
 const a=periodForDate(gemini,date), b=periodForDate(fixture,date);
 assert.equal(a.input,b.input);
 assert.equal(a.output,b.output);
 assert.equal(a.cached_input,b.cached_input);
}
for (const js of ["models/pricing/pricing.js","tools/ai-model-cost-calculator/calculator.js","compare/compare.js"]) {
 const content=fs.readFileSync(js,"utf8");
 assert.match(content,/window\.SXFPricing/);
 assert.doesNotMatch(content,/const periodForDate\s*=/);
 assert.match(content,/\{cache:\s*"no-store"\}/);
}
for (const page of ["compare/index.html","models/pricing/index.html","tools/ai-model-cost-calculator/index.html"]) {
 const html=fs.readFileSync(page,"utf8");
 assert.match(html,/\/assets\/pricing-policy\.js\?v=20261009/);
}
console.log("PASS: shared browser date selection, overlap/gap boundaries, Gemini schedule, and cache policy");
