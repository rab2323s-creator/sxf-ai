const body=document.body;
const category=body.dataset.category||'';
const isOpenSource=category==='Open Source';
const feed=document.getElementById('sectionFeed');
const empty=document.getElementById('sectionEmpty');
const search=document.getElementById('sectionSearch');
const count=document.getElementById('sectionCount');
const lenses=[...document.querySelectorAll('.lens')];
let items=[],activeKeywords='';

function esc(v=''){
  return String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
}
function ago(v){
  const d=new Date(v),m=Math.max(0,Math.floor((Date.now()-d.getTime())/60000));
  if(m<2)return'just now';
  if(m<60)return m+'m ago';
  const h=Math.floor(m/60);
  if(h<24)return h+'h ago';
  const days=Math.floor(h/24);
  return days<7?days+'d ago':d.toLocaleDateString(undefined,{month:'short',day:'numeric'});
}
function textFor(x){
  return ((x.title||'')+' '+(x.source||'')+(isOpenSource?' '+(x.summary||'')+' '+(x.tags||[]).join(' '):'')).toLowerCase();
}
function match(x){
  if(!activeKeywords)return true;
  const words=activeKeywords.toLowerCase().split(/\s+/).filter(Boolean);
  const hay=textFor(x);
  return words.some(w=>hay.includes(w));
}
function card(x){
  return '<a class="intel-card" href="'+esc(x.signal_url||x.url)+'"><div class="intel-meta"><strong>'+
    esc(x.source)+'</strong><span>'+esc(ago(x.published))+'</span></div><h3>'+
    esc(x.title)+'</h3><div class="intel-foot"><span>'+esc(x.category)+'</span><b>↗</b></div></a>';
}
function render(){
  const q=(search?.value||'').trim().toLowerCase();
  const visible=items.filter(x=>match(x)&&(!q||textFor(x).includes(q)));
  feed.innerHTML=visible.map(card).join('');
  empty.hidden=visible.length!==0;
  count.textContent=isOpenSource?visible.length:items.length;
}
lenses.forEach(b=>b.addEventListener('click',()=>{
  lenses.forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  activeKeywords=b.dataset.keywords||'';
  render();
}));
search?.addEventListener('input',render);
const source=isOpenSource?'../data/open-source.json':'../data/news.json';
fetch(source,{cache:'no-cache'})
  .then(r=>{if(!r.ok)throw new Error('Signal feed unavailable');return r.json();})
  .then(d=>{
    items=(d.items||[]).filter(x=>isOpenSource||
      String(x.category||'').trim().toLowerCase()===category.trim().toLowerCase());
    render();
  })
  .catch(()=>{/* Preserve server-rendered cards and count on fetch failure. */});
