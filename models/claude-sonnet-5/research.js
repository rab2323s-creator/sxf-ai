"use strict";
(()=>{
 const root=document.getElementById("cs5-price-tool");
 if(!root)return;
 const $=k=>root.querySelector('[name="'+k+'"]'),out=k=>root.querySelector('[data-cost="'+k+'"]');
 const get=(name)=>({input:Number(root.dataset[name+"Input"]),cached:Number(root.dataset[name+"Cached"]),five:Number(root.dataset[name+"Write5"]),hour:Number(root.dataset[name+"Write1"]),output:Number(root.dataset[name+"Output"])});
 const model5=get("p5"),model55=get("p55");
 const money=x=>"$"+(Math.abs(x)>=0.01?x.toFixed(2):x.toFixed(4));
 const quote=(m,prefix,fresh,output,kind)=>(prefix*(kind==="uncached"?m.input:m[kind])+fresh*m.input+output*m.output)/1e6;
 const total=(m,prefix,fresh,output,n,kind)=>kind==="uncached"?n*quote(m,prefix,fresh,output,"uncached"):quote(m,prefix,fresh,output,kind)+(n-1)*quote(m,prefix,fresh,output,"cached");
 function update(){
  const fields=["prefix","new","output","calls"].map(k=>Number($(k).value));
  const [p,n,o,c]=fields,ttl=$("ttl").value;
  if(!fields.every(Number.isSafeInteger)||p<2048||p+n>1000000||n<0||o<0||o>128000||c<1||c>100000){
   for(const k of ["five-uncached","five-cached","next-uncached","next-cached","saving"])out(k).textContent="—";
   out("message").textContent="Enter whole numbers, prefix ≥ 2,048; prefix + new input ≤ 1,000,000; output ≤ 128,000; calls 1–100,000.";
   return;
  }
  const u5=total(model5,p,n,o,c,"uncached"),v5=total(model5,p,n,o,c,ttl),u55=total(model55,p,n,o,c,"uncached"),v55=total(model55,p,n,o,c,ttl);
  out("five-uncached").textContent=money(u5);out("five-cached").textContent=money(v5);
  out("next-uncached").textContent=money(u55);out("next-cached").textContent=money(v55);
  out("saving").textContent=money(u5-v5);
  out("message").textContent="Hypothetical Standard token billing: one initial write, "+(c-1)+" successful cached reads, identical output size, all calls within retention.";
 }
 root.addEventListener("submit",e=>e.preventDefault());
 root.addEventListener("input",update);root.addEventListener("change",update);update();
})();