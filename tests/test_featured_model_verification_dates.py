#!/usr/bin/env python3
"""Assert the three current provider verification dates differ from immutable 2026 baselines.

Run after site generation, not against stale checked-in HTML from before the build.
"""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/"data/model-pricing.json").read_text(encoding="utf-8"))
history=json.loads((ROOT/"data/model-history.json").read_text(encoding="utf-8"))
by_id={m["model_id"]:m for m in catalog["models"]}
paths={
  "gpt-5.6-sol":"models/gpt-5-6-sol/index.html",
  "gpt-6-sol":"models/gpt-6-sol/index.html",
  "gpt-6-astra":"models/gpt-6-astra/index.html",
}
for model_id,path in paths.items():
  model=by_id[model_id]
  verified=model["provenance"]["verified_at"]
  assert verified=="2026-11-10",(model_id,verified)
  html=(ROOT/path).read_text(encoding="utf-8")
  assert f"<strong>{verified}</strong><span>last verified</span>" in html,model_id
  assert "HISTORICAL BASELINE" in html,model_id
  assert "Original ledger snapshot, not the latest source check." in html,model_id
  assert '<time datetime="2026-09-27">2026-09-27</time>' in html,model_id
  assert "2026-09-27" in html,model_id
  assert 'Technical editorial review:' in html or 'Editorial technical/source review:' in html,model_id
  blocks=re.findall(r'<script type="application/ld\+json">(.+?)</script>',html,re.S)
  assert blocks,model_id
  nodes=json.loads(blocks[0])["@graph"]
  article=next(n for n in nodes if n["@type"]=="TechArticle")
  assert article["dateModified"]=="2026-11-10",(model_id,article["dateModified"])
  assert model_id in history["state"],model_id
  assert history["state"][model_id]["last_event_verified_at"]=="2026-09-27",model_id
g56=(ROOT/paths["gpt-5.6-sol"]).read_text(encoding="utf-8")
assert "November 30, 2026" in g56
assert "November 21, 2026" not in g56
astra=(ROOT/paths["gpt-6-astra"]).read_text(encoding="utf-8")
assert "Provider specifications rechecked against OpenAI on 2026-11-10" in astra
assert "Provider specs last verified in SXF's model ledger: 27 September 2026" not in astra
print("PASS: all three current verification dates match evidence, history baselines and schema")
