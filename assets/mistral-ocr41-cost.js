/* SXF OCR 4.1 page-economics calculator; no network or stored user input. */
(function(){
  "use strict";
  const root=document.querySelector("[data-mocr41-calculator]");
  if(!root)return;
  const f={
    docs:root.querySelector("[data-mocr41-docs]"),
    pages:root.querySelector("[data-mocr41-pages]"),
    mode:root.querySelector("[data-mocr41-mode]"),
    retry:root.querySelector("[data-mocr41-retry]"),
    audit:root.querySelector("[data-mocr41-audit]"),
    minutes:root.querySelector("[data-mocr41-minutes]"),
    rate:root.querySelector("[data-mocr41-rate]")
  };
  const output={
    count:root.querySelector("[data-mocr41-count]"),
    api:root.querySelector("[data-mocr41-api]"),
    human:root.querySelector("[data-mocr41-human]"),
    total:root.querySelector("[data-mocr41-total]"),
    explain:root.querySelector("[data-mocr41-explain]")
  };
  if(Object.values(f).some(x=>!x)||Object.values(output).some(x=>!x))return;
  const read=(el,max)=>{
    const n=Number(el.value);
    return Number.isFinite(n)?Math.max(0,Math.min(max,n)):0;
  };
  const money=n=>new Intl.NumberFormat("en-US",{
    style:"currency",currency:"USD",
    minimumFractionDigits:2,maximumFractionDigits:2
  }).format(n);
  const fmt=n=>new Intl.NumberFormat("en-US",{maximumFractionDigits:2}).format(n);
  function update(){
    const docs=Math.floor(read(f.docs,1000000));
    const pages=read(f.pages,100000);
    const rate=f.mode.value==="annotated"?.005:.004;
    const retry=read(f.retry,300)/100;
    const reviewFraction=read(f.audit,100)/100;
    const minutes=read(f.minutes,600);
    const reviewerRate=read(f.rate,10000);
    const count=docs*pages;
    const api=count*(1+retry)*rate;
    const reviewedPages=count*reviewFraction;
    const human=reviewedPages*minutes/60*reviewerRate;
    output.count.textContent=fmt(count);
    output.api.textContent=money(api);
    output.human.textContent=money(human);
    output.total.textContent=money(api+human);
    output.explain.textContent=fmt(count)+" document pages, "+
      fmt(retry*100)+"% reprocessing, "+fmt(reviewedPages)+
      " pages reviewed at "+fmt(minutes)+" min/page and "+money(reviewerRate)+"/hour.";
  }
  Object.values(f).forEach(x=>{
    x.addEventListener("input",update);
    x.addEventListener("change",update);
  });
  update();
})();
