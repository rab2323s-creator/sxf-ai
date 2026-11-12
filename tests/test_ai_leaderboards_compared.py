"""SXF AI leaderboards guide SEO, evidence, internal links and archive integrity."""
from pathlib import Path
import csv,json,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
P=R/"guides/ai-leaderboards-compared"
h=(P/"index.html").read_text(encoding="utf-8")
assert h.count("<h1")==1
assert len(re.findall(r"<h2(?:\s|>)",h))>=11
assert h.count('rel="canonical"')==1
assert 'https://sxf.si/guides/ai-leaderboards-compared/' in h
for q in ("ai leaderboards compared","artificial analysis vs lmarena vs livebench","aa benchmark","intelligence index v5","livebench 2.0","bradley"):assert q in h.lower(),q
assert "9/12 and 3/12 counts describe the constructed examples only" in h
assert "not a measured industry error rate" in h
schema=json.loads(re.search(r'<script type="application/ld\+json">([\s\S]*?)</script>',h).group(1))["@graph"]
get=lambda t:next(x for x in schema if x["@type"]==t)
assert get("TechArticle")["datePublished"]=="2026-11-13"
assert get("WebPage")["@id"]==get("TechArticle")["mainEntityOfPage"]["@id"]
assert get("ItemList")["numberOfItems"]==3
assert get("SoftwareApplication")["offers"]["price"]==0
assert "AggregateRating" not in str(schema) and "Review" not in str(schema)
datasets=[x for x in schema if x["@type"]=="Dataset"]
assert len(datasets)==2 and all(x["distribution"]["contentUrl"] for x in datasets)
for name in ("leaderboards.css","leaderboards.js","audit_claims.py","sxf-leaderboard-claim-audit.csv","aa-index-transition.json","research-methodology.md","images/sxf-leaderboard-evidence-passport.svg"):assert (P/name).is_file(),name
ET.parse(P/"images/sxf-leaderboard-evidence-passport.svg")
with (P/"sxf-leaderboard-claim-audit.csv").open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
assert len(rows)==12 and sum(row["status"]=="REJECT" for row in rows)==9
assert len({row["id"] for row in rows})==12
j=json.loads((P/"aa-index-transition.json").read_text())
assert [z["evaluations"] for z in j["versions"]]==[10,9]
assert [z["private_evaluation_weight_pct"] for z in j["versions"]]==[45,60]
for to in re.findall(r'href="#([^"]+)"',h):assert 'id="'+to+'"' in h,to
for link in ("guides/ai-model-benchmarks-explained","guides/how-to-choose-ai-model","evaluations","guides/ai-agent-testing-tools","models/pricing"):assert 'href="/'+link+'/"' in h,link
assert 'href="/guides/ai-leaderboards-compared/"' in (R/"guides/index.html").read_text()
assert "https://sxf.si/guides/ai-leaderboards-compared/" in (R/"sitemap.xml").read_text()
assert '/guides/ai-leaderboards-compared/' in (R/"scripts/update_news.py").read_text()
assert 'href="/guides/ai-leaderboards-compared/"' in (R/"guides/ai-model-benchmarks-explained/index.html").read_text()
assert 'href="/guides/ai-leaderboards-compared/"' in (R/"scripts/ai_model_benchmarks_guide.py").read_text()
print("PASS: SXF leaderboard SEO, schema, sources, AA v4-v5 transition, synthetic case audit and inbound links")
