#!/usr/bin/env python3
"""Regression test for SXF procurement buyer guide, canonical, schema, links and responsive CSS."""
from pathlib import Path
import json, re, xml.etree.ElementTree as ET
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
slug='ai-procurement-negotiation-software'
url='https://sxf.si/guides/'+slug+'/'
page=(ROOT/'guides'/slug/'index.html').read_text(encoding='utf-8')
css=(ROOT/'guides'/slug/'procurement.css').read_text(encoding='utf-8')
assert page.count('<h1>')==1, 'Exactly one H1'
assert '<meta name="robots" content="index,follow' in page
assert f'<link rel="canonical" href="{url}">' in page
assert '<meta name="viewport" content="width=device-width,initial-scale=1">' in page
assert 'Pactum vs Nibble vs Keelvar' in page
assert page.count('<details class="proc-faq">')>=8
assert '@media(max-width:620px)' in css and 'overflow-x:auto' in css
assert 'role="region"' in page and 'aria-live="polite"' in page
assert 'Hands-on vendor tests</span><strong>Not conducted' in page
assert "no share of negotiated savings" in page.lower()
for internal in ('/guides/ai-negotiation-agents/','/research/ai-agent-payment-negotiation/','/guides/ai-agent-cost/','/guides/ai-agent-authorization/'):
    assert f'href="{internal}"' in page
for asset in ('procurement.css','procurement.js','procurement-audit-template.csv'):
    assert (ROOT/'guides'/slug/asset).exists()
assert page.index('<script type="application/ld+json">')<page.index('</head>')
m=re.search(r'<script type="application/ld[+]json">([\s\S]*?)</script>',page)
assert m
obj=json.loads(m.group(1))
graph=obj['@graph']
assert {'TechArticle','BreadcrumbList','FAQPage','ItemList','WebPage'}.issubset({v['@type'] for v in graph})
article=next(v for v in graph if v['@type']=='TechArticle')
assert article['url']==url and article['datePublished']==article['dateModified']=='2026-11-12'
assert all('price' not in v for v in next(g for g in graph if g['@type']=='ItemList')['itemListElement'])
faq=next(v for v in graph if v['@type']=='FAQPage')
assert all(q['name'] in page and q['acceptedAnswer']['text'] in page for q in faq['mainEntity'])
for p in ('guides/index.html','guides/ai-negotiation-agents/index.html','research/ai-agent-payment-negotiation/index.html'):
    assert f'href="/guides/{slug}/"' in (ROOT/p).read_text(encoding='utf-8')
hub=(ROOT/'guides/index.html').read_text(encoding='utf-8')
assert hub.count('class="guide-library-card"')>=45
assert int(re.search(r'id="guideVisibleCount">(\\d+)<', hub).group(1)) == hub.count('class="guide-library-card"')
hmatch=re.search(r'<script type="application/ld[+]json">([\s\S]*?)</script>',hub)
hgraph=json.loads(hmatch.group(1))['@graph']
assert any(url==x.get('url') for a in hgraph if a.get('@type')=='ItemList' for x in a.get('itemListElement',[]))
xml=(ROOT/'sitemap.xml').read_text(encoding='utf-8')
locs=[n.text for n in ET.fromstring(xml).iter() if n.tag.endswith('loc')]
assert locs.count(url)==1
assert 'append_missing_guide_rows' in (ROOT/'scripts/sitemap_generation.py').read_text(encoding='utf-8')
print('PASS: procurement guide metadata/schema, source integrity, accessible mobile styles, hubs and sitemap')