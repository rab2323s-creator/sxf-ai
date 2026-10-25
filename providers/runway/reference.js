/* Runway provider calculator. Base developer cost only; no network calls. */
(function () {
  "use strict";
  var root = document.querySelector("[data-runway-estimator]");
  if (!root) return;
  var duration = document.getElementById("runway-duration");
  var count = document.getElementById("runway-count");
  var durationLabel = document.getElementById("runway-duration-label");
  var countLabel = document.getElementById("runway-count-label");
  var cost = document.getElementById("runway-estimated-usd");
  var credits = document.getElementById("runway-estimated-credits");
  var seconds = document.getElementById("runway-estimated-seconds");
  if (!(duration && count && durationLabel && countLabel && cost && credits && seconds)) return;
  function update() {
    var d = Math.min(10, Math.max(2, Number(duration.value) || 5));
    var n = Math.min(20, Math.max(1, Number(count.value) || 1));
    var totalSeconds = d * n;
    var totalCredits = totalSeconds * 12;
    durationLabel.textContent = d + " s";
    countLabel.textContent = String(n);
    cost.textContent = "$" + (totalCredits * 0.01).toFixed(2);
    credits.textContent = totalCredits.toLocaleString("en-US") + " credits";
    seconds.textContent = totalSeconds + " generated seconds";
  }
  duration.addEventListener("input", update);
  count.addEventListener("input", update);
  update();
}());