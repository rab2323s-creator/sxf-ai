"""Local workstation comparison: metadata, SEO, source evidence, 60-case math and crosslinks."""
from pathlib import Path
import csv,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"guides/local-ai-workstations"
h=(P/"index.html").read_text()
m=re.search(r'<script type="application/ld\+json">([\s\S]*?)</script>',h)
assert m,"missing schema"
g=json.loads(m.group(1))["@graph"]
typ=lambda x:next(y for y in g if y["@type"]==x)
assert typ("TechArticle")["mainEntityOfPage"]["@id"]==typ("WebPage")["@id"]
assert typ("TechArticle")["datePublished"]=="2026-11-13"
assert typ("Dataset")["distribution"]["contentUrl"].endswith("sxf-workstation-memory-screen.csv")
assert typ("SoftwareApplication")["offers"]["price"]==0
assert typ("ItemList")["numberOfItems"]==4
assert not any(x["@type"] in ("Review","AggregateRating","FAQPage") for x in g)
assert h.count("<h1")==1
assert h.count('rel="canonical"')==1 and 'https://sxf.si/guides/local-ai-workstations/' in h
assert all(q in h.lower() for q in ("best local ai workstations","dgx spark","mac studio m5","ryzen ai max","local llm","unified memory","128gb"))
assert len(re.findall(r"<h2(?:\s|>)",h))>=13
for x in ("workstation.js","workstation.css","sxf-capacity-screen.py","sxf-workstation-memory-screen.csv","independent-benchmark-extract.csv","research-methodology.md","images/sxf-memory-fit-decision-map.svg"):assert (P/x).is_file(),x
ET.parse(P/"images/sxf-memory-fit-decision-map.svg")
with (P/"sxf-workstation-memory-screen.csv").open(newline="") as f:
 rows=list(csv.DictReader(f))
assert len(rows)==60 and len(set((r["system"],r["model"],r["format"]) for r in rows))==60
assert all(r["capacity_screen_only"] in ("borderline","over indicative budget","fits indicative budget") for r in rows)
with (P/"independent-benchmark-extract.csv").open(newline="") as f:benchmark=list(csv.DictReader(f))
assert len(benchmark)==4 and all("BAEM1N" not in r["source"] and "github.com/BAEM1N/llm-bench" in r["source"] for r in benchmark)
for link in ("guides/open-source-ai-models","guides/run-ai-models-locally","guides/llm-quantization-explained","tools/local-llm-vram-finder","guides/open-weight-llm-hosting"):
 assert 'href="/'+link+'/"' in h,link
for anchor in re.findall(r'href="#([^"]+)"',h):assert 'id="'+anchor+'"' in h,anchor
assert "/guides/local-ai-workstations/" in (ROOT/"guides/index.html").read_text()
assert "https://sxf.si/guides/local-ai-workstations/" in (ROOT/"sitemap.xml").read_text()
assert "/guides/local-ai-workstations/" in (ROOT/"scripts/update_news.py").read_text()
print("PASS: SEO, independent evidence, reproducible capacity screen and crosslinks")
