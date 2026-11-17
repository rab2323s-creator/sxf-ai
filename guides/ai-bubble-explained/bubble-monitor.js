
"use strict";
(() => {
  // Original SXF editorial scenario explorer. It contains no probabilities or API calls.
  const scenarios = Object.freeze({
    expansion: {
      title: "A · Productivity pays for the buildout",
      description: "Independent customer revenue and efficient capacity utilization improve alongside spending.",
      support: "Recurring third-party revenue, higher utilization and improved unit economics.",
      risk: "Orders accelerate while cash conversion and demand quality deteriorate.",
      households: "Faster tool adoption, changing skills demand and localized grid investment."
    },
    digestion: {
      title: "B · Selective correction and long digestion",
      description: "Companies delay marginal projects, maintain core products and focus on returns from installed capacity.",
      support: "Stable customer demand, slower capex, weaker suppliers but durable cloud economics.",
      risk: "Funding stress broadens or new demand and profit reaccelerate sharply.",
      households: "Uneven regional hiring, market volatility and possible AI tool repricing."
    },
    shock: {
      title: "C · Financing shock with spillovers",
      description: "Credit conditions tighten alongside weak demand, pushing vulnerable projects into cancellation.",
      support: "Cross-firm credit deterioration, refinance stress and correlated hiring/project cuts.",
      risk: "Healthy refinancing and strong independent earnings contain the correction.",
      households: "Concentrated portfolio losses, labor disruptions and ambiguous utility-cost effects."
    }
  });
  const buttons = Array.from(document.querySelectorAll("[data-scenario]"));
  const show = key => {
    const model = scenarios[key];
    if (!model) return;
    for (const b of buttons) b.setAttribute("aria-pressed", String(b.dataset.scenario === key));
    const bindings = {
      "b-dynamic-title": model.title,
      "b-dynamic-description": model.description,
      "b-dynamic-support": model.support,
      "b-dynamic-risk": model.risk,
      "b-dynamic-households": model.households
    };
    for(const [id, value] of Object.entries(bindings)) {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    }
  };
  buttons.forEach(button => button.addEventListener("click", () => show(button.dataset.scenario)));
  const share = document.getElementById("b-weight");
  const drop = document.getElementById("b-drop");
  const update = () => {
    if (!share || !drop) return;
    const weight = Number(share.value);
    const decline = Number(drop.value);
    const impact = weight * decline / 100;
    document.getElementById("b-weight-label").textContent = weight + "%";
    document.getElementById("b-drop-label").textContent = decline + "%";
    document.getElementById("b-loss-label").textContent = "\u2212" + impact.toFixed(1) + "%";
    document.getElementById("b-loss-method").textContent = weight + "% allocation \u00d7 " + decline + "% decline = " + impact.toFixed(1) + "% portfolio decline, if other assets do not move.";
  };
  for(const el of [share, drop]) if(el)el.addEventListener("input",update);
  update();show("expansion");
})();
