/* SXF local LLM selector. No external APIs, cookies or tracking.
 * Source sizes: official Ollama tag listings checked 2026-10-24.
 * Fit allowances are SXF planning heuristics, NOT measured VRAM usage.
 */
(function (root) {
  'use strict';
  const SOURCES = {
    qwen3: 'https://ollama.com/library/qwen3/tags',
    coder: 'https://ollama.com/library/qwen2.5-coder/tags',
    gemma: 'https://ollama.com/library/gemma3/tags',
    vision: 'https://ollama.com/library/qwen3-vl/tags'
  };
  const MODELS = [
    {tag:'qwen3:4b',name:'Qwen3 4B',size:2.5,use:['chat'],source:'qwen3',license:'Apache-2.0',note:'Lightweight text/reasoning starting point.'},
    {tag:'qwen3:8b',name:'Qwen3 8B',size:5.2,use:['chat'],source:'qwen3',license:'Apache-2.0',note:'General text model; start with modest context on 8GB cards.'},
    {tag:'qwen3:14b',name:'Qwen3 14B',size:9.3,use:['chat'],source:'qwen3',license:'Apache-2.0',note:'Larger general-purpose text candidate.'},
    {tag:'qwen3:30b',name:'Qwen3 30B',size:19,use:['chat'],source:'qwen3',license:'Apache-2.0',note:'Larger quantized model. Measure longer-context overhead.'},
    {tag:'qwen2.5-coder:7b',name:'Qwen2.5-Coder 7B',size:4.7,use:['coding'],source:'coder',license:'Apache-2.0',note:'Compact code-focused choice; test on real tasks.'},
    {tag:'qwen2.5-coder:14b',name:'Qwen2.5-Coder 14B',size:9,use:['coding'],source:'coder',license:'Apache-2.0',note:'Mid-size code-focused option; memory matters at 12GB.'},
    {tag:'qwen2.5-coder:32b',name:'Qwen2.5-Coder 32B',size:20,use:['coding'],source:'coder',license:'Apache-2.0',note:'Large code-focused option; verify full-GPU placement.'},
    {tag:'gemma3:4b',name:'Gemma 3 4B',size:3.4,use:['chat','vision'],source:'gemma',license:'Gemma terms',note:'Compact multimodal candidate; review Gemma license.'},
    {tag:'gemma3:12b',name:'Gemma 3 12B',size:8.2,use:['chat','vision'],source:'gemma',license:'Gemma terms',note:'Multimodal model; test additional image memory.'},
    {tag:'gemma3:27b',name:'Gemma 3 27B',size:17,use:['chat','vision'],source:'gemma',license:'Gemma terms',note:'Larger multimodal choice for ample VRAM.'},
    {tag:'qwen3-vl:4b',name:'Qwen3-VL 4B',size:3.3,use:['vision'],source:'vision',license:'Check model card',note:'Vision-language starting point for smaller GPUs.'},
    {tag:'qwen3-vl:8b',name:'Qwen3-VL 8B',size:6.2,use:['vision'],source:'vision',license:'Check model card',note:'Image interpretation; buffer for image resolution.'},
    {tag:'qwen3-vl:30b',name:'Qwen3-VL 30B',size:20,use:['vision'],source:'vision',license:'Check model card',note:'Large vision-language model; benchmark memory with images.'}
  ];
  const ALLOWANCES = Object.freeze({4096:2,8192:3,16384:4.5,32768:7});
  function evaluate(capacity,workload,context) {
    const cap=Number(capacity),ctx=Number(context);
    if (![8,12,16,24,32].includes(cap) || !['coding','chat','vision'].includes(workload) || !Object.prototype.hasOwnProperty.call(ALLOWANCES,ctx)) return [];
    const allowance=ALLOWANCES[ctx]+(workload==='vision'?1:0);
    return MODELS.filter(model=>model.use.includes(workload)).map(model=>{
      const planning=model.size+allowance;
      const status=planning<=cap?'budget':planning<=cap+2?'tight':'out';
      return Object.assign({},model,{allowance,planning,status,remaining:cap-planning});
    }).filter(model=>model.status!=='out')
      .sort((a,b)=>(a.status===b.status?b.size-a.size:a.status==='budget'?-1:1))
      .slice(0,5);
  }
  function esc(value) {return String(value).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));}
  function render() {
    const capEl=document.getElementById('vram-capacity');
    const workEl=document.getElementById('vram-workload');
    const ctxEl=document.getElementById('vram-context');
    const output=document.getElementById('vram-results');
    const count=document.getElementById('vram-count');
    if(!capEl || !workEl || !ctxEl || !output || !count)return;
    const cap=Number(capEl.value);
    const matches=evaluate(cap,workEl.value,Number(ctxEl.value));
    count.textContent=matches.length+' candidate'+(matches.length===1?'':'s')+' for '+cap+'GB';
    if(!matches.length){
      output.innerHTML='<p>No published models in this shortlist fit even the tight planning band at these settings. Try a shorter context, a smaller model, or CPU offloading—and verify actual behavior.</p>';
      return;
    }
    output.innerHTML=matches.map(model=>{
      const tight=model.status==='tight';
      const memoryPercent=Math.min(100,Math.round(model.planning/cap*100));
      return '<article class="vram-result">'+
        '<div class="vram-result-head"><div><h4>'+esc(model.name)+'</h4><p>'+esc(model.tag)+' · '+model.size.toFixed(1)+' GB published download</p></div>'+
        '<span class="vram-badge'+(tight?' caution':'')+'">'+(tight?'Tight estimate':'Within budget')+'</span></div>'+
        '<div class="vram-meter" aria-hidden="true"><span class="'+(tight?'caution':'')+'" style="width:'+memoryPercent+'%"></span></div>'+
        '<p><strong>'+model.planning.toFixed(1)+' GB</strong> planning target = '+model.size.toFixed(1)+' GB file + '+model.allowance.toFixed(1)+' GB allowance.</p>'+
        '<p>'+esc(model.note)+(tight?' Planning total exceeds selected VRAM; CPU offload or lower context may be needed.':'')+'</p>'+
        '<div class="vram-result-foot"><code>ollama run '+esc(model.tag)+'</code><a href="'+SOURCES[model.source]+'" target="_blank" rel="noopener noreferrer">Source &amp; tags ↗</a></div>'+
        '<p style="font-size:.75rem">License: '+esc(model.license)+'; verify the publisher terms for your exact model.</p></article>';
    }).join('');
  }
  function initialize() {
    const form=document.getElementById('vram-finder');
    if(!form)return;
    form.addEventListener('submit',event=>event.preventDefault());
    ['vram-capacity','vram-workload','vram-context'].forEach(id=>{
      const el=document.getElementById(id);
      if(el)el.addEventListener('change',render);
    });
    document.querySelectorAll('.vram-pick').forEach((el,i)=>{
      el.addEventListener('click',()=>{
        const options=['8','12','16','24','32'];
        const field=document.getElementById('vram-capacity');
        if(field){field.value=options[i];render();}
      });
    });
    document.querySelectorAll('.vram-copy').forEach(button=>{
      button.addEventListener('click',async()=>{
        const old=button.textContent,command=button.dataset.copy;
        if(!navigator.clipboard || !navigator.clipboard.writeText){button.textContent='Select text';return;}
        try{await navigator.clipboard.writeText(command);button.textContent='Copied';}
        catch(_){button.textContent='Select text';}
        window.setTimeout(()=>{button.textContent=old;},1800);
      });
    });
    render();
  }
  if (typeof module!=='undefined' && module.exports) module.exports={SOURCES,MODELS,ALLOWANCES,evaluate};
  if (typeof document!=='undefined') {
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});
    else initialize();
  }
})(typeof globalThis!=='undefined'?globalThis:this);
