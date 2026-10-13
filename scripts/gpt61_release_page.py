"""GPT-6.1 release hub: source-backed editorial page, distinct from GPT-6.1 Sol card."""
from __future__ import annotations
import json
import re
from html import escape
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARTIAL=ROOT/"data/model-page-content/gpt-6-1-release.html"
URL="https://sxf.si/models/gpt-6-1/"
TITLE="GPT-6.1 Models, Release Date, What's New & Updates | SXF / AI"
DESCRIPTION=("GPT-6.1 release guide: officially available GPT-6.1 Sol, launch changes, "
             "coding benchmarks, migration from GPT-6 Sol, cached input savings and updates.")
FAQ=[
 ("What is GPT-6.1?","GPT-6.1 is the updated GPT-6 release that launched with GPT-6.1 Sol on September 29, 2026. OpenAI positions the newer Sol model for coding, computer use and complex professional work."),
 ("When did GPT-6.1 come out?","OpenAI announced GPT-6.1 Sol on September 29, 2026, including an official API model card and changelog entry."),
 ("Which GPT-6.1 model variants are available?","The official GPT-6.1 model documented in the sources reviewed here is GPT-6.1 Sol. The existence of GPT-6 Astra, GPT-6 Luna or original GPT-6 Sol does not make them GPT-6.1 variants."),
 ("Is there a GPT-6.1 Astra or GPT-6.1 Luna?","The cited public model documentation establishes GPT-6.1 Sol, not separately documented GPT-6.1 Astra or GPT-6.1 Luna API identities. Do not assume such model IDs work without an official release."),
 ("What is the GPT-6.1 API model ID?","Use gpt-6.1-sol. This page covers the release; the separate SXF GPT-6.1 Sol model reference contains the technical model details."),
 ("What changed from GPT-6 Sol to GPT-6.1 Sol?","OpenAI reports stronger coding, computer-use, multi-tool professional workflows and factuality on specified evaluations, with cached input rates reduced from $0.20 to $0.10 per million short-context tokens."),
 ("Is GPT-6.1 more expensive than GPT-6 Sol?","Standard short-context uncached input and output rates remain $2 and $10 per million tokens. The 6.1 Sol cached-input read rate is $0.10, half the original Sol's $0.20."),
 ("What is the GPT-6.1 Sol context window?","GPT-6.1 Sol has a 1,050,000-token input window and a 128,000-token maximum output, according to the official model card."),
 ("Can GPT-6.1 Sol use reasoning effort none?","No. The model supports low, medium, high, xhigh and max with medium as its default. Original GPT-6 Sol also supported none, so integrations must review this setting."),
 ("Can I use GPT-6.1 Sol with Chat Completions?","The API documentation supports Chat Completions without tool calling. For tools with GPT-6.1 Sol, use the Responses API."),
 ("How does long-context pricing work for GPT-6.1?","Requests with more than 272,000 input tokens use twice the input, cached input and cache-write rates plus 1.5 times the output rate across the whole request."),
 ("Is GPT-6.1 available in ChatGPT?","The September 29 launch said 6.1 Sol was available in the API, Codex and ChatGPT Work for eligible users, but not yet in Chat at launch. Treat that as a launch-day statement and verify current product availability."),
 ("Is GPT-6.1 Sol better than Astra?","OpenAI positions GPT-6.1 Sol near Astra for some demanding tasks at lower Standard list prices. The best model depends on quality, tool success, context, latency and cost per accepted task."),
 ("Where can I see full GPT-6.1 pricing and API examples?","Use the dedicated /models/gpt-6-1-sol/ model reference. This release page focuses on what changed and which GPT-6.1 editions are officially documented."),
]
SOURCES=[
 "https://openai.com/index/introducing-gpt-6-1-sol/",
 "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
 "https://developers.openai.com/api/docs/models/gpt-6-sol",
 "https://developers.openai.com/api/docs/changelog",
 "https://developers.openai.com/api/docs/pricing",
 "https://developers.openai.com/api/docs/guides/latest-model",
]
def fmt(v):return "$"+f"{v:.4f}".rstrip("0").rstrip(".")
def replace_once(page,pattern,replacement):
    page,n=re.subn(pattern,lambda m:replacement,page,count=1,flags=re.S)
    if n!=1:raise ValueError("GPT-6.1 release page marker changed: "+pattern)
    return page
