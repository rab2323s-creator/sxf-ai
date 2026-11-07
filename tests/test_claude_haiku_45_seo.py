#!/usr/bin/env python3
"""Regressions for source-backed Claude Haiku 4.5 SEO, costs and links."""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import claude_haiku_45_model_page as editorial

PAGE=ROOT/"models/claude-haiku-4-5/index.html"
URL="https://sxf.si/models/claude-haiku-4-5/"

def validate():
    page=PAGE.read_text(encoding="utf-8")
    assert page.count('rel="canonical" href="'+URL+'"')==1
    assert page.count("<h1>")==1
    assert page.count("data-haiku45-guide")==1
    assert "<title>Claude Haiku 4.5: API Pricing, Context &amp; Python Guide | SXF</title>" in page
    assert 'src="/assets/haiku45-cost-lab.js"' in page
    assert 'href="/assets/haiku45-guide.css"' in page
    assert "claude-haiku-4-5-20251001" in page
    assert "Manual budget" in page
    assert "200,000" in page and "64,000" in page
    assert "SXF ORIGINAL UNIT ECONOMICS" in page
    assert "ORIGINAL SXF BREAK-EVEN ANALYSIS" in page
    assert "SXF ORIGINAL EVALUATION DESIGN" in page
    assert "not a claim that SXF has executed API calls" in page
    assert len(re.findall(r"<h2\b",page))>=18
    for anchor in ("haiku45-intro","haiku45-specs","haiku45-pricing","haiku45-cache",
                   "haiku45-code","haiku45-migration","haiku45-decisions",
                   "haiku45-lab","haiku45-faq","haiku45-sources"):
        assert page.count('id="'+anchor+'"')==1
    for path in ("/models/claude-haiku-5-5/","/models/claude-sonnet-5-5/",
                 "/compare/claude-haiku-5-5-vs-claude-sonnet-5-5/","/providers/anthropic/",
                 "/guides/ai-agent-cost/","/guides/ai-agent-security/",
                 "/guides/ai-agent-evaluation-checklist/","/evaluations/"):
        assert 'href="'+path+'"' in page,path
        assert (ROOT/path.strip("/")/"index.html").exists(),path
    assert editorial.CONTENT.read_text(encoding="utf-8").strip() in page
    generator=(ROOT/"scripts/update_news.py").read_text(encoding="utf-8")
    assert "from claude_haiku_45_model_page import enrich_claude_haiku_45_page" in generator
    assert 'if model_id == "claude-haiku-4-5-20251001":' in generator
    assert "page = enrich_claude_haiku_45_page(page)" in generator
    other=(ROOT/"models/claude-haiku-5-5/index.html").read_text(encoding="utf-8")
    assert 'data-haiku45-legacy-bridge' in other
    assert 'href="/models/claude-haiku-4-5/"' in other
    assert 'if model_id == "claude-haiku-5-5":' in generator
    schema=re.search(r'<script type="application/ld\+json">(.*?)</script>',page,re.S)
    assert schema
    graph=json.loads(schema.group(1))["@graph"]
    article=next(x for x in graph if x.get("@type")=="TechArticle")
    faq=next(x for x in graph if x.get("@type")=="FAQPage")
    assert article["dateModified"]=="2026-11-07"
    assert article["mainEntityOfPage"]["@id"]==URL
    assert len(article["citation"])>=7 and len(faq["mainEntity"])==8
    # Published Anthropic rate math: 1k requests at 2k input + 500 output.
    assert round(1000*(2000*1+500*5)/1000000,2)==4.50
    assert round(1000*(1000*1+1000*.1+500*5)/1000000,2)==3.60
    assert round(1000*(2000*.5+500*2.5)/1000000,2)==2.25
    assert 1.25+.1<2*1
    assert 2+2*.1<3*1
    js=(ROOT/"assets/haiku45-cost-lab.js").read_text(encoding="utf-8")
    assert "input*1+output*5+cacheRead*.1+write5*1.25+write60*2" in js
    assert "fetch(" not in js and "localStorage" not in js
    scorer=ROOT/"models/claude-haiku-4-5/sxf-haiku45-eval.py"
    fixtures=ROOT/"models/claude-haiku-4-5/sxf-haiku45-fixture.jsonl"
    result=subprocess.run([sys.executable,str(scorer),str(fixtures)],capture_output=True,text=True,check=True,timeout=30)
    data=json.loads(result.stdout)
    assert data["examples"]==12
    assert data["matched"]==11
    assert 0<data["exact_match_fraction"]<1
    assert "synthetic" in scorer.read_text(encoding="utf-8")

if __name__=="__main__":
    validate()
    print("PASS: Haiku 4.5 SEO, canonical, model facts, cost math, original analysis, and reciprocal links")
