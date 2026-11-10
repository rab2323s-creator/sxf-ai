"""Durable GPT-6 Astra research layer using the canonical SXF pricing catalog.

The same page generator runs on scheduled feed refreshes: no hand-edited
generated index.html can survive independently of this authored source.
"""
from __future__ import annotations

import json
import re
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data/model-page-content/gpt-6-astra.html"
CANONICAL = "https://sxf.si/models/gpt-6-astra/"
DATASET = CANONICAL.replace("/models/gpt-6-astra/", "/data/research/gpt6-astra-cost-lab-2026-11.csv")
TITLE = "GPT-6 Astra: Pricing, Benchmarks, API & 1.05M Context | SXF"
DESCRIPTION = ("GPT-6 Astra API pricing, 1.05M context, benchmark results, reasoning controls "
               "and SXF's original 272K-token billing experiment with cost calculator and CSV.")
FAQ = [
    ("What is GPT-6 Astra?", "GPT-6 Astra is OpenAI's highest-capability GPT-6 tier for demanding reasoning, computer use, coding, research and professional work."),
    ("What is the GPT-6 Astra model ID?", "The official OpenAI API model ID is gpt-6-astra."),
    ("How much does GPT-6 Astra cost per million tokens?", "At Standard short-context rates, GPT-6 Astra costs $10 per million uncached input tokens, $1 per million cached input reads, $12.50 per million cache-write tokens, and $50 per million output tokens. Longer prompts have higher rates."),
    ("What is the context window of GPT-6 Astra?", "The documented context window is 1,050,000 tokens, with a separate maximum output limit of 128,000 tokens."),
    ("When does long-context pricing start for GPT-6 Astra?", "For prompts exceeding 272,000 input tokens, all input and cache rates double and output rates rise by 1.5 times for the full request. Exactly 272,000 input tokens stays at short-context rates."),
    ("Does GPT-6 Astra accept images?", "Yes. OpenAI documents text and image input with text output."),
    ("Which reasoning effort values does GPT-6 Astra support?", "Astra supports low, medium, high, xhigh and max reasoning effort, with medium the default; none is not a supported effort setting."),
    ("How do I call GPT-6 Astra with the API?", "Use OpenAI's Responses API with model gpt-6-astra and a supported reasoning effort. Evaluate output quality and token usage before production use."),
    ("Is GPT-6 Astra better than GPT-6.1 Sol?", "Astra is positioned for the hardest tasks, while GPT-6.1 Sol has substantially lower Standard token list prices. Compare on representative tasks and cost per accepted result rather than assuming that a higher token price guarantees better results."),
    ("Did SXF run GPT-6 Astra inference benchmarks?", "No. SXF's original experiment is a deterministic pricing calculation using six published token-count scenarios and the official price schedule. Model performance numbers shown separately are attributed to OpenAI's launch report."),
    ("Is the SXF calculator a real API bill?", "No. It estimates Standard text-token list charges for hypothetical workloads. Actual usage, caching, other processing modes, tools and deployment fees can change final bills."),
]

def _replace_once(page, pattern, value):
    updated, n = re.subn(pattern, lambda _: value, page, count=1, flags=re.S)
    if n != 1:
        raise ValueError("Astra required generator marker missing: " + pattern)
    return updated

def _rate(model, current):
    matches = [p for p in model["pricing"]["standard"]
               if p["start"] <= current and (not p.get("end") or current <= p["end"])]
    if len(matches) != 1:
        raise ValueError("Astra: exactly one active Standard rate is required")
    return matches[0]

def calculate(model, current, new=0, cached=0, write=0, output=0):
    parts = (new, cached, write, output)
    if any(not isinstance(v, int) or v < 0 for v in parts):
        raise ValueError("Token counts must be non-negative integers")
    total = new + cached + write
    if total > model["context_window"] or output > model["max_output"]:
        raise ValueError("Token count exceeds model limits")
    rates = _rate(model, current)
    long_info = model["pricing"]["long_context"]
    long = total > long_info["threshold_input_tokens"]
    factors = long_info["multipliers"] if long else {k: 1 for k in ("input","cached_input","cache_write","output")}
    return ((new * rates["input"] * factors["input"] +
             cached * rates["cached_input"] * factors["cached_input"] +
             write * rates["cache_write"] * factors["cache_write"] +
             output * rates["output"] * factors["output"]) / 1000000)

