#!/usr/bin/env node
// DOM-level regression tests: no browser dependency and no live requests.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const open=JSON.parse(fs.readFileSync(path.join(root,'data/open-source.json'),'utf8'));
const news=JSON.parse(fs.readFileSync(path.join(root,'data/news.json'),'utf8'));
function cards(html,cls){return (html.match(new RegExp('class="'+cls+'"','g'))||[]).length;}

async function section(){
  const calls={};
  const feed={innerHTML:''},empty={hidden:true},count={textContent:'0'};
  const search={value:'',addEventListener:(_,fn)=>calls.search=fn};
  const keys=['','model weights checkpoint quant','inference llama.cpp runtime serving',
    'framework transformers gradio library','local mlx ollama llama.cpp',
    'github repository repo open source'];
  const lenses=keys.map(key=>({dataset:{keywords:key},
    classList:{remove(){},add(){}},addEventListener:(_,fn)=>{this._unused=fn}}));
  lenses.forEach((b,i)=>{b.addEventListener=(_event,cb)=>b.click=cb;});
  const nodes={sectionFeed:feed,sectionEmpty:empty,sectionSearch:search,
    sectionCount:count,year:{textContent:''}};
  const sandbox={
    document:{body:{dataset:{category:'Open Source'}},
      getElementById:id=>nodes[id],querySelectorAll:()=>lenses},
    Date,console,fetch:async url=>{
      assert.equal(url,'../data/open-source.json');
      return {ok:true,json:async()=>open};
    },
  };
  vm.runInNewContext(fs.readFileSync(path.join(root,'section.js'),'utf8'),sandbox);
  await new Promise(done=>setImmediate(done));
  assert.equal(Number(count.textContent),open.items.length);
  assert.equal(cards(feed.innerHTML,'intel-card'),open.items.length);
  for(const b of lenses){
    b.click();
    const terms=b.dataset.keywords.toLowerCase().split(/\s+/).filter(Boolean);
    const expected=open.items.filter(x=>!terms.length||terms.some(w=>
      [x.title,x.source,x.summary,...(x.tags||[])].join(' ').toLowerCase().includes(w)));
    assert.equal(Number(count.textContent),expected.length,'lens: '+b.dataset.keywords);
    assert.equal(cards(feed.innerHTML,'intel-card'),expected.length);
    assert.equal(empty.hidden,expected.length!==0);
  }
  lenses[0].click();
  search.value='no-such-open-source-signal-999999';
  calls.search();
  assert.equal(cards(feed.innerHTML,'intel-card'),0);
  assert.equal(Number(count.textContent),0);
  assert.equal(empty.hidden,false);
  if(open.items.length){
    search.value=open.items[0].title.slice(0,12);
    calls.search();
    assert.ok(Number(count.textContent)>0);
  }
}

async function signals(){
  const feed={innerHTML:''},empty={hidden:true},meta={textContent:''};
  const search={value:'',addEventListener(){}};
  const filters=['All','Models','Agents','Research','Tools','Open Source'].map(key=>({
    dataset:{signalFilter:key},classList:{remove(){},add(){}},
    addEventListener(_event,cb){this.click=cb;},
  }));
  const nodes={signalsFeed:feed,signalsEmpty:empty,
    signalsSearch:search,signalsResultMeta:meta};
  const sandbox={
    document:{getElementById:id=>nodes[id],querySelectorAll:()=>filters},
    Date,console,fetch:async url=>({ok:true,
      json:async()=>(url==='/data/open-source.json'?open:news)}),
  };
  vm.runInNewContext(fs.readFileSync(path.join(root,'signals.js'),'utf8'),sandbox);
  await new Promise(done=>setImmediate(done));
  filters[5].click();
  const urls=new Set(open.items.map(x=>x.url));
  const expected=news.items.filter(x=>urls.has(x.url)||
    String(x.category).trim().toLowerCase()==='open source');
  assert.equal(cards(feed.innerHTML,'signal-row'),expected.length);
  assert.ok(meta.textContent.startsWith('Showing '+expected.length+' of '));
  filters[0].click();
  assert.equal(cards(feed.innerHTML,'signal-row'),news.items.length);
}
(async()=>{
  await section();
  await signals();
  console.log('PASS: Open Source six lenses, search, empty state, counters and Signals index');
})().catch(error=>{console.error(error);process.exitCode=1;});
