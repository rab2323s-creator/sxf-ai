/* SXF / AI Water Footprint Lab — educational scenario tool, not a provider meter. */
(() => {
  "use strict";
  const decoder = document.querySelector("[data-water-decoder]");
  const claims = {
    google:{category:"GOOGLE RESEARCH / MAY 2025",title:"Google’s median Gemini text prompt",number:"0.26 mL per median text prompt; 0.24 Wh.",workload:"Median text prompt in Gemini Apps, May 2025.",boundary:"On-site data-center water for cooling in Google's serving estimates; not a complete lifecycle water total.",caveat:"Cannot infer an individual ChatGPT request or compare against wider lifecycle totals.",url:"https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference"},
    openai:{category:"PUBLIC COMPANY STATEMENT / JUNE 2025",title:"Average ChatGPT query estimate",number:"Approximately 0.32 mL of water; 0.34 Wh.",workload:"An average ChatGPT query, described in a June 2025 public statement.",boundary:"The public statement did not provide a full reproducible water-boundary method.",caveat:"Not independently verifiable per workload, model, data-center location or lifecycle stage.",url:"https://blog.samaltman.com/the-gentle-singularity"},
    mistral:{category:"PROVIDER LIFECYCLE DISCLOSURE / 2025",title:"Mistral’s 400-token Le Chat response",number:"45 mL of water in the stated lifecycle approach.",workload:"A 400-token answer from Le Chat.",boundary:"Broader lifecycle assessment than an on-site-only cooling figure; end-user device excluded.",caveat:"Do not treat 45 mL versus 0.26 mL as an apples-to-apples comparison of model efficiency.",url:"https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai/"},
    research:{category:"ACADEMIC MODEL / GPT-3",title:"Li et al. ‘Making AI Less Thirsty’",number:"500 mL for about 10–50 medium-length GPT-3 responses in the model.",workload:"A modeled group of GPT-3 text responses; location and timing affect the result.",boundary:"Both on-site cooling and water for electricity production were considered.",caveat:"Not a direct measurement of a present-day ChatGPT prompt, or a single bottle per question.",url:"https://doi.org/10.1145/3724499"}
  };
  if (decoder) {
    const fields = {claimCategory:"category",claimTitle:"title",claimNumber:"number",claimWorkload:"workload",claimBoundary:"boundary",claimCaveat:"caveat"};
    decoder.querySelectorAll("[data-claim]").forEach(button => {
      button.addEventListener("click", () => {
        const data=claims[button.dataset.claim];
        if(!data)return;
        decoder.querySelectorAll("[data-claim]").forEach(x => x.setAttribute("aria-pressed",String(x===button)));
        for(const [id,k] of Object.entries(fields)) {const el=document.getElementById(id);if(el)el.textContent=data[k];}
        const link=document.getElementById("claimLink");if(link)link.href=data.url;
      });
    });
  }
  const lab=document.querySelector("[data-water-lab]");
  if(!lab)return;
  const get=id=>document.getElementById(id);
  const inputs={requests:get("waterRequests"),energy:get("waterEnergy"),wue:get("waterWue"),pue:get("waterPue"),grid:get("waterGrid")};
  if(Object.values(inputs).some(x=>!x))return;
  const fmt=(num,max=1)=>new Intl.NumberFormat("en-US",{maximumFractionDigits:max}).format(num);
  const presets={
    dry:{requests:100,energy:0.3,wue:0,pue:1.35,grid:1.5},
    reference:{requests:100,energy:0.3,wue:1.15,pue:1.2,grid:1.5},
    evap:{requests:100,energy:0.3,wue:2.5,pue:1.15,grid:1.5}
  };
  let last="";
  const render=()=>{
    const requests=Number(inputs.requests.value),energy=Number(inputs.energy.value),wue=Number(inputs.wue.value),pue=Number(inputs.pue.value),grid=Number(inputs.grid.value);
    const direct=requests*energy*wue,indirect=requests*energy*pue*grid,total=direct+indirect,facility=requests*energy*pue;
    get("waterRequestsValue").textContent=fmt(requests,0)+" requests";get("waterEnergyValue").textContent=fmt(energy)+" Wh";get("waterWueValue").textContent=fmt(wue,2)+" L/kWh";get("waterPueValue").textContent=fmt(pue,2)+"×";get("waterGridValue").textContent=fmt(grid)+" L/kWh";
    get("waterTotal").innerHTML=fmt(total)+" <small>mL</small>";get("waterRequestSummary").textContent=fmt(requests,0);get("waterDirect").textContent=fmt(direct)+" mL";get("waterIndirect").textContent=fmt(indirect)+" mL";get("waterElectricity").textContent=fmt(facility)+" Wh";
    get("waterDirectBar").style.width=(total>0?100*direct/total:0)+"%";get("waterIndirectBar").style.width=(total>0?100*indirect/total:0)+"%";
    last="SXF Water Footprint Lab — illustrative scenario, not provider measurement. Requests: "+requests+"; IT energy/request: "+energy+" Wh; WUE: "+wue+" L/kWh; PUE: "+pue+"; grid water intensity: "+grid+" L/kWh. On-site: "+fmt(direct,2)+" mL; electricity-related: "+fmt(indirect,2)+" mL; total: "+fmt(total,2)+" mL; facility electricity: "+fmt(facility,2)+" Wh. Source: https://sxf.si/guides/why-does-ai-use-water/";
  };
  Object.values(inputs).forEach(x=>x.addEventListener("input",render));
  lab.querySelectorAll("[data-water-preset]").forEach(button=>button.addEventListener("click",()=>{const values=presets[button.dataset.waterPreset];if(!values)return;for(const [key,val] of Object.entries(values))inputs[key].value=String(val);render();}));
  get("waterCopy").addEventListener("click",async()=>{const target=get("waterCopyStatus");try {if(!navigator.clipboard||!window.isSecureContext)throw new Error("Clipboard unavailable");await navigator.clipboard.writeText(last);target.textContent="Scenario copied."; }catch(e){target.textContent="Copy is unavailable in this browser; use the displayed values."; }});
  render();
})();