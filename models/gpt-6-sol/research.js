"use strict";
/* SXF original Sol study: client-side Standard pricing math, no network requests. */
(() => {
  const form = document.getElementById("sol-cost-calculator");
  if (!form) return;
  const fields = Object.fromEntries(["new","cached","write","output","requests"].map(k => [k,form.querySelector('[name="'+k+'"]')]));
  const display = name => form.querySelector('[data-result="'+name+'"]');
  const rate = (prefix,part) => Number(form.dataset[prefix+part]);
  const fmt = (value,digits=6) => "$"+value.toFixed(digits);
  const quote = (prefix,values,long) => (
    (values.new*rate(prefix,"Input")+values.cached*rate(prefix,"Cached")+values.write*rate(prefix,"Write"))*(long?2:1)
    +values.output*rate(prefix,"Output")*(long?1.5:1)
  )/1000000;
  function refresh(){
    const values = Object.fromEntries(Object.entries(fields).map(([key,input])=>[key,Number(input.value)]));
    const total = values.new + values.cached + values.write;
    const bad = Object.values(values).some(v=>!Number.isSafeInteger(v)||v<0) || total>1050000 || values.output>128000 || values.requests<1 || values.requests>10000000;
    if(bad){
      display("tier").textContent = "Invalid";
      for(const key of ["sol","new","difference"])display(key).textContent="—";
      display("message").textContent="Use non-negative whole token counts: total input ≤1,050,000; output ≤128,000; requests 1–10,000,000.";
      return;
    }
    const long=total>272000;
    const oldSol=quote("sol",values,long), newer=quote("new",values,long);
    display("tier").textContent=long?"Long >272K":"Short ≤272K";
    display("sol").textContent=fmt(oldSol);
    display("new").textContent=fmt(newer);
    display("difference").textContent="$"+((oldSol-newer)*values.requests).toFixed(2);
    display("message").textContent="Hypothetical Standard API token rates only. Real cache hits, model output, tools and processing fees may differ.";
  }
  for(const input of Object.values(fields)) input.addEventListener("input",refresh);
  form.addEventListener("submit",event=>event.preventDefault());
  refresh();
})();