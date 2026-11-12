#!/usr/bin/env python3
"""SXF original LLM hosting guide metadata, schema, evergreen sources, and discovery QA."""
from pathlib import Path
import json,re,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
slug="open-weight-llm-hosting"
url="https://sxf.si/guides/"+slug+"/"
page=(root/"guides"/slug/"index.html").read_text(encoding="utf-8")
css=(root/"guides"/slug/"hosting.css").read_text(encoding="utf-8")
assert page.count("<h1>")==1
assert 'name="viewport"' in page
assert f'<link rel="canonical" href="{url}">' in page
assert 'index,follow' in page and 'lang="en"' in page
assert page.count('class="host-faq"')==9
assert page.count('class="host-answer"')>=15
assert "Not conducted" in page
assert "@media(max-width:650px)" in css and "overflow-x:auto" in css
assert 'aria-live="polite"' in page
for filename in ["hosting.css","hosting.js","hosting_probe.py","benchmark-protocol.md","hosting-evaluation-template.csv"]:
 assert (root/"guides"/slug/filename).is_file(),filename
for link in ["/guides/open-source-ai-models/","/guides/run-ai-models-locally/","/guides/llm-quantization-explained/","/guides/llm-gateway/","/tools/ai-model-cost-calculator/"]:
 assert f'href="{link}"' in page,link
m=re.search(r'<script type="application/ld[+]json">([\s\S]*?)</script>',page);assert m
graph=json.loads(m.group(1))["@graph"]
assert {"WebPage","TechArticle","BreadcrumbList","ItemList","FAQPage","SoftwareSourceCode"}.issubset({x["@type"] for x in graph})
art=next(x for x in graph if x["@type"]=="TechArticle")
assert art["url"]==url and art["datePublished"]==art["dateModified"]=="2026-11-12"
faq=next(x for x in graph if x["@type"]=="FAQPage")
assert all(q["name"] in page and q["acceptedAnswer"]["text"] in page for q in faq["mainEntity"])
hub=(root/"guides/index.html").read_text(encoding="utf-8")
assert f'href="/guides/{slug}/"' in hub
assert int(re.search(r'id="guideVisibleCount">(\d+)<',hub).group(1))==hub.count('class="guide-library-card"')
hs=json.loads(re.search(r'<script type="application/ld[+]json">([\s\S]*?)</script>',hub).group(1))["@graph"]
assert any(item.get("url")==url for g in hs if g.get("@type")=="ItemList" for item in g.get("itemListElement",[]))
generator=(root/"scripts/update_news.py").read_text(encoding="utf-8")
assert '"href": "/guides/open-weight-llm-hosting/"' in generator
assert 'ROOT / "guides" / "open-weight-llm-hosting" / "index.html"' in generator
assert "add_hosting_buyer_path" in generator
assert f'href="/guides/{slug}/"' in (root/"guides/llm-gateway/index.html").read_text(encoding="utf-8")
urls=[x.text for x in ET.fromstring((root/"sitemap.xml").read_text(encoding="utf-8")).iter() if x.tag.endswith("loc")]
assert urls.count(url)==1
print("PASS SXF open-weight LLM hosting SEO, schema, prices, generator, inbound links, sitemap")
