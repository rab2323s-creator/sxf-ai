"""Durable original GPT-6 Sol dossier, pricing experiment and source-backed SEO.

The canonical model database is authoritative for model facts and rates.
Called after the generic model page is generated on every scheduled build.
"""
from __future__ import annotations

import csv
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data/model-page-content/gpt-6-sol.html"
CSV_PATH = ROOT / "data/research/gpt6-sol-cache-migration-2026-11.csv"
CANONICAL = "https://sxf.si/models/gpt-6-sol/"
DATASET = "https://sxf.si/data/research/gpt6-sol-cache-migration-2026-11.csv"
TITLE = "GPT-6 Sol: API Pricing, Benchmarks, Specs & 6.1 Comparison | SXF"
DESCRIPTION = ("GPT-6 Sol API pricing, 1.05M context, benchmarks, reasoning and GPT-6.1 Sol "
               "comparison. Explore SXF's original nine-scenario caching cost study.")
SOURCES = [
    "https://developers.openai.com/api/docs/models/gpt-6-sol",
    "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
    "https://developers.openai.com/api/docs/pricing",
    "https://developers.openai.com/api/docs/guides/prompt-caching",
    "https://openai.com/index/introducing-gpt-6-sol-and-luna/",
    DATASET,
]
FAQ = [
    ("What is GPT-6 Sol?", "GPT-6 Sol is the original OpenAI GPT-6 reasoning model released September 22, 2026 for complex coding and agentic tasks; its API model ID is gpt-6-sol."),
    ("What is the GPT-6 Sol model ID?", "The original model identifier is gpt-6-sol; GPT-6.1 Sol uses the distinct gpt-6.1-sol API identifier."),
    ("How much does GPT-6 Sol cost?", "At Standard short-context API prices per one million tokens, GPT-6 Sol costs $2 uncached input, $0.20 cached reads, $2.50 cache writes and $10 output. Long-context requests above 272,000 input tokens use higher rates across the whole request."),
    ("What is the GPT-6 Sol context window?", "GPT-6 Sol supports a 1,050,000-token context window and up to 128,000 output tokens. Actual response quality and output length depend on task and settings."),
    ("Is GPT-6.1 Sol the same as GPT-6 Sol?", "No. GPT-6.1 Sol is a newer September 29, 2026 release with a different model ID, lower cached-input rates and different reasoning/tool compatibility. The two models should not be treated as aliases."),
    ("Which GPT-6 Sol version is newer?", "GPT-6.1 Sol is newer than original GPT-6 Sol; compare the exact provider model IDs when migrating."),
    ("Is GPT-6.1 Sol cheaper than original GPT-6 Sol?", "The two models have identical Standard short-context uncached input, cache-write and output list rates, but GPT-6.1 Sol cached reads are $0.10 per million tokens versus $0.20 for original Sol. Actual savings depend on cache hit rate."),
    ("When does GPT-6 Sol long-context pricing apply?", "The higher long-context tier applies when total prompt input exceeds 272,000 tokens. Input and cache rates double and output increases by 50 percent for the entire request."),
    ("Does GPT-6 Sol support none reasoning effort?", "Yes. Original GPT-6 Sol supports none, low, medium, high, xhigh and max. GPT-6.1 Sol does not support none."),
    ("Does GPT-6 Sol support function calling?", "Yes. The Responses API supports function calling and built-in tools. OpenAI documents Chat Completions tool calling for original Sol only when reasoning_effort is set to none."),
    ("Can GPT-6 Sol process images?", "GPT-6 Sol accepts text and image inputs and produces text output, according to its OpenAI API model card."),
    ("What is GPT-6 Sol's knowledge cutoff?", "OpenAI lists April 20, 2026 as the original GPT-6 Sol knowledge cutoff."),
    ("What did SXF test for GPT-6 Sol?", "SXF published an original deterministic cost model across nine hypothetical token workloads, comparing original GPT-6 Sol and GPT-6.1 Sol rates. SXF did not conduct paid model-inference or quality benchmarks."),
    ("Are the benchmark numbers on this page independent?", "No. The AutomationBench, Agents' Last Exam and DeepSWE scores on this page are explicitly attributed to OpenAI's September 2026 launch report and are not presented as SXF's own independent results."),
    ("How do I use the GPT-6 Sol API?", "Use the OpenAI Responses API with model gpt-6-sol and a supported reasoning effort. Store the API key on the server or in an environment variable, not in browser source."),
    ("Is GPT-6 Sol available in ChatGPT?", "API availability and ChatGPT subscription availability are separate products. Consult current plan documentation rather than assuming an API model ID appears in all ChatGPT model selectors."),
]

