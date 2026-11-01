#!/usr/bin/env python3
"""Verify the editorial DSpark model route and search contracts survive regeneration."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news
from lfm25_vl_dspark_model_page import FAQ, TITLE, DESCRIPTION, URL, SOURCES
def main():
    page=(ROOT/"models/lfm2-5-vl-dspark/index.html").read_text(encoding="utf-8")
    assert update_news.model_page_indexable("LFM2.5-VL-DSpark",[]), "Authored model must remain indexable"
    assert '<meta name="robots" content="index,follow' in page
    assert f'<link rel="canonical" href="{URL}"' in page
    assert "<h1" in page and "279.5M" in page
    assert "not a standalone vision-language model" in page.lower()
    assert 'data-dspark-explorer' in page
    assert "LFM2.5-VL-3B" in page and "H100" in page and "MLX-VLM" in page
    assert 'width=device-width' in page
    for source in SOURCES.values():
        assert source in page, source
    schema=json.loads(page.split('<script type="application/ld+json">')[1].split("</script>")[0])["@graph"]
    assert [entity["@type"] for entity in schema]==["WebPage","TechArticle","Thing","BreadcrumbList","FAQPage"]
    assert schema[1]["datePublished"]=="2026-09-24T00:00:00Z"
    assert schema[1]["citation"]==list(SOURCES.values())
    assert len(schema[-1]["mainEntity"])==len(FAQ)
    assert URL in (ROOT/"sitemap.xml").read_text(encoding="utf-8")
    for path in ["assets/lfm25-vl-dspark.css","assets/lfm25-vl-dspark.js"]:
        assert (ROOT/path).is_file()
    archive=json.loads((ROOT/"data/archive.json").read_text(encoding="utf-8"))["items"]
    matched=[x for x in archive if x.get("signal_slug")=="accelerating-vision-language-models-with-lfm2-5-vl-dspark-ea150f6"]
    assert matched,"Expected preserved news row"
    rebuilt=update_news.model_page_html("LFM2.5-VL-DSpark", matched)
    assert "data-dspark-explorer" in rebuilt
    assert f'<link rel="canonical" href="{URL}"' in rebuilt
    assert '<meta name="robots" content="index,follow' in rebuilt
    print("PASS: DSpark primary-source model page, indexing, canonical, FAQ schema, tools and generator")
if __name__=="__main__":
    main()
