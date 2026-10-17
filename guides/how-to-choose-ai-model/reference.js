(()=>{"use strict";
const root=document.querySelector(".select-model-page");if(!root)return;
const $=id=>document.getElementById(id);
const link=(path,label)=>'<a href="'+path+'">'+label+' ↗</a>';
const data={
 coding:{question:"Can it deliver changes that pass your real repository tests?",metrics:"CI pass rate, review fixes, p95 completion time and tool-call cost",api:[["Claude Sonnet 5.5","/models/claude-sonnet-5-5/"],["GPT-6.1 Sol","/models/gpt-6-1-sol/"],["Claude Opus 5.5","/models/claude-opus-5-5/"]],local:[["Mistral Small 4","/models/mistral-small-4/"],["Gemma 4 31B","/models/gemma-4-31b-it/"]]},
 rag:{question:"Are answers factual, grounded in retrieved evidence and correct when evidence is missing?",metrics:"Citation faithfulness, abstention, long-document accuracy, p95 time",api:[["GPT-6.1 Sol","/models/gpt-6-1-sol/"],["Claude Sonnet 5.5","/models/claude-sonnet-5-5/"],["GPT-6 Luna","/models/gpt-6-luna/"]],local:[["Mistral Small 4","/models/mistral-small-4/"],["Gemma 4 31B","/models/gemma-4-31b-it/"]]},
 agent:{question:"Does the agent actually complete authorized tasks across repeated runs?",metrics:"Verified state, run-to-run reliability, tool recovery, permissions",api:[["GPT-6.1 Sol","/models/gpt-6-1-sol/"],["Claude Sonnet 5.5","/models/claude-sonnet-5-5/"],["GPT-6 Astra","/models/gpt-6-astra/"]],local:[["Mistral Small 4","/models/mistral-small-4/"],["Gemma 4 31B","/models/gemma-4-31b-it/"]]},
 support:{question:"Does it produce valid answers or structured records within your SLA?",metrics:"Correct structured outputs, escalation rate, throughput, cost per valid record",api:[["GPT-6 Luna","/models/gpt-6-luna/"],["Claude Haiku 5.5","/models/claude-haiku-5-5/"],["GPT-6.1 Sol","/models/gpt-6-1-sol/"]],local:[["Gemma 4 31B","/models/gemma-4-31b-it/"],["Mistral Small 4","/models/mistral-small-4/"]]},
 research:{question:"Are factual findings traceable, grounded and useful?",metrics:"Verified factual claims, abstention, long-context accuracy and review time",api:[["GPT-6 Astra","/models/gpt-6-astra/"],["Claude Opus 5.5","/models/claude-opus-5-5/"],["GPT-6.1 Sol","/models/gpt-6-1-sol/"]],local:[["Mistral Small 4","/models/mistral-small-4/"],["Gemma 4 31B","/models/gemma-4-31b-it/"]]}
};
const concerns={quality:"Set a hard acceptance threshold before comparing price.",cost:"Compare cost per accepted outcome, including repeat attempts and reviewer time.",speed:"Make p95 end-to-end latency a release gate, not just tokens per second.",privacy:"Verify data retention, service region, tool permissions and contract terms first."};
function render(){const task=$("useCase").value,host=$("hosting").value,p=$("priority").value,entry=data[task],candidates=entry[host];const out=$("selectorResult");out.textContent="";
const heading=document.createElement("strong");heading.textContent="Starting shortlist · "+(host==="local"?"self-hosted":"managed API");out.appendChild(heading);
const para=document.createElement("p");para.textContent="Decision question: "+entry.question;out.appendChild(para);
const list=document.createElement("ul");[["Hard gate",host==="local"?"Validate weights, license, GPU/RAM, local logs and network access.":"Validate endpoint access, region, retention and required features."],["Primary metric",entry.metrics],["Priority",concerns[p]],["Comparison method","Run the same 50 representative tests per candidate. This shortlist is not a model ranking."]].forEach(pair=>{const li=document.createElement("li");const b=document.createElement("b");b.textContent=pair[0]+": ";li.appendChild(b);li.appendChild(document.createTextNode(pair[1]));list.appendChild(li)});out.appendChild(list);
const div=document.createElement("div");div.className="select-links";candidates.forEach(([name,path])=>{const a=document.createElement("a");a.href=path;a.textContent="Evaluate "+name+" ↗";div.appendChild(a)});out.appendChild(div);
}
$("findModels").addEventListener("click",render);render();
const ids=["requests","tokensIn","tokensOut","priceIn","priceOut","passRate","extras"];
const usd=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:3});
const fmt=new Intl.NumberFormat("en-US",{maximumFractionDigits:0});
function calculate(){const values=ids.map(id=>Number($(id).value));const [n,ti,to,pi,po,pct,extra]=values;if(values.some(v=>!Number.isFinite(v)||v<0)||n<=0||pct<=0||pct>100||n>100000000||ti>10000000||to>10000000){["costTotal","costAccepted","costPerSuccess"].forEach(id=>$(id).textContent="Check inputs");return}
const perAttempt=ti*pi/1000000+to*po/1000000+extra,monthly=perAttempt*n,accepted=n*pct/100;
$("costTotal").textContent=usd.format(monthly);$("costAccepted").textContent=fmt.format(accepted);$("costPerSuccess").textContent=usd.format(monthly/accepted)}
ids.forEach(id=>$(id).addEventListener("input",calculate));calculate();
})();