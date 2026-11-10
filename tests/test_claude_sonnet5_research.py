#!/usr/bin/env python3
"""Reproducible original Claude Sonnet 5 research, SEO, provenance, and source contracts."""
import csv
import json
import re
import sys
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from claude_sonnet5_model_page import (
 URL,DATASET,TITLE,DESCRIPTION,FAQ,DATA,TEMPLATE,SOURCES,rate_cost,scenarios,enrich_claude_sonnet5_page)
catalog=json.loads((ROOT/"data/model-pricing.json").read_text(encoding="utf-8"))
models={m["model_id"]:m for m in catalog["models"]}
m=models["claude-sonnet-5"]
new=models["claude-sonnet-5-5"]
assert m["provenance"]["verified_at"]=="2026-11-10"
assert m["provenance"]["verification_method"]=="manual primary-source verification"
assert new["provenance"]["verified_at"]>="2026-11-10"
ra=m["pricing"]["standard"][-1]
assert abs(rate_cost(ra,100000,2000,4000,"uncached")-.244)<1e-9
assert all(abs(v-ref)<1e-9 for v,ref in zip(scenarios(ra,100000,2000,4000,10),[2.44,.87,1.02]))
for args in ((1000000,1,0,"uncached"),(-1,100,0,"five"),(1000,-1,0,"read"),(100,2000,128001,"hour")):
 try:rate_cost(ra,*args)
 except ValueError:pass
 else:raise AssertionError("Invalid token arguments accepted")
with DATA.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
assert len(rows)==20 and len({row["scenario_id"] for row in rows})==20
page=(ROOT/"models/claude-sonnet-5/index.html").read_text(encoding="utf-8")
if 'id="sxf-sonnet5-research"' not in page:
 page=enrich_claude_sonnet5_page(page,models)
assert page.count('id="sxf-sonnet5-research"')==1
assert page.count("<h1>")==1
assert "<h1>Claude Sonnet 5<br><span>API Pricing, Specs &amp; Benchmarks</span></h1>" in page
assert 'class="model-reference model-reference-deep shell"' not in page
assert "AA-Briefcase 1.1" in page
assert "Displayed USD values are rounded for readability" in page
assert 'href="'+URL+'"' in page
assert "cs5-page" in page
assert "<title>"+escape(TITLE)+"</title>" in page
assert escape(DESCRIPTION,quote=True) in page
assert "research.css?v=20261110-b" in page
assert "research.js?v=20261110-b" in page
assert "HISTORICAL BASELINE" in page
assert '<strong>2026-11-10</strong><span>last verified</span>' in page
assert "data-model-history" in page and "data-model-evaluations" in page
assert "{{" not in page
for heading in ("cs5-overview","cs5-pricing","cs5-lab","cs5-calculator","cs5-comparison","cs5-benchmarks","cs5-api","cs5-faq","cs5-method"):
 assert 'id="'+heading+'"' in page
for question,answer in FAQ:
 assert escape(question) in page and escape(answer) in page,question
s=re.search(r'<script type="application/ld\+json">(.+?)</script>',page,re.S)
assert s
nodes=json.loads(s.group(1))["@graph"]
assert {"TechArticle","BreadcrumbList","FAQPage","Dataset"} <= {n["@type"] for n in nodes}
a=next(n for n in nodes if n["@type"]=="TechArticle")
assert a["mainEntityOfPage"]==URL and a["dateModified"]=="2026-11-10"
assert a["citation"]==SOURCES
faq=next(n for n in nodes if n["@type"]=="FAQPage")
assert len(faq["mainEntity"])==len(FAQ)
dataset=next(n for n in nodes if n["@type"]=="Dataset")
assert dataset["distribution"]["contentUrl"]==DATASET
assert (ROOT/"models/claude-sonnet-5/research.css").is_file()
assert (ROOT/"models/claude-sonnet-5/research.js").is_file()
print("PASS Sonnet 5: canonical metadata, verified source date, historical baseline, FAQ Dataset TechArticle and 20-row research")
