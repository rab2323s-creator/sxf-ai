/* Premium comparison decision cockpit. Non-destructive enhancement to Compare V2.
   Facts are drawn only from the existing rendered comparison and verified evaluation data. */
(() => {
  "use strict";
  const root = document.querySelector("[data-compare-builder]");
  if (!root) return;
  const panel = document.getElementById("compareDecisionCockpit");
  const goal = document.getElementById("compareDecisionGoal");
  const evidenceOnly = document.getElementById("compareDecisionEvidenceOnly");
  const share = document.getElementById("compareDecisionShare");
  const shareStatus = document.getElementById("compareDecisionShareStatus");
  const engines = window.SxfCompareEngine;
  const selects = [document.getElementById("compareModelA"), document.getElementById("compareModelB")];
  const ids = ["compareInputTokens","compareCachedTokens","compareOutputTokens","compareMonthlyRequests"];
  let catalog, evals;
  const escapeHtml = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const money = n => "$" + n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
  const goals = {
    budget: {label:"Lowest verified direct token cost", categories:[]},
    coding: {label:"Coding and agent workflows", categories:["agentic-coding","scientific-coding"]},
    research: {label:"Research and scientific reasoning",categories:["frontier-science-reasoning","multidisciplinary-reasoning","long-context-reasoning"]},
    business: {label:"Business and knowledge work",categories:["agentic-knowledge-work","business-automation","professional-knowledge-work"]}
  };
  const output = (headline, lead, cards, foot) => {
    panel.innerHTML = '<div class="compare-decision-head"><div><span class="compare-decision-kicker">DECISION DESK</span><h3>'+headline+'</h3><p>'+lead+'</p></div><span class="compare-decision-pill">Evidence first</span></div><div class="compare-decision-grid">'+cards+'</div><p class="compare-decision-foot">'+foot+'</p>';
  };
  const cell = (label,value,note) => '<div class="compare-decision-cell"><span>'+label+'</span><strong>'+value+'</strong><small>'+note+'</small></div>';
  function render() {
    if (!panel || !catalog || !evals || !engines) return;
    const byId = new Map(catalog.models.map(m => [m.model_id,m]));
    const left=byId.get(selects[0]?.value), right=byId.get(selects[1]?.value);
    if (!left || !right || left.model_id===right.model_id) {
      output("Select two different models","A comparison requires two valid model selections.","","No winner is inferred.");return;
    }
    const task=engines.workload(Object.fromEntries(["input","cached","output","requests"].map((key,i)=>[key,document.getElementById(ids[i])?.value])));
    if (!task.ok){output("Review workload inputs",escapeHtml(task.error),"","Results are withheld until inputs are valid.");return;}
    const warnings=[engines.capacityWarnings(left,task),engines.capacityWarnings(right,task)];
    const priced=[left,right].map((m,i)=> warnings[i].length ? {available:false,reason:"Exceeds model limits"}:engines.pricing(m,task,catalog.source_verified));
    const pairs=engines.benchmarkPairs(evals,left.model_id,right.model_id);
    const cfgMatches=pairs.filter(p=>!p.configurationDiffers);
    const chosen=goals[goal.value]||goals.budget;
    const relevant=pairs.filter(p=>chosen.categories.includes(p.benchmark.category));
    const comparable=relevant.filter(p=>!p.configurationDiffers);
    const useful=relevant.filter(p=>!evidenceOnly.checked||!p.configurationDiffers);
    const evidenceLabel = comparable.length >= 3 ? "Multi-test evidence" : comparable.length ? "Limited evidence" : "Insufficient comparable evidence";
    let title="",desc="";
    if(goal.value==="budget"){
      if(priced.every(p=>p.available)){
        const delta=priced[0].monthly-priced[1].monthly;
        title=Math.abs(delta)<1e-8?"Comparable direct cost":"Lower estimated direct cost";
        desc=Math.abs(delta)<1e-8?"Both models have equal estimated direct-token costs for this workload.":
          escapeHtml(delta<0?left.model:right.model)+" costs "+money(Math.abs(delta))+" less per month on these assumptions.";
      }else{
        title="No supported cost conclusion";
        desc="At least one model lacks applicable verified token prices, or this workload exceeds its limits.";
      }
    }else{
      title="Evidence for "+chosen.label.toLowerCase();
      desc=comparable.length ? "Matching-configuration benchmark observations are available below; validate fit on your own tasks." :
        "Insufficient matching-configuration evidence for a task winner. Do not infer quality from price or capability tags.";
    }
    const priceCard=(m,i)=>{
      const p=priced[i];
      return cell(escapeHtml(m.model)+(i===0?" · A":" · B"),p.available?money(p.monthly)+"/mo":"Unavailable",p.available?"Direct tokens · "+(p.long?"long-context":"standard")+" pricing":escapeHtml(p.reason||"Unavailable"));
    };
    const shown=useful.slice(0,4);
    const evidenceCards=shown.map(p=>{
      const condition=p.configurationDiffers?"Different settings — not controlled":"Same recorded configuration";
      return cell(escapeHtml(p.benchmark.name),
        escapeHtml(p.left.score)+" vs "+escapeHtml(p.right.score)+" "+escapeHtml(p.benchmark.unit||""),
        escapeHtml(condition)+" · <a href='"+escapeHtml(p.left.source_url)+"' target='_blank' rel='noopener noreferrer'>Source A ↗</a> · <a href='"+escapeHtml(p.right.source_url)+"' target='_blank' rel='noopener noreferrer'>Source B ↗</a>");
    }).join("");
    const capabilityComparison = cell("Documented features",
      escapeHtml(left.model)+" / "+escapeHtml(right.model),
      "Input: "+escapeHtml((left.modalities?.input||[]).join(", ") || "Not published")+" vs "+escapeHtml((right.modalities?.input||[]).join(", ") || "Not published")+
      " · Context: "+escapeHtml(left.context_window?.toLocaleString?.() || "Unknown")+" vs "+escapeHtml(right.context_window?.toLocaleString?.() || "Unknown")+" tokens");
    const evidenceCoverage = cell("Task evidence confidence",evidenceLabel,
      comparable.length+" matched-configuration independent observations for "+escapeHtml(chosen.label)+
      "; "+(relevant.length-comparable.length)+" with differing configurations. Benchmark categories without matched evidence are excluded.");
    const factCards=cell("Price evidence",priced.every(p=>p.available)?"Both available":"Incomplete","Catalog dated "+escapeHtml(catalog.source_verified||"unknown"))+
      cell("Independent measurements",String(pairs.length)+" shared","Only same benchmark and evaluation group are paired")+
      cell("Matching configurations",String(cfgMatches.length)+" observations","Different reasoning effort / fallback is kept separate");
    output(title,desc,priceCard(left,0)+priceCard(right,1)+factCards+capabilityComparison+evidenceCoverage+
      (goal.value==="budget"?"":evidenceCards), 
      "Not a universal ranking. "+pairs.length+" paired independent benchmark observations; "+cfgMatches.length+" recorded with the same configuration. "+
      "Quality, latency and reliability on your workloads remain untested. "+
      "Evaluation data dated "+escapeHtml(evals.source_verified||"unknown")+".");
  }
  function restore() {
    const q=new URLSearchParams(location.search),g=q.get("goal");
    if(g && goals[g]) goal.value=g;
    for(const [param,id] of [["input",ids[0]],["cached",ids[1]],["output",ids[2]],["monthly",ids[3]]]){
      const v=q.get(param);if(v!==null && /^\d{1,9}$/.test(v)){const el=document.getElementById(id);if(el)el.value=v;}
    }
  }
  goal.addEventListener("change",render);
  evidenceOnly.addEventListener("change",render);
  root.addEventListener("compare:ready",render);
  root.addEventListener("change",render);
  root.addEventListener("input",render);
  share.addEventListener("click",async ()=>{
    const u=new URL(location.href);
    for(const key of ["a","b","goal","input","cached","output","monthly"])u.searchParams.delete(key);
    [["a",selects[0]?.value],["b",selects[1]?.value],["goal",goal.value],
      ...ids.map((id,i)=>[["input","cached","output","monthly"][i],document.getElementById(id)?.value])].forEach(([key,value])=>{if(value!=null)u.searchParams.set(key,value);});
    try{await navigator.clipboard.writeText(u.href);shareStatus.textContent="Comparison link copied.";}
    catch{shareStatus.textContent="Copy this URL from the address bar: "+u.href;}
  });
  restore();
  Promise.all([fetch("/data/model-pricing.json").then(r=>{if(!r.ok)throw Error("catalog");return r.json()}),
    fetch("/data/model-evaluations.json").then(r=>{if(!r.ok)throw Error("evaluations");return r.json()})])
    .then(([c,e])=>{catalog=c;evals=e;render()})
    .catch(()=>{panel.textContent="Decision data unavailable. Existing comparison remains accessible.";});
})();
