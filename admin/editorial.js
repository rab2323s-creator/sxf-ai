"use strict";
/* SXF human editorial console: GitHub is the sole source of approval truth.
   Credentials exist only in JS memory; never localStorage, cookies or URLs. */
(() => {
  const REPO = "rab2323s-creator/sxf-ai";
  const API = "https://api.github.com/repos/" + REPO + "/contents/";
  const RAW = "https://raw.githubusercontent.com/" + REPO + "/main/data/editorial-inbox.json";
  let token = "", user = "", inbox = [], decisions = [], rejectedFingerprints = [], ledgerSha = "", busy = false;
  const $ = id => document.getElementById(id);
  const message = (value, error = false) => {
    $("message").textContent = value;
    $("message").classList.toggle("error", error);
  };
  async function request(path, opts = {}) {
    const response = await fetch(path, {
      ...opts, cache: "no-store",
      headers: {Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        ...(token ? {Authorization: "Bearer " + token} : {}),
        ...(opts.headers || {})
      },
    });
    if (!response.ok) throw Error("GitHub request failed (" + response.status + ")");
    return response.json();
  }
  function decode64(s) {
    const raw = atob(s.replace(/\s/g, ""));
    return JSON.parse(new TextDecoder().decode(Uint8Array.from(raw, c => c.charCodeAt(0))));
  }
  function encode64(data) {
    const raw = new TextEncoder().encode(JSON.stringify(data, null, 2) + "\n");
    let str = ""; for (let i = 0; i < raw.length; i += 8192)
      str += String.fromCharCode(...raw.subarray(i, i + 8192));
    return btoa(str);
  }
  async function loadLedger() {
    const file = await request(API + "data/editorial-decisions.json?ref=main");
    const ledger = decode64(file.content);
    if (ledger.version !== "sxf-editorial-decisions-v1" || !Array.isArray(ledger.decisions))
      throw Error("Approval ledger format mismatch");
    decisions = ledger.decisions;
    rejectedFingerprints = ledger.rejected_fingerprints || [];
    ledgerSha = file.sha;
  }
  async function reload() {
    const response = await fetch(RAW + "?v=" + Date.now(), {cache:"no-store"});
    if (!response.ok) throw Error("Cannot load editorial inbox");
    const payload = await response.json();
    if (payload.version !== "sxf-editorial-inbox-v1" || !Array.isArray(payload.items))
      throw Error("Editorial inbox format mismatch");
    inbox = payload.items;
    if (token) await loadLedger();
    render();
  }
  function decisionFor(row) {
    const found = decisions.find(d => d.url === row.url &&
      d.title === row.title && d.source === row.source);
    return found ? found.decision : "pending";
  }
  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  }
  function render() {
    const output = $("stories"); output.replaceChildren();
    const filtered = inbox.filter(row => $("filter").value === "all" ||
      decisionFor(row) === $("filter").value);
    $("counts").textContent = filtered.length + " of " + inbox.length + " candidate stories";
    if (!filtered.length) {output.append(el("p", "No stories in this view."));return;}
    for (const row of filtered) {
      const card = el("article", undefined, "story");
      const title = el("h2", row.title); title.style.fontSize = "1.1rem";
      const link = el("a", "Open verified source");
      if (/^https:\/\/[^\s]+$/.test(row.url)) {
        link.href = row.url; link.target = "_blank"; link.rel = "noopener noreferrer";
      } else {link.removeAttribute("href");}
      card.append(title);
      const meta = el("div", undefined, "meta");
      for (const val of [row.source, row.published?.slice(0, 10) || "Undated",
        "Filter: " + (row.editorial_status || "unknown"),
        "SEO: " + (row.seo_eligible ? "pass" : "not eligible"),
        "Decision: " + decisionFor(row)]) meta.append(el("span", val, "tag"));
      card.append(meta, el("p", row.summary || "No source summary available.", "summary"), link);
      const rowBtns = el("div", undefined, "row"); rowBtns.style.marginTop = "12px";
      for (const [status, label, color] of [
        ["approved","Accept","approve"],["hold","Hold","hold"],["rejected","Reject","reject"]]) {
        const btn = el("button", label, color);
        btn.disabled = busy || !token || !user || decisionFor(row) === status;
        btn.onclick = () => commit(row, status);
        rowBtns.append(btn);
      }
      card.append(rowBtns);output.append(card);
    }
  }
  async function commit(row, status) {
    if (busy || !token || !user) return;
    if (status === "approved" && !row.seo_eligible) {
      message("Approval blocked: this article failed SEO evidence checks. Request a better source summary first.", true);
      return;
    }
    if (!confirm("Record " + status + " for " + row.title + "?")) return;
    busy = true;render();message("Saving decision via authenticated GitHub API...");
    try {
      await loadLedger(); // CAS: always fetch current commit state before PUT
      const previous = decisions.findIndex(d => d.url === row.url);
      if (status === "rejected") {
        const bytes = new TextEncoder().encode(row.url);
        const digest = await crypto.subtle.digest("SHA-256", bytes);
        const fingerprint = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
        if (!rejectedFingerprints.includes(fingerprint)) rejectedFingerprints.push(fingerprint);
        if (previous >= 0) decisions.splice(previous, 1);
      }
      const entry = {url: row.url, title: row.title, source: row.source,
        decision: status, reviewed_by: "github:" + user,
        reviewed_at: new Date().toISOString()};
      if (status !== "rejected") {
        if (previous < 0) decisions.push(entry);
        else decisions[previous] = entry;
      }
      const payload = {version:"sxf-editorial-decisions-v1",decisions,rejected_fingerprints:rejectedFingerprints};
      await request(API + "data/editorial-decisions.json", {
        method: "PUT", headers: {"Content-Type":"application/json"},
        body: JSON.stringify({message:"editorial: " + status + " " + row.title.slice(0, 65),
          content:encode64(payload), sha:ledgerSha, branch:"main"})
      });
      message("Decision recorded in GitHub. The next successful feed build will apply it.");
      await reload();
    } catch (error) {message(error.message + " — no publication was confirmed.", true);}
    finally {busy = false;render();}
  }
  $("connect").onclick = async () => {
    const candidate = $("token").value.trim();
    $("token").value = "";
    if (!candidate) return message("Enter an authorized GitHub fine-grained token.", true);
    token = candidate;
    try {
      const me = await request("https://api.github.com/user");
      user = me.login;
      await loadLedger();
      $("disconnect").disabled = false;
      message("Connected as " + user + ". Your credentials remain only in this page session.");
      await reload();
    } catch (error) {token = "";user = "";$("disconnect").disabled = true;message(error.message, true);}
  };
  $("disconnect").onclick = () => {token = "";user = "";decisions = [];rejectedFingerprints = [];ledgerSha = "";
    $("disconnect").disabled = true;message("Disconnected. Close this tab to clear the session.");render();};
  $("reload").onclick = () => reload().catch(e => message(e.message,true));
  $("filter").onchange = render;
  reload().catch(e => message(e.message,true));
})();