(() => {
"use strict";
const ids = ["dep-tasks", "dep-attempts", "dep-run-cost", "dep-fixed", "dep-review", "dep-worker"];
const inputs = ids.map(id => document.getElementById(id));
if (inputs.some(el => !el)) return;
const money = v => new Intl.NumberFormat("en-US", {style:"currency", currency:"USD", maximumFractionDigits:3}).format(v);
const num = v => new Intl.NumberFormat("en-US", {maximumFractionDigits:1}).format(v);
function update() {
  const [tasks, attempts, run, fixed, review, worker] = inputs.map(x => Number(x.value));
  const out = ["dep-monthly", "dep-per-task", "dep-monthly-attempts"].map(id => document.getElementById(id));
  if (![tasks, attempts, run, fixed, review, worker].every(Number.isFinite) || tasks < 1 || attempts < 1 || run < 0 || fixed < 0 || review < 0 || worker < 1) {
    out.forEach(x => x.textContent = "Check inputs");
    return;
  }
  const monthly = tasks * attempts * run + fixed + tasks * review;
  out[0].textContent = money(monthly);
  out[1].textContent = money(monthly/tasks);
  out[2].textContent = num(tasks*attempts);
}
inputs.forEach(el => el.addEventListener("input",update)); update();
})();