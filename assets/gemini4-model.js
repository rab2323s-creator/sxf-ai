(function(){"use strict";
var root=document.querySelector("[data-g4-planner]");
if(root){
 var price=root.querySelector("[data-g4-rate]"),input=root.querySelector("[data-g4-input]"),cached=root.querySelector("[data-g4-cache]"),thinking=root.querySelector("[data-g4-think]"),output=root.querySelector("[data-g4-output]");
 var cost=root.querySelector("[data-g4-cost]"),ic=root.querySelector("[data-g4-input-cost]"),oc=root.querySelector("[data-g4-output-cost]"),total=root.querySelector("[data-g4-tokens]"),status=root.querySelector("[data-g4-status]"),explain=root.querySelector("[data-g4-explain]"),meter=root.querySelector("[role=meter]"),bar=root.querySelector("[data-g4-bar]");
 var LIMIT=1048576,SYNC=65536;
 function whole(el){var x=Number(el.value);return Number.isFinite(x)?Math.max(0,Math.min(LIMIT,Math.floor(x))):0;}
 function money(x){return "$"+x.toFixed(4);}
 function update(){
  var i=whole(input),c=whole(cached),t=whole(thinking),o=whole(output),intro=price.value==="intro";
  var inRate=intro?2:4,cachedRate=intro?.10:.20,outRate=intro?10:20;
  var actualCached=Math.min(i,c),iCost=((i-actualCached)*inRate+actualCached*cachedRate)/1000000,oCost=(t+o)*outRate/1000000;
  var used=i+t+o,generated=t+o,percentage=Math.min(100,100*used/LIMIT);
  cost.textContent=money(iCost+oCost);ic.textContent=money(iCost);oc.textContent=money(oCost);
  total.textContent=used.toLocaleString("en-US")+" / "+LIMIT.toLocaleString("en-US");
  bar.style.width=percentage.toFixed(2)+"%";meter.setAttribute("aria-valuenow",Math.round(percentage));meter.setAttribute("aria-valuetext",used.toLocaleString("en-US")+" of "+LIMIT.toLocaleString("en-US")+" tokens");
  if(c>i){status.textContent="Cache value exceeds prompt input";explain.textContent="Only the overlapping cached input is counted in this illustrative calculation. Change the cached input to be at most total input.";}
  else if(used>LIMIT){status.textContent="Planned tokens exceed the 1M shared context";explain.textContent="Reduce input, thinking or output. Background long decode does not raise the 1,048,576-token total shared window.";}
  else if(generated>SYNC){status.textContent="Background long decode required";explain.textContent="Requested thinking plus visible output exceeds 65,536 tokens. Use background execution and check API usage, continuation and timeouts.";}
  else{status.textContent="Fits the synchronous token ceiling on paper";explain.textContent="Illustrative standard-rate estimate only; usage measured by Google, tool charges, cache hit and retries can change the bill.";}
 }
 for(var el of [price,input,cached,thinking,output]){el.addEventListener("input",update);el.addEventListener("change",update);}update();
}
document.querySelectorAll("[data-g4-copy]").forEach(function(button){
 button.addEventListener("click",function(){
  var id=button.getAttribute("data-g4-copy"),code=document.querySelector("#g4-code-"+id+" code");if(!code)return;
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(code.textContent).then(function(){button.textContent="Copied";button.setAttribute("aria-label","Code copied");},function(){button.textContent="Select code";});}
  else{button.textContent="Select code";}
 });
});
})();