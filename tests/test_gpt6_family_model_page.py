#!/usr/bin/env python3
"""GPT-6 family page static and catalog regression checks."""
import json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]
html=(P/"models/gpt-6/index.html").read_text()
assert html.count('rel="canonical" href="https://sxf.si/models/gpt-6/"')==1
assert html.count("data-gpt6-family")==1 and html.count("data-gpt6-calc")==1
assert html.count("data-model-history")==1 and html.count("data-what-changed")==1
assert "{{" not in html
assert '/models/gpt-6/family.css' in html and '/models/gpt-6/family.js' in html
j=json.loads(html.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0])
assert len(next(v for v in j["@graph"] if v["@type"]=="FAQPage")["mainEntity"])==13
models={m["model_id"]:m for m in json.loads((P/"data/model-pricing.json").read_text())["models"]}
assert models["gpt-6.1-sol"]["pricing"]["standard"][0]["cached_input"]==.1
assert "enrich_gpt6_family_page" in (P/"scripts/update_news.py").read_text()
print("PASS: GPT-6 family SEO, canonical, schema, pricing and generator")
