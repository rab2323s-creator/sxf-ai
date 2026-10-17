(()=>{"use strict";if(!document.querySelector(".af-article-page"))return;
const $=id=>document.getElementById(id);
const info={
graph:{name:"LangGraph",url:"https://docs.langchain.com/oss/python/langgraph/quickstart",why:"You need observable execution states, checkpoints, interrupts and retries across long-running runs.",alt:"Microsoft Agent Framework when typed enterprise workflow integration matters."},
roles:{name:"CrewAI",url:"https://docs.crewai.com/en/concepts/flows",why:"Specialist agent roles and explicit Flows are core to the workflow design.",alt:"LangGraph when branch control and replay dominate."},
handoffs:{name:"OpenAI Agents SDK",url:"https://developers.openai.com/api/docs/guides/agents/sdk",why:"Code-first agents, tools and handoffs with SDK-managed runs and tracing fit the stated requirement.",alt:"LangGraph for explicit cross-step graph checkpoints."},
enterprise:{name:"Microsoft Agent Framework",url:"https://learn.microsoft.com/en-us/agent-framework/overview/",why:"Typed executors, enterprise middleware, state and graph workflows fit this requirement.",alt:"LangGraph if the application is Python-first and requires custom graph orchestration."},
cloud:{name:"Google ADK",url:"https://adk.dev/agents/workflow-agents/",why:"The Google agent ecosystem offers sessions, workflow composition and cloud integration.",alt:"LangGraph when vendor-neutral graph control is central."},
simple:{name:"Plain Python workflow",url:"#simple",why:"Predictable policy steps need straightforward functions, not autonomous delegation.",alt:"Add an agent library only when a measurable requirement justifies it."}
};
function render(){
const need=$("afControl").value,stack=$("afStack").value,risk=$("afRisk").value;
let v=info[need];
if(need!=="simple"&&need!=="graph"&&need!=="roles"&&need!=="handoffs"){
  if(stack==="microsoft")v=info.enterprise;
  else if(stack==="google")v=info.cloud;
  else if(stack==="openai"&&need!=="enterprise")v=info.handoffs;
}
const box=$("afDecisionResult");box.replaceChildren();
const h=document.createElement("h3");h.textContent="Start by testing: "+v.name;box.append(h);
const p=document.createElement("p");p.textContent=v.why;box.append(p);
const ul=document.createElement("ul");
const notes=[
"Test the same policy fixture, model settings and allowed tool set.",
risk==="high"?"MANDATORY: use backend authorization, a human approval step before writes and idempotent side effects.":risk==="medium"?"Require review/rollback for write actions, audit trail and retry tests.":"Keep the pilot read-only and use short-lived credentials.",
"Compare verified acceptance rate, p95 runtime, unit cost and restart recovery.",
"Alternative: "+v.alt
];notes.forEach(t=>{const li=document.createElement("li");li.textContent=t;ul.append(li)});box.append(ul);
const a=document.createElement("a");a.href=v.url;a.textContent="Read the starting documentation ↗";if(v.url.startsWith("https")){a.target="_blank";a.rel="noopener noreferrer"}box.append(a);
}
$("afDecide").addEventListener("click",render);render();
document.querySelectorAll("[data-copy-code]").forEach(btn=>btn.addEventListener("click",async()=>{
const code=btn.closest(".af-code")?.querySelector("code")?.textContent||"";
try{await navigator.clipboard.writeText(code);btn.textContent="Copied";setTimeout(()=>btn.textContent="Copy code",1400)}
catch(e){btn.textContent="Select code to copy"}
}));
})();