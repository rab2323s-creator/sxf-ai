/* SXF Mistral Embed economics and raw float32 storage only; no tracking/network. */
(function(){
  "use strict";
  const root=document.querySelector("[data-membed-calculator]");
  if(!root)return;
  const f={
    chunks:root.querySelector("[data-me-chunks]"),
    tokens:root.querySelector("[data-me-tokens]"),
    reindex:root.querySelector("[data-me-reindex]"),
    queries:root.querySelector("[data-me-queries]"),
    queryTokens:root.querySelector("[data-me-query-tokens]"),
    retries:root.querySelector("[data-me-retries]")
  };
  const o={
    initial:root.querySelector("[data-me-initial]"),
    month:root.querySelector("[data-me-month]"),
    storage:root.querySelector("[data-me-storage]"),
    explain:root.querySelector("[data-me-explain]")
  };
  if(Object.values(f).some(x=>!x)||Object.values(o).some(x=>!x))return;
  const read=(x,max)=>{const n=Number(x.value);return Number.isFinite(n)?Math.max(0,Math.min(max,n)):0;};
  const dollars=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:4}).format(n);
  const number=n=>new Intl.NumberFormat("en-US",{maximumFractionDigits:2}).format(n);
  function update(){
    const chunks=Math.floor(read(f.chunks,100000000));
    const tokens=read(f.tokens,8000);
    const reindex=read(f.reindex,300)/100;
    const queries=Math.floor(read(f.queries,100000000));
    const queryTokens=read(f.queryTokens,8000);
    const retries=read(f.retries,300)/100;
    const rate=0.10/1000000;
    const initial=chunks*tokens*rate*(1+retries);
    const monthly=(chunks*reindex*tokens+queries*queryTokens)*rate*(1+retries);
    const rawBytes=chunks*1024*4;
    o.initial.textContent=dollars(initial);
    o.month.textContent=dollars(monthly);
    o.storage.textContent=rawBytes>=1e9?number(rawBytes/1e9)+" GB":number(rawBytes/1e6)+" MB";
    o.explain.textContent=number(chunks)+" chunks × "+number(tokens)+" tokens; "+
      number(reindex*100)+"% re-indexed monthly; "+number(queries)+" queries × "+
      number(queryTokens)+" tokens; "+number(retries*100)+"% extra billed retries.";
  }
  Object.values(f).forEach(x=>{x.addEventListener("input",update);x.addEventListener("change",update);});
  update();
})();
