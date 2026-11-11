/* SXF Cost-per-Success Lab — transparent, local, no external requests. */
(() => {
"use strict";
const root = document.querySelector("[data-sg-cost-lab]");
if (!root) return;
const get = selector => root.querySelector(selector);
const period=get("[data-sg-period]"), tasks=get("[data-sg-tasks]"), input=get("[data-sg-input]");
const cache=get("[data-sg-cache]"), solOutput=get("[data-sg-sol-output]"), gemOutput=get("[data-sg-gem-output]");
const solSuccess=get("[data-sg-sol-success]"), gemSuccess=get("[data-sg-gem-success]");
const solTotal=get("[data-sg-sol-total]"), gemTotal=get("[data-sg-gem-total]");
const diff=get("[data-sg-difference]"), caveat=get("[data-sg-caveat]");
const clipped=(field,min,max)=>{const number=Number(field.value);return Number.isFinite(number)?Math.max(min,Math.min(max,number)):min;};
const usd=n=>(n<0?"-$":"$")+Math.abs(n).toFixed(4);
function update(){
 const target=clipped(tasks,1,1000000);
 const inTokens=clipped(input,0,1048576);
 const cachedFraction=clipped(cache,0,100)/100;
 const solOut=clipped(solOutput,0,128000), gemOut=clipped(gemOutput,0,65536);
 const solProbability=clipped(solSuccess,1,100)/100, gemProbability=clipped(gemSuccess,1,100)/100;
 const longContext=inTokens>272000;
 const solRates=longContext?[4,0.4,15]:[2,0.2,10];
 const gemRates=period.value==="2027"?[1.5,0.15,7.5]:[0.75,0.075,3.75];
 const compute=(out,p,rates)=>target/p*(inTokens*(1-cachedFraction)*rates[0]+inTokens*cachedFraction*rates[1]+out*rates[2])/1000000;
 const sol=compute(solOut,solProbability,solRates);
 const gem=compute(gemOut,gemProbability,gemRates);
 solTotal.textContent=usd(sol);gemTotal.textContent=usd(gem);diff.textContent=usd(sol-gem);
 caveat.textContent="Sol input above 272K: "+(longContext?"yes, whole-request long-context rates":"no, standard short-context rates")+" · Gemini Standard period: "+(period.value==="2027"?"2027 onward":"through 2026")+". Assumed success rates are entered by you, not measured by SXF.";
}
for (const field of [period,tasks,input,cache,solOutput,gemOutput,solSuccess,gemSuccess]){
 field.addEventListener("input",update);field.addEventListener("change",update);
}
update();
})();
