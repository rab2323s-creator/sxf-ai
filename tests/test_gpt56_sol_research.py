#!/usr/bin/env python3
"""GPT-5.6 Sol source-driven SEO / model-study contract."""
from __future__ import annotations
import json,re,sys,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from gpt56_sol_model_page import (enrich_gpt56_sol_page, cost,scenarios,FAQ,DATASET,URL,TITLE,CSV_PATH,CONTENT)
models={m["model_id"]:m for m in json.loads((ROOT/"data/model-pricing.json").read_text(encoding="utf-8"))["models"]}
model=models["gpt-5.6-sol"]
assert abs(cost(model,"2026-11-10",272000,0,4000,"no")-1.168)<1e-9
assert abs(cost(model,"2026-11-10",272001,0,4000,"no")-2.296008)<1e-9
a,b,c=scenarios(model,"2026-11-10",100000,2000,4000,10)
assert (round(a,6),round(b,6),round(c,6))==(4.88,1.74,2.24)
assert all(isinstance(x,(float,int)) for x in (a,b,c))
assert CONTENT.is_file()
with CSV_PATH.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
assert len(rows)==20 and len({r["case_id"] for r in rows})==20
source=(ROOT/"models/gpt-5-6-sol/index.html").read_text(encoding="utf-8")
rendered=source if 'id="sxf-gpt56-sol-research"' in source else enrich_gpt56_sol_page(source,models)
assert rendered.count('id="sxf-gpt56-sol-research"')==1
assert rendered.count("<h1>")==1
assert '<link rel="canonical" href="'+URL+'"' in rendered
assert "<title>"+TITLE.replace("&","&amp;")+"</title>" in rendered
assert "g56-page" in rendered
assert "data-model-history" in rendered and "data-what-changed" in rendered
assert "research.css?v=20261110-a" in rendered and "research.js?v=20261110-a" in rendered
assert "id=\"g56-calculator\"" in rendered and "id=\"g56-comparison\"" in rendered
assert "gpt56-sol-cache-economics-2026-11.csv" in rendered
assert "{{" not in rendered
assert "not a model inference run" in rendered
for q,answer in FAQ:
 assert q in rendered and answer in rendered,(q,answer)
schema=re.search(r'<script type="application/ld\+json">(.+?)</script>',rendered,re.S)
assert schema
nodes=json.loads(schema.group(1))["@graph"]
assert {"TechArticle","BreadcrumbList","FAQPage","Dataset"} <= {n["@type"] for n in nodes}
faq=next(n for n in nodes if n["@type"]=="FAQPage")
assert len(faq["mainEntity"])==len(FAQ)
dataset=next(n for n in nodes if n["@type"]=="Dataset")
assert dataset["distribution"]["contentUrl"]==DATASET
article=next(n for n in nodes if n["@type"]=="TechArticle")
assert article["mainEntityOfPage"]==URL and article["dateModified"]>="2026-11-10"
assert (ROOT/"models/gpt-5-6-sol/research.css").is_file()
assert (ROOT/"models/gpt-5-6-sol/research.js").is_file()
print("GPT-5.6 Sol: 20 pricing scenarios, canonical schema, FAQs, model provenance and page generation PASS")
