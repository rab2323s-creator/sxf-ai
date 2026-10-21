(()=>{"use strict";const el=id=>document.getElementById(id);
const price={standard:{old:[2.5,4,15],flare:[5,8,30]},batch:{old:[1.25,2,7.5],flare:[2.5,4,15]}};
const ids=["gf-mode","gf-text","gf-image","gf-out-old","gf-out-flare","gf-attempts","gf-accept-old","gf-accept-flare"].map(el);
if(ids.every(Boolean)){const render=()=>{const [mode,txt,img,outOld,outNew,tries,acceptOld,acceptFlare]=ids.map(x=>x.value);
const vals=[txt,img,outOld,outNew,tries,acceptOld,acceptFlare].map(Number);
const targets=["gf-unit-old","gf-unit-flare","gf-total-old","gf-total-flare","gf-accepted-old","gf-accepted-flare"].map(el);
if(!vals.every(Number.isFinite)||vals.some(v=>v<0)||Number(tries)>10000000||Number(acceptOld)>100||Number(acceptFlare)>100||Number(acceptOld)<=0||Number(acceptFlare)<=0){targets.forEach(x=>x.textContent="Check inputs");return;}
const [t,i,a,b,n,qa,qb]=vals,r1=price[mode].old,r2=price[mode].flare;
const c1=(r1[0]*t+r1[1]*i+r1[2]*a)/1e6,c2=(r2[0]*t+r2[1]*i+r2[2]*b)/1e6;
const fmt=v=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:5}).format(v);
targets[0].textContent=fmt(c1);targets[1].textContent=fmt(c2);
targets[2].textContent=fmt(n*c1);targets[3].textContent=fmt(n*c2);
targets[4].textContent=fmt(c1/(qa/100));targets[5].textContent=fmt(c2/(qb/100));
el("gf-assumptions").textContent="Inputs are hypothetical usage/acceptance, not SXF-measured performance. Different quality settings and models may use different output tokens. No caching or extra mainline Responses model charges are included.";};
ids.forEach(x=>x.addEventListener("input",render));render();}
const opts=["gf-task","gf-edit","gf-speed","gf-scale"].map(el),result=el("gf-plan");
if(opts.every(Boolean)&&result){const update=()=>{const [task,edit,speed,scale]=opts.map(x=>x.value);const lines=[];
if(task==="brand")lines.push("Test Flare and GPT-Image-2 on exact logos, product labels and subject preservation; use a blind written failure rubric.");
if(task==="text")lines.push("Include numerals, multilingual labels and cropped poster formats. Verify every rendered word manually.");
if(task==="photo")lines.push("Test reference identity, geometry, material properties, background and permitted asset rights.");
if(edit==="many")lines.push("Run multi-turn edits with Responses API and log how often unrelated details drift; distinguish direct Images API limits.");
if(speed==="critical")lines.push("Collect median and p95 wall-clock latency with your own API requests; company-reported speed improvement is not a guaranteed SLA.");
if(scale==="large")lines.push("Measure completed images, rejected variants, text/image token usage, Batch availability, caching eligibility, moderation and costs per accepted asset.");
else lines.push("Start with a small, pre-registered portfolio of prompts using low/medium/high quality, and compare variants separately.");
result.replaceChildren();const h=document.createElement("strong");h.textContent="Your workload-first evaluation priorities";result.append(h);
const ul=document.createElement("ul");lines.forEach(x=>{const li=document.createElement("li");li.textContent=x;ul.append(li)});result.append(ul);
const p=document.createElement("p");p.textContent="Editorial checklist only; no hidden winner ranking and no personal data sent.";result.append(p);};opts.forEach(x=>x.addEventListener("change",update));update();}})();