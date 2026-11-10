"use strict";
/* SXF Astra price study: purely client-side scenarios; no API access, no secrets. */
(() => {
  const lab = document.querySelector("#astra-calculator");
  if (!lab) return;
  const inputs = Object.fromEntries(["input","cached","write","output"].map(k => [k,lab.querySelector('[data-tokens="'+k+'"]')]));
  const out = key => lab.querySelector('[data-result="'+key+'"]');
  const read = key => Number(lab.dataset[key]);
  const quote = (prefix,t,long) => ((t.input*read(prefix+"Input") + t.cached*read(prefix+"Cached") + t.write*read(prefix+"Write"))*(long?2:1) + t.output*read(prefix+"Output")*(long?1.5:1))/1e6;
  function refresh(){
    const t = Object.fromEntries(Object.entries(inputs).map(([k,el])=>[k,Number(el.value)]));
    const total = t.input+t.cached+t.write;
    const invalid = Object.values(t).some(v=>!Number.isFinite(v)||v<0||!Number.isInteger(v))||total>1050000||t.output>128000;
    if (invalid) { out("tier").textContent="Invalid token counts";out("astra").textContent="—";out("sol").textContent="—";out("warning").textContent="Use non-negative whole tokens; total input ≤1,050,000 and output ≤128,000.";return; }
    const long=total>272000;
    out("tier").textContent=long?"Long >272K":"Short ≤272K";
    out("astra").textContent="$"+quote("astra",t,long).toFixed(5);
    out("sol").textContent="$"+quote("sol",t,long).toFixed(5);
    out("warning").textContent="Estimated Standard API list-price tokens only. Cache events, processing modes, tools and actual usage may change billed cost.";
  }
  Object.values(inputs).forEach(el=>el.addEventListener("input",refresh));
  refresh();
})();