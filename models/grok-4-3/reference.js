(()=>{"use strict";const $=id=>document.getElementById(id);
const ids=["g43-input","g43-cached","g43-output","g43-mode","g43-calls","g43-tools"].map($);
if(ids.every(Boolean)){const calculate=()=>{const [p,c,o,mode,n,extras]=ids.map(x=>x.value);const [inp,cache,out,calls,toolCost]=[p,c,o,n,extras].map(Number);
const outputs=["g43-tier","g43-single","g43-month","g43-comparison"].map($);
if(![inp,cache,out,calls,toolCost].every(Number.isFinite)||inp<0||inp>1000000||cache<0||cache>inp||out<0||inp+out>1000000||calls<0||calls>1e7||toolCost<0){outputs.forEach(e=>e.textContent="Check input / 1M window");return}
const long=inp>=200000,mult=mode==="batch"?.8:1,uncached=inp-cache;
const unit=((uncached*(long?2.5:1.25)+cache*(long?.4:.2)+out*(long?5:2.5))/1e6)*mult+toolCost;
const fmt=x=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:5}).format(x);
outputs[0].textContent=long?"Long-context rates (≥200K prompt)":"Short-context rates";
outputs[1].textContent=fmt(unit);outputs[2].textContent=fmt(unit*calls);
outputs[3].textContent=(inp/1000).toLocaleString("en-US")+"K prompt + "+(out/1000).toLocaleString("en-US")+"K output; "+(cache/1000).toLocaleString("en-US")+"K assumed cached";};
ids.forEach(x=>x.addEventListener("input",calculate));calculate();}
const task=["g43-use","g43-context-need","g43-cost","g43-output-need"].map($),target=$("g43-plan");
if(task.every(Boolean)&&target){const render=()=>{const [use,context,budget,format]=task.map(x=>x.value);
const lines=[];
if(context==="huge")lines.push("Inspect tokenized prompt sizes and long-context cost tiers; test retrieval or context reduction before sending 200K+ tokens.");
if(context==="normal")lines.push("Use the short-context price tier when your full prompt stays below 200K tokens; verify totals and token truncation.");
if(use==="agents")lines.push("Test function argument schema validity, tool side-effect idempotency, multi-turn reasoning preservation and failure recovery.");
if(use==="vision")lines.push("Verify image input and JSON output quality on permission-cleared diagrams and scanned documents; this model is not an image generator.");
if(use==="documents")lines.push("Score evidence citation, unsupported claims and extraction accuracy with a separate human-verified reference set.");
if(budget==="tight")lines.push("Try cache-friendly conversation structure and eligible Batch processing; include real server-tool fees and retries.");
if(format==="json")lines.push("Use documented structured output schema and validate semantic correctness after schema validation.");
if(format==="prose")lines.push("Evaluate clarity, grounded citations and direct task completion instead of relying on vendor leaderboard ranks.");
target.replaceChildren();const h=document.createElement("strong");h.textContent="Priorities for your Grok 4.3 evaluation";target.append(h);let ul=document.createElement("ul");lines.forEach(x=>{const li=document.createElement("li");li.textContent=x;ul.append(li)});target.append(ul);let p=document.createElement("p");p.textContent="A transparent workload rubric, not a quality benchmark or paid request.";target.append(p);};task.forEach(x=>x.addEventListener("change",render));render();}
})();