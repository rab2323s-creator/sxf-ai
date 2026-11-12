"""SXF AI Agent Testing Tools SEO, evidence and crosslink contract (stdlib only)."""
from pathlib import Path
import csv, json, re, html, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"guides/ai-agent-testing-tools"
article=(PATH/"index.html").read_text(encoding="utf-8")
site=(ROOT/"sitemap.xml").read_text(encoding="utf-8")
listing=(ROOT/"guides/index.html").read_text(encoding="utf-8")
schema=json.loads(re.search(r'<script type="application/ld\+json">([\s\S]*?)</script>',article).group(1))
graph=schema["@graph"]
get=lambda t:next(item for item in graph if item["@type"]==t)
assert article.count("<h1")==1
assert all(q in article.lower() for q in ("best ai agent testing tools","langsmith","braintrust","deepeval","phoenix","ai agent reliability","tool correctness"))
assert "https://sxf.si/guides/ai-agent-testing-tools/" in article and article.count('rel="canonical"')==1
assert get("TechArticle")["datePublished"]=="2026-11-12"
assert get("TechArticle")["image"]["@id"]==get("ImageObject")["@id"]
assert get("Dataset")["distribution"]["contentUrl"].endswith("/fixtures.csv")
assert get("ItemList")["numberOfItems"]==4
assert "FAQPage" not in [entry["@type"] for entry in graph]
assert len(re.findall(r'<h2(?:\s|>)',article))>=12
for f in ("testing.css","testing.js","fixtures.csv","images/sxf-three-layer-agent-testing.svg"):assert (PATH/f).is_file()
ET.parse(PATH/"images/sxf-three-layer-agent-testing.svg")
assert "ai-agent-testing-tools/" in site
assert 'href="/guides/ai-agent-testing-tools/"' in listing
for link in ("ai-agent-observability","ai-agent-evaluation-checklist","ai-agent-security","ai-agent-cost","ai-agent-frameworks-comparison"):
 assert 'href="/guides/'+link+'/' in article
rows=list(csv.DictReader((PATH/"fixtures.csv").open(encoding="utf-8",newline="")))
assert len(rows)==12 and len(set(row["id"] for row in rows))==12
flag=lambda row,key:row[key]=="1"
answer=sum(flag(row,"answer_correct") for row in rows)
full=sum(all(flag(row,key) for key in ("answer_correct","tool_correct","args_correct","state_correct","approval_ok")) and not any(flag(row,key) for key in ("duplicate_side_effect","retry_budget_breached","sensitive_trace_leak")) for row in rows)
assert (answer,full)==(10,4),(answer,full)
assert "10 of 12" in article and "4 of 12" in article
for target in re.findall(r'href="#([^"]+)"',article):
 assert 'id="'+target+'"' in article,("broken anchor",target)
print("PASS: published guide SEO + schema + 12-case synthetic evidence + internal links")
