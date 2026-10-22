"use strict";
// SXF reference lab: deterministic model/API token budget calculations.
// No network requests, API keys, or claims of AI model evaluation.
function calculate(input) {
  const keys=["requests","inputTokens","outputTokens","inputUsdPerMillion","outputUsdPerMillion"];
  const n={};for(const k of keys){
    const raw=input[k];
    if((typeof raw!=="string"&&typeof raw!=="number")||(typeof raw==="string"&&raw.trim()==="")) throw new RangeError(k+" must be a numeric value");
    n[k]=Number(raw);if(!Number.isFinite(n[k])||n[k]<0)throw new RangeError(k+" must be finite and nonnegative");
  }
  for(const k of ["requests","inputTokens","outputTokens"])if(!Number.isSafeInteger(n[k]))throw new RangeError(k+" must be an integer");
  const inputCost=n.requests*n.inputTokens*n.inputUsdPerMillion/1000000;
  const outputCost=n.requests*n.outputTokens*n.outputUsdPerMillion/1000000;
  const total=inputCost+outputCost;if(!Number.isFinite(total))throw new RangeError("cost overflow");
  return {inputCost,outputCost,total};
}
if(typeof module!=="undefined"&&module.exports)module.exports={calculate};
if(typeof document!=="undefined"){
const form=document.querySelector("#vc-lab-form"),result=document.querySelector("#vc-lab-result");
if(form&&result){form.addEventListener("submit",event=>{
event.preventDefault();try{const data=Object.fromEntries(new FormData(form));const {inputCost,outputCost,total}=calculate(data);
const fmt=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumFractionDigits:4,maximumFractionDigits:6});
result.textContent="Estimated input "+fmt.format(inputCost)+" + output "+fmt.format(outputCost)+" = "+fmt.format(total)+" total, excluding tools, caching, retries, taxes and platform fees.";
}catch(error){result.textContent="Check inputs: "+error.message;}
});}
}
