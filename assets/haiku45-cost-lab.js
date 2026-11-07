/* SXF Haiku 4.5 calculator: no network, tracking or local storage. */
(function () {
  "use strict";
  const root=document.querySelector("[data-h45-cost-lab]");
  if(!root) return;
  const fields={
    requests:root.querySelector("[data-h45-requests]"),
    input:root.querySelector("[data-h45-input]"),
    output:root.querySelector("[data-h45-output]"),
    read:root.querySelector("[data-h45-read]"),
    write5:root.querySelector("[data-h45-write5]"),
    write60:root.querySelector("[data-h45-write60]"),
    mode:root.querySelector("[data-h45-mode]")
  };
  const views={
    each:root.querySelector("[data-h45-each]"),
    month:root.querySelector("[data-h45-month]"),
    explain:root.querySelector("[data-h45-explain]")
  };
  if(Object.values(fields).some(x=>!x)||Object.values(views).some(x=>!x)) return;
  const read=(el,maximum)=>{
    const n=Number(el.value);
    return Number.isFinite(n)?Math.max(0,Math.min(maximum,n)):0;
  };
  const usd=(n,decimals)=>new Intl.NumberFormat("en-US",{
    style:"currency",currency:"USD",minimumFractionDigits:decimals,
    maximumFractionDigits:decimals
  }).format(n);
  const refresh=()=>{
    const requests=Math.floor(read(fields.requests,10000000));
    const input=read(fields.input,200000);
    const output=read(fields.output,64000);
    const batch=fields.mode.value==="batch";
    const cacheRead=read(fields.read,200000);
    const write5=read(fields.write5,200000);
    const write60=read(fields.write60,200000);
    const per=batch?
      (input*0.5+output*2.5)/1000000:
      (input*1+output*5+cacheRead*.1+write5*1.25+write60*2)/1000000;
    views.each.textContent=usd(per,6);
    views.month.textContent=usd(per*requests,2);
    views.explain.textContent=batch?
      "Batch estimate: uncached input × $0.50/MTok + output × $2.50/MTok. Cache fields are excluded.":
      "Standard estimate: fresh input × $1, output × $5, cache read × $0.10, 5m write × $1.25 and 1h write × $2 per MTok.";
  };
  Object.values(fields).forEach(el=>{el.addEventListener("input",refresh);el.addEventListener("change",refresh);});
  refresh();
})();
