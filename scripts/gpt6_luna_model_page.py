"""Source-verified, durable GPT-6 Luna editorial model page.

All money and model comparison data comes from the canonical model-pricing
catalog. Model change history, related signals and benchmark observations
remain part of the generated original page.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTIAL = ROOT / "data/model-page-content/gpt-6-luna.html"
CANONICAL = "https://sxf.si/models/gpt-6-luna/"
TITLE = "GPT-6 Luna: Pricing, 1.05M Context, API & Comparison | SXF / AI"
DESCRIPTION = (
    "GPT-6 Luna guide: $0.10 input/$0.50 output API pricing, 272K long-context "
    "rates, cost calculator, 1.05M context, reasoning and Luna vs Sol vs Astra."
)
IDS = {"luna": "gpt-6-luna", "sol": "gpt-6.1-sol", "astra": "gpt-6-astra"}
LABELS = {"luna": "GPT-6 Luna", "sol": "GPT-6.1 Sol", "astra": "GPT-6 Astra"}
FAQ = [
    ("What is GPT-6 Luna?", "GPT-6 Luna is OpenAI's efficient GPT-6 tier for focused reasoning and high-volume, cost-sensitive tasks. It accepts text and image input and generates text output."),
    ("How much does GPT-6 Luna cost?", "Standard API pricing for requests up to 272,000 input tokens is $0.10 input, $0.01 cached input, $0.125 cache write and $0.50 output per million tokens. Above 272K input tokens, rates increase across the entire request."),
    ("What is the GPT-6 Luna model ID?", "The exact API model ID is gpt-6-luna."),
    ("What is the GPT-6 Luna context window?", "1,050,000 input tokens with a maximum of 128,000 output tokens, according to OpenAI's published model card."),
    ("What happens above 272K input tokens?", "For a request with more than 272,000 input tokens, the whole request is billed at double the input and cache rates and 1.5 times the output rate. The trigger is strictly greater than 272K."),
    ("How much does a long-context Luna request cost?", "At Standard rates a request with 300,000 uncached input and 20,000 output tokens costs $0.075 before tool or regional-processing fees."),
    ("How does GPT-6 Luna compare with GPT-6.1 Sol?", "Luna has lower Standard token prices and is positioned for efficiency. GPT-6.1 Sol is the newer middle tier for more complex coding, agentic tasks and professional work. Test both on actual workloads to decide."),
    ("How does GPT-6 Luna compare with Astra?", "GPT-6 Astra targets the highest-capability GPT-6 tasks while Luna prioritizes lower per-token cost. Astra's Standard short-context uncached input and output rates are 100 times Luna's."),
    ("Does Luna support reasoning effort none?", "Yes. GPT-6 Luna supports none, low, medium, high, xhigh and max, with medium as the default."),
    ("Does GPT-6 Luna support the Responses API?", "Yes. The Responses API supports Luna reasoning and tools. In Chat Completions, function calling is supported with reasoning effort set to none."),
    ("What is GPT-6 Luna's knowledge cutoff?", "OpenAI publishes May 18, 2026 as the knowledge cutoff. Use retrieval or tools for information after that date."),
    ("Is GPT-6 Luna good for coding?", "It can be useful for focused, testable coding tasks. For complex multi-file debugging and high-risk changes, compare GPT-6.1 Sol or Astra using your own unit tests and acceptance criteria."),
    ("Does GPT-6 Luna accept images?", "Yes. Its published modalities include text and image input with text output; it is not a dedicated voice or video-generation endpoint."),
    ("Is GPT-6 Luna cheaper than GPT-6 Sol?", "On Standard short-context list rates, Luna is 20 times cheaper per uncached input and output token than both original GPT-6 Sol and newer GPT-6.1 Sol. Actual task cost depends on retries, reasoning, tools, caching and outcome quality."),
    ("Can I use prompt caching with Luna?", "Yes. OpenAI lists separate cached-input and cache-write rates. A cache hit and a cache write are not the same; monitor billed usage in your deployment."),
]
SOURCES = [
    "https://developers.openai.com/api/docs/models/gpt-6-luna",
    "https://developers.openai.com/api/docs/pricing",
    "https://developers.openai.com/api/docs/guides/latest-model",
    "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
    "https://developers.openai.com/api/docs/models/gpt-6-astra",
]


def active_standard(model, date):
    return next(
        row for row in model["pricing"]["standard"]
        if row["start"] <= date and (row.get("end") is None or row["end"] >= date)
    )


def rate_str(value):
    return "$" + f"{value:.4f}".rstrip("0").rstrip(".")


def total_cost(model, date, uncached=0, cached=0, write=0, output=0):
    prompt = uncached + cached + write
    if prompt > model["context_window"] or output > model["max_output"]:
        raise ValueError("GPT-6 Luna request exceeds the documented token limits")
    price = active_standard(model, date)
    long = prompt > model["pricing"]["long_context"]["threshold_input_tokens"]
    return (uncached * price["input"] * (2 if long else 1)
            + cached * price["cached_input"] * (2 if long else 1)
            + write * price["cache_write"] * (2 if long else 1)
            + output * price["output"] * (1.5 if long else 1)) / 1_000_000


def cost_str(amount):
    return "$" + f"{amount:.6f}".rstrip("0").rstrip(".") if amount < .01 else "$" + f"{amount:.4f}".rstrip("0").rstrip(".")


def replace_once(page, pattern, value):
    output, count = re.subn(pattern, lambda _: value, page, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"GPT-6 Luna generator marker missing: {pattern}")
    return output


def enrich_gpt6_luna_page(page, models_by_id):
    models = {key: models_by_id[model_id] for key, model_id in IDS.items()}
    luna = models["luna"]
    if luna["context_window"] != 1_050_000 or luna["max_output"] != 128_000:
        raise ValueError("GPT-6 Luna specifications changed: editorial review needed")
    for model in models.values():
        if model["pricing"]["long_context"]["threshold_input_tokens"] != 272_000:
            raise ValueError("GPT-6 long-context threshold changed: editorial review needed")
        if model["pricing"]["long_context"]["multipliers"] != {"input": 2, "cached_input": 2, "cache_write": 2, "output": 1.5}:
            raise ValueError("GPT-6 long-context multipliers changed: editorial review needed")
    date = max("2026-10-13", *(m["provenance"]["verified_at"] for m in models.values()))
    rates = {key: active_standard(model, date) for key, model in models.items()}

    luna_rows = "".join(
        "<tr><th scope='row'>" + label + "</th><td>" + rate_str(rates["luna"][name]) +
        "</td><td>" + rate_str(rates["luna"][name] * (1.5 if name == "output" else 2)) + "</td></tr>"
        for name, label in (("input", "Uncached input"), ("cached_input", "Cached input"), ("cache_write", "Cache write"), ("output", "Generated output"))
    )
    example_specs = [
        ("Simple classification", "8K input · 2K output", {"uncached": 8000, "output": 2000}),
        ("Repeated agent request", "100K new · 40K cached · 10K output", {"uncached": 100000, "cached": 40000, "output": 10000}),
        ("Large research input", "300K new input · 20K output", {"uncached": 300000, "output": 20000}),
        ("Heavy cached prefix", "12K new · 200K cached · 4K output", {"uncached": 12000, "cached": 200000, "output": 4000}),
    ]
    examples = "".join(
        "<tr><th scope='row'>" + escape(label) + "<small class='luna-example-note'>" + escape(note) +
        "</small></th>" + "".join(
            "<td>" + cost_str(total_cost(models[key], date, **spec)) + "</td>"
            for key in ("luna", "sol", "astra")
        ) + "</tr>"
        for label, note, spec in example_specs
    )
    rate_data = {
        key: {"input": p["input"], "cached": p["cached_input"], "write": p["cache_write"], "output": p["output"]}
        for key, p in rates.items()
    }
    fill = {
        "LUNA_INPUT":rate_str(rates["luna"]["input"]),
        "LUNA_OUTPUT":rate_str(rates["luna"]["output"]),
        "LUNA_LONG_INPUT":rate_str(rates["luna"]["input"] * 2),
        "LUNA_LONG_OUTPUT":rate_str(rates["luna"]["output"] * 1.5),
        "SOL_INPUT":rate_str(rates["sol"]["input"]),
        "SOL_OUTPUT":rate_str(rates["sol"]["output"]),
        "ASTRA_INPUT":rate_str(rates["astra"]["input"]),
        "ASTRA_OUTPUT":rate_str(rates["astra"]["output"]),
        "LUNA_RATE_ROWS":luna_rows,
        "EXAMPLE_ROWS":examples,
        "THRESHOLD_SHORT":cost_str(total_cost(luna,date,uncached=272000,output=2000)),
        "THRESHOLD_LONG":cost_str(total_cost(luna,date,uncached=272001,output=2000)),
        "DEFAULT_LUNA":cost_str(total_cost(luna,date,uncached=8000,output=2000)),
        "DEFAULT_SOL":cost_str(total_cost(models["sol"],date,uncached=8000,output=2000)),
        "DEFAULT_ASTRA":cost_str(total_cost(models["astra"],date,uncached=8000,output=2000)),
        "RATE_JSON":escape(json.dumps(rate_data,separators=(",",":")),quote=True),
        "FAQ_HTML":"".join("<details><summary>"+escape(q)+"</summary><p>"+escape(a)+"</p></details>" for q,a in FAQ),
    }
    body = PARTIAL.read_text(encoding="utf-8").strip()
    for field, value in fill.items():
        placeholder = "{{"+field+"}}"
        if placeholder not in body: raise ValueError("Missing Luna editorial placeholder: " + field)
        body = body.replace(placeholder,str(value))
    if "{{" in body: raise ValueError("Unresolved Luna editorial placeholder")

    start = '<section class="model-reference model-reference-deep shell">'
    end = '<section class="model-change-watch shell"'
    if page.count(start) != 1 or page.count(end) != 1:
        raise ValueError("GPT-6 Luna catalog template model boundaries changed")
    first = page.index(start)
    last = page.index(end, first)
    page = page[:first] + body + "\n\n      " + page[last:]

    graph = {
        "@context":"https://schema.org",
        "@graph":[
            {"@type":"TechArticle","@id":CANONICAL+"#article","headline":TITLE,
             "description":DESCRIPTION,"url":CANONICAL,"dateModified":date,
             "mainEntityOfPage":{"@id":CANONICAL+"#webpage"},"about":{"@id":CANONICAL+"#model"},
             "author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
             "publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
             "citation":SOURCES,"inLanguage":"en"},
            {"@type":"WebPage","@id":CANONICAL+"#webpage","url":CANONICAL,"name":TITLE,
             "description":DESCRIPTION,"mainEntity":{"@id":CANONICAL+"#model"},
             "breadcrumb":{"@id":CANONICAL+"#breadcrumb"},"inLanguage":"en"},
            {"@type":"SoftwareApplication","@id":CANONICAL+"#model","name":"GPT-6 Luna",
             "applicationCategory":"DeveloperApplication",
             "description":luna["positioning"],"url":CANONICAL,
             "creator":{"@type":"Organization","name":"OpenAI","url":"https://openai.com/"},
             "softwareHelp":"https://developers.openai.com/api/docs/models/gpt-6-luna",
             "additionalProperty":[
                 {"@type":"PropertyValue","name":"API model ID","value":"gpt-6-luna"},
                 {"@type":"PropertyValue","name":"Context window in tokens","value":luna["context_window"]},
                 {"@type":"PropertyValue","name":"Maximum output tokens","value":luna["max_output"]},
                 {"@type":"PropertyValue","name":"Knowledge cutoff","value":luna["knowledge_cutoff"]},
             ]},
            {"@type":"BreadcrumbList","@id":CANONICAL+"#breadcrumb","itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},
                {"@type":"ListItem","position":2,"name":"Models","item":"https://sxf.si/models/"},
                {"@type":"ListItem","position":3,"name":"GPT-6 Luna","item":CANONICAL},
            ]},
            {"@type":"FAQPage","@id":CANONICAL+"#faq",
             "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in FAQ]},
        ],
    }
    seo_fields = [
        (r"<title>.*?</title>", "<title>"+escape(TITLE)+"</title>"),
        (r'<meta name="description" content="[^"]*" />', '<meta name="description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
        (r'<meta property="og:title" content="[^"]*" />', '<meta property="og:title" content="'+escape(TITLE,quote=True)+'" />'),
        (r'<meta property="og:description" content="[^"]*" />', '<meta property="og:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
        (r'<meta name="twitter:title" content="[^"]*" />', '<meta name="twitter:title" content="'+escape(TITLE,quote=True)+'" />'),
        (r'<meta name="twitter:description" content="[^"]*" />', '<meta name="twitter:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
        (r'<script type="application/ld\+json">.*?</script>', '<script type="application/ld+json">'+json.dumps(graph,separators=(",",":"),ensure_ascii=False).replace("<","\\u003c")+'</script>'),
        (r'<h1>GPT-6 Luna<br><span>verified model reference\.</span></h1>',
         '<h1>GPT-6 Luna<br><span>pricing, context &amp; API guide.</span></h1>'),
        (r'<link rel="stylesheet" href="/intelligence\.css" />',
         '<link rel="stylesheet" href="/intelligence.css" />\n'
         '      <link rel="stylesheet" href="/models/gpt-6-luna/luna.css" />\n'
         '      <script src="/models/gpt-6-luna/luna.js" defer></script>'),
    ]
    for pattern, value in seo_fields:
        page = replace_once(page,pattern,value)
    if page.count("data-luna-reference") != 1 or page.count('rel="canonical" href="'+CANONICAL+'"') != 1:
        raise ValueError("GPT-6 Luna editorial SEO verification failed")
    return page
