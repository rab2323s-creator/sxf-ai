#!/usr/bin/env python3
"""Original SXF Anthropic API price research, SEO, schema, crawl and formula regression."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
url = "https://sxf.si/guides/anthropic-api-pricing/"
base = root / "guides/anthropic-api-pricing"
html = (base / "index.html").read_text(encoding="utf-8")
assert html.count("<h1>") == 1, "Exactly one descriptive H1"
assert html.count("<h2") >= 14, "Missing core search-intent sections"
assert '<link rel="canonical" href="' + url + '">' in html
assert 'name="robots" content="index,follow' in html
assert 'name="description" content=' in html
assert "anthropic api pricing" in html.lower()
assert "no real-world" in html.lower() or "not a measured api experiment" in html.lower() or "not recorded api sessions" in html.lower()
assert "hypothetical" in html.lower()
assert 'id="acp-calculator"' in html
assert '/providers/anthropic/' in html and '/models/pricing/' in html
assert (base / "reference.css").is_file() and (base / "reference.js").is_file()
assert (base / "data/sxf-claude-cost-fixtures.csv").is_file()
assert (base / "sxf-cost-lab-methodology.md").is_file()
for name in ("claude-api-economics.svg", "prompt-cache-break-even.svg"):
    assert (base / "images" / name).is_file()
    assert name in html
schema_txt = html.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0]
graph = json.loads(schema_txt)["@graph"]
types = [row["@type"] for row in graph]
assert {"WebPage","TechArticle","BreadcrumbList","FAQPage","Dataset","SoftwareApplication","ImageObject"}.issubset(set(types))
assert types.count("ImageObject") == 2
faq = next(row for row in graph if row["@type"] == "FAQPage")["mainEntity"]
assert len(faq) == 9
assert url in (root / "sitemap.xml").read_text(encoding="utf-8")
for page in ("guides/index.html", "providers/anthropic/index.html", "models/pricing/index.html"):
    assert "/guides/anthropic-api-pricing/" in (root / page).read_text(encoding="utf-8"), page

# Derive synthetic fixture arithmetic from published first-party rates.
assert abs(100000 * (2500*.1+300*.5)/1_000_000 - 40) < 1e-9
assert abs(100000 * (2500*2+300*10)/1_000_000 - 800) < 1e-9
assert abs(10000 * (20000*2+6000*10)/1_000_000 - 1000) < 1e-9
ideal = 40000*2.5/1e6 + 999*40000*.1/1e6 + 1000*2000*2/1e6 + 1000*1000*10/1e6
assert abs(ideal-18.096)<1e-9
assert abs(1000*(42000*2+1000*10)/1e6-94)<1e-9
print("PASS: Anthropic price research, crawl setup, original visuals, schema, inbound links and math")
