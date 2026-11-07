/* SXF Voxtral 2 transcription cost lab: no network, storage, or audio capture. */
(function () {
  "use strict";
  const root = document.querySelector("[data-vox2-cost-lab]");
  if (!root) return;
  const fields = {
    count: root.querySelector("[data-vox2-count]"),
    minutes: root.querySelector("[data-vox2-minutes]"),
    tier: root.querySelector("[data-vox2-tier]"),
    retries: root.querySelector("[data-vox2-retries]"),
    review: root.querySelector("[data-vox2-review]"),
    hourly: root.querySelector("[data-vox2-hourly]")
  };
  const views = {
    audio: root.querySelector("[data-vox2-audio]"),
    api: root.querySelector("[data-vox2-api]"),
    human: root.querySelector("[data-vox2-human]"),
    total: root.querySelector("[data-vox2-total]"),
    details: root.querySelector("[data-vox2-details]")
  };
  if (Object.values(fields).some((field) => !field) ||
      Object.values(views).some((field) => !field)) return;
  const number = (control, max) => {
    const value = Number(control.value);
    return Number.isFinite(value) ? Math.max(0, Math.min(max, value)) : 0;
  };
  const usd = (value) => new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 2
  }).format(value);
  const fmt = (value) => new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value);
  function update() {
    const count = Math.floor(number(fields.count, 1000000));
    const length = number(fields.minutes, 180);
    const tier = fields.tier.value === "batch" ? "batch" : "standard";
    const rate = tier === "batch" ? 0.0003 : 0.003;
    const retryFraction = number(fields.retries, 500) / 100;
    const review = number(fields.review, 600);
    const hourly = number(fields.hourly, 10000);
    const audio = count * length;
    const api = audio * (1 + retryFraction) * rate;
    const reviewHours = audio / 60 * review / 60;
    const human = reviewHours * hourly;
    views.audio.textContent = fmt(audio) + " min";
    views.api.textContent = usd(api);
    views.human.textContent = usd(human);
    views.total.textContent = usd(api + human);
    views.details.textContent = fmt(count) + " × " + fmt(length) + " minutes; " +
      fmt(retryFraction * 100) + "% expected reprocessing; " + fmt(reviewHours) +
      " reviewer hours at " + usd(hourly) + " per hour. Historical V2 " + tier + " tier.";
  }
  Object.values(fields).forEach((field) => field.addEventListener("input", update));
  Object.values(fields).forEach((field) => field.addEventListener("change", update));
  update();
})();
