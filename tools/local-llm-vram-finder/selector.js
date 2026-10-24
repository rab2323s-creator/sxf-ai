/* SXF Local LLM VRAM Finder accuracy v3.
 * All memory figures are unmeasured planning estimates, in decimal GB.
 * Never infer runtime compatibility, model quality or speed from file bytes.
 */
(function (root) {
'use strict';
const ALLOWANCES=Object.freeze({4096:2,8192:3,16384:4.5,32768:7});
const CAPACITIES=[4,6,8,10,12,16,20,24,32,48,64,80,96,128];
const CATALOG_URL='/data/local-llm-catalog.json';
const LOW_BIT=/^(?:Q2_|Q3_|UD-Q3_)/i;
const GOOD_QUANTS=['Q4_K_M','Q5_K_M','Q4_K_S','Q5_K_S','Q6_K','Q8_0','UD-Q4_K_XL','UD-Q5_K_XL','IQ4_XS'];
let MODELS=[];
let resultLimit=8;
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const validUrl=u=>typeof u==='string'&&/^https:\/\/(huggingface\.co|ollama\.com)(\/|$)/.test(u);
function validate(data){
 if(!data||data.schemaVersion!==2||!Array.isArray(data.models))throw Error('Invalid catalog schema');
 const ids=new Set();
 const out=[];
 for(const m of data.models){
  if(!m||typeof m.id!=='string'||ids.has(m.id)||typeof m.name!=='string'||!Number.isFinite(m.sizeGb)||m.sizeGb<=0||m.sizeGb>600||!validUrl(m.sourceUrl)||!Array.isArray(m.workloads)||!m.workloads.length||m.workloads.some(x=>!['coding','chat','vision'].includes(x)))throw Error('Invalid model record');
  if(m.format==='GGUF'&&(!Number.isSafeInteger(m.sizeBytes)||m.sizeBytes<1e6||m.sizeEvidence!=='hub-file-bytes'))throw Error('Unverified GGUF file bytes');
  ids.add(m.id);out.push(m);
 }
 if(!out.length)throw Error('Empty catalog');
 return out;
}
function joinBenchmarks(list,data){
 if(!data||data.schemaVersion!==1||!Array.isArray(data.measurements))return list;
 const map=new Map();
 for(const b of data.measurements){
  if(!b||typeof b.modelId!=='string'||typeof b.gpu!=='string'||!b.gpu.trim()||typeof b.runtime!=='string'||!b.runtime.trim()||typeof b.quantization!=='string'||!b.quantization.trim()||typeof b.measuredAt!=='string'||!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(b.measuredAt)||typeof b.sourceUrl!=='string'||!/^https:\/\/[^\s<>"]+$/.test(b.sourceUrl)||!(b.tokensPerSecond>0&&Number.isFinite(b.tokensPerSecond))||!Number.isSafeInteger(b.contextTokens)||b.contextTokens<128||!Number.isSafeInteger(b.concurrency)||b.concurrency<1||b.evidenceType!=='measured'||b.reviewStatus!=='approved')continue;
  if(!map.has(b.modelId))map.set(b.modelId,[]);
  map.get(b.modelId).push(b);
 }
 return list.map(m=>({...m,measurements:(map.get(m.id)||[]).filter(b=>b.quantization===(m.quantization||m.tag||''))}));
}
function estimate(model,context,workload){
 const ctx=Number(context);
 if(!Object.prototype.hasOwnProperty.call(ALLOWANCES,ctx)||!['coding','chat','vision'].includes(workload))return null;
 if(!model.workloads.includes(workload))return null;
 const allowance=ALLOWANCES[ctx]+(workload==='vision'?1:0)+(workload==='vision'&&model.extraAssets?1:0);
 return {total:Number((model.sizeGb+allowance).toFixed(2)),allowance};
}
function evaluate(capacity,workload,context,list=MODELS){
 const cap=Number(capacity);
 if(!(cap>0&&cap<=256)||!['coding','chat','vision'].includes(workload))return [];
 return (Array.isArray(list)?list:[]).filter(m=>m.workloads.includes(workload)).map(m=>{
  const e=estimate(m,context,workload);if(!e)return null;
  const status=e.total<=cap?'budget':e.total<=cap+2?'tight':'out';
  return {...m,planning:e.total,allowance:e.allowance,status,remaining:Number((cap-e.total).toFixed(2))};
 }).filter(Boolean);
}
function hardwareFor(model,context,workload){
 const e=estimate(model,context,workload);if(!e)return null;
 const suggested=CAPACITIES.find(cap=>cap>=e.total)||null;
 return {planning:e.total,allowance:e.allowance,suggested,aboveCatalog:suggested===null};
}
function search(query,workload,list=MODELS){
 const normal=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'');
 const term=normal(query);
 return (Array.isArray(list)?list:[]).filter(m=>(!term||[m.name,m.id,m.family,m.tag,m.quantization,m.filename].some(v=>normal(v).includes(term)))&&(!workload||workload==='all'||m.workloads.includes(workload)));
}
function familyKey(m){
 const label=m.format==='GGUF'?m.name.replace(/\s(?:UD-Q[345]_[A-Z0-9_]+|IQ4_XS|Q[234568]_[A-Z0-9_]+)$/i,''):m.name;
 return label.replace(/\s*\(Unsloth\)/i,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
}
function familyName(m){
 return (m.format==='GGUF'?m.name.replace(/\s(?:UD-Q[345]_[A-Z0-9_]+|IQ4_XS|Q[234568]_[A-Z0-9_]+)$/i,''):m.name).replace(/\s*\(Unsloth\)/i,'');
}
function quantRank(m){
 if(m.quantization&&LOW_BIT.test(m.quantization))return 100;
 if(m.format==='Ollama')return 6; // publisher artifact; quant may not be disclosed
 const pos=GOOD_QUANTS.indexOf(m.quantization);
 return pos>=0?pos:35;
}
function runtimeEvidence(m){
 return m.format==='Ollama'?'Listed in Ollama registry — not runtime-tested':'GGUF file indexed — runtime not tested';
}
function visionEvidence(m){
 if(!m.workloads.includes('vision'))return null;
 if(m.format==='Ollama')return 'Vision-capable Ollama tag listed; image memory is unmeasured.';
 const aux=Array.isArray(m.auxiliaryFiles)?m.auxiliaryFiles:[];
 return aux.length?
  'Projector candidates published ('+aux.length+'); matching projector, version and runtime compatibility NOT validated. Extra file and VRAM needed.':
  'Projector / extra vision assets NOT validated; model file alone may not enable image input.';
}
function variantOrder(a,b){
 const level={budget:0,tight:1,out:2};
 return (level[a.status]-level[b.status])||(quantRank(a)-quantRank(b))||a.planning-b.planning||a.id.localeCompare(b.id);
}
function groupFamilies(entries){
 const grouped=new Map();
 for(const m of entries){
  const key=familyKey(m);
  if(!grouped.has(key))grouped.set(key,{key,name:familyName(m),variants:[]});
  grouped.get(key).variants.push(m);
 }
 const out=[...grouped.values()].map(g=>{
  g.variants.sort(variantOrder);
  g.primary=g.variants[0];
  g.quantWarning=!!(g.primary.quantization&&LOW_BIT.test(g.primary.quantization));
  g.visionReview=g.primary.workloads.includes('vision')&&g.primary.format==='GGUF';
  return g;
 });
 return out.sort((a,b)=>{
  const tier=x=>x.primary.status==='out'?3:x.visionReview?2:x.quantWarning?1:0;
  return tier(a)-tier(b)||quantRank(a.primary)-quantRank(b.primary)||a.primary.planning-b.primary.planning||a.name.localeCompare(b.name);
 });
}
/* Screening labels describe evidence only, never benchmarked quality or guaranteed GPU fit. */
function screeningAssessment(g,mode,workload){
 const m=g.primary;
 const low=!!(m.quantization&&LOW_BIT.test(m.quantization));
 const vision=workload==='vision'&&m.format==='GGUF';
 const borderline=mode==='gpu'&&m.status==='tight';
 let label,why,limits;
 if(low){
  label='Conditional: aggressive quantization';
  why='Only a 2–3-bit variant of this family meets the selected memory screening conditions. Listed for comparison, NOT recommended as a quality pick.';
  limits='Quality impact, runtime support and full-GPU loading require independent testing.';
 }else if(vision){
  label='Needs validation: vision assets';
  why='A source-listed GGUF file meets the memory screening criteria, but its image-processing assets have not been validated.';
  limits='Projector and any extra files, runtime support, and actual VRAM use are not confirmed.';
 }else if(borderline){
  label='Borderline: above planning budget';
  why='The published file size plus illustrative memory allowance exceeds the selected GPU budget by up to 2 GB.';
  limits='Do not assume full GPU loading; shorter context, smaller quantization or CPU offload may be required.';
 }else if(mode==='model'){
  label='Estimated GPU tier only';
  why='The listed GPU tier comes from published file size plus the stated task/context allowance, not a hardware benchmark.';
  limits='No verified performance, full-GPU residency, or model-quality ranking.';
 }else{
  label='Memory candidate: not tested';
  why='The source-listed file size plus illustrative memory allowance falls within the selected GPU budget.';
  limits='This is not a measured memory peak, verified runtime compatibility, or a quality ranking.';
 }
 if(borderline&&low)limits+=' The planning target also exceeds the selected GPU budget.';
 if(vision&&low)limits+=' Vision projector files and image memory have not been validated.';
 return {label,why,limits,low,vision,borderline};
}
function evidenceHTML(m,workload,context){
 const e=estimate(m,context,workload);
 if(!e)return '';
 const h=hardwareFor(m,context,workload);
 const vision=workload==='vision'?visionEvidence(m):null;
 return '<p class="vram-evidence"><strong>File:</strong> '+m.sizeGb.toFixed(3)+' GB ('+esc(m.sizeEvidence)+') · <strong>VRAM plan:</strong> '+e.total.toFixed(2)+' GB ('+e.allowance.toFixed(2)+' GB illustrative allowance) · <strong>GPU tier:</strong> '+(h.suggested?h.suggested+' GB':'Above 128 GB')+' (estimate only).</p>'+
  '<p class="vram-evidence"><strong>Compatibility:</strong> '+esc(runtimeEvidence(m))+' · <strong>Measured peak VRAM:</strong> Unavailable · <strong>Speed:</strong> '+((m.measurements||[]).length?'See source-specific measurement':'Not measured')+'.</p>'+
  (vision?'<p class="vram-warning"><strong>Vision check:</strong> '+esc(vision)+'</p>':'')+
  (m.quantization&&LOW_BIT.test(m.quantization)?'<p class="vram-warning">Aggressive 2–3-bit quantization: quality and runtime trade-offs require evaluation. Not labeled best.</p>':'');
}
function variantItem(m,workload,context){
 const e=estimate(m,context,workload);
 const q=m.quantization||'Ollama registry tag (quantization unspecified)';
 const vision=workload==='vision'?visionEvidence(m):null;
 const source='<a href="'+esc(m.sourceUrl)+'" target="_blank" rel="noopener noreferrer">Original source ↗</a>';
 const page=typeof m.sxfUrl==='string'&&/^\/models\/[a-z0-9-]+\/$/.test(m.sxfUrl)?' · <a href="'+esc(m.sxfUrl)+'">SXF model profile ↗</a>':'';
 return '<li><span><strong>'+esc(q)+'</strong> · '+m.sizeGb.toFixed(3)+' GB file · '+e.total.toFixed(2)+' GB estimated target · '+(m.status==='out'?'above selected GPU':m.status==='tight'?'tight GPU budget':'within planning budget')+(m.quantization&&LOW_BIT.test(m.quantization)?' · CONDITIONAL: aggressive quantization':'')+'</span><small>'+source+page+' · '+esc(runtimeEvidence(m))+(vision?' · Vision assets unverified':'')+'</small></li>';
}
function familyCard(g,mode,cap,workload,context){
 const m=g.primary,h=hardwareFor(m,context,workload);
 const assessment=screeningAssessment(g,mode,workload);
 const tight=m.status==='tight',out=m.status==='out';
 const label=assessment.label;
 const capLabel=mode==='model'?'Nearest listed GPU tier: '+(h.suggested?h.suggested+' GB':'Above 128 GB'):'Selected GPU: '+cap+' GB';
 const all=g.variants.map(v=>variantItem(v,workload,context)).join('');
 const license=esc(m.license||'Needs source review');
 const note=m.tag?'<code>ollama run '+esc(m.tag)+'</code>':'<span>Check the GGUF repository instructions; no tested launch command.</span>';
 const bench=(m.measurements||[]).slice(0,2).map(b=>'<p class="vram-evidence">Measured '+Number(b.tokensPerSecond).toFixed(1)+' tokens/sec · '+esc(b.gpu)+' · '+esc(b.runtime)+' · context '+esc(b.contextTokens)+' · <a href="'+esc(b.sourceUrl)+'" target="_blank" rel="noopener noreferrer">Benchmark evidence ↗</a></p>').join('');
 return '<article class="vram-result vram-family"><div class="vram-result-head"><div><h4>'+esc(g.name)+'</h4><p>'+g.variants.length+' source-listed variant'+(g.variants.length===1?'':'s')+' · screening choice: '+esc(m.quantization||'Ollama published tag')+'</p></div><span class="vram-badge'+(tight||out||g.quantWarning||g.visionReview?' caution':'')+'">'+esc(label)+'</span></div>'+
  '<p><strong>'+m.planning.toFixed(2)+' GB</strong> estimated planning target · '+esc(capLabel)+' · Not a measured VRAM requirement.</p>'+
  '<div class="vram-decision"><p><strong>Why shown:</strong> '+esc(assessment.why)+'</p><p><strong>What to check:</strong> '+esc(assessment.limits)+'</p></div>'+
  evidenceHTML(m,workload,context)+
  '<p class="vram-card-small"><strong>License:</strong> '+license+' (check exact model card) · <strong>Source checked:</strong> '+esc(m.checkedAt||'unknown')+'</p>'+
  '<div class="vram-result-foot">'+note+' <a href="'+esc(m.sourceUrl)+'" target="_blank" rel="noopener noreferrer">Model file source ↗</a></div>'+bench+
  '<details class="vram-variants"><summary>Compare all '+g.variants.length+' variants, quantizations and GPU estimates</summary><ul class="vram-variant-list">'+all+'</ul></details></article>';
}
function reviewedCaseStudy(data,query,workload){
 if(workload!=='vision'||!data||data.schemaVersion!==1||!Array.isArray(data.observations))return null;
 const normalized=String(query||'').toLowerCase().replace(/[^a-z0-9]+/g,'');
 // A distinct Ollama Instruct release: never attach this evidence to qwen3-vl:4b or a GGUF variant.
 if(normalized&&!['qwen3vl','qwen3vl4b','qwen3vl4binstruct','qwen','vision','instruct'].some(term=>term.includes(normalized)))return null;
 const b=data.observations.find(v=>v.modelId==='ollama:qwen3-vl:4b-instruct');
 if(!b||b.modelTag!=='qwen3-vl:4b-instruct'||b.reviewStatus!=='reviewed-user-capture'||b.publicationScope!=='source-linked-case-study-only'||b.measurementKind!=='generation-only'||b.contextTokens!==4096||b.workload!=='vision'||b.runtime!=='Ollama'||b.gpu!=='NVIDIA Tesla T4'||typeof b.sourceUrl!=='string'||!/^https:\/\/github\.com\/rab2323s-creator\/sxf-ai\/blob\/main\/docs\/benchmarks\//.test(b.sourceUrl)||!Array.isArray(b.measuredGenerationTokensPerSecond)||b.measuredGenerationTokensPerSecond.length!==3||!b.measuredGenerationTokensPerSecond.every(x=>Number.isFinite(x)&&x>0))return null;
 return b;
}
function reviewedCaseStudyHTML(b){
 if(!b)return '';
 const mean=b.measuredGenerationTokensPerSecond.reduce((a,x)=>a+x,0)/3;
 return '<article class="vram-reviewed-card"><h4>Reviewed user-captured Vision test — '+esc(b.modelDisplayName)+'</h4>'+
  '<p><strong>'+mean.toFixed(2)+' generated tokens/second</strong> (three measured runs, warmup excluded). Generation-only, not end-to-end latency.</p>'+
  '<p><strong>Exact version:</strong> <code>'+esc(b.modelTag)+'</code> · '+esc(b.quantization)+' · '+esc(b.gpu)+' · Ollama '+esc(b.runtimeVersion)+' · context '+esc(b.contextTokens)+'.</p>'+
  '<p><strong>GPU-wide observed peak:</strong> '+esc(b.gpuWideObservedPeakUsedMiB)+' MiB (entire GPU, not model-only VRAM). <strong>Ollama-reported GPU residency:</strong> '+esc(b.ollamaReportedGpuResidentMiB)+' MiB (runtime-reported, not independently verified).</p>'+
  '<p><strong>Image check:</strong> '+esc(b.fixtureResult)+'</p>'+
  '<p><strong>Scope:</strong> This is a separate Ollama Instruct case study, not a benchmark for the catalogued <code>qwen3-vl:4b</code> thinking tag or any GGUF file. Does not change screening, compatibility, or estimated VRAM requirements.</p>'+
  '<p><a href="'+esc(b.sourceUrl)+'" target="_blank" rel="noopener noreferrer">Reviewed source report ↗</a> · Original ZIP privately retained, not publicly hosted.</p></article>';
}
function initialize(){
 const form=document.getElementById('vram-finder');if(!form)return;
 form.addEventListener('submit',e=>e.preventDefault());
 const status=document.getElementById('vram-data-status');
 const result=document.getElementById('vram-results'),count=document.getElementById('vram-count'),more=document.getElementById('vram-show-more');
 let reviewedData=null;
 const reviewedSlot=document.getElementById('vram-reviewed-evidence');
 const ids=['vram-mode','vram-capacity','vram-workload','vram-context','vram-search'];
 function render(){
  const mode=document.getElementById('vram-mode').value,cap=Number(document.getElementById('vram-capacity').value),workload=document.getElementById('vram-workload').value,ctx=Number(document.getElementById('vram-context').value),query=document.getElementById('vram-search').value;
  const note=document.getElementById('vram-mode-help');
  if(note)note.textContent=mode==='model'?'Search a model and pick its task/context. GPU estimates use the SAME inputs as GPU-first results.':'Select a GPU tier, task and context. Results are grouped by model family, not ranked by model quality.';
  if(!MODELS.length){count.textContent='Catalog unavailable';result.textContent='The source catalog did not load. See the sourced static comparison table below.';if(more)more.hidden=true;return;}
  // The GPU selector is hidden in reverse mode, so it must not influence variant ordering.
  if(reviewedSlot){
   const caseStudy=reviewedCaseStudy(reviewedData,query,workload);
   // Case study is not part of the catalog and does not change model counts or GPU filtering.
   reviewedSlot.innerHTML=reviewedCaseStudyHTML(caseStudy);
   reviewedSlot.hidden=!caseStudy;
  }
  const candidates=evaluate(mode==='model'?256:cap,workload,ctx,search(query,workload));
  const matched=mode==='gpu'?candidates.filter(m=>m.status!=='out'):candidates;
  const families=groupFamilies(matched);
  const visible=families.slice(0,resultLimit);
  count.textContent=families.length+' model famil'+(families.length===1?'y':'ies')+' ('+matched.length+' sourced variants) · showing '+visible.length;
  result.innerHTML=visible.length?visible.map(g=>familyCard(g,mode,cap,workload,ctx)).join(''):'<p>No matching models for this task and context. Change task, search or VRAM. File fit does not prove runtime compatibility.</p>';
  if(more){more.hidden=families.length<=resultLimit;more.textContent='Show '+Math.min(8,families.length-resultLimit)+' more model families';}
 }
 for(const id of ids){const el=document.getElementById(id);if(el)el.addEventListener(id==='vram-search'?'input':'change',()=>{resultLimit=8;render();});}
 if(more)more.addEventListener('click',()=>{resultLimit+=8;render();});
 document.querySelectorAll('.vram-pick').forEach((el,i)=>el.addEventListener('click',()=>{const field=document.getElementById('vram-capacity');if(field){field.value=['8','12','16','24','32'][i];document.getElementById('vram-mode').value='gpu';resultLimit=8;render();}}));
 document.querySelectorAll('.vram-copy').forEach(button=>button.addEventListener('click',async()=>{try{if(!navigator.clipboard)return;await navigator.clipboard.writeText(button.dataset.copy);button.textContent='Copied';}catch(_){button.textContent='Select text';}}));
 fetch(CATALOG_URL,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Catalog unavailable');return r.json();}).then(data=>{
  MODELS=validate(data);
  if(status)status.textContent=MODELS.length+' source-linked artifacts · memory numbers are estimates, not tests · catalog '+String(data.generatedAt||'unknown');
  render();
  fetch('/data/local-llm-reviewed-evidence.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(data=>{reviewedData=data;render();}).catch(()=>{reviewedData=null;render();});
  fetch('/data/local-llm-benchmarks.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(b=>{MODELS=joinBenchmarks(MODELS,b);render();}).catch(()=>{});
 }).catch(()=>{if(status)status.textContent='Catalog temporarily unavailable. The 13-entry source-linked comparison table below remains accessible.';render();});
}
if(typeof module!=='undefined'&&module.exports)module.exports={ALLOWANCES,CAPACITIES,validate,joinBenchmarks,estimate,evaluate,hardwareFor,search,familyKey,groupFamilies,quantRank,visionEvidence,screeningAssessment,reviewedCaseStudy,reviewedCaseStudyHTML};
if(typeof document!=='undefined'){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});else initialize();}
})(typeof globalThis!=='undefined'?globalThis:this);
