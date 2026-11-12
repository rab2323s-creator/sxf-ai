#!/usr/bin/env python3
"""SXF Browser Agents 2026: metadata, schema, policy, index, internal links and fixture QA."""
from pathlib import Path
import json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
slug="ai-browser-agents-comparison"; url="https://sxf.si/guides/"+slug+"/"
page=(ROOT/"guides"/slug/"index.html").read_text(encoding="utf-8")
css=(ROOT/"guides"/slug/"reference.css").read_text(encoding="utf-8")
assert page.count("<h1>")==1
assert 'name="viewport"' in page and "index,follow" in page and 'lang="en"' in page
assert f'<link rel="canonical" href="{url}">' in page
assert page.count('class="ba-faq"')==11
assert page.count('class="ba-answer"')>=15
assert "Not conducted" in page and "Not measured" in page
assert "@media(max-width:640px)" in css and "overflow-x:auto" in css
assert 'aria-live="polite"' in page and 'role="region"' in page
for f in ["reference.css","cost-lab.js","fixture.html","browser-task-manifest.json","run_fixture_baseline.py","benchmark-methodology.md","benchmark-results-template.csv"]:
 assert (ROOT/"guides"/slug/f).is_file(),f
manifest=json.loads((ROOT/"guides"/slug/"browser-task-manifest.json").read_text(encoding="utf-8"))
assert len(manifest["tasks"])==12 and len(set(x["id"] for x in manifest["tasks"]))==12
assert manifest["status"].startswith("controlled")
fixture=(ROOT/"guides"/slug/"fixture.html").read_text(encoding="utf-8")
assert 'noindex,nofollow' in fixture
for task in range(1,13):
 assert 'id="task-'+f"{task:02d}"+'"' in fixture
for h in ["/guides/ai-agent-frameworks-comparison/","/research/ai-agent-reliability/","/guides/ai-agent-security/","/guides/ai-agent-cost/"]:
 assert f'href="{h}"' in page,h
m=re.search(r'<script type="application/ld[+]json">([\s\S]*?)</script>',page);assert m
graph=json.loads(m.group(1))["@graph"]
assert {"TechArticle","WebPage","BreadcrumbList","ItemList","SoftwareSourceCode","FAQPage"}.issubset({v["@type"] for v in graph})
article=next(v for v in graph if v["@type"]=="TechArticle")
assert article["url"]==url and article["datePublished"]==article["dateModified"]=="2026-11-12"
assert not any("aggregateRating" in x or "offers" in x for x in graph)
faq=next(v for v in graph if v["@type"]=="FAQPage")
assert len(faq["mainEntity"])==11
assert all(q["name"] in page and q["acceptedAnswer"]["text"] in page for q in faq["mainEntity"])
hub=(ROOT/"guides/index.html").read_text(encoding="utf-8")
assert f'href="/guides/{slug}/"' in hub
assert int(re.search(r'id="guideVisibleCount">([0-9]+)<',hub).group(1))==hub.count('class="guide-library-card"')
hs=json.loads(re.search(r'<script type="application/ld[+]json">([\s\S]*?)</script>',hub).group(1))["@graph"]
assert any(x.get("url")==url for g in hs if g.get("@type")=="ItemList" for x in g.get("itemListElement",[]))
generator=(ROOT/"scripts/update_news.py").read_text(encoding="utf-8")
assert '"href": "/guides/ai-browser-agents-comparison/"' in generator
assert 'ROOT / "guides" / "ai-browser-agents-comparison" / "index.html"' in generator
for linked in ["guides/ai-agent-frameworks-comparison/index.html","research/ai-agent-reliability/index.html","guides/ai-agent-security/index.html"]:
 assert f'href="/guides/{slug}/"' in (ROOT/linked).read_text(encoding="utf-8"),linked
locs=[x.text for x in ET.fromstring((ROOT/"sitemap.xml").read_text(encoding="utf-8")).iter() if x.tag.endswith("loc")]
assert locs.count(url)==1
print("PASS SXF Browser Agents SEO, structured data, real source claims, index links and 12 original task fixtures")
