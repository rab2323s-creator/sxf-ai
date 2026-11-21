(() => {
  "use strict";
  const root = document.getElementById("skillLab");
  if (!root) return;
  const all = [...root.querySelectorAll("select.sk-observation")];
  const get = id => document.getElementById(id);
  const pct = (a,b) => b ? (100*a/b).toFixed(0)+"%" : "N/A";
  const recalc = () => {
    let tp=0,tn=0,fp=0,fn=0,done=0;
    all.forEach(select => {
      const row = select.closest("tr");
      const expected = row.dataset.expected === "1";
      if (select.value === "") { delete row.dataset.result; return; }
      done++;
      const observed = select.value === "1";
      row.dataset.result = observed===expected ? "correct" : "wrong";
      if (expected && observed) tp++;
      else if (!expected && observed) fp++;
      else if (expected) fn++;
      else tn++;
    });
    get("skMeasured").textContent=done+" / "+all.length;
    get("skPrecision").textContent=pct(tp,tp+fp);
    get("skRecall").textContent=pct(tp,tp+fn);
    get("skFalsePositives").textContent=String(fp);
    get("skLabNote").textContent=done===0?"No agent execution is included. Mark outcomes only after observing an actual invocation trace.":(done<all.length?"Partial manual observations.":"All cases annotated manually; results have not been independently verified.");
  };
  root.addEventListener("change", e=>{if(e.target.matches("select.sk-observation")) recalc();});
  get("resetSkillLab").addEventListener("click", ()=>{all.forEach(select=>{select.value="";});recalc();});
  recalc();
})();