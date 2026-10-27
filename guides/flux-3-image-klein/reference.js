(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const el = $('[data-flux-lab]');
  const cash = $('[data-price-lab]');
  if (el) {
    const fields = ['#fluxVram','#fluxArch','#fluxRuntime','#fluxPrecision'].map($);
    const render = () => {
      const [vram,arch,runtime,precision] = fields.map(x => x.value);
      const memory = Number(vram);
      let grade = 'Conditional / verify locally', msg = 'This exact combination is not a vendor-documented 8GB recipe. Verify the loader, memory profile, text encoder and prompt upsampler in the official model card.';
      const checks=[];
      if (runtime==='comfy' && precision==='int8' && memory>=8 && (arch==='old'||arch==='ada'||arch==='blackwell')) {
        grade='Documented candidate — not guaranteed';
        msg='BFL documents a ComfyUI INT8 route on some NVIDIA RTX GPUs starting at 8GB. Your specific card, system RAM, offload and workflow must still be tested.';
        checks.push('Start with the official distilled INT8 workflow and a 1MP image.');
      } else if (memory<8) {
        grade='Outside documented 8GB minimum';
        msg='The official local INT8 claim starts at 8GB RTX. A smaller card may require unsupported modifications or a remote API; SXF does not label it compatible.';
      } else if (runtime==='reference' && memory<32) {
        grade='Not the documented low-memory route';
        msg='Reference-pipeline peak memory can exceed the GPU budget, especially when the prompt upsampler is enabled. Use the official full-pipeline numbers for your chosen precision and offload plan.';
      } else if (runtime==='diffusers' && precision==='int8' && memory>=8) {
        grade='Source-documented family; implementation-specific';
        msg='BFL cites an INT8 Diffusers path, but the exact peak memory depends on component placement and software versions. Do not transfer ComfyUI measurements to your own implementation.';
      }
      if (precision==='nvfp4' && arch!=='blackwell') {grade='Architecture warning';msg='The published NVFP4-accelerated path is intended for supported Blackwell architecture and compatible runtimes. Do not assume RTX 20/30/40 can load this optimized format.';}
      if (precision==='bf16' && memory<=16) {grade='Likely unsuitable without substantial offload';msg='BF16 transformer weights alone are approximately 11.2GB, excluding encoder, upsampler and activation buffers. Check the measured reference run; 8-16GB is not the vendor\'s standard BF16 guarantee.';}
      if (precision==='fp8' && memory<=12) {grade='Conditional: no 8GB FP8 guarantee';msg='The FP8 weights are smaller than BF16, but a full pipeline needs more than the transformer file. BFL\'s 8GB claim refers to the specified INT8 path.';}
      checks.push('Review gated download and the FLUX Kommunity License before use.','Measure actual peak VRAM and host RAM; record checkpoint, prompt-upscaler and resolution.');
      $('#fluxDecision').innerHTML='<span class="flux-result-label">'+grade+'</span><h3>Recommended next step</h3><p>'+msg+'</p><ul>'+checks.map(x=>'<li>'+x+'</li>').join('')+'</ul>';
    };
    fields.forEach(f=>f.addEventListener('change',render)); render();
  }
  if (cash) {
    const render = () => {
      const count = Math.min(100000,Math.max(1,Math.trunc(Number($('#fluxImages').value)||1)));
      const reruns=Number($('#fluxRetry').value)/100;
      const n=Math.ceil(count*(1+reruns));
      const amount=(n*0.009).toLocaleString('en-US',{style:'currency',currency:'USD'});
      $('#fluxCost').innerHTML='<span class="flux-result-label">Illustrative 1K starting-rate scenario</span><h3>'+amount+'</h3><p>'+n.toLocaleString('en-US')+' total image requests at the announced starting price of $0.009 each. Budgeted accepted outputs: '+count.toLocaleString('en-US')+'.</p>';
    };
    $('#fluxImages').addEventListener('input',render);$('#fluxRetry').addEventListener('change',render);render();
  }
})();
