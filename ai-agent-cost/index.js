(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const fields = ["monthlyTasks","callsPerTask","inputTokens","outputTokens","cachePercent","retryPercent","toolCost","infraCost","opsCost","buildCost","reviewPercent","reviewMinutes","hourlyCost","successRate","valuePerSuccess"];
  const currency = (n, decimals = 2) => "$" + n.toLocaleString("en-US", {minimumFractionDigits:decimals, maximumFractionDigits:decimals});
  const rateText = n => n == null ? "—" : "$" + Number(n).toLocaleString("en-US", {maximumFractionDigits:6});
  const fmtCount = n => n.toLocaleString("en-US",{maximumFractionDigits:0});
  const catalogUrl = "/data/model-pricing.json";
  let catalog = null;
  let tokenModels = [];
  let visibleRows = [];
  let byId = new Map();
  let lastSnapshot = null;
  let currentPreset = "support";
  const PRESETS = Object.freeze({
    support: {monthlyTasks:10000,callsPerTask:2,inputTokens:2000,outputTokens:500,cachePercent:0,retryPercent:10,toolCost:0.002,infraCost:300,opsCost:600,buildCost:500,reviewPercent:15,reviewMinutes:2,hourlyCost:35,successRate:85,valuePerSuccess:1.8},
    documents: {monthlyTasks:2500,callsPerTask:3,inputTokens:5500,outputTokens:900,cachePercent:20,retryPercent:15,toolCost:0.008,infraCost:400,opsCost:850,buildCost:900,reviewPercent:25,reviewMinutes:4,hourlyCost:45,successRate:78,valuePerSuccess:7},
    research: {monthlyTasks:1200,callsPerTask:6,inputTokens:8000,outputTokens:1800,cachePercent:35,retryPercent:25,toolCost:0.02,infraCost:650,opsCost:1200,buildCost:1500,reviewPercent:35,reviewMinutes:6,hourlyCost:55,successRate:70,valuePerSuccess:24}
  });
  const BASE = "2026-10-09";

  function validTokenModel(m) {
    return m && m.pricing_status === "official-paid" && m.calculator_eligible === true &&
      m.pricing_basis?.meter === "tokens" && m.pricing_basis?.quantity > 0 &&
      Array.isArray(m.pricing?.standard) && m.pricing.standard.length > 0;
  }
  function activeRates(m, totalInput) {
    if (!window.SXFPricing || !m) return null;
    const date = new Date().toISOString().slice(0,10);
    return window.SXFPricing.effectiveRates(m, date, totalInput);
  }
  function status(state, message) {
    const node = $("catalogStatus");
    node.dataset.state = state;
    node.querySelector("span:last-child").textContent = message;
  }
  function populateCatalog() {
    tokenModels = catalog.models.filter(validTokenModel);
    byId = new Map(tokenModels.map(m => [m.model_id,m]));
    $("statModels").textContent = fmtCount(catalog.models.length);
    $("statEligible").textContent = fmtCount(tokenModels.length);
    $("statProviders").textContent = fmtCount(new Set(catalog.models.map(m=>m.provider)).size);
    $("statVerified").textContent = catalog.source_verified || "Not listed";
    const providers = [...new Set(tokenModels.map(m=>m.provider))].sort((a,b)=>a.localeCompare(b));
    const filter=$("providerFilter");
    providers.forEach(provider => {const opt=document.createElement("option");opt.value=provider;opt.textContent=provider;filter.appendChild(opt)});
    const select=$("calcModel");
    select.replaceChildren();
    const options = new Map();
    tokenModels.forEach(model => {
      let group=options.get(model.provider);
      if (!group) {group=document.createElement("optgroup");group.label=model.provider;select.appendChild(group);options.set(model.provider,group)}
      const opt=document.createElement("option");opt.value=model.model_id;opt.textContent=model.model;group.appendChild(opt);
    });
    select.disabled=false;
    const preferred=["gpt-6-sol","claude-sonnet-5","gpt-6-luna"];
    select.value=preferred.find(key=>byId.has(key))||tokenModels[0]?.model_id||"";
    $("exportRates").disabled=false;
    $("rateRows").replaceChildren();
    updateRows();
    calculate();
    status("ok","SXF catalog loaded. Prices are provider-source documented records, not real-time vendor API quotes. Last catalog review: "+(catalog.source_verified||"not listed")+".");
  }
  function filteredModels() {
    const term=$("rateSearch").value.trim().toLowerCase();
    const provider=$("providerFilter").value;
    const agentOnly=$("agentOnly").checked;
    return tokenModels.filter(m=>(provider==="all"||m.provider===provider)&&
      (!term||(m.model+" "+m.provider).toLowerCase().includes(term))&&
      (!agentOnly||(m.capabilities||[]).includes("agents")||(m.capabilities||[]).includes("tool-use")));
  }
  function cell(content,cls) {
    const td=document.createElement("td");
    if(cls)td.className=cls;
    td.textContent=content;
    return td;
  }
  function updateRows() {
    if (!catalog) return;
    visibleRows=filteredModels();
    const body=$("rateRows");
    body.replaceChildren();
    if (!visibleRows.length){
      const tr=document.createElement("tr");
      const td=cell("No models match these filters.");
      td.colSpan=6;tr.appendChild(td);body.appendChild(tr);
    }
    const today=new Date().toISOString().slice(0,10);
    visibleRows.forEach(m=>{
      const tr=document.createElement("tr");
      const titleTd=document.createElement("td");
      const name=document.createElement("strong");name.className="aci-model-name";name.textContent=m.model;
      const sub=document.createElement("span");sub.className="aci-model-meta";
      sub.appendChild(document.createTextNode(m.provider+" · "));
      const link=document.createElement("a");
      const raw=m.provenance?.evidence?.pricing||m.official_sources?.[0];
      if(raw&&/^https:\/\//i.test(raw)){link.href=raw;link.textContent="Provider pricing";link.target="_blank";link.rel="noopener noreferrer";sub.appendChild(link)}else sub.appendChild(document.createTextNode("Source unavailable"));
      titleTd.append(name,sub);tr.appendChild(titleTd);
      const entry=activeRates(m,0);
      const price=entry?.rates||null;
      tr.appendChild(cell(price?rateText(price.input):"—"));
      tr.appendChild(cell(price?rateText(price.cached_input):"—"));
      tr.appendChild(cell(price?rateText(price.output):"—"));
      tr.appendChild(cell(m.provenance?.verified_at||"—"));
      const choose=document.createElement("td");
      const btn=document.createElement("button");btn.type="button";btn.className="aci-table-select";btn.textContent="Select ↗";
      btn.addEventListener("click",()=>{$("calcModel").value=m.model_id;calculate();$("calculator").scrollIntoView({behavior:"smooth",block:"start"})});
      choose.appendChild(btn);tr.appendChild(choose);body.appendChild(tr);
    });
    $("rateCount").textContent=fmtCount(visibleRows.length)+" eligible models shown · pricing date "+today;
  }
  function readInputs() {
    const vals={};
    for(const id of fields){
      const el=$(id),v=Number(el.value);
      if(el.value.trim()===""||!Number.isFinite(v)||v<0||v>Number(el.max||Number.POSITIVE_INFINITY)||(el.min!==""&&v<Number(el.min))){
        throw new Error("Enter a valid value for "+el.closest("label").textContent.trim()+".");
      }
      vals[id]=v;
    }
    if(!Number.isInteger(vals.monthlyTasks)||!Number.isInteger(vals.callsPerTask))throw new Error("Tasks per month and calls per task must be whole numbers.");
    return vals;
  }
  function resetOutputs(message) {
    for(const id of ["totalCost","costPerSuccess","costPerTask","successfulTasks","roiPercent","apiMonthly","toolsMonthly","humanMonthly","fixedMonthly","monthlyValue","monthlyNet"]) $(id).textContent="—";
    $("resultStatus").textContent=message;
    $("breakdownBar").replaceChildren();
    lastSnapshot=null;
  }
  function calculate() {
    if(!catalog||!window.SXFPricing){resetOutputs("Awaiting price data");return}
    const m=byId.get($("calcModel").value);
    if(!m){resetOutputs("Select a supported model");return}
    try {
      const v=readInputs();
      $("calcWarning").hidden=true;
      // A valid price estimate must also describe a technically valid model request.
      if (!Number.isInteger(v.inputTokens) || !Number.isInteger(v.outputTokens)) {
        throw new Error("Input and output token counts must be whole numbers.");
      }
      const context = Number(m.context_window);
      if (Number.isFinite(context) && context > 0 && v.inputTokens + v.outputTokens > context) {
        throw new Error("The total input and output tokens per call exceed this model's documented context window (" + context.toLocaleString("en-US") + ").");
      }
      if (typeof m.max_output === "number" && Number.isFinite(m.max_output) && v.outputTokens > m.max_output) {
        throw new Error("The output tokens per call exceed this model's documented maximum output (" + m.max_output.toLocaleString("en-US") + ").");
      }
      // Cache tokens are a subset of total input tokens; do not double count them.
      const cachedTokens=v.inputTokens*v.cachePercent/100;
      const uncachedTokens=v.inputTokens-cachedTokens;
      const effective=activeRates(m,v.inputTokens);
      if(!effective)throw new Error("No applicable catalog rate exists for this model and date.");
      const r=effective.rates;
      const unit=Number(m.pricing_basis.quantity);
      // Models without an explicit cached-input price use the normal input price.
      const cachedRate=typeof r.cached_input==="number"?r.cached_input:r.input;
      const apiPerCall=(uncachedTokens*r.input+cachedTokens*cachedRate+v.outputTokens*r.output)/unit;
      // Extra retries are modeled as an average additional call count per attempt.
      const callCount=v.monthlyTasks*v.callsPerTask*(1+v.retryPercent/100);
      const apiCost=callCount*apiPerCall;
      const toolsCost=callCount*v.toolCost;
      const humanCost=v.monthlyTasks*v.reviewPercent/100*v.reviewMinutes/60*v.hourlyCost;
      const fixedCost=v.infraCost+v.opsCost+v.buildCost;
      const total=apiCost+toolsCost+humanCost+fixedCost;
      const success=v.monthlyTasks*v.successRate/100;
      const incrementalValue=success*v.valuePerSuccess;
      const net=incrementalValue-total;
      const roi=total>0?net/total*100:null;
      const money=x=>currency(x,2);
      $("totalCost").textContent=money(total);
      $("costPerSuccess").textContent=success>0?money(total/success):"N/A";
      $("costPerTask").textContent=money(total/v.monthlyTasks);
      $("successfulTasks").textContent=success.toLocaleString("en-US",{maximumFractionDigits:1});
      $("roiPercent").textContent=roi===null?"N/A":roi.toLocaleString("en-US",{maximumFractionDigits:1})+"%";
      $("apiMonthly").textContent=money(apiCost);
      $("toolsMonthly").textContent=money(toolsCost);
      $("humanMonthly").textContent=money(humanCost);
      $("fixedMonthly").textContent=money(fixedCost);
      $("monthlyValue").textContent=money(incrementalValue);
      $("monthlyNet").textContent=money(net);
      const breakdown=$("breakdownBar");breakdown.replaceChildren();
      [[apiCost,"#c8ff4d","Model API"],[toolsCost,"#67dcd0","Tools"],[humanCost,"#dfa76e","Human review"],[fixedCost,"#8f9fc6","Fixed operational costs"]].forEach(([amount,color,name])=>{
        if(total<=0||amount<=0)return;
        const span=document.createElement("span");
        span.style.width=(amount/total*100)+"%";span.style.background=color;
        span.title=name+": "+money(amount);breakdown.appendChild(span);
      });
      $("selectedRates").textContent=m.model+" · input "+rateText(r.input)+", cached "+rateText(cachedRate)+", output "+rateText(r.output)+" per "+unit.toLocaleString("en-US")+" tokens"+(effective.long?" · long-context multiplier applied":"")+". Source verified: "+(m.provenance?.verified_at||"not provided")+".";
      $("resultStatus").textContent="Illustrative monthly estimate · "+m.model+" · "+(effective.long?"long-context":"Standard")+" rates";
      lastSnapshot={model:m.model,provider:m.provider,verification:m.provenance?.verified_at,inputs:v,monthly_cost:total,model_api:apiCost,tools:toolsCost,human:humanCost,fixed:fixedCost,successful_tasks:success,cost_per_success:success>0?total/success:null,roi_percentage:roi,incremental_value:incrementalValue,net_value:net,assumption_note:"Illustrative scenario, not an actual enterprise quote or industry benchmark."};
    }catch(e){
      resetOutputs("Check calculator inputs");
      $("calcWarning").hidden=false;
      $("calcWarning").textContent=e.message||"Unable to calculate this scenario.";
      $("selectedRates").textContent="Review your fields to continue.";
    }
  }
  function applyPreset(key) {
    const scenario=PRESETS[key];
    if(!scenario)return;
    currentPreset=key;
    for(const [id,value] of Object.entries(scenario))$(id).value=value;
    document.querySelectorAll("[data-preset]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.preset===key)));
    calculate();
  }
  function exportRows() {
    if(!visibleRows.length)return;
    const escape=s=>'"'+String(s??"").replaceAll('"','""')+'"';
    const data=[["Provider","Model","Model ID","Input USD / 1M","Cached input USD / 1M","Output USD / 1M","Source verified UTC","Official pricing source"]];
    for(const m of visibleRows){
      const p=activeRates(m,0)?.rates||{};
      data.push([m.provider,m.model,m.model_id,p.input??"",p.cached_input??"",p.output??"",m.provenance?.verified_at||"",m.provenance?.evidence?.pricing||""]);
    }
    const csv=data.map(row=>row.map(escape).join(",")).join("\r\n");
    const blob=new Blob(["\ufeff",csv],{type:"text/csv;charset=utf-8"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a");a.href=url;a.download="sxf-agent-cost-model-prices.csv";document.body.appendChild(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),2000);
  }
  async function copySummary(){
    if(!lastSnapshot)return;
    const s=lastSnapshot;
    const report=[
      "SXF AI Agent Cost Index — illustrative scenario",
      "Model: "+s.model+" ("+s.provider+")",
      "Source verified: "+(s.verification||"Not recorded"),
      "Monthly task volume: "+s.inputs.monthlyTasks,
      "Modeled monthly cost: "+currency(s.monthly_cost),
      "Model API: "+currency(s.model_api),
      "Tools: "+currency(s.tools),
      "Human review: "+currency(s.human),
      "Infrastructure + operations + build allocation: "+currency(s.fixed),
      "Expected successful tasks: "+s.successful_tasks,
      "Cost / successful task: "+(s.cost_per_success===null?"N/A":currency(s.cost_per_success)),
      "Modeled incremental value: "+currency(s.incremental_value),
      "Modeled ROI: "+(s.roi_percentage===null?"N/A":s.roi_percentage.toFixed(1)+"%"),
      "Methodology: https://sxf.si/ai-agent-cost/#method",
      "Illustrative estimate; verify all enterprise assumptions."
    ].join("\n");
    try {
      await navigator.clipboard.writeText(report);
      const button=$("copyScenario");
      const old=button.textContent;button.textContent="Copied to clipboard ✓";setTimeout(()=>button.textContent=old,1800);
    }catch(e){
      const blob=new Blob([report],{type:"text/plain"});
      const url=URL.createObjectURL(blob);
      const a=document.createElement("a");a.href=url;a.download="sxf-ai-agent-cost-scenario.txt";document.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),2000);
    }
  }
  async function init(){
    // The calculator is interactive, not a server form: Enter must not reload the page.
    $("agentCostForm").addEventListener("submit", event => event.preventDefault());
    for(const id of fields)$(id).addEventListener("input",calculate);
    $("calcModel").addEventListener("change",calculate);
    for(const id of ["rateSearch","providerFilter","agentOnly"])$(id).addEventListener(id==="rateSearch"?"input":"change",updateRows);
    $("exportRates").addEventListener("click",exportRows);
    $("copyScenario").addEventListener("click",copySummary);
    document.querySelectorAll("[data-preset]").forEach(btn=>btn.addEventListener("click",()=>applyPreset(btn.dataset.preset)));
    document.querySelector('[data-preset="support"]')?.setAttribute("aria-pressed","true");
    try{
      const response=await fetch(catalogUrl,{cache:"no-store"});
      if(!response.ok)throw new Error("HTTP "+response.status);
      const payload=await response.json();
      if(!Array.isArray(payload.models)||!payload.models.length||!payload.source_verified)throw new Error("Invalid SXF catalog response");
      catalog=payload;
      populateCatalog();
    }catch(error){
      status("error","The source-linked model catalog is unavailable. No cached or guessed prices are shown. Retry the page later or use the main SXF pricing directory.");
      resetOutputs("Catalog unavailable");
      $("rateRows").replaceChildren();
      const tr=document.createElement("tr"),td=cell("Model prices temporarily unavailable. Visit the main pricing database.");td.colSpan=6;tr.appendChild(td);$("rateRows").appendChild(tr);
      $("rateCount").textContent="No verified data loaded";
    }
  }
  init();
})();
