/* SXF Claude Haiku 5.5 vs Sonnet 5.5 workload estimator.
 * Standard Claude API token rates, per million; no network, cookies or telemetry.
 * A prompt above 100K is billed at Haiku's higher tier for the entire request.
 */
"use strict";
const HAIKU_SONNET_RATES=Object.freeze({
  haikuShort:Object.freeze({input:.10,output:.50,read:.01,write:.125}),
  haikuLong:Object.freeze({input:.50,output:2.50,read:.05,write:.625}),
  sonnet:Object.freeze({input:2,output:10,read:.10,write:2.50})
});
function computeHaikuSonnetCost({requests,input,output,cacheRead=0,cacheWrite=0}){
  const values=[requests,input,output,cacheRead,cacheWrite];
  if(values.some(x=>!Number.isFinite(x)))throw Error("All values must be finite numbers.");
  if(!Number.isInteger(requests)||requests<1||requests>10000000)throw Error("Requests must be an integer from 1 to 10,000,000.");
  if(!Number.isInteger(input)||input<1||input>1000000)throw Error("Input tokens must be an integer from 1 to 1,000,000.");
  if(!Number.isInteger(output)||output<0||output>128000)throw Error("Output tokens must be an integer from 0 to 128,000.");
  if(!Number.isInteger(cacheRead)||!Number.isInteger(cacheWrite)||cacheRead<0||cacheWrite<0||cacheRead>100||cacheWrite>100||cacheRead+cacheWrite>100)
    throw Error("Cache read and write percentages must be whole numbers totaling at most 100%.");
  const uncached=input*(100-cacheRead-cacheWrite)/100;
  const reads=input*cacheRead/100;
  const writes=input*cacheWrite/100;
  const longPrompt=input>100000;
  const rH=longPrompt?HAIKU_SONNET_RATES.haikuLong:HAIKU_SONNET_RATES.haikuShort;
  const rS=HAIKU_SONNET_RATES.sonnet;
  const cost=r=>requests*(uncached*r.input+reads*r.read+writes*r.write+output*r.output)/1000000;
  const haiku=cost(rH),sonnet=cost(rS);
  return {haiku,sonnet,savings:sonnet-haiku,longPrompt,uncached,reads,writes,requests,input,output,ratio:haiku>0?sonnet/haiku:0};
}
if(typeof module!=="undefined"&&module.exports)module.exports={computeHaikuSonnetCost,HAIKU_SONNET_RATES};
if(typeof document!=="undefined"){
  const form=document.getElementById("hs-cost-form");
  if(form){
    const input=(id)=>document.getElementById(id);
    const total=(v)=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2}).format(v);
    const display=(id,value)=>{const node=input(id);if(node)node.textContent=value;};
    const alert=input("hs-lab-error");
    const update=()=>{
      try{
        const data={
          requests:Number(input("hs-requests").value),input:Number(input("hs-input").value),
          output:Number(input("hs-output").value),cacheRead:Number(input("hs-cache-read").value),
          cacheWrite:Number(input("hs-cache-write").value)
        };
        if(["hs-requests","hs-input","hs-output","hs-cache-read","hs-cache-write"].some(id=>input(id).value.trim()===""))
          throw Error("Fill in every field to calculate your scenario.");
        const out=computeHaikuSonnetCost(data);
        display("hs-haiku-total",total(out.haiku));
        display("hs-sonnet-total",total(out.sonnet));
        display("hs-savings",total(out.savings));
        display("hs-haiku-tier",out.longPrompt?">100K prompt tier":"≤100K prompt tier");
        display("hs-cost-comparison","Haiku token cost is "+out.ratio.toFixed(1)+"× lower for these identical token counts. Actual quality, retries, prompt caching and tokenization can change end-to-end value.");
        if(alert){alert.hidden=true;alert.textContent="";}
      }catch(error){
        if(alert){alert.hidden=false;alert.textContent=error.message;}
        display("hs-haiku-total","—");display("hs-sonnet-total","—");display("hs-savings","—");
        display("hs-cost-comparison","Enter a valid workload to compare both models.");
      }
    };
    form.addEventListener("submit",event=>{event.preventDefault();update();});
    form.addEventListener("input",update);
    update();
  }
}
