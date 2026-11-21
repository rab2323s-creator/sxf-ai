(() => {
  'use strict';
  const select = document.getElementById('memoryCaseFilter');
  const count = document.getElementById('memoryVisibleCount');
  const table = document.getElementById('memoryCasesTable');
  if (!select || !count || !table) return;
  const rows = [...table.querySelectorAll('tbody tr')];
  const update = () => {
    const filter = select.value;
    let visible = 0;
    for (const row of rows) {
      const category = row.cells[1]?.textContent.toLowerCase().trim();
      row.hidden = filter !== 'all' && category !== filter;
      if (!row.hidden) visible++;
    }
    count.textContent = `${visible} of ${rows.length} cases shown`;
  };
  select.addEventListener('change',update);
  update();
})();