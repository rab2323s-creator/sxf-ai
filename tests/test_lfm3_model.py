#!/usr/bin/env python3
"""Regeneration, SEO and evidence checks for the authored Liquid AI LFM3 family page."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news
import lfm3_model_page as model
def main():
    html=(ROOT/"models/lfm3/index.html").read_text(encoding="utf-8")
    assert update_news.model_page_indexable("LFM3", [])
    assert '<meta name="robots" content="index,follow' in html
    assert f'<link rel="canonical" href="{model.URL}"' in html
    assert 'data-lfm3-finder' in html
    assert 'lfm3-model.css' in html and 'lfm3-model.js' in html
    assert "LFM3-1.7B" in html and "d1-Omni-2B" in html
    assert "not a universal 2B model" in html
    assert "vendor" in html.lower() and "256K" in html
    for source in model.SOURCES.values():
        assert source in html, source
    graph=json.loads(html.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0])["@graph"]
    assert [e["@type"] for e in graph]==["WebPage","TechArticle","Thing","ItemList","BreadcrumbList","FAQPage"]
    assert graph[1]["datePublished"]=="2026-10-27"
    assert graph[1]["citation"]==list(model.SOURCES.values())
    assert graph[3]["numberOfItems"]==6
    assert len(graph[-1]["mainEntity"])==len(model.FAQ)
    assert model.URL in (ROOT/"sitemap.xml").read_text(encoding="utf-8")
    for p in ["assets/lfm3-model.css","assets/lfm3-model.js"]:
        assert (ROOT/p).is_file()
    archive=json.loads((ROOT/"data/archive.json").read_text(encoding="utf-8"))["items"]
    matched=[x for x in archive if x.get("signal_slug")=="build-specialized-multimodal-models-with-lfm3-db98bf5"]
    assert matched
    regenerated=update_news.model_page_html("LFM3",matched)
    assert 'data-lfm3-finder' in regenerated
    assert model.URL in regenerated
    assert '<meta name="robots" content="index,follow' in regenerated
    assert graph[0]["dateModified"] == graph[1]["dateModified"] == model.MODIFIED
    assert model.MODIFIED >= "2026-11-24"
    contexts = {row[0]: row[4] for row in model.VARIANTS}
    assert contexts["LFM3-Omni-2B"] == "32K"
    assert contexts["d1-Omni-2B"] == "128K"
    js = (ROOT / "assets/lfm3-model.js").read_text(encoding="utf-8")
    assert '"32K tokens","Choose omni' in js
    assert '"128K tokens","Choose this branch' in js
    for page in (html, regenerated):
        assert 'id="what-changed"' in page
        assert '2.17B parameters' in page
        assert 'ollama run lfm3' in page
        assert 'd1.2-ultra' in page and 'OpenVINO' in page and 'NVFP4' in page
        assert 'data-change-models=""' not in page
        assert 'See model card</td>' not in page
        assert f'"dateModified":"{model.MODIFIED}"' in page
    print("PASS: LFM3 model family, primary sources, SEO, UI, schema and regeneration")
if __name__=="__main__":
    main()
