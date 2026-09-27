(() => {
  const root = document.querySelector("[data-model-explorer]");
  if (!root) return;
  const rows = [...root.querySelectorAll("[data-model-row]")];
  const body = document.getElementById("modelExplorerBody");
  const search = document.getElementById("modelExplorerSearch");
  const sort = document.getElementById("modelExplorerSort");
  const count = document.getElementById("modelExplorerCount");
  const empty = document.getElementById("modelExplorerEmpty");
  const filters = [...root.querySelectorAll("[data-model-provider]")];
  let provider = "all";

  const numeric = (row, key) => Number(row.dataset[key] || 0);
  const apply = () => {
    const query = (search?.value || "").trim().toLowerCase();
    const mode = sort?.value || "default";
    const ordered = [...rows].sort((a, b) => {
      if (mode === "input-asc") return numeric(a, "input") - numeric(b, "input");
      if (mode === "output-asc") return numeric(a, "output") - numeric(b, "output");
      if (mode === "context-desc") return numeric(b, "context") - numeric(a, "context");
      return numeric(a, "order") - numeric(b, "order");
    });
    ordered.forEach(row => body?.appendChild(row));

    let visible = 0;
    ordered.forEach(row => {
      const providerMatch = provider === "all" || row.dataset.provider === provider;
      const queryMatch = !query || (row.dataset.search || "").includes(query);
      const show = providerMatch && queryMatch;
      row.hidden = !show;
      if (show) visible += 1;
    });
    if (count) count.textContent = visible + (visible === 1 ? " model shown" : " models shown");
    if (empty) empty.hidden = visible !== 0;
  };

  filters.forEach(button => button.addEventListener("click", () => {
    filters.forEach(item => item.classList.remove("is-active"));
    button.classList.add("is-active");
    provider = button.dataset.modelProvider || "all";
    apply();
  }));
  search?.addEventListener("input", apply);
  sort?.addEventListener("change", apply);
  apply();
})();