def enrich_gpt6_astra_page(page, models_by_id):
    if 'id="sxf-astra-study"' in page:
        raise ValueError("Astra research layer already present")
    astra, sol = (models_by_id[k] for k in ("gpt-6-astra", "gpt-6.1-sol"))
    current = max("2026-11-10", astra["provenance"]["verified_at"], sol["provenance"]["verified_at"])
    for m in (astra, sol):
        if (m["context_window"], m["max_output"]) != (1050000, 128000):
            raise ValueError("Astra study needs a review of published token limits")
        pricing = m["pricing"]["long_context"]
        if pricing["threshold_input_tokens"] != 272000 or pricing["multipliers"] != {
            "input":2, "cached_input":2, "cache_write":2, "output":1.5
        }:
            raise ValueError("Astra study needs a review of the long-context contract")
    original_schema = re.search(r'<script type="application/ld\+json">(.+?)</script>', page, re.S)
    if not original_schema:
        raise ValueError("Astra missing base JSON-LD schema")
    schema = json.loads(original_schema.group(1))
    article = next(x for x in schema["@graph"] if x["@type"] == "TechArticle")
    article.update({"headline": TITLE.replace(" | SXF", ""),
                    "description": DESCRIPTION,
                    "dateModified": current,
                    "mainEntityOfPage": CANONICAL,
                    "isPartOf":{"@id":"https://sxf.si/#website"},
                    "citation":[
                       "https://developers.openai.com/api/docs/models/gpt-6-astra",
                       "https://developers.openai.com/api/docs/pricing",
                       "https://openai.com/index/gpt-6-astra/",
                       "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
                       DATASET
                    ]})
    schema["@graph"].append({"@type":"FAQPage","@id":CANONICAL+"#faq",
        "mainEntity":[{"@type":"Question","name":question,
        "acceptedAnswer":{"@type":"Answer","text":answer}} for question,answer in FAQ]})
    schema["@graph"].append({"@type":"Dataset","@id":DATASET+"#dataset",
        "name":"SXF GPT-6 Astra deterministic API cost scenarios — November 2026",
        "description":"Six hypothetical reproducible GPT-6 Astra and GPT-6.1 Sol Standard API pricing scenarios. Billing arithmetic only; no inference performance measurements.",
        "url":DATASET,"license":"https://creativecommons.org/licenses/by/4.0/",
        "datePublished":"2026-11-10","creator":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
        "measurementTechnique":"Deterministic computation using provider-published token pricing, long-context multipliers and fixed token counts.",
        "isBasedOn":"https://developers.openai.com/api/docs/pricing",
        "distribution":{"@type":"DataDownload","encodingFormat":"text/csv","contentUrl":DATASET}})
    rendered_schema = '<script type="application/ld+json">' + json.dumps(
        schema, ensure_ascii=False, separators=(",", ":")).replace("<", r"\u003c") + '</script>'
    page = _replace_once(page, r'<script type="application/ld\+json">.+?</script>', rendered_schema)
    for pattern, replacement in [
        (r"<title>.*?</title>", "<title>"+escape(TITLE)+"</title>"),
        (r'<meta name="description" content="[^"]*" />', '<meta name="description" content="'+escape(DESCRIPTION, quote=True)+'" />'),
        (r'<meta property="og:title" content="[^"]*" />', '<meta property="og:title" content="'+escape(TITLE,quote=True)+'" />'),
        (r'<meta property="og:description" content="[^"]*" />', '<meta property="og:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
        (r'<meta name="twitter:title" content="[^"]*" />', '<meta name="twitter:title" content="'+escape(TITLE,quote=True)+'" />'),
        (r'<meta name="twitter:description" content="[^"]*" />', '<meta name="twitter:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
    ]:
        page = _replace_once(page, pattern, replacement)

    with CONTENT.open(encoding="utf-8") as f:
        authored = f.read()
    records = [
        ("Short technical Q&A", 20000,0,0,4000),
        ("Cached agent workflow",12000,200000,0,4000),
        ("First-turn cache write",12000,0,200000,4000),
        ("272K exact boundary",272000,0,0,4000),
        ("272K plus one token",272001,0,0,4000),
        ("Long-context cached research",120000,200000,0,8000),
    ]
    rows=[]
    for label,new,cached,write,output in records:
        a = calculate(astra,current,new,cached,write,output)
        s = calculate(sol,current,new,cached,write,output)
        rows.append("<tr><th scope='row'>"+escape(label)+"</th>"+
                    "".join(f"<td>{v:,}</td>" for v in (new,cached,write,output))+
                    f"<td>${a:.5f}</td><td>${s:.5f}</td></tr>")
    # Verify the public CSV and visible table derive from the same scenario contract.
    import csv
    with (ROOT / "data/research/gpt6-astra-cost-lab-2026-11.csv").open(newline="",encoding="utf-8") as f:
        csv_rows=list(csv.DictReader(f))
    if len(csv_rows) != len(records):
        raise ValueError("SXF published CSV scenario count differs from the authored page")
    for row, (_,new,cached,write,output) in zip(csv_rows,records):
        if [int(row[k]) for k in ("uncached_input","cached_input","cache_write_input","output_tokens")] != [new,cached,write,output]:
            raise ValueError("SXF published CSV input scenario changed")
        if float(row["astra_usd"]) != round(calculate(astra,current,new,cached,write,output),5):
            raise ValueError("SXF public Astra CSV cost differs from catalog calculation")
        if float(row["sol_usd"]) != round(calculate(sol,current,new,cached,write,output),5):
            raise ValueError("SXF public Sol CSV cost differs from catalog calculation")
    a_rate,s_rate = _rate(astra,current),_rate(sol,current)
    tokens={"LAB_ROWS":"".join(rows),"FAQ_HTML":"".join(
        "<details><summary>"+escape(q)+"</summary><p>"+escape(a)+"</p></details>" for q,a in FAQ)}
    for label,rates in (("ASTRA",a_rate),("SOL",s_rate)):
        for suffix,field in (("INPUT","input"),("CACHED","cached_input"),("WRITE","cache_write"),("OUTPUT","output")):
            tokens[label+"_"+suffix]=str(rates[field])
    for key,value in tokens.items():
        token="{{"+key+"}}"
        if authored.count(token) != 1:
            raise ValueError("Astra missing/duplicate template token "+token)
        authored=authored.replace(token,value)
    page = _replace_once(page,r'(?=<section class="model-change-watch shell")', authored+"\n      ")
    page = _replace_once(page,r'<body class="intel-page model-page">','<body class="intel-page model-page astra-research-page">')
    page = _replace_once(page,r"(?=</head>)",'<link rel="stylesheet" href="/models/gpt-6-astra/research.css?v=20261110-mobile" />\n      ')
    page = _replace_once(page,r"(?=</body>)",'<script src="/models/gpt-6-astra/research.js" defer></script>')
    if "data-model-history" not in page or "data-model-evaluations" not in page:
        # Evaluations link is injected downstream by the main site generator.
        if "data-model-history" not in page:
            raise ValueError("Astra regression: original provenance module was lost")
    return page
