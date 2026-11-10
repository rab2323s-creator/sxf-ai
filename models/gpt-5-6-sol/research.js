"use strict";
/* SXF GPT-5.6 Sol deterministic caching calculator. No network or private data. */
(()=>{
 const form=document.getElementById("g56-cache-calculator");
 if(!form)return;
 const field=k=>form.querySelector('[name="'+k+'"]');
 const result=k=>form.querySelector('[data-result="'+k+'"]');
 const rates={input:Number(form.dataset.input),cached:Number(form.dataset.cached),write30:Number(form.dataset.write30),write12:Number(form.dataset.write12),output:Number(form.dataset.output)};
 const dollars=n=>"$"+n.toFixed(6);
 const quote=(category,prefix,newTokens,output)=>{
   const long=prefix+newTokens>272000;
   return ((prefix*rates[category]+newTokens*rates.input)*(long?2:1)+output*rates.output*(long?1.5:1))/1000000;
 };
 function update(){
   const values=Object.fromEntries(["prefix","new","output","calls"].map(k=>[k,Number(field(k).value)]));
   const valid=Object.values(values).every(Number.isSafeInteger)&&Object.values(values).every(x=>x>=0)&&values.calls>=1&&values.calls<=100000&&values.prefix+values.new<=1050000&&values.output<=128000;
   if(!valid){result("tier").textContent="Invalid";for(const k of ["uncached","thirty","twelve","saving"])result(k).textContent="—";result("message").textContent="Enter whole tokens: prefix + new input ≤ 1,050,000; output ≤ 128,000; 1–100,000 calls.";return;}
   const {prefix,new:newTokens,output,calls}=values;
   const uncached=calls*quote("input",prefix,newTokens,output);
   const thirty=quote("write30",prefix,newTokens,output)+(calls-1)*quote("cached",prefix,newTokens,output);
   const twelve=quote("write12",prefix,newTokens,output)+(calls-1)*quote("cached",prefix,newTokens,output);
   result("tier").textContent=prefix+newTokens>272000?"Long >272K":"Short ≤272K";
   result("uncached").textContent=dollars(uncached);
   result("thirty").textContent=dollars(thirty);
   result("twelve").textContent=dollars(twelve);
   result("saving").textContent=dollars(uncached-thirty);
   result("message").textContent="List-price arithmetic only. Assumes an initial write, subsequent cache hits and all calls within retention; actual API invoices vary.";
 }
 form.addEventListener("submit",e=>e.preventDefault());
 for(const k of ["prefix","new","output","calls"])field(k).addEventListener("input",update);
 update();
})();