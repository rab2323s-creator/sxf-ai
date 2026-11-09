/* SXF topic navigation event bridge. No cookies, storage, or network calls.
 * Analytics software must explicitly subscribe; no data is collected by default. */
(() => {
  "use strict";
  if (typeof document === "undefined") return;
  document.addEventListener("click", event => {
    const target = event.target;
    if (!target || typeof target.closest !== "function") return;
    const link = target.closest("a[href]");
    if (!link) return;
    const fromHub = !!link.closest(".topics-hub-page main");
    const fromContext = !!link.closest("[data-topic-context]");
    if (!fromHub && !fromContext) return;
    const href = link.getAttribute("href") || "";
    if (!/^\/(?!\/)[^?#]+\/(?:[?#].*)?$/.test(href)) return;
    if (!/^\/(?:topics|guides|research|models|signals|compare|tools|open-source)\//.test(href)) return;
    const payload = {
      event: "sxf_topic_navigation",
      topic_source: fromHub ? "topics_hub" : "related_context",
      topic_origin: window.location.pathname,
      topic_destination: href.split(/[?#]/, 1)[0]
    };
    if (Array.isArray(window.dataLayer)) window.dataLayer.push(payload);
    window.dispatchEvent(new CustomEvent("sxf:topic-navigation", { detail: payload }));
  }, { passive: true });
})();