def enrich_gpt61_release_page(page,models_by_id):
    old=models_by_id["gpt-6-sol"];new=models_by_id["gpt-6.1-sol"]
    p_old=old["pricing"]["standard"][0];p_new=new["pricing"]["standard"][0]
    if (p_old["cached_input"],p_new["cached_input"],p_new["input"],p_new["output"]) != (.2,.1,2,10):
        raise ValueError("GPT-6.1 rate changed; editorial review required")
    if new["context_window"] != 1050000 or new["max_output"] != 128000:
        raise ValueError("GPT-6.1 limits changed; editorial review required")
    template=PARTIAL.read_text(encoding="utf-8").strip()
    values={
      "CACHED_OLD":fmt(p_old["cached_input"]),
      "CACHED_NEW":fmt(p_new["cached_input"]),
      "INPUT_NEW":fmt(p_new["input"]),
      "OUTPUT_NEW":fmt(p_new["output"]),
      "CACHE_RATES_JSON":escape(json.dumps({"old":p_old["cached_input"],"current":p_new["cached_input"]},separators=(",",":")),quote=True),
      "DEFAULT_OLD_CACHE":fmt(100*p_old["cached_input"]),
      "DEFAULT_NEW_CACHE":fmt(100*p_new["cached_input"]),
      "DEFAULT_CACHE_SAVING":fmt(100*(p_old["cached_input"]-p_new["cached_input"])),
      "FAQ_HTML":"".join("<details><summary>"+escape(q)+"</summary><p>"+escape(a)+"</p></details>" for q,a in FAQ)
    }
    for key,value in values.items():
        if "{{"+key+"}}" not in template:raise ValueError("Missing release template variable: "+key)
        template=template.replace("{{"+key+"}}",str(value))
    if "{{" in template:raise ValueError("GPT-6.1 release template contains unfilled variables")
    start='      <section class="signal-layout shell">'
    if page.count(start)!=1:raise ValueError("GPT-6.1 signal layout boundary changed")
    page=page.replace(start,"      "+template+"\n\n"+start,1)
    graph={"@context":"https://schema.org","@graph":[
      {"@type":"CollectionPage","@id":URL+"#webpage","url":URL,"name":TITLE,"description":DESCRIPTION,
       "mainEntity":{"@id":URL+"#models"},"breadcrumb":{"@id":URL+"#breadcrumb"},
       "dateModified":"2026-10-13","inLanguage":"en","isPartOf":{"@id":"https://sxf.si/#website"}},
      {"@type":"ItemList","@id":URL+"#models","name":"Officially documented GPT-6.1 models",
       "numberOfItems":1,"itemListElement":[{"@type":"ListItem","position":1,"name":"GPT-6.1 Sol",
       "url":"https://sxf.si/models/gpt-6-1-sol/"}]},
      {"@type":"TechArticle","@id":URL+"#article","headline":TITLE,"description":DESCRIPTION,
       "mainEntityOfPage":{"@id":URL+"#webpage"},"about":{"@id":URL+"#models"},
       "datePublished":"2026-10-13","dateModified":"2026-10-13","url":URL,
       "author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
       "publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
       "citation":SOURCES,"inLanguage":"en"},
      {"@type":"BreadcrumbList","@id":URL+"#breadcrumb","itemListElement":[
       {"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},
       {"@type":"ListItem","position":2,"name":"Models","item":"https://sxf.si/models/"},
       {"@type":"ListItem","position":3,"name":"GPT-6.1","item":URL}]},
      {"@type":"FAQPage","@id":URL+"#faq","mainEntity":[
       {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in FAQ]},
    ]}
    fields=[
      (r"<title>.*?</title>","<title>"+escape(TITLE)+"</title>"),
      (r'<meta name="description" content="[^"]*" />','<meta name="description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
      (r'<meta property="og:title" content="[^"]*" />','<meta property="og:title" content="'+escape(TITLE,quote=True)+'" />'),
      (r'<meta property="og:description" content="[^"]*" />','<meta property="og:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
      (r'<meta name="twitter:title" content="[^"]*" />','<meta name="twitter:title" content="'+escape(TITLE,quote=True)+'" />'),
      (r'<meta name="twitter:description" content="[^"]*" />','<meta name="twitter:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
      (r'<script type="application/ld\+json">.*?</script>',
       '<script type="application/ld+json">'+json.dumps(graph,separators=(",",":"),ensure_ascii=False).replace("<","\\u003c")+'</script>'),
      (r'<h1>GPT-6\.1<br><span>release signals\.</span></h1>',
       '<h1>GPT-6.1 Models<br><span>release, changes &amp; updates.</span></h1>'),
      (r'<link rel="stylesheet" href="/intelligence\.css" />',
       '<link rel="stylesheet" href="/intelligence.css" />\n'
       '      <link rel="stylesheet" href="/models/gpt-6-1/release.css" />\n'
       '      <script src="/models/gpt-6-1/release.js" defer></script>'),
    ]
    for pattern,v in fields:page=replace_once(page,pattern,v)
    if page.count("data-gpt61-release-guide")!=1 or page.count('rel="canonical" href="'+URL+'"')!=1:
        raise ValueError("GPT-6.1 release SEO or canonical failed")
    return page
