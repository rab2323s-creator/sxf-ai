"""Gemini 3.8 Flash-Lite TTS: durable, source-driven model-page enrichment.

Uses the verified pricing catalog for 2026/2027 and keeps model history intact.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BODY = ROOT / "data/model-page-content/gemini-3-8-flash-lite-tts.html"
URL = "https://sxf.si/models/gemini-3-8-flash-lite-tts/"
TITLE = "Gemini 3.8 Flash-Lite TTS: Pricing, API & Comparison | SXF / AI"
DESCRIPTION = ("Gemini 3.8 Flash-Lite TTS guide: $6/M audio tokens, 2027 prices, "
               "Flash TTS comparison, voice API example and audio cost calculator.")
FAQ = [
 ("What is Gemini 3.8 Flash-Lite TTS?", "It is Google's production text-to-speech model for high-volume, low-latency and cost-efficient speech synthesis. It takes text input and generates audio."),
 ("What is the Gemini 3.8 Flash-Lite TTS model ID?", "Use gemini-3.8-flash-lite-tts in the Gemini API Interactions speech-generation endpoint."),
 ("How much does Gemini 3.8 Flash-Lite TTS cost?", "Paid Standard pricing through December 31, 2026 is $0.50 per million text input tokens and $6 per million audio output tokens. From January 1, 2027, the listed rates are $1 input and $12 audio output."),
 ("How much does a minute of Flash-Lite TTS audio cost?", "Google lists 25 generated audio tokens per second. At the 2026 Standard $6 per million audio output tokens, a 60-second result uses roughly 1,500 audio tokens, costing $0.009 for audio before transcript-input charges."),
 ("Is Flash-Lite TTS cheaper than Flash TTS?", "Yes. Its Standard audio output costs $6 per million tokens through December 2026 versus $9 for Flash TTS, or one-third less for the same generated audio tokens. Text input is the same rate on both models."),
 ("What happens to Flash-Lite pricing in January 2027?", "Google's published Standard schedule changes to $1 per million text input tokens and $12 per million audio output tokens from January 1, 2027. The corresponding Flash TTS audio rate is $18."),
 ("What is the difference between Flash-Lite TTS and Flash TTS?", "Flash-Lite targets low latency, high throughput and cost-sensitive speech. Flash TTS targets maximum fidelity, nuanced acting and complex narration. Flash-Lite supports 101 languages, while Flash supports 130."),
 ("How many languages does Flash-Lite TTS support?", "Google documents 101 supported languages and automatic language detection. Evaluate pronunciation for your particular language, voice, dialect and script."),
 ("What are the context and output limits?", "Google lists 8,192 input tokens and 16,384 output serving tokens for Gemini 3.8 Flash-Lite TTS."),
 ("Does Flash-Lite support multi-speaker speech?", "Google documents structured speaker metadata for up to two prebuilt-voice speakers per request. For custom voices or more than two characters, use separate synthesis calls as appropriate."),
 ("How do I control speaking style?", "Use speech_metadata.style annotations for turn-level delivery. Use inline audio tags such as <short pause> for point-in-time events rather than writing plain stage directions in the spoken text."),
 ("What audio format does the API return?", "The default complete-request output is WAV with its RIFF header included. Chunked streaming uses raw 16-bit, 24-kHz mono PCM by default; other output formats can be requested."),
 ("Can I use Gemini 3.8 Flash-Lite TTS for voice agents?", "Yes, as the speech-output stage of a voice-agent pipeline. It is not the Gemini Live API: ASR, agent reasoning and live interaction are separate components."),
 ("Does Flash-Lite TTS support prompt caching?", "The Google price list shows cached-input pricing, but the model card lists caching as unsupported. Do not count on a caching discount until Google documents support for the exact model and endpoint."),
 ("Can I use Google Batch or Flex pricing for Flash-Lite?", "Google lists paid Batch and Flex serving rates for Gemini 3.8 Flash-Lite TTS. Check availability, processing behavior and your account eligibility before choosing a tier."),
 ("Should I use Flash-Lite TTS for audiobooks?", "Flash-Lite is cost-efficient for substantial narration, but Flash TTS is positioned for higher-fidelity long-form reading, difficult pronunciations and expressive characters. Compare both on representative listening samples."),
 ("What model replaces gemini-3.1-flash-tts-preview?", "Google describes Gemini 3.8 Flash-Lite TTS as its production successor. Migration requires attention to structured speech metadata, output formats and voice settings."),
]
SOURCES = [
 "https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-lite-tts",
 "https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts",
 "https://ai.google.dev/gemini-api/docs/pricing",
 "https://ai.google.dev/gemini-api/docs/speech-generation",
]

def money(x):
    return "$" + f"{x:.6f}".rstrip("0").rstrip(".") if x < .01 else "$" + f"{x:.4f}".rstrip("0").rstrip(".")

def active_price(model, date):
    return next(p for p in model["pricing"]["standard"] if p["start"] <= date and
                (not p.get("end") or date <= p["end"]))

def api_tier(standard, tier):
    # Published rate-card relationships for this Google TTS family.
    factor = {"standard":1, "batch":.5, "flex":.5, "priority":1.8}[tier]
    return {"input":standard["input"]*factor, "output":standard["output"]*factor}

def estimate(model, date, minutes, text_tokens=0, tier="standard"):
    p = api_tier(active_price(model,date), tier)
    return minutes * 60 * 25 * p["output"] / 1000000 + text_tokens * p["input"] / 1000000

def replace_one(page, pattern, replacement):
    page, count = re.subn(pattern, lambda _: replacement, page, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Flash-Lite TTS generator marker changed: "+pattern)
    return page

def enrich_gemini_38_flash_lite_tts_page(page, models_by_id):
    lite = models_by_id["gemini-3.8-flash-lite-tts"]
    flash = models_by_id["gemini-3.8-flash-tts"]
    for m in (lite,flash):
        if m["context_window"] != 8192 or m["max_output"] != 16384:
            raise ValueError("TTS model serving limits changed; editorial audit required")
        if m["modalities"] != {"input":["text"],"output":["audio"]}:
            raise ValueError("TTS model modality contract changed")
    # Explicitly keep 2026 effective and 2027 future rates separate.
    p26, p27 = {key:(active_price(m,"2026-10-13"),active_price(m,"2027-01-01"))
                 for key,m in (("lite",lite),("flash",flash))}.values()
    # Dict insertion order above is intentional: Lite then Flash.
    lite26, lite27 = p26
    flash26, flash27 = p27
    if (lite26["output"], lite27["output"], flash26["output"], flash27["output"]) != (6,12,9,18):
        raise ValueError("Provider's TTS pricing schedule changed; editorial audit required")
    rate_map = {
       date: {tier: {key:api_tier(price,tier) for key,price in
                      (("lite",current_lite),("flash",current_flash))}
              for tier in ("standard","batch","flex","priority")}
       for date,current_lite,current_flash in
       (("2026",lite26,flash26),("2027",lite27,flash27))
    }
    rows = "".join(
       "<tr><th scope='row'>"+name+"</th><td>"+money(rate_map["2026"][tier]["lite"]["input"])+
       "</td><td>"+money(rate_map["2026"][tier]["lite"]["output"])+
       "</td><td>"+money(rate_map["2027"][tier]["lite"]["input"])+
       "</td><td>"+money(rate_map["2027"][tier]["lite"]["output"])+
       "</td></tr>"
       for tier,name in (("standard","Standard"),("batch","Batch"),("flex","Flex"),("priority","Priority"))
    )
    durations = [(1,"1 minute"),(10,"10 minutes"),(60,"1 hour"),(600,"10 hours"),(6000,"100 hours")]
    sample_rows = "".join(
       "<tr><th scope='row'>"+label+"</th><td>"+f"{round(m*60*25):,}"+
       "</td><td>"+money(estimate(lite,"2026-10-13",m))+
       "</td><td>"+money(estimate(flash,"2026-10-13",m))+
       "</td><td>"+money(estimate(lite,"2027-01-01",m))+"</td></tr>"
       for m,label in durations
    )
    replacements = {
       "LITE_2026_IN":money(lite26["input"]),
       "LITE_2026_OUT":money(lite26["output"]),
       "FLASH_2026_OUT":money(flash26["output"]),
       "LITE_2027_IN":money(lite27["input"]),
       "LITE_2027_OUT":money(lite27["output"]),
       "FLASH_2027_OUT":money(flash27["output"]),
       "LITE_2026_CACHE":money(lite26["cached_input"]),
       "LITE_2027_CACHE":money(lite27["cached_input"]),
       "LITE_2026_TEN_SEC":money(estimate(lite,"2026-10-13",10/60)),
       "LITE_MINUTE_2026":money(estimate(lite,"2026-10-13",1)),
       "FLASH_MINUTE_2026":money(estimate(flash,"2026-10-13",1)),
       "LITE_1000_TEXT_2026":money(1000*lite26["input"]/1000000),
       "PRICING_TIERS":rows,
       "COST_EXAMPLES":sample_rows,
       "CALCULATOR_RATES":escape(json.dumps(rate_map,separators=(",",":")),quote=True),
       "EXAMPLE_LITE":money(estimate(lite,"2026-10-13",60,12000)),
       "EXAMPLE_FLASH":money(estimate(flash,"2026-10-13",60,12000)),
       "EXAMPLE_SAVED":money(estimate(flash,"2026-10-13",60,12000)-estimate(lite,"2026-10-13",60,12000)),
       "FAQ_HTML":"".join("<details><summary>"+escape(q)+"</summary><p>"+escape(a)+"</p></details>" for q,a in FAQ),
    }
    body = BODY.read_text(encoding="utf-8").strip()
    for key,value in replacements.items():
        marker = "{{"+key+"}}"
        if marker not in body: raise ValueError("Missing TTS field: "+key)
        body = body.replace(marker,str(value))
    if "{{" in body: raise ValueError("Unfilled Flash-Lite template marker")
    start = '      <section class="model-reference model-reference-deep shell">'
    end = '      <section class="model-change-watch shell"'
    if page.count(start) != 1 or page.count(end) != 1:
        raise ValueError("Flash-Lite model section markers changed")
    a = page.index(start)
    b = page.index(end,a)
    page = page[:a] + "      " + body + "\n\n" + page[b:]
    graph = {
      "@context":"https://schema.org",
      "@graph":[
        {"@type":"TechArticle","@id":URL+"#article","headline":TITLE,"description":DESCRIPTION,
         "url":URL,"dateModified":"2026-10-13","inLanguage":"en",
         "mainEntityOfPage":{"@id":URL+"#webpage"},"about":{"@id":URL+"#model"},
         "author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
         "publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
         "citation":SOURCES},
        {"@type":"WebPage","@id":URL+"#webpage","url":URL,"name":TITLE,"description":DESCRIPTION,
         "breadcrumb":{"@id":URL+"#breadcrumb"},"mainEntity":{"@id":URL+"#model"},"inLanguage":"en"},
        {"@type":"SoftwareApplication","@id":URL+"#model","name":"Gemini 3.8 Flash-Lite TTS",
         "applicationCategory":"DeveloperApplication","creator":{"@type":"Organization","name":"Google","url":"https://ai.google.dev/"},
         "url":URL,"description":lite["positioning"],
         "softwareHelp":SOURCES[0],
         "additionalProperty":[
            {"@type":"PropertyValue","name":"API model ID","value":"gemini-3.8-flash-lite-tts"},
            {"@type":"PropertyValue","name":"Input token limit","value":8192},
            {"@type":"PropertyValue","name":"Output serving token limit","value":16384},
            {"@type":"PropertyValue","name":"Output modality","value":"audio"},
          ]},
        {"@type":"BreadcrumbList","@id":URL+"#breadcrumb","itemListElement":[
            {"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},
            {"@type":"ListItem","position":2,"name":"Models","item":"https://sxf.si/models/"},
            {"@type":"ListItem","position":3,"name":"Gemini 3.8 Flash-Lite TTS","item":URL}]},
        {"@type":"FAQPage","@id":URL+"#faq","mainEntity":[
            {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}}
            for q,a in FAQ]},
      ]}
    fields = [
      (r"<title>.*?</title>", "<title>"+escape(TITLE)+"</title>"),
      (r'<meta name="description" content="[^"]*" />',
       '<meta name="description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
      (r'<meta property="og:title" content="[^"]*" />',
       '<meta property="og:title" content="'+escape(TITLE,quote=True)+'" />'),
      (r'<meta property="og:description" content="[^"]*" />',
       '<meta property="og:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
      (r'<meta name="twitter:title" content="[^"]*" />',
       '<meta name="twitter:title" content="'+escape(TITLE,quote=True)+'" />'),
      (r'<meta name="twitter:description" content="[^"]*" />',
       '<meta name="twitter:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
      (r'<script type="application/ld\+json">.*?</script>',
       '<script type="application/ld+json">'+json.dumps(graph,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+'</script>'),
      (r'<h1>Gemini 3.8 Flash-Lite TTS<br><span>verified model reference\.</span></h1>',
       '<h1>Gemini 3.8 Flash-Lite TTS<br><span>pricing, API &amp; comparison.</span></h1>'),
      (r'<link rel="stylesheet" href="/intelligence\.css" />',
       '<link rel="stylesheet" href="/intelligence.css" />\n'
       '      <link rel="stylesheet" href="/models/gemini-3-8-flash-lite-tts/lite.css" />\n'
       '      <script src="/models/gemini-3-8-flash-lite-tts/lite.js" defer></script>'),
    ]
    for pattern,replacement in fields:
        page=replace_one(page,pattern,replacement)
    if page.count('data-flash-lite-tts-guide') != 1 or page.count('rel="canonical" href="'+URL+'"') != 1:
        raise ValueError("Flash-Lite TTS SEO verification failed")
    return page
