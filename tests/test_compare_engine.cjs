"use strict";
const assert = require("node:assert/strict");
const E = require("../compare/decision-engine.js");
function t(input=2000,cached=0,output=600,requests=1000){
  return E.workload({input,cached,output,requests});
}
function model(){
  return {model_id:"a",pricing_status:"official-paid",calculator_eligible:true,
    pricing_basis:{meter:"tokens",quantity:1000000},
    context_window:1000000,max_output:128000,
    pricing:{standard:[{start:"2026-01-01",end:null,input:2,cached_input:.2,output:10}],
      long_context:{threshold_input_tokens:272000,multipliers:{input:2,cached_input:2,output:1.5}}}};
}
assert.equal(t().ok,true);
assert.equal(t("",0,0).ok,false);
assert.equal(t(-1,0,100).ok,false);
assert.equal(t("abc",0,100).ok,false);
assert.equal(t(1.2,0,0).ok,false);
assert.equal(t(0,0,0).ok,false);
assert.equal(t(0,0,100,0).ok,false);
assert.equal(t(0,0,100,"Infinity").ok,false);
assert.equal(t(10000001,0,2).ok,false);
assert.equal(t(9000000,2000000,2).ok,false);
const p=E.pricing(model(),t(), "2026-10-08");
assert.equal(p.available,true);
assert.ok(Math.abs(p.total-(2000*2+600*10)/1e6)<1e-10);
assert.ok(Math.abs(p.monthly-10)<1e-10);
const cache=E.pricing(model(),t(0,1000,0),"2026-10-08");
assert.ok(Math.abs(cache.total-.0002)<1e-12);
let noCache=model();delete noCache.pricing.standard[0].cached_input;
assert.equal(E.pricing(noCache,t(0,1000,0),"2026-10-08").available,false);
assert.equal(E.pricing(model(),t(),"2025-01-01").available,false);
let tooLong=model();tooLong.context_window=100;
assert.equal(E.capacityWarnings(tooLong,t()).length,1);
const long=E.pricing(model(),t(280000,0,1000),"2026-10-08");
assert.equal(long.long,true);
assert.ok(Math.abs(long.total-(280000*4+1000*15)/1e6)<1e-10);
const edge=E.pricing(model(),t(272000,0,1000),"2026-10-08");
assert.equal(edge.long,false);
const b={benchmarks:[{benchmark_id:"one",name:"Test",version:"1"}],observations:[
  {model_id:"a",benchmark_id:"one",comparable_group:"group1",evidence_type:"independent",score:20,source_url:"https://example.com/a",model_configuration:{reasoning_effort:"high"}},
  {model_id:"b",benchmark_id:"one",comparable_group:"group1",evidence_type:"independent",score:30,source_url:"https://example.com/b",model_configuration:{reasoning_effort:"max"}},
  {model_id:"b",benchmark_id:"one",comparable_group:"different",evidence_type:"independent",score:99,source_url:"https://example.com/c"}]};
assert.equal(E.benchmarkPairs(b,"a","b").length,1);
assert.equal(E.benchmarkPairs(b,"a","b")[0].configurationDiffers,true);
b.observations[1].comparable_group="another";
assert.equal(E.benchmarkPairs(b,"a","b").length,0);
console.log("PASS: 17 workload, pricing, limits and evidence regression assertions");
