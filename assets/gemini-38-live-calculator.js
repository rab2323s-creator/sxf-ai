/* SXF Gemini 3.8 Live media-cost estimator.
   Illustrative Google's published approximate minute equivalents, not live billing.
   No network calls, tracking, external dependencies, or storage. */
(function () {
  "use strict";
  const root = document.querySelector("[data-g38-calculator]");
  if (!root) return;
  const fields = {
    input: root.querySelector("[data-g38-in]"),
    output: root.querySelector("[data-g38-out]"),
    video: root.querySelector("[data-g38-video]"),
    sessions: root.querySelector("[data-g38-sessions]")
  };
  const per = root.querySelector("[data-g38-per]");
  const total = root.querySelector("[data-g38-total]");
  const breakdown = root.querySelector("[data-g38-breakdown]");
  if (!fields.input || !fields.output || !fields.video || !fields.sessions ||
      !per || !total || !breakdown) return;
  const read = (control) => {
    const value = Number(control.value);
    return Number.isFinite(value) ? Math.min(10000000, Math.max(0, value)) : 0;
  };
  const money = (amount, decimals) => new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(amount);
  const update = () => {
    const input = read(fields.input), output = read(fields.output);
    const video = read(fields.video);
    const sessions = Math.floor(read(fields.sessions));
    const perSession = input * 0.005 + output * 0.018 + video * 0.002;
    per.textContent = money(perSession, 4);
    total.textContent = money(perSession * sessions, 2);
    breakdown.textContent = input + " × $0.005 + " + output + " × $0.018 + " +
      video + " × $0.002 = " + money(perSession, 4) + " per session.";
  };
  Object.values(fields).forEach((element) => element.addEventListener("input", update));
  update();
})();
