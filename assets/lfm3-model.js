(function(){ "use strict";
var root=document.querySelector("[data-lfm3-finder]");
if(root){
 var task=root.querySelector("[data-lfm3-task]"), local=root.querySelector("[data-lfm3-private]"), custom=root.querySelector("[data-lfm3-custom]");
 var models={
  agent:["LFM3-1.7B","Text → text","256K tokens","Use the text model for local agents, structured JSON extraction and tool selection.","Evaluate valid JSON, context recall and tool authorization.","https://huggingface.co/LiquidAI/LFM3-1.7B"],
  image:["LFM3-VL-2B","Text + image/video → text","128K tokens","Choose the vision branch for charts, screenshots, receipts and video frames.","Evaluate OCR, spatial grounding and false descriptions on your images.","https://huggingface.co/LiquidAI/LFM3-VL-2B"],
  speech:["LFM3-Audio-2B","Text/audio → text/speech","32K tokens","Choose the audio branch for speech recognition, voice replies and sound interpretation.","Measure word errors, streaming latency and language quality.","https://huggingface.co/LiquidAI/LFM3-Audio-2B"],
  omni:["LFM3-Omni-2B","Text + images + audio/video → text/speech","See model card","Choose omni when spoken input and visual evidence must be combined in a response.","Check cross-modal grounding, latency and safe tool use.","https://huggingface.co/LiquidAI/LFM3-Omni-2B"],
  decide:["d1-2B","Text + images/video → typed decisions","128K tokens","Use the decision branch for classification, ranking or structured extraction.","Test probability calibration and false-positive costs.","https://huggingface.co/LiquidAI/d1-2B"],
  "voice-decide":["d1-Omni-2B","Text + images + audio/video → typed decisions","See model card","Choose this branch for audio-aware routing and calibrated multimodal decisions.","Measure robustness to voice accents, recording quality and calibration drift.","https://huggingface.co/LiquidAI/d1-Omni-2B"]
 };
 var name=root.querySelector("[data-lfm3-name]"),reason=root.querySelector("[data-lfm3-reason]"),io=root.querySelector("[data-lfm3-io]"),context=root.querySelector("[data-lfm3-context]"),check=root.querySelector("[data-lfm3-check]"),link=root.querySelector("[data-lfm3-link]");
 function update(){
  var row=models[task.value]||models.agent;
  name.textContent=row[0];reason.textContent=row[3];io.textContent=row[1];context.textContent=row[2];
  check.textContent=row[4]+(local.checked?" Verify preprocessing and logs remain on device.":" Check provider retention, access and billing.")+(custom.checked?" Keep a held-out test set after fine-tuning.":" Start with an untuned checkpoint baseline.");
  link.href=row[5];link.setAttribute("aria-label","Open official "+row[0]+" model card");
 }
 task.addEventListener("change",update);local.addEventListener("change",update);custom.addEventListener("change",update);update();
}
document.querySelectorAll("[data-lfm3-copy]").forEach(function(button){
 button.addEventListener("click",function(){
  var key=button.getAttribute("data-lfm3-copy");
  var el=document.querySelector("#lfm3-code-"+key+" code");
  if(!el)return;
  if(navigator.clipboard&&navigator.clipboard.writeText){
   navigator.clipboard.writeText(el.textContent).then(function(){button.textContent="Copied";button.setAttribute("aria-label","Code copied");},function(){button.textContent="Select code";});
  }else{button.textContent="Select code";}
 });
});
})();