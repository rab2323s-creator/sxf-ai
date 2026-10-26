/* SXF Evidence Ladder — local-only guide; never analyzes or uploads an image. */
(() => {
  "use strict";
  const byId = id => document.getElementById(id);
  if (!byId("sxf-image-evidence-tool")) return;
  const file = byId("sxf-file-type"), obs = byId("sxf-observation");
  const stakes = byId("sxf-stakes"), provider = byId("sxf-provider");
  const title = byId("sxf-result-title"), explainer = byId("sxf-result-explainer");
  const steps = byId("sxf-result-steps"), feedback = byId("sxf-copy-feedback");
  let last = null;
  const decide = () => {
    const observation = obs.value;
    let result = {title:"Unverified — start with evidence, not appearance",
      explain:"No verified AI origin, camera provenance or trustworthy context has been established yet. An unknown result is not an authentic-or-AI verdict.",
      steps:[
        file.value==="original" ? "Preserve the original image before cropping or re-exporting it." : "Find the original file if possible; a screenshot or forwarded copy may lack origin signals.",
        "Try Google Lens, then open the earliest available credible source.",
        "Check signed Content Credentials and an appropriate official watermark tool."
      ]};
    if (observation==="verified-ai") result={
      title:"Positive evidence of AI involvement",
      explain:"A valid signed AI-origin record or official supported watermark is evidence that this file was generated or edited with the relevant AI tool. Check the issuer and whether the signal describes some or all of the content; it does not prove who posted the image or whether its caption is accurate.",
      steps:["Preserve the original file and verification result.","Record the issuer and any declared creation/editing scope.","Check the claim or caption separately against trustworthy reporting."]
    };
    if (observation==="signed-camera") result={
      title:"Signed camera history — scene still needs checking",
      explain:"Signed capture provenance can support the file's creation history but cannot prove that the scene, screen or event captured is genuine.",
      steps:["Inspect what the signed issuer actually certifies.","Check for edits and the publisher's original description.","Find independent evidence of the depicted event."]
    };
    if (observation==="reverse-mismatch") result={
      title:"Possible misleading caption or recycled image",
      explain:"An older matching picture with a different claim can challenge the current caption, but it does not establish that the image pixels were AI-generated.",
      steps:["Save the earlier source URL and compare the claimed place and date.","Check independent reporting about the current event.","Describe the issue as a context mismatch, not automatically an AI fake."]
    };
    if (observation==="detector") result={
      title:"Weak indication only — not a verdict",
      explain:"A generic AI classifier score or unusual visual detail is not authenticated provenance. Both can be wrong.",
      steps:["Look for the original source and reverse-image matches.","Check credentials and provider watermark tools where appropriate.","Use independent corroboration before making public accusations."]
    };
    if (observation==="negative") result={
      title:"No supported signal detected; origin remains unknown",
      explain:"Missing metadata or an undetected watermark does not prove that a person created this picture. Sharing, editing, screenshots or coverage limits may explain the missing signal.",
      steps:["Try the original file if available.","Use source history and corroboration instead of calling it 'verified real'.","Try the relevant official provider's tool, noting its coverage."]
    };
    if (provider.value==="openai" && observation!=="verified-ai") result.steps.push("For suspected OpenAI origin, check the original at openai.com/verify.");
    if (provider.value==="google" && observation!=="verified-ai") result.steps.push("For suspected Google AI origin, use Gemini's supported verification flow.");
    if (stakes.value==="high") result.steps.push("High stakes: get independent first-hand confirmation before sharing, paying or taking action.");
    return result;
  };
  const render=()=>{
    last=decide();
    title.textContent=last.title;explainer.textContent=last.explain;
    steps.replaceChildren();
    last.steps.forEach(line=>{const li=document.createElement("li");li.textContent=line;steps.appendChild(li);});
    feedback.textContent="Guidance only. SXF receives no image or selected options.";
  };
  [file,obs,stakes,provider].forEach(control=>control.addEventListener("change",render));
  byId("sxf-reset-plan").addEventListener("click",()=>{
    file.value="original";obs.value="none";stakes.value="casual";provider.value="unknown";render();file.focus();
  });
  byId("sxf-copy-plan").addEventListener("click",async()=>{
    const summary=["SXF Evidence Ladder",last.title,last.explain,"","Suggested next checks:",...last.steps.map((s,i)=>(i+1)+". "+s),"","Not an AI detector or proof of authenticity.","https://sxf.si/guides/how-to-tell-if-an-image-is-ai-generated/"].join("\n");
    try {
      if(navigator.clipboard && navigator.clipboard.writeText){await navigator.clipboard.writeText(summary);feedback.textContent="Verification plan copied.";}
      else feedback.textContent="Clipboard access unavailable. Select the visible plan to copy it.";
    } catch (_) { feedback.textContent="Clipboard permission blocked. Select the visible plan to copy it."; }
  });
  render();
})();
