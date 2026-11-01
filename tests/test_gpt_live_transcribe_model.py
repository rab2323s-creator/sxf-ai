#!/usr/bin/env python3
"""GPT-Live-Transcribe source, runtime UI, schema, and regeneration checks."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news
import gpt_live_transcribe_model_page as model
def main():
    html=(ROOT/"models/gpt-live-transcribe/index.html").read_text(encoding="utf-8")
    assert update_news.model_page_indexable("GPT-Live-Transcribe",[])
    assert '<meta name="robots" content="index,follow' in html
    assert f'<link rel="canonical" href="{model.URL}"' in html
    for fragment in ["data-ltx-event-lab","data-ltx-cost","gpt-live-transcribe.css",
                     "gpt-live-transcribe.js","$0.017","$0.0045","transcription.delta",
                     "transcription.completed","server_vad","session.update"]:
        assert fragment in html,fragment
    for source in model.SOURCES.values(): assert source in html,source
    graph=json.loads(html.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0])["@graph"]
    assert [e["@type"] for e in graph]==["WebPage","TechArticle","Thing","ItemList","BreadcrumbList","FAQPage"]
    assert graph[1]["datePublished"]=="2026-07-28"
    assert graph[1]["citation"]==list(model.SOURCES.values())
    assert len(graph[-1]["mainEntity"])==len(model.FAQ)==14
    assert graph[3]["numberOfItems"]==3
    assert model.URL in (ROOT/"sitemap.xml").read_text(encoding="utf-8")
    for path in ["assets/gpt-live-transcribe.css","assets/gpt-live-transcribe.js"]:
        assert (ROOT/path).is_file()
    # Regression for the real failure: the pricing catalog owns this route and
    # overwrote the authored page AFTER the news page had rendered successfully.
    catalog_page=update_news.render_catalog_model_page("gpt-live-transcribe",[])
    assert catalog_page is not None
    assert "data-ltx-event-lab" in catalog_page
    assert "data-ltx-cost" in catalog_page
    assert "verified model reference." not in catalog_page
    assert f'<link rel="canonical" href="{model.URL}"' in catalog_page
    assert "data-model-history" in catalog_page
    # Whole catalog build must preserve the same source-backed content.
    update_news.build_catalog_model_pages([])
    rebuilt=(ROOT/"models/gpt-live-transcribe/index.html").read_text(encoding="utf-8")
    assert "data-ltx-event-lab" in rebuilt
    assert "GPT-Live-Transcribe: Realtime API" in rebuilt
    rendered=update_news.model_page_html("GPT-Live-Transcribe",[])
    assert 'data-ltx-event-lab' in rendered
    assert f'<link rel="canonical" href="{model.URL}"' in rendered
    print("PASS: GPT-Live-Transcribe source-verified model page, UX, schema, generator")
if __name__=="__main__":
    main()
