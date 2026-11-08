#!/usr/bin/env python3
"""Mistral Embed SEO, first-party pricing, original research and reciprocal links."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import mistral_embed_model_page as editorial

URL="https://sxf.si/models/mistral-embed/"
PAGE=ROOT/"models/mistral-embed/index.html"

def test_model_page():
    page=PAGE.read_text(encoding="utf-8")
    assert page.count('rel="canonical" href="'+URL+'"')==1
    assert page.count("<h1>")==1
    assert page.count("data-membed-guide")==1
    assert "<title>Mistral Embed: API Pricing, 1024 Dimensions &amp; RAG | SXF</title>" in page
    assert 'href="/assets/mistral-embed-guide.css"' in page
    assert 'src="/assets/mistral-embed-cost.js"' in page
    assert "mistral-embed-2312" in page
    assert "mistral-embed" in page
    assert "1,024-dimensional" in page
    assert "8,000-token input context" in page
    assert "$0.10 per million input tokens" in page
    assert "data-membed-calculator" in page
    assert "SXF ORIGINAL EMBEDDING ECONOMICS" in page
    assert "SXF ORIGINAL REPRODUCIBLE EVALUATION DESIGN" in page
    assert "not vectors or search results returned by Mistral" in page
    assert len(re.findall(r"<h2\b",page))>=18
    for anchor in (
        "membed-overview","membed-specs","membed-pricing","membed-calculator",
        "membed-api","membed-rag","membed-compare","membed-evaluation",
        "membed-faq","membed-sources",
    ):
        assert page.count('id="'+anchor+'"')==1,anchor
    for route in (
        "/providers/mistral-ai/","/models/codestral-embed/",
        "/models/gemini-embedding-001/","/models/mistral-ocr-4-1/",
        "/guides/best-embedding-models-for-rag/","/guides/vector-database-for-rag/",
        "/guides/rag-vs-fine-tuning-vs-long-context/",
        "/guides/ai-model-benchmarks-explained/","/evaluations/",
    ):
        assert 'href="'+route+'"' in page,route
        assert (ROOT/route.lstrip("/")/"index.html").exists(),route
    assert editorial.CONTENT.read_text(encoding="utf-8").strip() in page
    match=re.search(r'<script type="application/ld\+json">(.*?)</script>',page,re.S)
    assert match
    graph=json.loads(match.group(1))["@graph"]
    article=next(x for x in graph if x["@type"]=="TechArticle")
    faq=next(x for x in graph if x["@type"]=="FAQPage")
    assert article["mainEntityOfPage"]["@id"]==URL
    assert article["dateModified"]=="2026-11-08"
    assert len(article["citation"])==8
    assert len(faq["mainEntity"])==8
    generator=(ROOT/"scripts/update_news.py").read_text(encoding="utf-8")
    assert "from mistral_embed_model_page import enrich_mistral_embed_page" in generator
    assert 'if model_id == "mistral-embed-2312":' in generator
    assert "page = enrich_mistral_embed_page(page)" in generator
    assert 'if model_id == "codestral-embed-2505":' in generator
    assert "data-membed-code-bridge" in generator

def test_inbound_links():
    for path,marker in (
        ("models/codestral-embed/index.html","data-membed-code-bridge"),
        ("guides/best-embedding-models-for-rag/index.html",'data-membed-inbound="embeddings-guide"'),
        ("guides/vector-database-for-rag/index.html",'data-membed-inbound="vector-database"'),
    ):
        s=(ROOT/path).read_text(encoding="utf-8")
        assert marker in s
        assert 'href="/models/mistral-embed/"' in s
        assert s.count("<h1>")==1

def test_cost_and_research():
    assert round(100*500*.10/1e6,6)==.005
    assert round(10000*500*.10/1e6,6)==.5
    assert round(100000*500*.10/1e6,6)==5
    assert round(1000000*500*.10/1e6,6)==50
    assert round(100000*20*.10/1e6,6)==.2
    assert round(100000*.05*500*.10/1e6 + 100000*20*.10/1e6,6)==.45
    assert 1024*4==4096
    assert 1000000*4096/1e9==4.096
    assert round(1000000*4096/1024**3,3)==3.815
    js=(ROOT/"assets/mistral-embed-cost.js").read_text(encoding="utf-8")
    assert "const rate=0.10/1000000;" in js
    assert "chunks*1024*4" in js
    assert "fetch(" not in js and "localStorage" not in js
    base=ROOT/"models/mistral-embed"
    proc=subprocess.run(
        [sys.executable,str(base/"sxf-mistral-embed-retrieval.py"),
         str(base/"sxf-mistral-embed-synthetic.jsonl")],
        text=True,capture_output=True,check=True,timeout=20,
    )
    report=json.loads(proc.stdout)
    assert report["total"]["queries"]==12
    assert report["total"]["recall_at_5"]==1.0
    assert 0<report["total"]["recall_at_1"]<1
    assert 0<report["total"]["mrr"]<1
    assert set(report["by_group"])=={
        "english-policy","multilingual","critical-numbers","near-duplicates",
    }
    assert "Synthetic" in report["disclosure"]

if __name__=="__main__":
    test_model_page()
    test_inbound_links()
    test_cost_and_research()
    print("PASS: Mistral Embed SEO, costs, vectors, research, persistence and reciprocal links")
