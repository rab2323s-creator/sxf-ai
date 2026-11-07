"""Persistent source-backed SEO for generated Cohere Command A+ model page.

Preserve provider catalog as source of truth, unchanged prices and history.
"""
from __future__ import annotations
import json
import re
from html import escape
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/"data/model-page-content/command-a-plus-seo.html"
URL="https://sxf.si/models/command-a-plus/"
TITLE="Cohere Command A+: API, 128K Context, Pricing & GPU | SXF"
DESCRIPTION=("Cohere Command A+ guide: 128K context, 218B MoE, free API limits, "
             "Model Vault pricing, Python Chat v2, reasoning, GPUs and SXF cost calculator.")
SOURCES=[
    "https://docs.cohere.com/docs/command-a-plus",
    "https://docs.cohere.com/docs/model-vault/standard/pricing",
    "https://docs.cohere.com/reference/chat",
    "https://docs.cohere.com/docs/reasoning",
    "https://docs.cohere.com/docs/tool-use-overview",
    "https://cohere.com/blog/command-a-plus",
    "https://huggingface.co/CohereLabs/command-a-plus-05-2026-bf16",
    "https://docs.cohere.com/docs/command-a-reasoning",
]
QUESTIONS=[
    ("What is the Cohere Command A+ API model ID?",
     "The pinned Cohere API model ID is command-a-plus-05-2026. Use Cohere's Chat v2 endpoint /v2/chat or ClientV2 Python SDK."),
    ("Is Cohere Command A+ free?",
     "The shared Cohere API is free until rate limits are reached. Managed Model Vault capacity is separately billed by instance-hour, subject to availability and commitments."),
    ("How much does Command A+ Model Vault cost?",
     "Cohere lists Standard Model Vault L at $17.50 per instance-hour and XL at $32.50 per instance-hour. Check current tiers and contractual monthly/annual commitments."),
    ("What is Command A+ context and output capacity?",
     "Cohere documents 128,000 context tokens and 64,000 maximum output tokens."),
    ("Is Command A+ available under an open source license?",
     "Yes. Cohere released downloadable model weights under Apache 2.0, with GPU and operational infrastructure costs separate."),
    ("How much GPU memory does Command A+ need?",
     "The model has 218B total and 25B active parameters. Cohere documents W4A4 serving using one NVIDIA B200 or two H100 accelerators. Raw 4-bit weight storage is approximately 109 decimal GB before overhead."),
    ("Can Command A+ process images or Arabic?",
     "Yes. Cohere documents text and image inputs, text output and 48 supported languages, including Arabic."),
    ("How does Command A+ compare with Command A Reasoning?",
     "Command A+ is a 218B-total/25B-active MoE with 128K context and vision, while Command A Reasoning offers 256K context and 32K maximum output. Evaluate application-specific outcomes, not a universal winner."),
]
CAVEATS='<section class="model-deep-section"><div class="model-section-head"><p class="eyebrow">CAVEATS</p>'

def once(page:str,old:str,new:str,label:str)->str:
    count=page.count(old)
    if count!=1: raise ValueError(f"Command A+ {label}: expected exactly one match, got {count}")
    return page.replace(old,new,1)

def meta(page:str,name:str,value:str)->str:
    kind="property" if name.startswith("og:") else "name"
    pat=r'(<meta '+kind+r'="'+re.escape(name)+r'" content=")[^"]*(")'
    new,count=re.subn(pat,lambda m:m.group(1)+escape(value,quote=True)+m.group(2),page,count=1)
    if count!=1: raise ValueError(f"Command A+ missing {name} meta")
    return new

