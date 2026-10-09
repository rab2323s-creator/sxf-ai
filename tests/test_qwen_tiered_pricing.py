#!/usr/bin/env python3
"""Regression: region-and-input-tier API list prices are displayed, not hidden or flattened."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
model=next(m for m in json.loads((ROOT/"data/model-pricing.json").read_text())["models"] if m["model_id"]=="qwen3.5-397b-a17b")
assert model["calculator_eligible"] is False
assert model["pricing_status"]=="official-paid"
assert not model["pricing"].get("standard")
tiers=model["pricing"]["tiered"]["scopes"]
by_scope={s["scope"]:s for s in tiers}
assert set(by_scope)=={"China","International","Global"}
assert by_scope["Global"]["tiers"]==[
 {"min_input_tokens":1,"max_input_tokens":131072,"input":0.172,"output":1.032},
 {"min_input_tokens":131073,"max_input_tokens":262144,"input":0.43,"output":2.58}
]
assert by_scope["International"]["tiers"][0]["input"]==0.6
assert by_scope["International"]["tiers"][0]["output"]==3.6
p=(ROOT/"index.html").read_text()
anchor=p.index('href="/models/qwen3-5-397b-a17b/"')
card=p[anchor:p.index("</article>",anchor)]
assert "Tiered Global" in card and "$0.172" in card and "$1.032" in card
assert "Pricing not published" not in card
details=(ROOT/"models/qwen3-5-397b-a17b/index.html").read_text()
for term in ("REGIONAL TIERED PRICING","$0.172","$1.032","$0.43","$2.58","$0.60","$3.60","Singapore","Frankfurt"):
    assert term in details,term
pricing=(ROOT/"models/pricing/index.html").read_text()
start=pricing.index("<small>qwen3.5-397b-a17b</small>")
row=pricing[start:pricing.index("</tr>",start)]
for term in ("From $0.172","From $1.032","$0.43","$2.58","Singapore"):
    assert term in row,term
model_page=(ROOT/"models/index.html").read_text()
start=model_page.index('data-model-id="qwen3.5-397b-a17b"')
row=model_page[start:model_page.index("</tr>",start)]
assert "From $0.172" in row and "From $1.032" in row
provider=(ROOT/"providers/alibaba-cloud/index.html").read_text()
start=provider.index('href="/models/qwen3-5-397b-a17b/"')
row=provider[start:provider.index("</article>",start)]
assert "Tiered Global" in row and "$0.172" in row
print("PASS: Qwen exact tiered regional API prices, exclusions and generated views")
