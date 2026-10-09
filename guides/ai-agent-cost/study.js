(function(root){
  "use strict";
  // Pure scenario economics: no server writes and no live vendor-rate assumptions.
  function compute(c, rates, overrides) {
    overrides=overrides||{};
    const v=Object.assign({},c,overrides);
    const input=Number(rates.input), output=Number(rates.output);
    if(!Number.isFinite(input)||!Number.isFinite(output)||input<0||output<0)throw Error("Missing model API prices");
    const nonnegative=["monthly_tasks","calls_per_task","input_tokens_per_call","output_tokens_per_call","retry_overhead","tool_cost_per_call_usd","human_review_fraction","review_minutes","review_loaded_hourly_usd","monthly_infrastructure_usd","monthly_operations_usd","monthly_maintenance_usd","monthly_security_usd","monthly_platform_usd","implementation_one_time_usd","accepted_success_rate","manual_baseline_minutes_per_task","manual_baseline_loaded_hourly_usd","value_realization_fraction"];
    for(const key of nonnegative){if(!Number.isFinite(v[key])||v[key]<0)throw Error("Invalid "+key)}
    for(const key of ["human_review_fraction","accepted_success_rate","value_realization_fraction"]){if(v[key]>1)throw Error("Invalid fraction "+key)}
    if(v.monthly_tasks===0||v.calls_per_task===0)throw Error("Volume and calls must be positive");
    const calls=v.monthly_tasks*v.calls_per_task*(1+v.retry_overhead);
    const api=calls*(v.input_tokens_per_call*input+v.output_tokens_per_call*output)/1e6;
    const tools=calls*v.tool_cost_per_call_usd;
    const human=v.monthly_tasks*v.human_review_fraction*v.review_minutes/60*v.review_loaded_hourly_usd;
    const fixed=v.monthly_infrastructure_usd+v.monthly_operations_usd+v.monthly_maintenance_usd+v.monthly_security_usd+v.monthly_platform_usd;
    const recurring=api+tools+human+fixed, firstYear=recurring*12+v.implementation_one_time_usd;
    const successes=v.monthly_tasks*v.accepted_success_rate;
    const captured=successes*v.manual_baseline_minutes_per_task/60*v.manual_baseline_loaded_hourly_usd*v.value_realization_fraction;
    const yearValue=captured*12, net=yearValue-firstYear;
    const monthlyReturn=captured-recurring;
    // Financial outcome applies only to accepted successes, not all attempted tasks.
    return {calls,api,tools,human,fixed,recurring,firstYear,successes,captured,yearValue,net,
      roi:firstYear>0?100*net/firstYear:null,
      costPerAccepted:successes>0?firstYear/(12*successes):null,
      costPerAttempt:firstYear/(12*v.monthly_tasks),
      payback:monthlyReturn>0?v.implementation_one_time_usd/monthlyReturn:null,
      breakEvenSuccess:(v.monthly_tasks*v.manual_baseline_minutes_per_task/60*v.manual_baseline_loaded_hourly_usd*v.value_realization_fraction)>0?
        (firstYear/12)/(v.monthly_tasks*v.manual_baseline_minutes_per_task/60*v.manual_baseline_loaded_hourly_usd*v.value_realization_fraction):null};
  }
  const money=(v,d=0)=>"$"+Number(v).toLocaleString("en-US",{minimumFractionDigits:d,maximumFractionDigits:d});
  const percent=v=>v==null?"N/A":v.toLocaleString("en-US",{maximumFractionDigits:1})+"%";
  const ids=["studyCase","studySuccess","studyReview","studyRealization"];
  async function init(){
    const selector=document.getElementById("studyCase");
    if(!selector)return;
    const status=document.getElementById("studyStatus");
    try{
      const [a,b]=await Promise.all([fetch("/data/enterprise-agent-economics-assumptions.json",{cache:"no-store"}),fetch("/data/model-pricing.json",{cache:"no-store"})]);
      if(!a.ok||!b.ok)throw Error("Source data unavailable");
      const assumptions=await a.json(),catalog=await b.json();
      if(!Array.isArray(assumptions.cases)||!Array.isArray(catalog.models))throw Error("Invalid source data");
      const cases=Object.fromEntries(assumptions.cases.map(c=>[c.id,c]));
      const models=Object.fromEntries(catalog.models.map(m=>[m.model_id,m]));
      const rate=m=>{
        const date="2026-10-10";
        const row=m.pricing?.standard?.find(x=>x.start<=date&&(!x.end||date<=x.end));
        if(!row||m.pricing_basis?.quantity!==1000000||m.pricing_status!=="official-paid")throw Error("Pricing record unavailable");
        return row;
      };
      const savedResults={};
      for(const c of assumptions.cases){const m=models[c.model_id];if(!m)throw Error("Missing model "+c.model_id);savedResults[c.id]=compute(c,rate(m));}
      const fmtSmall=n=>n==null?"N/A":money(n,2);
      function populate(){
        const c=cases[selector.value];
        if(!c)return;
        document.getElementById("studySuccess").value=Math.round(c.accepted_success_rate*100);
        document.getElementById("studyReview").value=Math.round(c.human_review_fraction*100);
        document.getElementById("studyRealization").value=Math.round(c.value_realization_fraction*100);
        draw();
      }
      function draw(){
        const c=cases[selector.value],m=models[c.model_id];
        if(!c||!m)return;
        const success=Number(document.getElementById("studySuccess").value);
        const review=Number(document.getElementById("studyReview").value);
        const realization=Number(document.getElementById("studyRealization").value);
        const result=compute(c,rate(m),{accepted_success_rate:success/100,human_review_fraction:review/100,value_realization_fraction:realization/100});
        const byId=(id,v)=>{document.getElementById(id).textContent=v};
        byId("studySuccessLabel",success+"%");
        byId("studyReviewLabel",review+"%");
        byId("studyRealizationLabel",realization+"%");
        byId("studyUnit",fmtSmall(result.costPerAccepted));
        byId("studyYear",money(result.firstYear));
        byId("studyROI",percent(result.roi));
        byId("studyNet",(result.net>=0?"+":"−")+money(Math.abs(result.net)));
        byId("studyAccepted",result.successes.toLocaleString("en-US",{maximumFractionDigits:0}));
        byId("studyCaptured",money(result.captured));
        byId("studyBreakeven",result.breakEvenSuccess===null?"N/A":result.breakEvenSuccess>1?"Not reachable at fixed assumptions":(result.breakEvenSuccess*100).toFixed(1)+"%");
        byId("studyCaseCaption",c.name+" · "+m.model+" · "+catalog.source_verified+" catalog snapshot · hypothetical assumptions");
        byId("studyNote",result.net>=0?"The modeled year-one case is positive. This does not establish actual cash savings.":"The modeled year-one case is negative. Reducing review time or changing workflow may matter more than token prices.");
        const meter=document.getElementById("studyMeter");
        meter.style.width=Math.max(0,Math.min(100,success))+"%";
        document.getElementById("studySummaryLink").href="/ai-agent-cost/#calculator";
      }
      selector.addEventListener("change",populate);
      for(const id of ids.slice(1))document.getElementById(id).addEventListener("input",draw);
      populate();
      status.textContent="Scenario file and SXF catalog loaded · independent calculations, not deployment measurements.";
      status.dataset.state="ready";
    }catch(error){
      status.textContent="The scenario dataset could not be loaded. Static research analysis remains available; no substitute prices are inferred.";
      status.dataset.state="error";
      for(const id of ids){document.getElementById(id).disabled=true}
    }
  }
  if(typeof module!=="undefined"&&module.exports)module.exports={compute};
  if(root&&root.document)root.document.addEventListener("DOMContentLoaded",init);
})(typeof window!=="undefined"?window:null);
