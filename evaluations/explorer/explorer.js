(() => {
  const root = document.querySelector("[data-evaluation-explorer]");
  if (!root) return;

  const benchmarkSelect = document.getElementById("evalBenchmark");
  const categorySelect = document.getElementById("evalCategory");
  const providerSelect = document.getElementById("evalProvider");
  const evidenceSelect = document.getElementById("evalEvidence");
  const groupSelect = document.getElementById("evalGroup");
  const body = document.getElementById("evaluationExplorerBody");
  const status = document.getElementById("evaluationExplorerStatus");
  const chart = document.getElementById("evaluationExplorerChart");
  const table = document.getElementById("evaluationExplorerTable");
  const summary = document.getElementById("evaluationParetoSummary");
  const tabs = [...document.querySelectorAll("[data-eval-view]")];

  let view = "table";
  let evaluations = null;
  let catalog = null;
  let benchmarkById = new Map();
  let modelById = new Map();

  const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  })[ch]);

  const money = value => Number.isFinite(value)
    ? "$" + value.toLocaleString(undefined,{maximumFractionDigits:value >= 1 ? 4 : 6})
    : "—";

  const scoreLabel = (benchmark, value) => {
    if (benchmark.unit === "percent") return Number(value).toFixed(1) + "%";
    if (benchmark.unit === "Elo") return Math.round(Number(value)).toLocaleString() + " Elo";
    return String(Number(value).toFixed(2)).replace(/\.00$/,"").replace(/(\.\d)0$/,"$1");
  };

  const standardPeriod = model => {
    if (model?.pricing_status !== "official-paid" || model?.calculator_eligible !== true) return null;
    const date = catalog.source_verified;
    return (model?.pricing?.standard || []).find(period => date >= period.start && (!period.end || date <= period.end)) || null;
  };

  const workloadCost = model => {
    const base = standardPeriod(model);
    if (!base) return null;
    const input = 100000, output = 10000, cached = 0;
    let rates = {...base};
    const rule = model?.pricing?.long_context;
    if (rule && input + cached > Number(rule.threshold_input_tokens)) {
      for (const field of ["input","cached_input","cache_write","output"]) {
        if (typeof rates[field] === "number" && typeof rule.multipliers?.[field] === "number") {
          rates[field] *= rule.multipliers[field];
        }
      }
    }
    return input / 1_000_000 * rates.input +
      cached / 1_000_000 * rates.cached_input +
      output / 1_000_000 * rates.output;
  };

  const selectedBenchmark = () => benchmarkById.get(benchmarkSelect.value);

  const availableRows = () => {
    const benchmark = selectedBenchmark();
    if (!benchmark) return [];
    let rows = (evaluations.observations || []).filter(row => row.benchmark_id === benchmark.benchmark_id);

    const evidence = evidenceSelect.value;
    if (evidence !== "all") rows = rows.filter(row => row.evidence_type === evidence);

    const category = categorySelect.value;
    if (category !== "all" && benchmark.category !== category) return [];

    const provider = providerSelect.value;
    if (provider !== "all") rows = rows.filter(row => modelById.get(row.model_id)?.provider === provider);

    const group = groupSelect.value;
    if (group !== "auto") rows = rows.filter(row => row.comparable_group === group);

    return rows;
  };

  const updateGroups = () => {
    const benchmark = selectedBenchmark();
    if (!benchmark) return;
    let rows = (evaluations.observations || []).filter(row => row.benchmark_id === benchmark.benchmark_id);
    const evidence = evidenceSelect.value;
    if (evidence !== "all") rows = rows.filter(row => row.evidence_type === evidence);

    const groups = [...new Set(rows.map(row => row.comparable_group).filter(Boolean))].sort();
    const current = groupSelect.value;
    groupSelect.innerHTML = '<option value="auto">Auto</option>' + groups.map(group =>
      '<option value="' + esc(group) + '">' + esc(group) + '</option>'
    ).join("");
    if (groups.includes(current)) groupSelect.value = current;
    else if (groups.length === 1) groupSelect.value = groups[0];
    else groupSelect.value = "auto";
  };

  const comparableRows = () => {
    const rows = availableRows();
    if (!rows.length) return {rows, warning:"No observations match these filters."};
    const groups = [...new Set(rows.map(row => row.comparable_group))];
    if (groupSelect.value === "auto" && groups.length > 1) {
      return {
        rows:[],
        warning:"Multiple comparable groups are present. Choose one group before ranking or plotting scores."
      };
    }
    return {rows, warning:""};
  };

  const pareto = (points, xBetter, yBetter) => points.filter(a =>
    !points.some(b => {
      if (a === b) return false;
      const xDominates = xBetter === "lower" ? b.x <= a.x : b.x >= a.x;
      const yDominates = yBetter === "lower" ? b.y <= a.y : b.y >= a.y;
      const strict = (xBetter === "lower" ? b.x < a.x : b.x > a.x) ||
        (yBetter === "lower" ? b.y < a.y : b.y > a.y);
      return xDominates && yDominates && strict;
    })
  );

  const renderTable = (benchmark, rows) => {
    const reverse = benchmark.direction === "higher-is-better";
    rows = [...rows].sort((a,b) => reverse ? Number(b.score)-Number(a.score) : Number(a.score)-Number(b.score));
    body.innerHTML = rows.map(row => {
      const model = modelById.get(row.model_id);
      const cost = workloadCost(model);
      return '<tr>' +
        '<th scope="row"><a href="' + esc(model.sxf_url) + '">' + esc(model.model) + '</a><small>' + esc(model.provider) + '</small></th>' +
        '<td>' + esc(scoreLabel(benchmark,row.score)) + '</td>' +
        '<td>' + Number(model.context_window).toLocaleString() + '<small>tokens</small></td>' +
        '<td>' + (cost == null ? 'Not directly comparable' : money(cost)) + '<small>100K input + 10K output</small></td>' +
        '<td>' + esc(row.model_configuration?.reasoning_effort || 'not published') + '</td>' +
        '<td><a href="' + esc(row.source_url) + '" target="_blank" rel="noopener noreferrer">Evidence ↗</a></td>' +
      '</tr>';
    }).join("");
  };

  const renderChart = (benchmark, rows, mode) => {
    const points = [];
    for (const row of rows) {
      const model = modelById.get(row.model_id);
      const x = mode === "cost" ? workloadCost(model) : Number(model.context_window);
      if (!Number.isFinite(x)) continue;
      points.push({row,model,x,y:Number(row.score)});
    }

    if (!points.length) {
      chart.innerHTML = '<div class="evaluation-chart-empty">No plottable observations for this view.</div>';
      summary.innerHTML = mode === "cost"
        ? '<p>Cost view requires calculator-eligible provider Standard pricing.</p>'
        : '<p>No models with compatible context data are available for this group.</p>';
      return;
    }

    const xBetter = mode === "cost" ? "lower" : "higher";
    const yBetter = benchmark.direction === "higher-is-better" ? "higher" : "lower";
    const frontier = pareto(points,xBetter,yBetter);
    const frontierIds = new Set(frontier.map(point => point.row.observation_id));

    const minX = Math.min(...points.map(p=>p.x)), maxX = Math.max(...points.map(p=>p.x));
    const minY = Math.min(...points.map(p=>p.y)), maxY = Math.max(...points.map(p=>p.y));
    const norm = (v,min,max) => max === min ? 50 : ((v-min)/(max-min))*86+7;

    chart.innerHTML = '<div class="evaluation-axis-label y">' + esc(benchmark.name) + '</div>' +
      '<div class="evaluation-axis-label x">' + (mode === "cost" ? 'Direct workload cost →' : 'Context window →') + '</div>' +
      points.map(point => {
        const left = norm(point.x,minX,maxX);
        const top = 93 - norm(point.y,minY,maxY);
        const isFrontier = frontierIds.has(point.row.observation_id);
        const xLabel = mode === "cost" ? money(point.x) : Math.round(point.x).toLocaleString()+" ctx";
        return '<button class="evaluation-point' + (isFrontier ? ' is-pareto' : '') + '" style="left:' + left + '%;top:' + top + '%" type="button" title="' +
          esc(point.model.model + ' · ' + scoreLabel(benchmark,point.y) + ' · ' + xLabel) + '">' +
          '<span>' + esc(point.model.model) + '</span><small>' + esc(scoreLabel(benchmark,point.y)) + '</small>' +
        '</button>';
      }).join("");

    summary.innerHTML = '<strong>Pareto-efficient:</strong> ' +
      frontier.map(point => '<a href="' + esc(point.model.sxf_url) + '">' + esc(point.model.model) + '</a>').join(' · ') +
      '<small>' + (mode === "cost"
        ? 'Efficient here means no visible model has both lower direct token cost and a better benchmark score.'
        : 'Efficient here means no visible model has both a larger context window and a better benchmark score.') +
      '</small>';
  };

  const render = () => {
    if (!evaluations || !catalog) return;
    const benchmark = selectedBenchmark();
    const result = comparableRows();

    const review = benchmark?.status === "under-review";
    status.innerHTML = '<div><span>' + esc(benchmark?.evidence_type || '') + '</span><strong>' + esc(benchmark?.name || '') +
      (benchmark?.version ? ' v' + esc(benchmark.version) : '') + '</strong><small>' +
      esc(review ? 'UNDER REVIEW · ' + result.warning : result.warning || benchmark?.category?.replace(/-/g,' ') || '') +
      '</small></div>' +
      (benchmark ? '<a href="' + esc(benchmark.methodology_url) + '" target="_blank" rel="noopener noreferrer">Methodology ↗</a>' : '');

    table.hidden = view !== "table";
    chart.hidden = view === "table";
    if (!result.rows.length) {
      if (view === "table") body.innerHTML = '<tr><td colspan="6">Choose one comparable group to rank results.</td></tr>';
      else chart.innerHTML = '<div class="evaluation-chart-empty">Choose one comparable group to plot results.</div>';
      summary.innerHTML = '';
      return;
    }

    if (view === "table") {
      renderTable(benchmark,result.rows);
      summary.innerHTML = '';
    } else {
      renderChart(benchmark,result.rows,view);
    }
  };

  const setView = next => {
    view = next;
    tabs.forEach(tab => tab.classList.toggle("is-active",tab.dataset.evalView === view));
    render();
  };
  tabs.forEach(tab => tab.addEventListener("click",()=>setView(tab.dataset.evalView)));

  Promise.all([
    fetch(root.dataset.evaluations,{cache:"no-cache"}).then(r=>{if(!r.ok)throw new Error("evaluations");return r.json();}),
    fetch(root.dataset.catalog,{cache:"no-cache"}).then(r=>{if(!r.ok)throw new Error("catalog");return r.json();})
  ]).then(([evalData,catalogData])=>{
    evaluations=evalData; catalog=catalogData;
    benchmarkById=new Map((evaluations.benchmarks||[]).map(b=>[b.benchmark_id,b]));
    modelById=new Map((catalog.models||[]).map(m=>[m.model_id,m]));
    updateGroups();
    render();
  }).catch(()=>{
    status.innerHTML='<div><strong>Explorer data could not be loaded.</strong></div>';
  });

  benchmarkSelect.addEventListener("change",()=>{
    const benchmark=benchmarkById.get(benchmarkSelect.value);
    if (benchmark) {
      categorySelect.value=benchmark.category;
      if (evidenceSelect.value !== "all" && evidenceSelect.value !== benchmark.evidence_type) {
        evidenceSelect.value=benchmark.evidence_type;
      }
    }
    updateGroups(); render();
  });
  evidenceSelect.addEventListener("change",()=>{updateGroups();render();});
  groupSelect.addEventListener("change",render);
  categorySelect.addEventListener("change",render);
  providerSelect.addEventListener("change",render);
})();
