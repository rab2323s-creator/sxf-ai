#!/usr/bin/env python3
"""AI receptionist editorial guide, discoverability, structured data and assets."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news
import ai_receptionist_guide as ref
def main():
    html=ref.guide_html({"page_head":update_news.page_head,"page_header":update_news.page_header,"page_footer":update_news.page_footer})
    assert html.count('rel="canonical" href="'+ref.CANONICAL+'"')==1
    assert html.count('data-ai-receptionist-guide')==1
    assert html.count("<h1>")==1
    assert '<meta name="robots" content="index,follow' in html
    assert "Vapi" in html and "Retell AI" in html and "ElevenLabs Reception" in html and "OpenAI Realtime" in html
    assert "$0.05" in html and "$0.31" in html and "$29" in html
    assert "only confirm after" in html.lower() or "Only say" in html or "only announce" in html.lower()
    assert "20-call acceptance matrix" in html
    assert 'data-receptionist-calculator' in html
    assert '<script src="/guides/ai-receptionist/calculator.js"' in html
    assert '<link rel="stylesheet" href="/guides/ai-receptionist/reference.css"' in html
    assert 'images/ai-receptionist-architecture.svg' in html
    assert '/guides/ai-agent-security/' in html and '/models/gpt-realtime-2-1/' in html
    assert len(ref.SOURCES)>=15 and all(x.startswith("https://") for x in ref.SOURCES)
    assert 120<=len(ref.DESCRIPTION)<=160
    graph=json.loads(html.split('<script type="application/ld+json">',1)[1].split('</script>',1)[0])["@graph"]
    article=next(x for x in graph if x.get("@type")=="TechArticle")
    assert article["citation"]==ref.SOURCES
    assert article["mainEntityOfPage"]["@id"]==ref.CANONICAL+"#webpage"
    assert "AI receptionist" in article["keywords"]
    faq=next(x for x in graph if x.get("@type")=="FAQPage")
    assert len(faq["mainEntity"])>=12
    itemlist=next(x for x in graph if x.get("@type")=="ItemList")
    assert itemlist["numberOfItems"]==5
    index=update_news.guides_index_html([],[])
    assert 'href="/guides/ai-receptionist/"' in index
    assert (ROOT/"guides/ai-receptionist/calculator.js").exists()
    assert (ROOT/"guides/ai-receptionist/reference.css").exists()
    assert (ROOT/"guides/ai-receptionist/images/ai-receptionist-architecture.svg").exists()
    for p in ["guides/best-ai-text-to-speech-models/index.html","guides/ai-agent-use-cases/index.html","models/gpt-realtime-2-1/index.html"]:
        assert 'href="/guides/ai-receptionist/"' in (ROOT/p).read_text(encoding="utf-8")
    print("PASS: receptionist guide, schema, billing assumptions, interactivity, index and inbound links")
if __name__=="__main__":main()
