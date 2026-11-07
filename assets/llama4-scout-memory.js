/* SXF Scout sensitivity model: theoretical parameters, not measured GPU usage.
   No network requests, tracking, or persistent storage. */
(function(){
  "use strict";
  const root=document.querySelector("[data-scout-memory-lab]");
  if(!root)return;
  const el={
    bits:root.querySelector("[data-scout-bits]"),
    overhead:root.querySelector("[data-scout-overhead]"),
    tokens:root.querySelector("[data-scout-tokens]"),
    kv:root.querySelector("[data-scout-kv]"),
    weights:root.querySelector("[data-scout-weights]"),
    kvResult:root.querySelector("[data-scout-kv-result]"),
    total:root.querySelector("[data-scout-total]"),
    formula:root.querySelector("[data-scout-formula]")
  };
  if(Object.values(el).some(v=>!v))return;
  const val=(node,max)=>{
    const n=Number(node.value);
    return Number.isFinite(n)?Math.max(0,Math.min(max,n)):0;
  };
  const fmt=n=>new Intl.NumberFormat("en-US",{maximumFractionDigits:2}).format(n);
  function calculate(){
    const bits=val(el.bits,16);
    const overhead=val(el.overhead,300)/100;
    const tokens=val(el.tokens,10000000);
    const cacheKiB=val(el.kv,1024);
    const weightGB=109000000000*bits/8/1000000000;
    const cacheGB=tokens*cacheKiB*1024/1000000000;
    const combinedGB=weightGB*(1+overhead)+cacheGB;
    el.weights.textContent=fmt(weightGB)+" GB";
    el.kvResult.textContent=fmt(cacheGB)+" GB";
    el.total.textContent=fmt(combinedGB)+" GB";
    el.formula.textContent="109B parameters × "+fmt(bits)+" bits + "+
      fmt(overhead*100)+"% allowance + "+fmt(tokens)+" tokens × "+
      fmt(cacheKiB)+" KiB/token (hypothetical).";
  }
  [el.bits,el.overhead,el.tokens,el.kv].forEach(n=>{
    n.addEventListener("input",calculate);n.addEventListener("change",calculate);
  });
  calculate();
})();
