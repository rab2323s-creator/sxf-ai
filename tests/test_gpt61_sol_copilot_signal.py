#!/usr/bin/env python3
"""GPT-6.1 Sol in Copilot: canonical, editorial and structured-data regression."""
from __future__ import annotations
import json
import sys
from html import unescape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news
import gpt61_sol_copilot_signal_page as ref

def main():
    archive=json.loads((ROOT/"data/archive.json").read_text(encoding="utf-8"))["items"]
    item=next(x for x in archive if x["signal_slug"]=="gpt-6-1-sol-in-github-copilot-9be84db")
    html=update_news.signal_page_html(item,[item])
    url="https://sxf.si"+ref.SLUG
    assert html.count('<link rel="canonical" href="'+url+'"')==1
    assert "<h1>"+ref.H1+"</h1>" in unescape(html)
    assert ref.DESCRIPTION in html
    assert html.count("data-gpt61-copilot-guide")==1
    assert "This update matters if it changes a concrete workflow" not in html
    assert "premium requests" in html
    assert "VS Code" in html and "GitHub Copilot" in html
    assert "/models/gpt-6-1-sol/" in html
    graph=json.loads(html.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0])["@graph"]
    article=next(x for x in graph if x.get("@id")==url+"#article")
    assert article["datePublished"]==item["published"]
    assert article["dateModified"]>=ref.EDITED_AT
    assert "TechArticle" in article["@type"]
    assert article["citation"]==ref.SOURCES
    assert article["keywords"]==ref.KEYWORDS
    faq=next(x for x in graph if x.get("@type")=="FAQPage")
    assert len(faq["mainEntity"])>=8
    assert 120<=len(ref.DESCRIPTION)<=165
    assert len(ref.BODY.split())>=1100
    print("PASS: Copilot Sol content, SEO, references, dates and FAQ")

if __name__=="__main__":
    main()
