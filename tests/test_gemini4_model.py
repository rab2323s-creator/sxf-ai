#!/usr/bin/env python3
"""Gemini 4 model family SEO, evidence and rebuild regression."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news
import gemini4_model_page as model
def main():
    html=(ROOT/"models/gemini-4/index.html").read_text(encoding="utf-8")
    assert update_news.model_page_indexable("Gemini 4",[])
    assert '<meta name="robots" content="index,follow' in html
    assert f'<link rel="canonical" href="{model.URL}"' in html
    assert 'data-g4-planner' in html
    assert 'gemini4-model.css' in html and 'gemini4-model.js' in html
    assert "Carbon" in html and "Argon" in html
    assert "1,048,576" in html and "65,536" in html
    assert "not independently reproduced by SXF" in html
    for url in model.SOURCES.values(): assert url in html, url
    schema=json.loads(html.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0])["@graph"]
    assert [node["@type"] for node in schema]==["WebPage","TechArticle","Thing","ItemList","BreadcrumbList","FAQPage"]
    assert schema[1]["datePublished"]=="2026-10-13"
    assert schema[1]["citation"]==list(model.SOURCES.values())
    assert len(schema[-1]["mainEntity"])==len(model.FAQ)
    assert schema[3]["numberOfItems"]==2
    assert model.URL in (ROOT/"sitemap.xml").read_text(encoding="utf-8")
    for asset in ["assets/gemini4-model.css","assets/gemini4-model.js"]:
        assert (ROOT/asset).is_file()
    archive=json.loads((ROOT/"data/archive.json").read_text(encoding="utf-8"))["items"]
    matched=[row for row in archive if row.get("signal_slug") in {
        "gemini-4-argon-in-github-copilot-619c2f7",
        "gemini-4-argon-built-to-solve-your-hardest-problems-c1e94fc"}]
    assert matched
    rendered=update_news.model_page_html("Gemini 4",matched)
    assert 'data-g4-planner' in rendered
    assert f'<link rel="canonical" href="{model.URL}"' in rendered
    print("PASS: Gemini 4 family sources, rich schema, pricing UI, sitemap and rebuild")
if __name__=="__main__":
    main()
