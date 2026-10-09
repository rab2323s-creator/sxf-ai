"use strict";
const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
const html=fs.readFileSync("ai-agent-cost/index.html","utf8");
const source=fs.readFileSync("ai-agent-cost/index.js","utf8");
const pricing=fs.readFileSync("assets/pricing-policy.js","utf8");
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
assert.equal(new Set(ids).size,ids.length,"Duplicate HTML IDs");
class Element {
  constructor(tag){this.tagName=tag;this.children=[];this.handlers={};this.dataset={};this.style={};this._value="";Object.defineProperty(this,"value",{get:()=>this._value,set:v=>{this._value=String(v)}});this.textContent="";this.disabled=false;this.hidden=false;this.checked=false;this.min="";this.max="";}
  addEventListener(k,fn){(this.handlers[k]??=[]).push(fn)}
  trigger(k){(this.handlers[k]||[]).forEach(fn=>fn({target:this}))}
  appendChild(el){this.children.push(el);return el}
  append(...nodes){this.children.push(...nodes)}
  replaceChildren(...nodes){this.children=nodes}
  setAttribute(k,v){this[k]=v}
  querySelector(){return this.statusText||(this.statusText=new Element("span"))}
  closest(){return {textContent:"test input"}}
  scrollIntoView(){}
  remove(){}
}
const els=Object.fromEntries(ids.map(id=>[id,new Element("div")]));
for(const match of html.matchAll(/<input\b[^>]*>/gi)){
  const tag=match[0],id=tag.match(/\bid="([^"]+)"/)?.[1];if(!id||!els[id])continue;
  for(const attr of ["value","min","max"]){const v=tag.match(new RegExp("\\b"+attr+'="([^"]*)"'));if(v)els[id][attr]=v[1]}
}
const presets=Object.fromEntries(["support","documents","research"].map(k=>{const e=new Element("button");e.dataset.preset=k;return [k,e]}));
const doc={
  getElementById:id=>els[id]||null,
  querySelector:()=>presets.support,
  querySelectorAll:()=>Object.values(presets),
  createElement:tag=>new Element(tag),
  createTextNode:text=>({textContent:text}),
  body:new Element("body")
};
const catalog={source_verified:"2026-10-09",models:[
 {provider:"OpenAI",model:"Test Agent",model_id:"gpt-6-sol",pricing_status:"official-paid",calculator_eligible:true,pricing_basis:{meter:"tokens",quantity:1000000},pricing:{standard:[{start:"2026-01-01",end:null,input:2,cached_input:0.2,output:10}]},provenance:{verified_at:"2026-09-27",evidence:{pricing:"https://example.com/pricing"}},capabilities:["agents"]},
 {provider:"Anthropic",model:"No Cached Rate",model_id:"other",pricing_status:"official-paid",calculator_eligible:true,pricing_basis:{meter:"tokens",quantity:1000000},pricing:{standard:[{start:"2026-01-01",end:null,input:1,output:5}]},provenance:{verified_at:"2026-09-27",evidence:{pricing:"https://example.com/pricing"}},capabilities:[]},
 {provider:"X",model:"Unavailable",model_id:"unavailable",pricing_status:"not-published",calculator_eligible:false,pricing_basis:{meter:"tokens",quantity:1000000},pricing:{standard:[]},provenance:{verified_at:"2026-09-27"},capabilities:[]}
]};
const window={};
vm.runInNewContext(pricing,{window,console});
const context={document:doc,window,fetch:async()=>({ok:true,json:async()=>catalog}),setTimeout:()=>{},navigator:{clipboard:{writeText:async()=>{}}},console};
vm.runInNewContext(source,context);
const val=id=>Number(String(els[id].textContent).replace(/[$,%]/g,""));
function approximately(actual,expected){assert.ok(Math.abs(actual-expected)<0.051,actual+" not close to "+expected)}
async function run(){
 for(let i=0;i<5;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.equal(els.statModels.textContent,"3");
 assert.equal(els.statEligible.textContent,"2");
 assert.equal(els.calcModel.value,"gpt-6-sol");
 const total=198+44+1750+1400; // 1500 reviews × 2 minutes × $35/hour
 approximately(val("totalCost"),total);
 approximately(val("costPerSuccess"),total/8500);
 approximately(val("costPerTask"),total/10000);
 approximately(val("roiPercent"),(8500*1.8/total-1)*100);
 els.cachePercent.value="50";els.cachePercent.trigger("input");
 approximately(val("apiMonthly"),158.4);
 els.successRate.value="0";els.successRate.trigger("input");
 assert.equal(els.costPerSuccess.textContent,"N/A");
 approximately(val("roiPercent"),-100);
 els.monthlyTasks.value="-1";els.monthlyTasks.trigger("input");
 assert.equal(els.calcWarning.hidden,false);
 assert.equal(els.totalCost.textContent,"—");
 els.monthlyTasks.value="10000";els.successRate.value="85";
 els.calcModel.value="other";els.calcModel.trigger("change");
 approximately(val("apiMonthly"),99);
 for(const id of ["inputTokens","outputTokens","toolCost","infraCost","opsCost","buildCost","reviewPercent","valuePerSuccess"])els[id].value="0";
 els.valuePerSuccess.trigger("input");
 assert.equal(els.totalCost.textContent,"$0.00");
 assert.equal(els.roiPercent.textContent,"N/A");
 presets.documents.trigger("click");
 assert.equal(els.monthlyTasks.value,"2500");
 assert.ok(val("totalCost")>0);
 console.log("PASS: Catalog loading, eligible-rate filters, cost arithmetic, cached inputs, zero success, invalid input, no-cache fallback, zero-cost handling, and presets.");
}
run().catch(err=>{console.error(err);process.exitCode=1});