SCENARIOS = [
    ("minimal", "Focused code review", 20000, 0, 0, 2000),
    ("cache-heavy", "200K repeated context", 12000, 200000, 0, 4000),
    ("cache-write", "Cache write first turn", 12000, 0, 200000, 4000),
    ("boundary-exact", "Exactly 272K input", 272000, 0, 0, 4000),
    ("boundary-plus-one", "272K + one input token", 272001, 0, 0, 4000),
    ("long-cache", "Long-context cache-heavy agent", 120000, 200000, 0, 8000),
    ("long-new", "Long document summarization", 400000, 0, 0, 20000),
    ("all-cached", "Fully cached short context", 0, 250000, 0, 2000),
    ("research-write", "Research cache construction", 90000, 50000, 50000, 18000),
]

def rate(model, date):
    valid = [row for row in model["pricing"]["standard"]
             if row["start"] <= date and (not row.get("end") or date <= row["end"])]
    if len(valid) != 1:
        raise ValueError("Original Sol research requires one active Standard rate per model")
    return valid[0]

def cost(model, date, new=0, cached=0, write=0, output=0):
    parts = (new, cached, write, output)
    if any(not isinstance(x, int) or x < 0 for x in parts):
        raise ValueError("Token counts must be whole and non-negative")
    total = new + cached + write
    if total > model["context_window"] or output > model["max_output"]:
        raise ValueError("Prompt exceeds model context or output limits")
    values = rate(model, date)
    lc = model["pricing"]["long_context"]
    long = total > lc["threshold_input_tokens"]
    multipliers = lc["multipliers"] if long else {k: 1 for k in ("input", "cached_input", "cache_write", "output")}
    return (
        new * values["input"] * multipliers["input"] +
        cached * values["cached_input"] * multipliers["cached_input"] +
        write * values["cache_write"] * multipliers["cache_write"] +
        output * values["output"] * multipliers["output"]
    ) / 1_000_000

def format_rate(value):
    return "$" + f"{value:.4f}".rstrip("0").rstrip(".")

def replace_one(html, pattern, replacement):
    html, count = re.subn(pattern, lambda _: replacement, html, count=1, flags=re.S)
    if count != 1:
        raise ValueError("GPT-6 Sol generation anchor not found: " + pattern)
    return html

