"use strict";
const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const path=require("node:path");
const read=p=>fs.readFileSync(path.join(process.cwd(),p),"utf8");
const cases=JSON.parse(read("data/enterprise-agent-economics-assumptions.json"));
const prices=JSON.parse(read("data/model-pricing.json"));
const page=read("guides/ai-agent-cost/index.html");
const js=read("guides/ai-agent-cost/study.js");
const shell={module:{exports:{}},console};
vm.runInNewContext(js,shell,{filename:"study.js"});
const compute=shell.module.exports.compute;
const near=(a,b,epsilon=0.02)=>assert.ok(Math.abs(a-b)<epsilon,`Expected ${b}, got ${a}`);
assert.equal(cases.cases.length,3);
assert.equal(prices.source_verified,"2026-10-09");
const expected={
  support:{api:16.8,tools:134.4,human:4900,recurring:8701.2,firstYear:122414.4,successes:8200,captured:18655,net:101445.6,roi:82.9,costPerAccepted:1.24},
  documents:{api:271.872,tools:158.592,human:5289.6,recurring:10190.064,firstYear:164280.768,successes:2160,captured:13305.6,net:-4613.568,roi:-2.8,costPerAccepted:6.34},
  research:{api:280,tools:280,human:8493.333333333334,recurring:15053.333333333334,firstYear:240640,successes:576,captured:12480,net:-90880,roi:-37.8,costPerAccepted:34.81}
};
for(const c of cases.cases){
  const m=prices.models.find(x=>x.model_id===c.model_id);
  assert.ok(m,"Missing model "+c.model_id);
  assert.equal(m.pricing_status,"official-paid");
  assert.equal(m.pricing_basis.quantity,1000000);
  const today="2026-10-10";
  const rate=m.pricing.standard.find(x=>x.start<=today&&(!x.end||today<=x.end));
  assert.ok(rate,"No applicable Standard rate for "+c.model_id);
  const out=compute(c,rate);
  for(const [key,val] of Object.entries(expected[c.id]))near(out[key],val,key==="roi"?0.06:0.02);
  assert.ok(out.costPerAccepted>0);
  assert.ok(out.costPerAttempt<=out.costPerAccepted);
  assert.ok(out.firstYear>=out.recurring*12);
  assert.equal(out.successes,c.monthly_tasks*c.accepted_success_rate);
  let zero=compute(c,rate,{accepted_success_rate:0});
  assert.equal(zero.costPerAccepted,null);
  assert.equal(zero.captured,0);
  let review=compute(c,rate,{human_review_fraction:1});
  assert.ok(review.human>=out.human);
  let acceptance=compute(c,rate,{accepted_success_rate:1});
  assert.ok(acceptance.costPerAccepted<=out.costPerAccepted);
  let disabled=compute(c,rate,{value_realization_fraction:0});
  assert.equal(disabled.captured,0);
  assert.ok(disabled.roi<=-99.99);
  assert.throws(()=>compute(c,rate,{accepted_success_rate:1.5}),/Invalid fraction/);
}
const ids=[...page.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
assert.equal(ids.length,new Set(ids).size,"Duplicate IDs");
assert.equal((page.match(/<h1\b/g)||[]).length,1,"One H1");
assert.ok(page.includes('<title>AI Agent Cost in 2026: Enterprise TCO, Reliability &amp; ROI Analysis | SXF / AI</title>')||page.includes('<title>AI Agent Cost in 2026: Enterprise TCO, Reliability & ROI Analysis | SXF / AI</title>'));
assert.ok(page.includes('<link rel="canonical" href="https://sxf.si/guides/ai-agent-cost/">'));
assert.ok(page.includes('href="/ai-agent-cost/"'));
assert.ok(page.includes("study.css")&&page.includes("study.js"));
assert.ok(page.includes("This is an independent, fully specified"));
assert.ok(read("scripts/update_news.py").includes('"href": "/guides/ai-agent-cost/"'));
assert.ok(read("scripts/sitemap_generation.py").includes('sitemap_entry(f"{BASE_URL}/guides/ai-agent-cost/"'));
assert.ok(read("sitemap.xml").includes("<loc>https://sxf.si/guides/ai-agent-cost/</loc>"));
console.log("PASS: Scenario arithmetic, catalogue rates, financial boundaries, edge cases, page SEO and durable generator.");
