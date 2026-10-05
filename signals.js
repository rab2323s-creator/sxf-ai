const feed=document.getElementById('signalsFeed');
const empty=document.getElementById('signalsEmpty');
const search=document.getElementById('signalsSearch');
const meta=document.getElementById('signalsResultMeta');
const filters=[...document.querySelectorAll('.signals-filter')];
let items=[];
let active='All';

function esc(v=''){
  return String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
}
function ago(v){
  const d=new Date(v),m=Math.max(0,Math.floor((Date.now()-d.getTime())/60000));
  if(m<2)return'just now'; if(m<60)return m+'m ago';
  const h=Math.floor(m/60); if(h<24)return h+'h ago';
  const days=Math.floor(h/24); return days<7?days+'d ago':d.toLocaleDateString(undefined,{month:'short',day:'numeric'});
}
function isAgent(x){
  const hay=((x.title||'')+' '+(x.summary||'')).toLowerCase();
  return /\bagent(?:s|ic)?\b|\bmcp\b|computer use|tool calling|multi[- ]step|long[- ]running/.test(hay);
}
function matchesFilter(x){
  if(active==='All')return true;
  if(active==='Agents')return isAgent(x);
  return x.category===active;
}
function card(x){
  const href=x.signal_url||x.url||'#';
  return '<a class="signal-row" href="'+esc(href)+'">'+
    '<div class="signal-row-meta"><span>'+esc(x.source||'')+'</span><time datetime="'+esc(x.published||'')+'">'+esc(ago(x.published))+'</time></div>'+
    '<h3>'+esc(x.title||'')+'</h3>'+
    '<div class="signal-row-foot"><span>'+esc(x.category||'')+'</span><b>Open signal ↗</b></div></a>';
}
function render(){
  const q=(search?.value||'').trim().toLowerCase();
  const visible=items.filter(x=>{
    if(!matchesFilter(x))return false;
    if(!q)return true;
    const hay=((x.title||'')+' '+(x.source||'')+' '+(x.category||'')+' '+(x.summary||'')).toLowerCase();
    return hay.includes(q);
  });
  feed.innerHTML=visible.map(card).join('');
  empty.hidden=visible.length!==0;
  const label=active==='All'?'all signals':active+' signals';
  meta.textContent='Showing '+visible.length+' of '+items.length+' current '+label+(q?' matching “'+q+'”.':'.');
}
filters.forEach(btn=>btn.addEventListener('click',()=>{
  filters.forEach(x=>x.classList.remove('active'));
  btn.classList.add('active');
  active=btn.dataset.signalFilter||'All';
  render();
}));
search?.addEventListener('input',render);

fetch('/data/news.json',{cache:'no-cache'})
  .then(r=>r.json())
  .then(data=>{
    items=Array.isArray(data.items)?data.items:[];
    render();
  })
  .catch(()=>{
    meta.textContent='Live filtering is temporarily unavailable. The latest indexed signals remain visible below.';
  });
