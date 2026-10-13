#!/usr/bin/env python3
"""Gemini 3.8 Flash-Lite TTS: model page SEO and pricing regression."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=(root/"models/gemini-3-8-flash-lite-tts/index.html").read_text()
assert p.count('rel="canonical" href="https://sxf.si/models/gemini-3-8-flash-lite-tts/"')==1
assert p.count("data-flash-lite-tts-guide")==1 and p.count("data-lite-calculator")==1
assert p.count("data-model-history")==1 and p.count("data-what-changed")==1
assert "{{" not in p and len(p)>35000
assert "/models/gemini-3-8-flash-lite-tts/lite.css" in p
assert "/models/gemini-3-8-flash-lite-tts/lite.js" in p
graph=json.loads(p.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0])["@graph"]
assert len(next(x for x in graph if x["@type"]=="FAQPage")["mainEntity"])==17
assert "enrich_gemini_38_flash_lite_tts_page(page, MODEL_PRICING_BY_ID)" in (root/"scripts/update_news.py").read_text()
models={m["model_id"]:m for m in json.loads((root/"data/model-pricing.json").read_text())["models"]}
p26=models["gemini-3.8-flash-lite-tts"]["pricing"]["standard"][0]
p27=models["gemini-3.8-flash-lite-tts"]["pricing"]["standard"][1]
assert (p26["output"],p27["output"])==(6,12)
assert "$0.009" in p and "$0.0135" in p
print("PASS Flash-Lite SEO, pricing, schema, calculator, history and regeneration")