def enrich_gpt6_sol_page(page, models_by_id):
    if 'id="sxf-sol-dossier"' in page:
        raise ValueError("Original Sol dossier already injected; refusing duplication")
    original, newer = (models_by_id[m] for m in ("gpt-6-sol", "gpt-6.1-sol"))
    date = max("2026-11-10", original["provenance"]["verified_at"], newer["provenance"]["verified_at"])
    for model in (original, newer):
        if (model["context_window"], model["max_output"]) != (1_050_000, 128_000):
            raise ValueError("Sol limits changed; editorial source review needed")
        lc = model["pricing"]["long_context"]
        if lc["threshold_input_tokens"] != 272000 or lc["multipliers"] != {
            "input": 2, "cached_input": 2, "cache_write": 2, "output": 1.5
        }:
            raise ValueError("Sol long-context pricing changed; editorial source review needed")
    old, new = rate(original, date), rate(newer, date)
    if not (old["cached_input"] == .2 and new["cached_input"] == .1):
        raise ValueError("Sol migration research conclusion changed; verify with provider")

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        records = list(csv.DictReader(f))
    if len(records) != len(SCENARIOS):
        raise ValueError("Sol published original dataset scenario count changed")
    table_rows=[]
    for row, (sid, label, new_input, cached, write, output) in zip(records,SCENARIOS):
        if (row["scenario_id"], row["scenario"]) != (sid,label):
            raise ValueError("Sol dataset scenario metadata changed")
        fields = [int(row[x]) for x in ("uncached_input","cached_input","cache_write_input","output_tokens")]
        if fields != [new_input,cached,write,output]:
            raise ValueError("Sol research CSV token counts diverge")
        a = cost(original,date,new_input,cached,write,output)
        b = cost(newer,date,new_input,cached,write,output)
        expected_tier = "long" if new_input+cached+write > 272000 else "short"
        if not all((row["tier"] == expected_tier, 
                    abs(float(row["original_sol_usd"])-a)<1e-8,
                    abs(float(row["sol_6_1_usd"])-b)<1e-8,
                    abs(float(row["saving_usd"])-(a-b))<1e-8)):
            raise ValueError("Sol published results diverge from canonical pricing data")
        table_rows.append(
            "<tr><th scope='row'>"+escape(label)+"</th>"+
            "".join("<td>"+f"{n:,}"+"</td>" for n in fields)+
            "<td>$"+f"{a:.6f}"+"</td><td>$"+f"{b:.6f}"+"</td><td>$"+f"{a-b:.6f}"+"</td></tr>"
        )
    content=CONTENT.read_text(encoding="utf-8")
    substitutions={
        "LAB_ROWS": "".join(table_rows),
        "FAQ_HTML": "".join("<details><summary>"+escape(q)+"</summary><p>"+escape(a)+"</p></details>" for q,a in FAQ),
    }
    for slug,modelrates in (("SOL",old),("NEW",new)):
        for label,key,multiplier in (("SHORT_INPUT","input",1),("SHORT_CACHED","cached_input",1),
                                     ("SHORT_WRITE","cache_write",1),("SHORT_OUTPUT","output",1),
                                     ("LONG_INPUT","input",2),("LONG_CACHED","cached_input",2),
                                     ("LONG_WRITE","cache_write",2),("LONG_OUTPUT","output",1.5)):
            substitutions[f"{slug}_{label}"]=format_rate(modelrates[key]*multiplier)
        for label,key in (("INPUT","input"),("CACHED","cached_input"),("WRITE","cache_write"),("OUTPUT","output")):
            substitutions[f"RATE_{slug}_{label}"]=str(modelrates[key])
    for key,value in substitutions.items():
        content=content.replace("{{"+key+"}}",value)
    if re.search(r"\{\{[^}]+\}\}",content):
        raise ValueError("Sol dossier unresolved source template tokens")

    ld=re.search(r'<script type="application/ld\+json">(.+?)</script>',page,re.S)
    if not ld:
        raise ValueError("Sol generic page lost original structured data")
    schema=json.loads(ld.group(1))
    article=next(n for n in schema["@graph"] if n["@type"]=="TechArticle")
    article.update({
        "headline":TITLE.replace(" | SXF",""),"description":DESCRIPTION,
        "mainEntityOfPage":CANONICAL,"dateModified":date,
        "citation":SOURCES,"isPartOf":{"@id":"https://sxf.si/#website"}
    })
    schema["@graph"].append({
        "@type":"FAQPage","@id":CANONICAL+"#faq",
        "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in FAQ],
    })
    schema["@graph"].append({
        "@type":"Dataset","@id":DATASET+"#dataset",
        "name":"SXF original GPT-6 Sol / GPT-6.1 Sol cache migration pricing scenarios",
        "description":"Nine hypothetical reproducible token-billing scenarios comparing original GPT-6 Sol and GPT-6.1 Sol. No inference/model quality tests were conducted.",
        "url":DATASET,"datePublished":"2026-11-10",
        "creator":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
        "isBasedOn":"https://developers.openai.com/api/docs/pricing",
        "measurementTechnique":"Deterministic recomputation of published token price schedules and long-context multipliers.",
        "distribution":{"@type":"DataDownload","encodingFormat":"text/csv","contentUrl":DATASET}
    })
    structured=json.dumps(schema,ensure_ascii=False,separators=(",",":")).replace("<",r"\u003c")
    page=replace_one(page,r'<script type="application/ld\+json">.+?</script>', '<script type="application/ld+json">'+structured+'</script>')
    for pattern,replacement in [
        (r"<title>.*?</title>","<title>"+escape(TITLE)+"</title>"),
        (r'<meta name="description" content="[^"]*" />','<meta name="description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
        (r'<meta property="og:title" content="[^"]*" />','<meta property="og:title" content="'+escape(TITLE,quote=True)+'" />'),
        (r'<meta property="og:description" content="[^"]*" />','<meta property="og:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
        (r'<meta name="twitter:title" content="[^"]*" />','<meta name="twitter:title" content="'+escape(TITLE,quote=True)+'" />'),
        (r'<meta name="twitter:description" content="[^"]*" />','<meta name="twitter:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
        (r'<body class="intel-page model-page">','<body class="intel-page model-page sol-research-page">'),
    ]:
        page=replace_one(page,pattern,replacement)
    page=replace_one(page,r'(?=<section class="model-change-watch shell")',content+"\n      ")
    page=replace_one(page,r"(?=</head>)",'<link rel="stylesheet" href="/models/gpt-6-sol/research.css?v=20261110-v1" />\n      ')
    page=replace_one(page,r"(?=</body>)",'<script src="/models/gpt-6-sol/research.js?v=20261110-v1" defer></script>')
    if page.count("<h1>")!=1 or "data-model-history" not in page:
        raise ValueError("Sol original index structure/regression failure")
    return page
