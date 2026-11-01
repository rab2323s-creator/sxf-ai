#!/usr/bin/env python3
"""LFM2.5-24B-A2B model guide regression: factual integrity and SEO."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news
import lfm25_24b_model_page as model

def main():
    page=(ROOT/"models/lfm2-5-24b-a2b/index.html").read_text(encoding="utf-8")
    assert update_news.model_page_indexable("LFM2.5-24B-A2B",[])
    assert '<meta name="robots" content="index,follow' in page
    assert f'<link rel="canonical" href="{model.URL}"' in page
    assert 'data-lfm24-fit' in page and 'lfm25-24b-model.js' in page
    assert '2.45B' in page and '131,072' in page and 'Q4_K_M' in page
    assert "vendor" in page.lower() and "not a measured memory test" in page
    for source in model.SOURCES.values():
        assert source in page,source
    schema=json.loads(page.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0])["@graph"]
    assert [e["@type"] for e in schema]==["WebPage","TechArticle","Thing","BreadcrumbList","FAQPage"]
    assert schema[1]["datePublished"]=="2026-10-13"
    assert schema[1]["citation"]==list(model.SOURCES.values())
    assert len(schema[4]["mainEntity"])==len(model.FAQ)
    assert model.URL in (ROOT/"sitemap.xml").read_text(encoding="utf-8")
    for p in ["assets/lfm25-24b-model.css","assets/lfm25-24b-model.js"]:
        assert (ROOT/p).is_file()
    archive=json.loads((ROOT/"data/archive.json").read_text(encoding="utf-8"))["items"]
    matched=[row for row in archive if row.get("signal_slug")=="run-fast-private-agents-on-device-with-lfm2-5-24b-a2b-550c4c0"]
    assert matched
    generated=update_news.model_page_html("LFM2.5-24B-A2B",matched)
    assert 'data-lfm24-fit' in generated
    assert f'<link rel="canonical" href="{model.URL}"' in generated
    assert '<meta name="robots" content="index,follow' in generated
    print("PASS: LFM2.5 24B primary sources, SEO, UI, schema and regeneration")
if __name__=="__main__":
    main()
