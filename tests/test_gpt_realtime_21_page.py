#!/usr/bin/env python3
"""Regression test for GPT-Realtime-2.1 editorial source and model SEO."""
import json
import sys
from pathlib import Path
from html import unescape

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news
import gpt_realtime_21_page as ref

def main():
    model=update_news.model_catalog_entry("gpt-realtime-2.1")
    assert model["sxf_url"]=="/models/gpt-realtime-2-1/"
    assert model["provenance"]["verified_at"]=="2026-10-12"
    assert model["context_window"]==128000 and model["max_output"]==32000
    html=update_news.render_catalog_model_page("gpt-realtime-2.1",[])
    assert html.count('data-gpt-realtime21-guide')==1
    assert html.count('<link rel="canonical" href="'+ref.CANONICAL+'"')==1
    assert "<h1>"+ref.H1+"</h1>" in unescape(html)
    assert ref.DESCRIPTION in html
    assert 'href="/models/gpt-realtime-2-1/reference.css"' in html
    assert '$0.1688' in html and '$32.00' in html and '$64.00' in html
    assert 'GPT-Realtime-2.1 Mini' in html
    assert 'data-model-history' in html
    assert 'data-what-changed' in html
    assert 'id="r21-api"' in html and 'id="r21-faq"' in html
    assert '/models/gpt-realtime-2-1-mini/' in html
    assert '<meta property="og:type" content="article"' in html
    assert 120<=len(ref.DESCRIPTION)<=165
    root=json.loads(html.split('<script type="application/ld+json">',1)[1].split('</script>',1)[0])
    graph=root["@graph"]
    assert len([r for r in graph if r.get("@type")=="TechArticle"])==1
    article=next(r for r in graph if r.get("@type")=="TechArticle")
    assert article["citation"]==ref.SOURCES
    assert article["dateModified"]==ref.VERIFIED_ON
    assert article["mainEntityOfPage"]["@id"]==ref.CANONICAL+"#webpage"
    assert len(article["keywords"])>=5
    assert len([r for r in graph if r.get("@type")=="FAQPage"])==1
    faq=next(r for r in graph if r.get("@type")=="FAQPage")
    assert len(faq["mainEntity"])>=10
    assert 'GPT-Realtime-2.1 Playground' in article["keywords"]
    assert all(u.startswith("https://developers.openai.com/") for u in ref.SOURCES)
    print("PASS: realtime model data, page generator, schema, FAQ, pricing, internal links and canonical")

if __name__=="__main__":main()
