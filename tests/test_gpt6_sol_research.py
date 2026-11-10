#!/usr/bin/env python3
"""SXF GPT-6 Sol editorial, SEO, data integrity and pricing research regression."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from gpt6_sol_model_page import (enrich_gpt6_sol_page, cost, rate, SCENARIOS, FAQ, CANONICAL,
                                CSV_PATH, DATASET, TITLE, DESCRIPTION)

catalog=json.loads((ROOT/"data/model-pricing.json").read_text(encoding="utf-8"))
models={x["model_id"]:x for x in catalog["models"]}
old,new=models["gpt-6-sol"],models["gpt-6.1-sol"]
day=max("2026-11-10",old["provenance"]["verified_at"],new["provenance"]["verified_at"])
assert abs(cost(old,day,new=272000,output=4000)-0.584)<1e-8
assert abs(cost(old,day,new=272001,output=4000)-1.148004)<1e-8
assert abs(cost(old,day,new=12000,cached=200000,output=4000)-.104)<1e-8
assert abs(cost(new,day,new=12000,cached=200000,output=4000)-.084)<1e-8
assert abs(cost(old,day,new=12000,write=200000,output=4000)-.564)<1e-8
for kwargs in ({"new":1050001},{"new":-1},{"output":128001},{"cached":1050001}):
    try:
        cost(old,day,**kwargs)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid token input accepted: "+str(kwargs))

with CSV_PATH.open(newline="",encoding="utf-8") as stream:
    rows=list(csv.DictReader(stream))
assert len(rows)==9 and len(set(row["scenario_id"] for row in rows))==9
assert len(SCENARIOS)==9

source=(ROOT/"models/gpt-6-sol/index.html").read_text(encoding="utf-8")
page=source if 'id="sxf-sol-dossier"' in source else enrich_gpt6_sol_page(source,models)
assert page.count('id="sxf-sol-dossier"')==1
assert page.count("<h1>")==1
assert '<link rel="canonical" href="'+CANONICAL+'"' in page
assert '<meta name="robots" content="index,follow' in page
assert "<title>"+TITLE.replace("&","&amp;")+"</title>" in page
assert DESCRIPTION.split("API pricing")[0] in page
assert page.count("sol-research-page")>=1
assert "/models/gpt-6-sol/research.css" in page
assert "/models/gpt-6-sol/research.js" in page
assert "data-model-history" in page and "data-what-changed" in page
assert "data-model-comparisons" in page and "data-model-evaluations" in page
assert page.count('id="sol-original-lab"')==1
assert page.count('id="sol-pricing"')==1
assert page.count('id="sol-vs-new"')==1
assert page.count('id="sol-faq"')==1
assert page.count('id="sol-calculator"')==1
assert "{{" not in page
assert page.count('href="/models/gpt-6-1-sol/"')>=2
assert 'href="/data/research/gpt6-sol-cache-migration-2026-11.csv"' in page
assert "not a paid model-inference run" in page
assert "not independent SXF" in page
for question,answer in FAQ:
    assert question in page and answer in page
s=re.search(r'<script type="application/ld\+json">(.+?)</script>',page,re.S)
assert s
graph=json.loads(s.group(1))["@graph"]
assert {"TechArticle","BreadcrumbList","FAQPage","Dataset"} <= {item["@type"] for item in graph}
faq=next(item for item in graph if item["@type"]=="FAQPage")
assert len(faq["mainEntity"]) == len(FAQ)
assert all(x["acceptedAnswer"]["text"] in page for x in faq["mainEntity"])
dataset=next(item for item in graph if item["@type"]=="Dataset")
assert dataset["distribution"]["contentUrl"]==DATASET
article=next(item for item in graph if item["@type"]=="TechArticle")
assert article["mainEntityOfPage"]==CANONICAL
assert article["dateModified"] >= "2026-11-10"
assert all(url in article["citation"] for url in [DATASET,"https://developers.openai.com/api/docs/models/gpt-6-sol"])
assert (ROOT/"models/gpt-6-sol/research.css").is_file()
assert (ROOT/"models/gpt-6-sol/research.js").is_file()
print("GPT-6 Sol: source-backed metadata, FAQ, dataset schema, study reproduction and generated page PASS")
