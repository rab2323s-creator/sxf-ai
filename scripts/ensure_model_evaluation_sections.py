#!/usr/bin/env python3
"""Restore source-linked model benchmark cards after generated site refreshes.

Some established model reference pages are family pages (multiple model IDs),
while the discovery-page generator does not automatically add evidence sections
to every newly evaluated model page. Build actual cards from the verified
observation dataset; never create empty placeholders or inferred scores.
"""
from __future__ import annotations

import html
import json
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "model-pricing.json"
EVALS = ROOT / "data" / "model-evaluations.json"


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def score_label(score: float | int, unit: str | None) -> str:
    numeric = f"{score:g}" if isinstance(score, float) else f"{score:,}"
    if unit == "percent":
        return numeric + "%"
    if unit == "Elo":
        return numeric + " Elo"
    if unit in ("points", "point"):
        return numeric + " points"
    return numeric + (" " + str(unit) if unit else "")


def section(model: dict, rows: list[dict], benchmarks: dict[str, dict]) -> str:
    model_id = model["model_id"]
    cards = []
    for obs in rows:
        bench = benchmarks[obs["benchmark_id"]]
        source = obs["source_url"]
        parsed = urlparse(source)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"{model_id}: invalid independent evaluation source")
        review = bench.get("status") == "under-review"
        reason = obs.get("model_configuration", {}).get("reasoning_effort") or "undisclosed"
        status = " · under review" if review else ""
        warning = '<p class="reference-note">Evaluator labels this benchmark under review.</p>' if review else ""
        cards.append(
            '<article>'
            '<div><span>independent</span><small>' + escape(obs["evaluator"]) + status + '</small></div>'
            '<h3>' + escape(bench["name"]) + (' ' + escape(bench["version"]) if bench.get("version") else '') + '</h3>'
            '<strong>' + escape(score_label(obs["score"], bench.get("unit"))) + '</strong>'
            '<p>' + escape(bench["category"].replace("-", " ")) + ' · reasoning ' + escape(reason) + '</p>'
            + warning
            + '<a href="' + escape(source) + '" target="_blank" rel="noopener noreferrer">Independent source ↗</a>'
            '</article>'
        )
    return (
        '\n    <section class="evaluation-model-bridge shell" data-model-evaluations="' + escape(model_id) + '">'
        '<div class="intel-section-head"><div><p class="eyebrow">EVALUATION EVIDENCE</p><h2>'
        + escape(model["model"]) + ' benchmark observations.</h2></div>'
        '<a href="/evaluations/">Evaluation methodology ↗</a></div>'
        '<div class="evaluation-card-grid">' + ''.join(cards) + '</div>'
        '<p class="reference-note">Source-verified observations · scores depend on evaluation settings. '
        'Not a universal model ranking.</p>'
        '</section>'
    )


def main() -> None:
    check_only = "--check" in sys.argv
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    evaluations = json.loads(EVALS.read_text(encoding="utf-8"))
    benchmarks = {b["benchmark_id"]: b for b in evaluations["benchmarks"]}
    models = {m["model_id"]: m for m in catalog["models"]}
    observations = defaultdict(list)
    for row in evaluations["observations"]:
        if row["evidence_type"] == "independent":
            observations[row["model_id"]].append(row)

    pages = defaultdict(list)
    for model_id, rows in observations.items():
        model = models[model_id]
        url = model.get("sxf_url", "")
        if not url.startswith("/models/") or url == "/models/pricing/":
            continue
        page = ROOT / url.lstrip("/") / "index.html"
        if not page.exists():
            raise ValueError(f"{model_id}: model page missing ({page})")
        pages[page].append((model, rows))

    modified = 0
    for page, entries in pages.items():
        body = page.read_text(encoding="utf-8")
        additions = []
        for model, rows in entries:
            marker = 'data-model-evaluations="' + escape(model["model_id"]) + '"'
            if body.count(marker) == 1:
                continue
            if marker in body:
                raise ValueError(f"{model['model_id']}: duplicate evidence marker")
            if check_only:
                raise ValueError(f"{model['model_id']}: model page missing independent evidence cards")
            additions.append(section(model, rows, benchmarks))
        if additions:
            if body.count("</main>") != 1:
                raise ValueError(f"{page}: missing or duplicated main close tag")
            body = body.replace("</main>", ''.join(additions) + "</main>", 1)
            page.write_text(body, encoding="utf-8")
            modified += 1

    print(f"PASS: {len(observations)} independently covered models; "
          f"{len(pages)} reference pages checked; {modified} pages enriched")


if __name__ == "__main__":
    main()
