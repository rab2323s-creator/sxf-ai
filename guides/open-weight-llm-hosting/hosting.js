/* SXF / AI LLM Hosting Cost Frontier: transparent hypothetical economics, never live vendor measurement. */
(function(){
"use strict";
function estimate(v){
const requests=v.requests,accepted=requests*v.accept/100;
const token=requests*(v.input*v.inputRate+v.output*v.outputRate)/1e6;
const gpu=v.hours*v.gpuRate*(1+v.overhead/100);
const breakEven=v.gpuRate>0 ? token/(v.gpuRate*(1+v.overhead/100)) : NaN;
return {token:token,gpu:gpu,difference:gpu-token,tokenAccepted:token/accepted*1000,gpuAccepted:gpu/accepted*1000,breakEven:breakEven,
neededTps:breakEven>0?(requests*v.output)/(breakEven*3600):NaN};
}
if(typeof module!=="undefined"&&module.exports)module.exports={estimate:estimate};
if(typeof document==="undefined")return;
const keys=["requests","input","output","inputRate","outputRate","gpuRate","hours","overhead","accept"];
const map={requests:"host-requests",input:"host-input",output:"host-output",inputRate:"host-input-rate",outputRate:"host-output-rate",gpuRate:"host-gpu",hours:"host-hours",overhead:"host-overhead",accept:"host-accept"};
const fields=Object.fromEntries(keys.map(k=>[k,document.getElementById(map[k])]));
if(keys.some(k=>!fields[k]))return;
const display={token:"host-result-token",gpu:"host-result-gpu",difference:"host-result-difference",tokenAccepted:"host-result-api-accepted",gpuAccepted:"host-result-gpu-accepted",breakEven:"host-result-breakeven",neededTps:"host-result-throughput"};
const outputs=Object.fromEntries(Object.entries(display).map(([k,id])=>[k,document.getElementById(id)]));
const status=document.getElementById("host-status");
const money=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2});
const number=new Intl.NumberFormat("en-US",{maximumFractionDigits:0});
function render(){
const v={};for(const k of keys){
const node=fields[k],num=Number(node.value);
if(node.value.trim()===""||!Number.isFinite(num)||num<Number(node.min)||num>Number(node.max)){
status.textContent="Check the highlighted limits: all fields must contain valid numbers.";return;
}v[k]=num;
}
const r=estimate(v);
outputs.token.textContent=money.format(r.token);
outputs.gpu.textContent=money.format(r.gpu);
outputs.difference.textContent=(r.difference>=0?"+":"")+money.format(r.difference);
outputs.tokenAccepted.textContent=money.format(r.tokenAccepted);
outputs.gpuAccepted.textContent=money.format(r.gpuAccepted);
outputs.breakEven.textContent=Number.isFinite(r.breakEven)?r.breakEven.toLocaleString("en-US",{maximumFractionDigits:2})+" h":"Not defined";
outputs.neededTps.textContent=Number.isFinite(r.neededTps)?number.format(r.neededTps)+" tok/s":"Not defined";
status.textContent="Illustrative result updated. GPU throughput feasibility is unverified; listed rates may change.";
}
const form=document.getElementById("host-calc");
form.addEventListener("input",render);
form.addEventListener("submit",ev=>{ev.preventDefault();render()});
render();
})();