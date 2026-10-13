"""Durable, source-backed GPT-6 family guide.

Rendered from the same canonical model catalog that powers pricing and model cards.
Only enriches the family route /models/gpt-6/; preserves signals and model history.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTIAL = ROOT / "data/model-page-content/gpt-6-family.html"
URL = "https://sxf.si/models/gpt-6/"
TITLE = "GPT-6 Models: Astra vs Sol vs Luna, Pricing & API | SXF / AI"
DESCRIPTION = ("Compare GPT-6 Astra, GPT-6.1 Sol and Luna: verified API pricing, "
               "1.05M context, long-context costs, reasoning, tools and model-selection guidance.")
IDS = {"astra":"gpt-6-astra", "sol":"gpt-6.1-sol", "luna":"gpt-6-luna", "old_sol":"gpt-6-sol"}
LABELS = {"astra":"GPT-6 Astra", "sol":"GPT-6.1 Sol", "luna":"GPT-6 Luna"}
ROUTES = {"astra":"/models/gpt-6-astra/", "sol":"/models/gpt-6-1-sol/", "luna":"/models/gpt-6-luna/"}
FAQ = [["What is GPT-6?","GPT-6 is OpenAI's family of large-context reasoning models. Its current main choices are GPT-6 Astra for the hardest tasks, GPT-6.1 Sol for near-Astra work at lower cost, and GPT-6 Luna for efficient high-volume requests."],["Is GPT-6 one model or a family?","It is a family, not a single interchangeable API model ID. Use gpt-6-astra, gpt-6.1-sol, or gpt-6-luna; the earlier gpt-6-sol is separately documented."],["What is the latest GPT-6 Sol model?","GPT-6.1 Sol was introduced on September 29, 2026 as the updated middle-tier choice. Original GPT-6 Sol remains documented separately and may still matter for migrations or compatibility."],["How large is the GPT-6 context window?","GPT-6 Astra, GPT-6.1 Sol, and GPT-6 Luna each document a 1,050,000-token context window and up to 128,000 output tokens."],["How much does the GPT-6 API cost?","For Standard short-context text requests, Astra costs $10 per million input tokens and $50 per million output tokens; GPT-6.1 Sol costs $2 and $10; Luna costs $0.10 and $0.50. Cached input, cache writes and long-context rates differ."],["When does long-context GPT-6 pricing apply?","When prompt input exceeds 272,000 tokens, OpenAI's published long-context schedule applies to the entire request: twice the input and cache rates and 1.5 times the output rate."],["Which GPT-6 model should I use for coding?","Use GPT-6.1 Sol as a baseline for complex coding and agents, compare Astra on difficult or high-risk tasks, and test Luna on focused work. Verify cost per successful task using your own evaluation data."],["Does GPT-6 support image input and audio output?","The family models compared here accept text and image input and produce text output. They are not dedicated speech, realtime audio or video-generation models."],["Which GPT-6 models support none reasoning effort?","GPT-6 Luna and the original GPT-6 Sol support none. GPT-6 Astra and GPT-6.1 Sol support low, medium, high, xhigh and max but not none."],["Can GPT-6 use Chat Completions?","Chat Completions supports model-specific requests, but Responses is the recommended API for reasoning with tools. Astra and GPT-6.1 Sol require Responses for tool calling; the original Sol and Luna have more limited Chat Completions tool support."],["What changed between GPT-6 Sol and GPT-6.1 Sol?","GPT-6.1 Sol is a newer, more capable Sol model at the same Standard short-context $2 input and $10 output rates. Its cached input is $0.10 per million versus $0.20 for original GPT-6 Sol."],["Are token prices the total cost of a GPT-6 agent?","Not necessarily. Total costs can include uncached input, cached reads, cache writes, output, long-context tier, tool calls, selected processing mode, regional charges, retries and operations."],["Do all GPT-6 models have the same performance because they share 1.05M context?","No. The context and output numbers are serving limits, not quality scores. Compare factual accuracy, agent reliability, latency and downstream task outcomes across models."]]
SOURCES = [
    "https://developers.openai.com/api/docs/guides/latest-model",
    "https://developers.openai.com/api/docs/pricing",
    "https://developers.openai.com/api/docs/models/gpt-6-astra",
    "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
    "https://developers.openai.com/api/docs/models/gpt-6-luna",
    "https://developers.openai.com/api/docs/models/gpt-6-sol",
]


def standard(model, at_date):
    return next(p for p in model["pricing"]["standard"] if p["start"] <= at_date and
                (p.get("end") is None or at_date <= p["end"]))


def currency(value):
    return "$" + f"{value:.4f}".rstrip("0").rstrip(".")


def request_cost(model, date, input_tokens=0, cached_tokens=0, write_tokens=0, output_tokens=0):
    total = input_tokens + cached_tokens + write_tokens
    if total > model["context_window"] or output_tokens > model["max_output"]:
        raise ValueError("GPT-6 example outside published token limits")
    p = standard(model, date)
    long = total > model["pricing"]["long_context"]["threshold_input_tokens"]
    return (input_tokens * p["input"] * (2 if long else 1) +
            cached_tokens * p["cached_input"] * (2 if long else 1) +
            write_tokens * p["cache_write"] * (2 if long else 1) +
            output_tokens * p["output"] * (1.5 if long else 1)) / 1000000


def format_cost(value):
    return "$" + f"{value:.5f}".rstrip("0").rstrip(".") if value < .01 else "$" + f"{value:.4f}".rstrip("0").rstrip(".")


def sub_once(page, pattern, replacement):
    page, count = re.subn(pattern, lambda _: replacement, page, count=1, flags=re.S)
    if count != 1:
        raise ValueError("GPT-6 family page structure changed: " + pattern)
    return page


def enrich_gpt6_family_page(page, models_by_id):
    models = {key: models_by_id[mid] for key, mid in IDS.items()}
    for key in ("astra","sol","luna"):
        if models[key]["context_window"] != 1050000 or models[key]["max_output"] != 128000:
            raise ValueError("GPT-6 serving limits changed: reassess the family editorial reference")
    date = max("2026-10-13", *(model["provenance"]["verified_at"] for model in models.values()))
    prices = {key: standard(model, date) for key, model in models.items()}

    def table_row(key, long_context=False):
        p = prices[key]
        rates = [p["input"],p["cached_input"],p["cache_write"],p["output"]]
        if long_context:
            rates = [rates[0]*2,rates[1]*2,rates[2]*2,rates[3]*1.5]
        cells = "".join("<td>"+currency(rate)+"</td>" for rate in rates)
        return f'<tr><th scope="row"><a href="{ROUTES[key]}">{LABELS[key]}</a></th>{cells}</tr>'

    examples = [
        ("Short Q&A", "8K new input, 2K output", dict(input_tokens=8000,output_tokens=2000)),
        ("Cached agent", "100K new, 40K cached, 10K output", dict(input_tokens=100000,cached_tokens=40000,output_tokens=10000)),
        ("Long document", "300K new input, 20K output", dict(input_tokens=300000,output_tokens=20000)),
    ]
    example_rows = "".join(
        "<tr><th scope='row'>" + escape(title) + "<small class='gpt6-example-note'>" + escape(note) + "</small></th>"
        + "".join("<td>" + format_cost(request_cost(models[key],date,**tokens)) + "</td>"
                  for key in ("astra","sol","luna")) + "</tr>"
        for title,note,tokens in examples
    )
    calculator_rates = {
        key: {"input":p["input"],"cached":p["cached_input"],
              "writes":p["cache_write"],"output":p["output"]}
        for key,p in prices.items() if key != "old_sol"
    }
    replacements = {
        "ASTRA_INPUT":currency(prices["astra"]["input"]),
        "ASTRA_OUTPUT":currency(prices["astra"]["output"]),
        "SOL_INPUT":currency(prices["sol"]["input"]),
        "SOL_OUTPUT":currency(prices["sol"]["output"]),
        "LUNA_INPUT":currency(prices["luna"]["input"]),
        "LUNA_OUTPUT":currency(prices["luna"]["output"]),
        "SOL_CACHED":currency(prices["sol"]["cached_input"]),
        "OLD_SOL_CACHED":currency(prices["old_sol"]["cached_input"]),
        "ASTRA_CUTOFF":models["astra"]["knowledge_cutoff"],
        "SOL_CUTOFF":models["sol"]["knowledge_cutoff"],
        "LUNA_CUTOFF":models["luna"]["knowledge_cutoff"],
        "SHORT_ROWS":"".join(table_row(key) for key in ("astra","sol","luna")),
        "LONG_ROWS":"".join(table_row(key,True) for key in ("astra","sol","luna")),
        "RATES_JSON":escape(json.dumps(calculator_rates,separators=(",",":")),quote=True),
        "DEFAULT_ASTRA":format_cost(request_cost(models["astra"],date,input_tokens=8000,output_tokens=2000)),
        "DEFAULT_SOL":format_cost(request_cost(models["sol"],date,input_tokens=8000,output_tokens=2000)),
        "DEFAULT_LUNA":format_cost(request_cost(models["luna"],date,input_tokens=8000,output_tokens=2000)),
        "EXAMPLE_ROWS":example_rows,
        "FAQ_HTML":"".join("<details><summary>"+escape(q)+"</summary><p>"+escape(a)+"</p></details>"
                           for q,a in FAQ),
    }
    body = PARTIAL.read_text(encoding="utf-8").strip()
    for key,value in replacements.items():
        marker = "{{"+key+"}}"
        if marker not in body: raise ValueError("Missing GPT-6 template field: "+key)
        body = body.replace(marker,str(value))
    if "{{" in body: raise ValueError("Unresolved GPT-6 template placeholder")

    start = '<section class="model-reference shell">'
    end = '<section class="signal-layout shell">'
    if page.count(start) != 1 or page.count(end) != 1:
        raise ValueError("GPT-6 family base section markers changed")
    first = page.index(start)
    last = page.index(end,first)
    page = page[:first] + body + "\n      " + page[last:]

    graph = {
      "@context":"https://schema.org",
      "@graph":[
        {"@type":"CollectionPage","@id":URL+"#webpage","url":URL,"name":TITLE,"description":DESCRIPTION,
         "mainEntity":{"@id":URL+"#models"},"hasPart":{"@id":URL+"#guide"},
         "breadcrumb":{"@id":URL+"#breadcrumb"},"isPartOf":{"@id":"https://sxf.si/#website"},
         "dateModified":date,"inLanguage":"en"},
        {"@type":"ItemList","@id":URL+"#models","name":"GPT-6 Astra, GPT-6.1 Sol and GPT-6 Luna",
         "numberOfItems":3,"itemListElement":[
           {"@type":"ListItem","position":i+1,"name":LABELS[key],"url":"https://sxf.si"+ROUTES[key]}
           for i,key in enumerate(("astra","sol","luna"))]},
        {"@type":"TechArticle","@id":URL+"#guide",
         "headline":"GPT-6 models compared: Astra vs Sol vs Luna, API pricing and selection",
         "description":DESCRIPTION,"url":URL,"mainEntityOfPage":{"@id":URL+"#webpage"},
         "about":{"@id":URL+"#models"},"dateModified":date,
         "author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
         "publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
         "citation":SOURCES,"inLanguage":"en"},
        {"@type":"BreadcrumbList","@id":URL+"#breadcrumb","itemListElement":[
         {"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},
         {"@type":"ListItem","position":2,"name":"Models","item":"https://sxf.si/models/"},
         {"@type":"ListItem","position":3,"name":"GPT-6","item":URL}]},
        {"@type":"FAQPage","@id":URL+"#faq","mainEntity":[
          {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}}
          for q,a in FAQ]},
      ]}
    seo = [
      (r"<title>.*?</title>","<title>"+escape(TITLE)+"</title>"),
      (r'<meta name="description" content="[^"]*" />','<meta name="description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
      (r'<meta property="og:title" content="[^"]*" />','<meta property="og:title" content="'+escape(TITLE,quote=True)+'" />'),
      (r'<meta property="og:description" content="[^"]*" />','<meta property="og:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
      (r'<meta name="twitter:title" content="[^"]*" />','<meta name="twitter:title" content="'+escape(TITLE,quote=True)+'" />'),
      (r'<meta name="twitter:description" content="[^"]*" />','<meta name="twitter:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
      (r'<script type="application/ld\+json">.*?</script>',
       '<script type="application/ld+json">'+json.dumps(graph,separators=(",",":"),ensure_ascii=False).replace("<","\\u003c")+'</script>'),
      (r'<h1>GPT-6<br><span>reference & signals\.</span></h1><p>.*?</p>',
       '<h1>GPT-6 Models<br><span>Astra vs Sol vs Luna.</span></h1>'
       '<p>Compare GPT-6 Astra, GPT-6.1 Sol and Luna: verified pricing, 1.05M-token '
       'context, working token-cost examples, reasoning options and API guidance.</p>'),
      (r'<link rel="stylesheet" href="/intelligence\.css" />',
       '<link rel="stylesheet" href="/intelligence.css" />\n'
       '      <link rel="stylesheet" href="/models/gpt-6/family.css" />\n'
       '      <script src="/models/gpt-6/family.js" defer></script>'),
    ]
    for pattern,value in seo:
        page = sub_once(page,pattern,value)
    if page.count("data-gpt6-family") != 1 or page.count('rel="canonical" href="'+URL+'"') != 1:
        raise ValueError("GPT-6 SEO or body failed verification")
    return page
