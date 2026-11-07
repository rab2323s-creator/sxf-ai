/* Cohere Command A+ Model Vault scenario calculator. No network or storage. */
(function(){
  "use strict";
  const root=document.querySelector("[data-caplus-calculator]");
  if(!root)return;
  const fields={
    instances:root.querySelector("[data-caplus-instances]"),
    hours:root.querySelector("[data-caplus-hours]"),
    throughput:root.querySelector("[data-caplus-throughput]"),
    pass:root.querySelector("[data-caplus-pass]")
  };
  const out={
    cost:root.querySelector("[data-caplus-cost]"),
    accepted:root.querySelector("[data-caplus-accepted]"),
    unit:root.querySelector("[data-caplus-unit]"),
    explain:root.querySelector("[data-caplus-explain]")
  };
  if(Object.values(fields).some(x=>!x)||Object.values(out).some(x=>!x))return;
  const read=(el,max)=>{
    const n=Number(el.value);
    return Number.isFinite(n)?Math.max(0,Math.min(max,n)):0;
  };
  const usd=(n,places)=>new Intl.NumberFormat("en-US",{
    style:"currency",currency:"USD",
    minimumFractionDigits:places,maximumFractionDigits:places
  }).format(n);
  const number=n=>new Intl.NumberFormat("en-US",{maximumFractionDigits:2}).format(n);
  function update(){
    const tier="XL";
    const hourly=57.5;
    const instances=Math.floor(read(fields.instances,10000));
    const hours=read(fields.hours,8760);
    const throughput=read(fields.throughput,1000000);
    const passFraction=read(fields.pass,100)/100;
    const cost=instances*hours*hourly;
    const accepted=instances*hours*throughput*passFraction;
    out.cost.textContent=usd(cost,2);
    out.accepted.textContent=number(accepted);
    out.unit.textContent=accepted>0?usd(cost/accepted,4):"N/A";
    out.explain.textContent=number(instances)+" "+tier+" instance(s) × "+
      number(hours)+" billed hours × "+usd(hourly,2)+"/hour; "+
      number(throughput)+" tasks/hour and "+number(passFraction*100)+"% approval assumption.";
  }
  Object.values(fields).forEach(el=>{
    el.addEventListener("input",update);
    el.addEventListener("change",update);
  });
  update();
})();
