/* SXF / AI: transparent, local-only speech transcription economics.
   Reference prices in USD per audio hour (9 November 2026); no API calls. */
(function () {
  "use strict";
  const root = document.querySelector("[data-sv2-lab]");
  if (!root) return;
  const RATE = Object.freeze({base: 0.22, keyterms: 0.05, editing: 0.07});
  const get = (name) => root.querySelector("[data-sv2-" + name + "]");
  const duration = get("minutes");
  const count = get("recordings");
  const channels = get("channels");
  const keyterms = get("keyterms");
  const editing = get("editing");
  const billed = get("hours");
  const monthly = get("monthly");
  const annual = get("annual");
  const details = get("details");
  const alert = get("alert");
  if ([duration,count,channels,keyterms,editing,billed,monthly,annual,details,alert].some(x => !x)) return;
  function clean(number, max) {
    const n = Number(number);
    return Number.isFinite(n) && n > 0 ? Math.min(n,max) : 0;
  }
  function dollars(n) {
    return n.toLocaleString("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2});
  }
  function update() {
    const mins = clean(duration.value, 600);
    const files = clean(count.value, 1e7);
    const n = Math.max(1,Math.min(5,Math.round(clean(channels.value,5)||1)));
    if(n>1 && editing.checked) editing.checked=false;
    editing.disabled = n>1;
    const hours = mins * files * n / 60;
    const hourly = RATE.base + (keyterms.checked?RATE.keyterms:0) + (editing.checked?RATE.editing:0);
    const total = hours * hourly;
    billed.textContent = hours.toLocaleString("en-US",{maximumFractionDigits:2})+" h";
    monthly.textContent = dollars(total);
    annual.textContent = dollars(total*12);
    details.textContent = "Hourly estimate: $0.22 base"+(keyterms.checked?" + $0.05 keyterms":"")+
      (editing.checked?" + $0.07 transcript editing":"")+
      " = "+dollars(hourly)+" per billed channel-hour.";
    alert.textContent = n>1
      ? "Multichannel mode bills each channel separately; transcript editing is unavailable with multichannel input."
      : "Illustrative duration-based estimate. Silence and pauses count toward billed audio.";
  }
  [duration,count,channels,keyterms,editing].forEach(el => el.addEventListener("input",update));
  update();
})();
