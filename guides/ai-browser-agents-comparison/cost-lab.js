/* SXF controlled browser task economics: hypothetical values, not observed provider benchmarks. */
(function(){
"use strict";
function estimate(v){
const attempts=v.tasks*(1+v.retries/100);
const model=attempts*v.model;
const infra=attempts*(v.minutes/60*v.hourly+v.proxy);
const human=v.tasks*v.humanMinutes/60*v.wage;
const total=v.subscription+model+infra+human;
const success=v.tasks*v.success/100;
return {attempts:attempts,model:model,infra:infra,human:human,total:total,success:success,
perSuccess:success>0?total/success:NaN,perAttempt:attempts>0?total/attempts:NaN,
lost:total-(success*(v.model+v.minutes/60*v.hourly+v.proxy))};
}
if(typeof module!=="undefined"&&module.exports)module.exports={estimate:estimate};
if(typeof document==="undefined")return;
const fields={tasks:"ba-tasks",success:"ba-success",retries:"ba-retries",model:"ba-model",minutes:"ba-minutes",hourly:"ba-hourly",proxy:"ba-proxy",subscription:"ba-subscription",humanMinutes:"ba-human",wage:"ba-wage"};
const nodes={};for(const k of Object.keys(fields))nodes[k]=document.getElementById(fields[k]);
if(Object.values(nodes).some(x=>!x))return;
const form=document.getElementById("ba-calculator"),status=document.getElementById("ba-lab-status");
const out={attempts:"ba-out-attempts",success:"ba-out-success",model:"ba-out-model",infra:"ba-out-infra",human:"ba-out-human",total:"ba-out-total",perSuccess:"ba-out-success-cost"};
const outputs={};for(const k of Object.keys(out))outputs[k]=document.getElementById(out[k]);
const dollars=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2});
const n=new Intl.NumberFormat("en-US",{maximumFractionDigits:1});
function draw(){
const v={};for(const k of Object.keys(nodes)){
const el=nodes[k],value=Number(el.value);
if(el.value.trim()===""||!Number.isFinite(value)||value<Number(el.min)||value>Number(el.max)){
status.textContent="Enter a valid value within every displayed range.";return;
}v[k]=value;
}
const result=estimate(v);
for(const key of Object.keys(outputs)){
const val=result[key];
outputs[key].textContent=key==="attempts"||key==="success"?n.format(val):(Number.isFinite(val)?dollars.format(val):"No completed tasks");
}
status.textContent="Hypothetical scenario updated. Subscription, model, browser, proxy and review inputs are user-defined—not vendor quotations.";
}
form.addEventListener("input",draw);form.addEventListener("submit",e=>{e.preventDefault();draw()});draw();
})();