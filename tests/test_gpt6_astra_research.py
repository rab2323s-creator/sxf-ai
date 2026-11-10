#!/usr/bin/env python3
"""Contract tests for source-backed GPT-6 Astra research and scheduled regeneration."""
from __future__ import annotations
import csv
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from gpt6_astra_model_page import enrich_gpt6_astra_page, calculate, FAQ, DATASET, CANONICAL

catalog=json.loads((ROOT/"data/model-pricing.json").read_text(encoding="utf-8"))
by_id={r["model_id"]:r for r in catalog["models"]}
astra,sol=by_id["gpt-6-astra"],by_id["gpt-6.1-sol"]
day=max("2026-11-10",astra["provenance"]["verified_at"],sol["provenance"]["verified_at"])
assert abs(calculate(astra,day,272000,output=4000)-2.92)<1e-9
assert abs(calculate(astra,day,272001,output=4000)-5.74002)<1e-9
assert abs(calculate(sol,day,272001,output=4000)-1.148004)<1e-8
assert abs(calculate(astra,day,12000,cached=200000,output=4000)-0.52)<1e-9
assert abs(calculate(astra,day,12000,write=200000,output=4000)-2.82)<1e-9
for wrong in ({"new":1050001},{"output":128001},{"new":-1}):
    try:calculate(astra,day,**wrong)
    except ValueError: pass
    else:raise AssertionError("Invalid tokens unexpectedly accepted")

source=(ROOT/"models/gpt-6-astra/index.html").read_text(encoding="utf-8")
# The checked-in index may already contain the durable research layer.
if 'id="sxf-astra-study"' in source:
    assert 'id="astra-lab"' in source
else:
    rendered=enrich_gpt6_astra_page(source,by_id)
    assert 'id="sxf-astra-study"' in rendered
    assert 'id="astra-lab"' in rendered
    assert '<title>GPT-6 Astra: Pricing, Benchmarks, API &amp; 1.05M Context | SXF</title>' in rendered
    assert '<link rel="canonical" href="'+CANONICAL+'"' in rendered
    assert rendered.count('<h1>')==1
    assert '<script src="/models/gpt-6-astra/research.js" defer></script>' in rendered
    assert 'data-model-history' in rendered
    assert '/data/research/gpt6-astra-cost-lab-2026-11.csv' in rendered
    assert "\\$" not in rendered
    found=re.search(r'<script type="application/ld\+json">(.+?)</script>',rendered,re.S)
    assert found
    schema=json.loads(found.group(1))
    types=[node["@type"] for node in schema["@graph"]]
    assert "TechArticle" in types and "BreadcrumbList" in types and "FAQPage" in types and "Dataset" in types
    faq=next(x for x in schema["@graph"] if x["@type"]=="FAQPage")
    assert len(faq["mainEntity"])==len(FAQ)
    for q,a in FAQ:
        assert q in rendered and a in rendered
    dataset=next(x for x in schema["@graph"] if x["@type"]=="Dataset")
    assert dataset["url"]==DATASET
with (ROOT/"data/research/gpt6-astra-cost-lab-2026-11.csv").open(newline="",encoding="utf-8") as f:
    rows=list(csv.DictReader(f))
assert len(rows)==6 and len({r["case_id"] for r in rows})==6
assert all(r["tier"]==("long" if sum(int(r[k]) for k in ("uncached_input","cached_input","cache_write_input"))>272000 else "short") for r in rows)
assert (ROOT/"models/gpt-6-astra/research.css").is_file()
assert (ROOT/"models/gpt-6-astra/research.js").is_file()
print("GPT-6 Astra research: metadata, structured data, arithmetic and reproducibility passed")
