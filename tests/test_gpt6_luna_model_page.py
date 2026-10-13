#!/usr/bin/env python3
"""GPT-6 Luna SEO / content / pricing regression."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/"models/gpt-6-luna/index.html").read_text()
assert s.count('rel="canonical" href="https://sxf.si/models/gpt-6-luna/"')==1
assert s.count("data-luna-reference")==1 and s.count("data-luna-calculator")==1
assert s.count("data-model-history")==1 and s.count("data-what-changed")==1
assert "{{" not in s and len(s)>35000
assert "/models/gpt-6-luna/luna.css" in s and "/models/gpt-6-luna/luna.js" in s
j=json.loads(s.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0])
assert len(next(x for x in j["@graph"] if x["@type"]=="FAQPage")["mainEntity"])==15
assert "enrich_gpt6_luna_page(page, MODEL_PRICING_BY_ID)" in (R/"scripts/update_news.py").read_text()
print("PASS: GPT-6 Luna editorial SEO and pricing")
