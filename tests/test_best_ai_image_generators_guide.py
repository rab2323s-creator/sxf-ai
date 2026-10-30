#!/usr/bin/env python3
"""Verify SXF image-generation comparison SEO, source evidence and discovery."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from html import unescape
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news
import best_ai_image_generators_guide as ref

def main():
    html=ref.guide_html({"page_head":update_news.page_head,"page_header":update_news.page_header,"page_footer":update_news.page_footer})
    assert html.count('rel="canonical" href="'+ref.CANONICAL+'"')==1
    assert html.count('data-image-buyers-guide')==1
    assert '<html lang="en">' in html and 'guide-article-page' in html
    assert '<link rel="stylesheet" href="/guides/best-ai-image-generators/reference.css"' in html
    assert html.count('<h1>')==1
    assert all(name in html for name in ["GPT Image","Midjourney","Nano Banana","FLUX","Ideogram"])
    assert "FLUX.2 Klein 4B" in html and "100 accepted Ideogram" in html
    assert 'href="/guides/ai-model-licensing/"' in html
    assert 'href="/guides/flux-3-image-klein/"' in html
    assert 'href="/guides/how-to-tell-if-an-image-is-ai-generated/"' in html
    assert len(ref.SOURCES)>=12 and all(link.startswith("https://") for link in ref.SOURCES)
    assert 110<=len(ref.DESCRIPTION)<=160
    assert "not a claim that SXF has generated" in html
    schema=json.loads(html.split('<script type="application/ld+json">',1)[1].split('</script>',1)[0])
    graph=schema["@graph"]
    article=next(x for x in graph if x.get("@type")=="TechArticle")
    assert article["citation"]==ref.SOURCES
    assert article["mainEntityOfPage"]["@id"]==ref.CANONICAL+"#webpage"
    assert "best AI image generator 2026" in article["keywords"]
    faq=next(x for x in graph if x.get("@type")=="FAQPage")
    assert len(faq["mainEntity"])>=10
    assert next(x for x in graph if x.get("@type")=="ItemList")["numberOfItems"]==5
    page=update_news.guides_index_html([],[])
    assert 'href="/guides/best-ai-image-generators/"' in page
    assert page.count('href="/guides/best-ai-image-generators/"')>=1
    print("PASS: generated image guide, primary-source schema, FAQ, index card, canonical and internal links")
if __name__=="__main__":main()