def enrich_command_a_plus_page(page:str)->str:
    if page.count('rel="canonical" href="'+URL+'"')!=1: raise ValueError("Canonical URL mismatch")
    fragment=CONTENT.read_text(encoding="utf-8").strip()
    if fragment.count("data-caplus-guide")!=1 or fragment.count('id="caplus-faq"')!=1:
        raise ValueError("Command A+ authored editorial fragment missing")
    page=once(page,"<title>Command A+ — API Specs, Context &amp; Pricing | SXF / AI</title>",
              "<title>"+escape(TITLE)+"</title>","title")
    for k,v in (("description",DESCRIPTION),("og:title",TITLE),("og:description",DESCRIPTION),
                ("twitter:title",TITLE),("twitter:description",DESCRIPTION)):
        page=meta(page,k,v)
    page=once(page,'<h1>Command A+<br><span>verified model reference.</span></h1>',
              '<h1>Cohere Command A+<br><span>API, 128K context, cost &amp; GPUs.</span></h1>',"H1")
    page=once(page,
              '<p>Cohere&#x27;s strongest Command-family agentic model, combining reasoning, vision, multilingual support, tool use and enterprise deployment efficiency.</p>',
              '<p>Cohere Command A+ (command-a-plus-05-2026): 128K context, 218B MoE, vision, free API rate limits, Model Vault pricing and Python.</p>',
              "hero")
    page=once(page,'<div><strong>64,000</strong><span>max output</span></div>',
              '<div><strong>218B / 25B</strong><span>total / active MoE weights</span></div>',"hero weights")
    page=once(page,
              '<div><span>STANDARD RATE</span><strong>Not published</strong><small>per 1 million tokens</small></div>',
              '<div><span>SHARED API</span><strong>Free to rate limits</strong><small>no published paid token rate</small></div>',
              "shared access")
    page=once(page,
              '<div><span>OUTPUT RATE</span><strong>—</strong><small>per 1 million tokens</small></div>',
              '<div><span>MODEL VAULT L</span><strong>$17.50/hour</strong><small>managed instance, subject to terms</small></div>',
              "managed price")
    page=once(page,
              '<article><span>REASONING</span><h3>supported</h3><p>Only provider-documented reasoning controls are shown; missing controls remain unpublished rather than inferred.</p></article>',
              '<article><span>REASONING / TOOL USE</span><h3>Configurable</h3><p>Cohere supports reasoning and tool-call workflows. Verify execution permissions and usage before automation.</p></article>',
              "reasoning")
    page=once(page,
              '<p>SXF preserves the provider-published native billing basis. Only calculator-eligible generative token models enter token-cost arithmetic; specialist units and input-only embeddings remain visible without forced conversion.</p>',
              '<p>The Cohere shared API is free within account rate limits; its paid Model Vault instance-hour prices are a separate billing basis. SXF does not invent a paid Standard per-token rate.</p>',
              "pricing explanation")
    page=once(page,CAVEATS,fragment+"\n\n        "+CAVEATS,"editorial")
    page=once(page,"</head>",'<link rel="stylesheet" href="/assets/command-a-plus-guide.css" />\n    </head>',"CSS")
    page=once(page,"</body>",'<script src="/assets/command-a-plus-cost.js" defer></script>\n    </body>',"calculator")
    m=re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)',page,re.S)
    if not m: raise ValueError("Missing structured data")
    schema=json.loads(m.group(2))
    a=next((x for x in schema["@graph"] if x.get("@type")=="TechArticle"),None)
    if not a: raise ValueError("Missing TechArticle")
    a.update({
        "headline":TITLE.removesuffix(" | SXF"),"description":DESCRIPTION,
        "dateModified":"2026-11-08","citation":SOURCES,
        "mainEntityOfPage":{"@type":"WebPage","@id":URL},
        "author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
        "publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
        "keywords":["Cohere Command A+","Command A Plus","command-a-plus-05-2026",
                    "Command A+ API","Command A+ pricing","Command A+ 128K context",
                    "Command A Plus GPU","Cohere Model Vault pricing","Command A+ vs Reasoning"],
    })
    schema["@graph"].append({
        "@type":"FAQPage","@id":URL+"#faq","url":URL+"#caplus-faq",
        "mainEntity":[{"@type":"Question","name":q,
                       "acceptedAnswer":{"@type":"Answer","text":answer}} for q,answer in QUESTIONS],
    })
    return page[:m.start(2)]+json.dumps(schema,ensure_ascii=False,separators=(",",":"))+page[m.end(2):]
