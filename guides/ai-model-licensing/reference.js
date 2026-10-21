(()=>{"use strict";const $=id=>document.getElementById(id);
const controls=["lic-family","lic-use","lic-changed","lic-region","lic-origin","lic-policy"].map($);
const out=$("lic-results");let last="";
if(controls.every(Boolean)&&out){function evaluate(){const [family,use,changed,region,origin,policy]=controls.map(x=>x.value),checks=[];
checks.push("Record the exact model ID, provider, weight commit/SHA256, source URL, retrieval date and any accepted terms.");
checks.push("Collect the complete license text covering the actual weights; model-card metadata alone is not authoritative.");
checks.push("Check separate licenses for tokenizer, code, adapters, datasets and deployment dependencies.");
if(family==="apache"){checks.push("Inspect Apache-2.0 section 3 patent provisions, section 4 redistribution, modified-file notices, and any required NOTICE file.");}
else if(family==="mit"){checks.push("Review the scope of the MIT grant and preserve the copyright and permission notice for copies/substantial portions distributed.");}
else if(family==="custom"){checks.push("Escalate the full version-specific custom agreement, referenced policies, commercial thresholds, attribution, territory and use restrictions to qualified legal review.");}
else checks.push("No verified license: do not infer commercial rights from a public download. Escalate to the rightsholder and counsel.");
if(use==="redistribute")checks.push("Prepare redistributed weight package: license copy, attribution notices, change log, third-party dependency inventory and recipient restrictions.");
if(use==="api")checks.push("Check whether hosted inference/API access counts as distribution or a separately defined hosted service under these exact terms.");
if(changed==="yes")checks.push("Document fine-tuning or quantization changes, derivative/redistribution clauses and notices for any modified files.");
if(region==="eu")checks.push("Review EU business location, role under the EU AI Act, privacy, copyright and version-specific geographic exceptions; do not presume the open-source exemption.");
if(region==="other")checks.push("Identify applicable jurisdiction, export controls, sanctions, privacy and local use restrictions.");
if(origin==="no")checks.push("BLOCKER: the released weight artifact has no pinned origin/hash evidence. Preserve provenance before launch.");
if(policy==="unknown")checks.push("BLOCKER: incorporated acceptable-use or model-specific conditions have not been checked.");
last="SXF AI Model License Evidence Checklist\nThis is not a legal clearance.\n\n"+checks.map((c,i)=>(i+1)+". "+c).join("\n")+"\n\nDocument human reviewer, evidence URLs and decision version.";
out.replaceChildren();let h=document.createElement("strong");h.textContent="Your due-diligence evidence checklist";out.append(h);let p=document.createElement("p");p.textContent="A research checklist only. Neither the license label nor this tool grants or verifies commercial permission.";out.append(p);const list=document.createElement("ul");checks.forEach(c=>{const li=document.createElement("li");li.textContent=c;list.append(li)});out.append(list);}
controls.forEach(x=>x.addEventListener("change",evaluate));evaluate();}
const btn=$("lic-copy");if(btn)btn.addEventListener("click",async()=>{try{await navigator.clipboard.writeText(last);btn.textContent="Copied";}catch(e){btn.textContent="Copy not supported";}});
})();
