"use strict";
/* SXF local workstation illustrative capacity model: no API calls, cookies, tracking or network. */
(function(){
const systems=[{"slug":"spark","name":"NVIDIA DGX Spark (128GB)","memory":128,"share":80,"bw":273,"notes":"GB10/CUDA; 128 GB model, not the 64 GB variant","source":"https://www.nvidia.com/en-us/products/workstations/dgx-spark/"},{"slug":"max","name":"Mac Studio M5 Max (128GB upgrade)","memory":128,"share":75,"bw":614,"notes":"40-core GPU option; 128GB is not the $2,499 base configuration","source":"https://support.apple.com/en-euro/128107"},{"slug":"ultra","name":"Mac Studio M5 Ultra (256GB upgrade)","memory":256,"share":80,"bw":1200,"notes":"96 GB is the base; 256 GB is a higher-cost option","source":"https://support.apple.com/en-euro/128107"},{"slug":"ryzen","name":"Ryzen AI Max+ 395 PC (128GB)","memory":128,"share":70,"bw":256,"notes":"AMD x86/ROCm support depends on OS and model/runtime build","source":"https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html"}];
const models=[{"slug":"qwen9","name":"Qwen3.5 9B dense","params":9,"active":9},{"slug":"qwen27","name":"Qwen3.5 27B dense","params":27,"active":27},{"slug":"qwen35","name":"Qwen3.5 35B-A3B MoE","params":35,"active":3},{"slug":"qwen122","name":"Qwen3.5 122B-A10B MoE","params":122,"active":10},{"slug":"qwen235","name":"Qwen3 235B-A22B MoE","params":235,"active":22}];
const el=id=>document.getElementById(id);
const device=el("lw-system"),model=el("lw-model"),quant=el("lw-quant"),reserve=el("lw-reserve"),share=el("lw-share");
if(!device||!model||!quant||!reserve||!share)return;
const toGB=n=>Number(n).toFixed(1)+"GB";
function calc(){
const sys=systems.find(x=>x.slug===device.value)||systems[0];
const m=models.find(x=>x.slug===model.value)||models[0];
const bits=Number(quant.value),reserved=Number(reserve.value),fraction=Number(share.value);
const estimatedWeights=m.params*(bits/8)*1.1,need=estimatedWeights+reserved,pool=sys.memory*fraction/100,margin=pool-need;
el("lw-share-val").textContent=fraction+"%";
el("lw-weight").textContent=toGB(estimatedWeights);el("lw-pool").textContent=toGB(pool);el("lw-demand").textContent=toGB(need);el("lw-margin").textContent=toGB(margin);
el("lw-bar").style.width=Math.min(100,(need/pool)*100).toFixed(1)+"%";
let label,cls;
if(margin<0){label="Over illustrative memory budget: reduce model size, quantization, context headroom or choose a larger memory tier.";cls="lw-risk"}
else if(margin<pool*.1){label="Borderline illustrative fit: real runtime/context differences could make it fail. Validate exact model and GPU allocation.";cls="lw-caution"}
else{label="Fits the illustrative memory screen only. Real runtime loading and useful generation speed are NOT verified.";cls="lw-ok"}
el("lw-verdict").textContent=label;el("lw-verdict").className=cls;
el("lw-case-summary").textContent="Device: "+sys.name+". Total model: "+m.params+"B parameters; active "+m.active+"B per token (where applicable). Total, not active, determines the simplified weight budget. Allocation and runtime reserve are user assumptions.";
}
device.addEventListener("change",()=>{const s=systems.find(x=>x.slug===device.value);share.value=s.share;calc()});
for(const e of [model,quant,reserve,share])e.addEventListener("input",calc);
calc();
})();