/* SXF local model finder v2: data-driven, browser-only, source-provenance aware.
 * File size != VRAM. The allowances are planning heuristics, never measurements.
 */
(function(root){
'use strict';
const ALLOWANCES=Object.freeze({4096:2,8192:3,16384:4.5,32768:7});
const CAPACITIES=[4,6,8,10,12,16,20,24,32,48,64,80,96,128];
const CATALOG_URL='/data/local-llm-catalog.json';
let MODELS=[];
let resultLimit=12;
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const validUrl=u=>typeof u==='string'&&u.startsWith('https://')&&/^(https:\/\/)(huggingface\.co|ollama\.com)(\/|$)/.test(u);
function validate(data){
 if(!data||data.schemaVersion!==2||!Array.isArray(data.models))throw Error('Invalid catalog schema');
 const ids=new Set();
 const out=[];
 for(const m of data.models){
  if(!m||typeof m.id!=='string'||ids.has(m.id)||typeof m.name!=='string'||!Number.isFinite(m.sizeGb)||m.sizeGb<=0||m.sizeGb>600||!validUrl(m.sourceUrl)||!Array.isArray(m.workloads)||!m.workloads.length||m.workloads.some(x=>!['coding','chat','vision'].includes(x)))throw Error('Invalid model record');
  if(m.format==='GGUF'&&(!Number.isSafeInteger(m.sizeBytes)||m.sizeBytes<1e6||m.sizeEvidence!=='hub-file-bytes'))throw Error('Unverified GGUF size');
  ids.add(m.id);out.push(m);
 }
 if(!out.length)throw Error('Empty catalog');
 return out;
}
function joinBenchmarks(list,data){
 if(!data||data.schemaVersion!==1||!Array.isArray(data.measurements))return list;
 const map=new Map();
 for(const b of data.measurements){
  if(!b||typeof b.modelId!=='string'||typeof b.gpu!=='string'||!b.gpu.trim()||typeof b.runtime!=='string'||!b.runtime.trim()||typeof b.quantization!=='string'||!b.quantization.trim()||typeof b.measuredAt!=='string'||!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(b.measuredAt)||typeof b.sourceUrl!=='string'||!/^https:\/\/[^\s<>"]+$/.test(b.sourceUrl)||!(b.tokensPerSecond>0&&Number.isFinite(b.tokensPerSecond))||!Number.isSafeInteger(b.contextTokens)||b.contextTokens<128||!Number.isSafeInteger(b.concurrency)||b.concurrency<1||b.evidenceType!=='measured')continue;
  if(!map.has(b.modelId))map.set(b.modelId,[]);
  map.get(b.modelId).push(b);
 }
 return list.map(m=>({...m,measurements:(map.get(m.id)||[]).filter(b=>b.quantization===(m.quantization||m.tag||''))}));
}
function estimate(model,context,workload){
 const ctx=Number(context);
 if(!Object.prototype.hasOwnProperty.call(ALLOWANCES,ctx))return null;
 const allowance=ALLOWANCES[ctx]+(workload==='vision'?1:0)+(model.extraAssets?1:0);
 const total=Number((model.sizeGb+allowance).toFixed(2));
 return {total,allowance};
}
function evaluate(capacity,workload,context,list=MODELS){
 const cap=Number(capacity);
 if(!(cap>0&&cap<=256)||!['coding','chat','vision'].includes(workload))return [];
 const entries=Array.isArray(list)?list:[];
 return entries.filter(m=>m.workloads.includes(workload)).map(m=>{
  const e=estimate(m,context,workload);if(!e)return null;
  const status=e.total<=cap?'budget':e.total<=cap+2?'tight':'out';
  return {...m,planning:e.total,allowance:e.allowance,status,remaining:cap-e.total};
 }).filter(Boolean).sort((a,b)=>{
 const rank={budget:0,tight:1,out:2};return rank[a.status]-rank[b.status]||b.sizeGb-a.sizeGb||a.id.localeCompare(b.id);
 });
}
function hardwareFor(model,context,workload){
 const e=estimate(model,context,workload);if(!e)return null;
 const suggested=CAPACITIES.find(cap=>cap>=e.total)||null;
 return {planning:e.total,allowance:e.allowance,suggested,aboveCatalog:suggested===null};
}
function search(query,workload,list=MODELS){
 const term=String(query||'').trim().toLowerCase();
 return (Array.isArray(list)?list:[]).filter(m=>(!term||[m.name,m.id,m.family,m.tag,m.quantization].join(' ').toLowerCase().includes(term))&&(!workload||workload==='all'||m.workloads.includes(workload)));
}
function card(m,cap){
 const e=cap?{planning:m.planning,allowance:m.allowance,status:m.status}:hardwareFor(m,readContext(),m.workloads[0]||'chat');
 const status=cap?(m.status==='budget'?'Within planning budget':m.status==='tight'?'Tight estimate':'Above GPU budget'):'Estimated hardware target';
 const warning=m.extraAssets?' Vision-language models can require additional projector files and memory; this is not a full download requirement.':'';
 const command=m.tag?'ollama run '+m.tag:'Check repository instructions and required artifacts';
 const benchmarks=(m.measurements||[]).slice(0,2).map(b=>'<p class="vram-card-small"><strong>Measured '+Number(b.tokensPerSecond).toFixed(1)+' tokens/sec</strong> · '+esc(b.gpu)+' · '+esc(b.runtime)+' · '+esc(b.contextTokens)+' context tokens · concurrency '+esc(b.concurrency)+' · '+esc(b.measuredAt)+' · <a href="'+esc(b.sourceUrl)+'" rel="noopener noreferrer" target="_blank">Measurement evidence ↗</a></p>').join('');
 const sxf=(typeof m.sxfUrl==='string'&&/^\/models\/[a-z0-9-]+\/$/.test(m.sxfUrl))?'<a href="'+esc(m.sxfUrl)+'">SXF model page ↗</a>':'';
 return '<article class="vram-result"><div class="vram-result-head"><div><h4>'+esc(m.name)+'</h4><p>'+esc(m.format)+' · '+m.sizeGb.toFixed(2)+' GB published file size'+(m.quantization?' · '+esc(m.quantization):'')+'</p></div><span class="vram-badge'+(e.status==='tight'?' caution':'')+'">'+esc(status)+'</span></div>'+
 '<p><strong>'+e.planning.toFixed(2)+' GB</strong> estimated planning target = '+m.sizeGb.toFixed(2)+' GB file + '+e.allowance.toFixed(2)+' GB allowance. Not measured peak VRAM.</p>'+
 (!cap?'<p>Nearest listed GPU size: <strong>'+(e.suggested?e.suggested+' GB':'Above 128 GB')+'</strong> (discrete GPU estimate; not guaranteed).</p>':'')+
 '<p>'+esc(m.note||'')+esc(warning)+'</p><div class="vram-result-foot"><code>'+esc(command)+'</code><a href="'+esc(m.sourceUrl)+'" target="_blank" rel="noopener noreferrer">Source ↗</a>'+sxf+'</div>'+
 '<p class="vram-card-small">Size evidence: '+esc(m.sizeEvidence)+' · checked '+esc(m.checkedAt||'unknown')+' · License: '+esc(m.license||'check source')+' · Speed: '+(benchmarks?'Configuration-specific measured result below':'Not measured')+'</p>'+benchmarks+'</article>';
}
function readContext(){const e=document.getElementById('vram-context');return e?Number(e.value):8192;}
function render(){
 const result=document.getElementById('vram-results'),count=document.getElementById('vram-count');
 if(!result||!count)return;
 const cap=Number(document.getElementById('vram-capacity').value),workload=document.getElementById('vram-workload').value,ctx=readContext();
 const mode=document.getElementById('vram-mode').value;
 const query=document.getElementById('vram-search').value;
 let matches;
 if(mode==='model'){
  matches=search(query,'all');
  count.textContent=matches.length+' model variant'+(matches.length===1?'':'s')+' shown'+(query?' for "'+query.slice(0,40)+'"':'');
 }else{
  matches=evaluate(cap,workload,ctx).filter(m=>m.status!=='out'&&(!query||[m.name,m.id,m.tag,m.quantization].join(' ').toLowerCase().includes(query.toLowerCase())));
  count.textContent=matches.length+' planning candidate'+(matches.length===1?'':'s')+' for '+cap+'GB';
 }
 const more=document.getElementById('vram-show-more');
 if(more){more.hidden=matches.length<=resultLimit;more.textContent='Show '+Math.min(12,matches.length-resultLimit)+' more variants';}
 count.textContent+=' · showing '+Math.min(resultLimit,matches.length)+' of '+matches.length;
 result.innerHTML=matches.length?matches.slice(0,resultLimit).map(m=>card(m,mode==='gpu'?cap:null)).join(''):'<p>No catalog matches. Try another model name, workload, smaller context, or CPU offloading. GPU estimates are not guarantees.</p>';
}
function initialize(){
 const form=document.getElementById('vram-finder');if(!form)return;
 form.addEventListener('submit',e=>e.preventDefault());
 for(const id of ['vram-mode','vram-capacity','vram-workload','vram-context','vram-search']){
  const el=document.getElementById(id);if(el)el.addEventListener(id==='vram-search'?'input':'change',()=>{resultLimit=12;showMode();render();});
 }
 document.querySelectorAll('.vram-pick').forEach((el,i)=>el.addEventListener('click',()=>{const f=document.getElementById('vram-capacity');if(f){f.value=['8','12','16','24','32'][i];document.getElementById('vram-mode').value='gpu';showMode();render();}}));
 document.querySelectorAll('.vram-copy').forEach(button=>button.addEventListener('click',async()=>{if(!navigator.clipboard)return;try{await navigator.clipboard.writeText(button.dataset.copy);button.textContent='Copied';}catch(_){button.textContent='Select text';}}));
 const more=document.getElementById('vram-show-more');if(more)more.addEventListener('click',()=>{resultLimit+=12;render();});
 showMode();
 const status=document.getElementById('vram-data-status');
 fetch(CATALOG_URL,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Catalog unavailable');return r.json();}).then(data=>{
  MODELS=validate(data);
  if(status)status.textContent=MODELS.length+' sourced model variants · latest catalog '+esc(data.generatedAt||'unknown')+' · no speeds inferred';
  render();
  fetch('/data/local-llm-benchmarks.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(b=>{MODELS=joinBenchmarks(MODELS,b);render();}).catch(()=>{});
 }).catch(err=>{
  if(status)status.textContent='Catalog temporarily unavailable. Browse the sourced comparison table below; interactive results require catalog data.';
  const output=document.getElementById('vram-results');if(output)output.textContent='Model catalog could not load. See the sourced static comparison table below.';
  if(document.getElementById('vram-count'))document.getElementById('vram-count').textContent='Catalog unavailable';
 });
}
function showMode(){
 const x=document.getElementById('vram-mode');if(!x)return;
 const model=x.value==='model';
 const hw=document.getElementById('vram-hardware-controls');
 if(hw)hw.hidden=model;
 const caption=document.getElementById('vram-mode-help');
 if(caption)caption.textContent=model?'Search a specific model or quantization; we show a planning GPU size, not a benchmark.':'Select GPU memory and task to shortlist models that may fit with runtime headroom.';
}
if(typeof module!=='undefined'&&module.exports)module.exports={ALLOWANCES,CAPACITIES,validate,joinBenchmarks,estimate,evaluate,hardwareFor,search};
if(typeof document!=='undefined'){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});else initialize();}
})(typeof globalThis!=='undefined'?globalThis:this);
