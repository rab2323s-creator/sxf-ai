
"use strict";
(() => {
  // SXF original local-only privacy request tracker; nothing is sent or stored.
  const form = document.getElementById("privacyTrackerForm");
  if (!form) return;
  const rows = [];
  const tbody = document.getElementById("prTrackerBody");
  const summary = document.getElementById("prTrackerSummary");
  const today = () => new Date().toISOString().slice(0, 10);
  const plusDays = (date, days) => {
    const d = new Date(date + "T12:00:00");
    d.setDate(d.getDate() + days);
    return [d.getFullYear(), String(d.getMonth() + 1).padStart(2,"0"), String(d.getDate()).padStart(2,"0")].join("-");
  };
  const cell = (row, value) => {
    const td = document.createElement("td");
    td.textContent = String(value);
    row.appendChild(td);
    return td;
  };
  const render = () => {
    tbody.replaceChildren();
    summary.textContent = rows.length ? rows.length + " record" + (rows.length === 1 ? "" : "s") + " in this page session; not uploaded or saved by SXF." : "No records added. Use an alias, not personal information.";
    if (!rows.length) {
      const tr = document.createElement("tr");
      cell(tr, "Your records appear here. Nothing is transmitted to SXF.").colSpan = 6;
      tbody.appendChild(tr);
      return;
    }
    rows.forEach((item, index) => {
      const tr = document.createElement("tr");
      [item.alias, item.layer, item.status, item.added, item.check].forEach(value => cell(tr,value));
      const td = document.createElement("td");
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "Remove";
      remove.setAttribute("aria-label", "Remove tracker row " + (index + 1));
      remove.addEventListener("click", () => { rows.splice(index, 1); render(); });
      td.appendChild(remove);tr.appendChild(td);tbody.appendChild(tr);
    });
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const alias = document.getElementById("prAlias").value.trim().slice(0,90);
    if (!alias) return;
    const now = today();
    rows.push({alias, layer: document.getElementById("prLayer").value, status: document.getElementById("prStatus").value, added: now, check: plusDays(now, 7)});
    document.getElementById("prAlias").value = "";
    render();
  });
  const csvEscape = (value) => '"' + String(value).replace(/"/g, '""') + '"';
  document.getElementById("prExport").addEventListener("click", () => {
    const matrix = [["Alias","Layer","Status","Added","Next check (SXF reminder only)"], ...rows.map(r => [r.alias, r.layer, r.status, r.added, r.check])];
    // Prefix untrusted spreadsheet-formula characters to prevent formula execution on open.
    const protect = v => /^[=+\-@]/.test(String(v)) ? "'" + v : v;
    const csv = "\uFEFF" + matrix.map(line => line.map(v=>csvEscape(protect(v))).join(",")).join("\r\n");
    const objectUrl = URL.createObjectURL(new Blob([csv], {type:"text/csv;charset=utf-8"}));
    const a = document.createElement("a"); a.href = objectUrl; a.download = "sxf-privacy-removal-tracker.csv"; document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(objectUrl),1000);
  });
  document.getElementById("prClear").addEventListener("click", () => {rows.length=0;render();});
  const copy = document.getElementById("copyEmailTemplate");
  if(copy)copy.addEventListener("click", () => {
    const plain = document.getElementById("removalEmailTemplate").textContent;
    if(navigator.clipboard?.writeText) navigator.clipboard.writeText(plain).then(()=>{copy.textContent="Copied";}).catch(()=>{copy.textContent="Select and copy the template";});
    else copy.textContent="Select and copy the template";
  });
  render();
})();
