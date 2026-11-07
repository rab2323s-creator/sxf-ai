#!/usr/bin/env python3
"""Cohere Command A+ SEO, provider pricing, model facts and research integrity."""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import command_a_plus_page as editorial

URL="https://sxf.si/models/command-a-plus/"
PAGE=ROOT/"models/command-a-plus/index.html"

def test_page():
    p=PAGE.read_text(encoding="utf-8")
    assert p.count('rel="canonical" href="'+URL+'"')==1
    assert p.count("<h1>")==1
    assert p.count("data-caplus-guide")==1
    assert '<title>Cohere Command A+: API, 128K Context, Pricing &amp; GPU | SXF</title>' in p
    assert 'src="/assets/command-a-plus-cost.js"' in p
    assert 'href="/assets/command-a-plus-guide.css"' in p
    assert "command-a-plus-05-2026" in p
    assert "218 billion total parameters" in p
    assert "25 billion active parameters" in p
    assert "128,000-token context window" in p
    assert "64,000-token maximum output" in p
    assert "Apache 2.0" in p
    assert "$57.50" in p
    assert "$17.50" not in p and "$32.50" not in p
    assert "Command A+ L rate is not listed" in p or "Command A+ L rate" in p
    assert "data-caplus-calculator" in p
    assert "SXF ORIGINAL REPRODUCIBLE EVALUATION DESIGN" in p
    assert "not Cohere model outputs" in p
    assert len(re.findall(r"<h2\b",p))>=18
    for ident in (
        "caplus-overview","caplus-specifications","caplus-pricing",
        "caplus-cost-method","caplus-code","caplus-agentic",
        "caplus-hardware","caplus-comparison","caplus-lab",
        "caplus-faq","caplus-sources",
    ):
        assert p.count('id="'+ident+'"')==1,ident
    for route in (
        "/providers/cohere/","/models/command-a-reasoning/",
        "/models/embed-v5-0-pro/","/models/rerank-4-pro/",
        "/models/parse-v5-0/","/models/pricing/",
        "/guides/llm-quantization-explained/",
        "/guides/vector-database-for-rag/",
        "/guides/ai-agent-security/",
        "/guides/deploy-ai-agents-production/",
        "/guides/ai-agent-evaluation-checklist/","/evaluations/",
    ):
        assert 'href="'+route+'"' in p,route
        assert (ROOT/route.strip("/")/"index.html").exists(),route
    assert editorial.CONTENT.read_text(encoding="utf-8").strip() in p
    m=re.search(r'<script type="application/ld\+json">(.*?)</script>',p,re.S)
    assert m
    graph=json.loads(m.group(1))["@graph"]
    article=next(x for x in graph if x["@type"]=="TechArticle")
    faq=next(x for x in graph if x["@type"]=="FAQPage")
    assert article["mainEntityOfPage"]["@id"]==URL
    assert article["dateModified"]=="2026-11-08"
    assert len(article["citation"])==8
    assert len(faq["mainEntity"])==8
    gen=(ROOT/"scripts/update_news.py").read_text(encoding="utf-8")
    assert "from command_a_plus_page import enrich_command_a_plus_page" in gen
    assert 'if model_id == "command-a-plus-05-2026":' in gen
    assert "page = enrich_command_a_plus_page(page)" in gen
    assert 'if model_id == "command-a-reasoning-08-2025":' in gen
    assert "data-caplus-reasoning-bridge" in gen


def test_links():
    for route,marker in (
        ("models/command-a-reasoning/index.html","data-caplus-reasoning-bridge"),
        ("guides/deploy-ai-agents-production/index.html",'data-caplus-inbound="agent-deployment"'),
        ("guides/how-to-choose-ai-model/index.html",'data-caplus-inbound="model-selection"'),
    ):
        s=(ROOT/route).read_text(encoding="utf-8")
        assert marker in s
        assert 'href="/models/command-a-plus/"' in s
        assert s.count("<h1>")==1


def test_economics_and_synthetic_scorer():
    for hours,expected in ((8,460),(176,10120),(720,41400)):
        assert hours*57.5==expected
    assert 176*57.5==10120
    assert 176*100*.9==15840
    assert round(10120/15840,4)==.6389
    for bits,expected in ((4,109),(8,218),(16,436)):
        assert 218_000_000_000*bits/8/1e9==expected
    js=(ROOT/"assets/command-a-plus-cost.js").read_text(encoding="utf-8")
    assert "const hourly=57.5;" in js
    assert "instances*hours*hourly" in js
    assert "cost/accepted" in js
    assert "fetch(" not in js and "localStorage" not in js
    assert "17.5" not in js and "32.5" not in js

    base=ROOT/"models/command-a-plus"
    run=subprocess.run(
        [sys.executable,str(base/"sxf-command-a-plus-eval.py"),
         str(base/"sxf-command-a-plus-synthetic.jsonl")],
        text=True,capture_output=True,check=True,timeout=20,
    )
    report=json.loads(run.stdout)
    assert report["cases"]==12
    assert report["matched"]==11
    assert set(report["by_group"])=={
        "multilingual-support","rag-citations","vision-extraction","authorized-tools",
    }
    assert "Synthetic" in report["disclosure"]


if __name__=="__main__":
    test_page()
    test_links()
    test_economics_and_synthetic_scorer()
    print("PASS: Command A+ SEO, pricing, source truth, calculator, reciprocal links and evidence")
