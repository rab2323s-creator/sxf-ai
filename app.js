const state={items:[],filter:'All',query:''};
const feed=document.getElementById('feed');
const featured=document.getElementById('featured');
const empty=document.getElementById('emptyState');
const search=document.getElementById('searchInput');
const filters=[...document.querySelectorAll('.filter')];

document.getElementById('year').textContent=new Date().getFullYear();

function escapeHtml(value=''){
  return String(value).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
}
function relativeTime(dateStr){
  const d=new Date(dateStr);
  if(Number.isNaN(d.getTime()))return '';
  const diff=Math.max(0,Date.now()-d.getTime());
  const mins=Math.floor(diff/60000);
  if(mins<2)return 'just now';
  if(mins<60)return mins+'m ago';
  const h=Math.floor(mins/60);
  if(h<24)return h+'h ago';
  const days=Math.floor(h/24);
  if(days<7)return days+'d ago';
  return d.toLocaleDateString(undefined,{month:'short',day:'numeric'});
}
function filteredItems(){
  const q=state.query.trim().toLowerCase();
  return state.items.filter(item=>{
    const categoryMatch=state.filter==='All'||item.category===state.filter;
    const haystack=(item.title+' '+item.source+' '+item.category).toLowerCase();
    return categoryMatch&&(!q||haystack.includes(q));
  });
}
function featuredMarkup(item){
  if(!item)return '';
  return `<a class="featured-story" href="${escapeHtml(item.signal_url||item.url)}">
    <div class="featured-main">
      <div>
        <div class="featured-topline"><strong>${escapeHtml(item.source)}</strong><i></i><span>${escapeHtml(relativeTime(item.published))}</span></div>
        <h3 class="featured-title">${escapeHtml(item.title)}</h3>
      </div>
      <div class="featured-footer">
        <span class="category-pill">${escapeHtml(item.category)}</span>
        <span class="open-label">Read signal <b>↗</b></span>
      </div>
    </div>
    <div class="featured-visual" aria-hidden="true"><span class="signal-cross">+</span><span class="signal-number">01</span></div>
  </a>`;
}
function cardMarkup(item,index){
  const n=String(index+2).padStart(2,'0');
  return `<a class="story-card" href="${escapeHtml(item.signal_url||item.url)}">
    <div class="story-card-top"><span class="story-source">${escapeHtml(item.source)}</span><span class="story-time">${escapeHtml(relativeTime(item.published))}</span></div>
    <h3 class="story-title">${escapeHtml(item.title)}</h3>
    <div class="story-card-bottom"><span class="category-pill">${escapeHtml(item.category)}</span><span class="story-arrow" aria-hidden="true">↗</span></div>
    <span class="sr-only">Signal ${n}</span>
  </a>`;
}
function updateHeroSignal(item){
  if(!item)return;
  const link=document.getElementById('heroSignalLink');
  const source=document.getElementById('heroSignalSource');
  const time=document.getElementById('heroSignalTime');
  const title=document.getElementById('heroSignalTitle');
  const category=document.getElementById('heroSignalCategory');
  if(link)link.href=item.signal_url||item.url||'#latest';
  if(link){link.removeAttribute('target');link.removeAttribute('rel')}
  if(source)source.textContent=item.source||'Primary source';
  if(time)time.textContent=relativeTime(item.published)||'recent';
  if(title)title.textContent=item.title||'Latest AI signal';
  if(category)category.textContent=item.category||'Signal';
}

function render(){
  const visible=filteredItems();
  featured.innerHTML=featuredMarkup(visible[0]);
  feed.innerHTML=visible.slice(1).map(cardMarkup).join('');
  empty.hidden=visible.length!==0;
  featured.hidden=visible.length===0;
  document.getElementById('storyCount').textContent=state.items.length||'0';
}
filters.forEach(btn=>btn.addEventListener('click',()=>{
  filters.forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  state.filter=btn.dataset.filter;
  render();
}));
search.addEventListener('input',e=>{state.query=e.target.value;render()});

fetch('./data/news.json',{cache:'no-store'})
  .then(r=>{if(!r.ok)throw new Error('Could not load news');return r.json()})
  .then(data=>{
    state.items=Array.isArray(data.items)?data.items:[];
    document.getElementById('lastUpdated').textContent=data.updated_at?relativeTime(data.updated_at):'automatic';
    updateHeroSignal(state.items[0]);
    render();
  })
  .catch(()=>{
    document.getElementById('lastUpdated').textContent='offline';
    featured.hidden=true;
    empty.hidden=false;
    empty.textContent='The live feed is temporarily unavailable.';
  });