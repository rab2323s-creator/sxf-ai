/* SXF procurement value estimator: hypothetical annualized economics, not vendor quotes or benchmark. */
(function(){
  "use strict";
  function estimate(v){
    const acceptedSpend=v.spend*v.accepted/100;
    const priceBenefit=acceptedSpend*v.price/100;
    const financingBenefit=acceptedSpend*v.days/365*v.capital/100;
    const costs=v.platform+v.review;
    return {acceptedSpend:acceptedSpend,priceBenefit:priceBenefit,financingBenefit:financingBenefit,costs:costs,net:priceBenefit+financingBenefit-costs};
  }
  if(typeof module!=="undefined"&&module.exports) module.exports={estimate:estimate};
  if(typeof document==="undefined")return;
  const fields=["spend","accepted","price","days","capital","platform","review"];
  const nodes={};
  fields.forEach(function(k){nodes[k]=document.getElementById("proc-"+k)});
  if(fields.some(function(k){return !nodes[k]}))return;
  const out={acceptedSpend:document.getElementById("proc-out-spend"),priceBenefit:document.getElementById("proc-out-price"),financingBenefit:document.getElementById("proc-out-financing"),costs:document.getElementById("proc-out-costs"),net:document.getElementById("proc-out-net")};
  const form=document.getElementById("proc-roi-form");
  const status=document.getElementById("proc-lab-status");
  const netCard=document.getElementById("proc-net-card");
  const currency=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0});
  function update(){
    const v={};
    for(const k of fields){
      const num=Number(nodes[k].value);
      if(nodes[k].value.trim()===""||!Number.isFinite(num)||num<Number(nodes[k].min)||num>Number(nodes[k].max)){
        status.textContent="Enter values within the labeled ranges to calculate this illustration.";
        return;
      }
      v[k]=num;
    }
    const r=estimate(v);
    for(const k in out)out[k].textContent=currency.format(r[k]);
    netCard.classList.toggle("negative",r.net<0);
    status.textContent="Illustrative estimate updated. Results are not vendor performance claims.";
  }
  form.addEventListener("input",update);
  form.addEventListener("submit",function(ev){ev.preventDefault();update()});
  update();
})();