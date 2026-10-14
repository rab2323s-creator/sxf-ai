"""Keep the Mistral Large 4 editorial page in automatic regenerations."""
import json
import re
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT = ROOT / "data/model-page-content/mistral-large-4-seo.html"
URL = "https://sxf.si/models/mistral-large-4/"
TITLE = "Mistral Large 4: Pricing, API, 1M Context & Features | SXF / AI"
DESCRIPTION = "Mistral Large 4 pricing guide: 1M context, 50% launch offer, API Python examples, reasoning, vision, benchmarks, comparison and verified Mistral sources."

def enrich_mistral_large_4(page, model):
    today = date.today().isoformat()
    periods = model["pricing"]["standard"]
    current = next((p for p in periods if p["start"] <= today and (not p.get("end") or today <= p["end"])), periods[-1])
    intro = periods[0]
    current_phase = "Launch offer" if current == intro else "Regular rates"
    replacement = {
        "{{CURRENT_INPUT}}": f'${current["input"]:.2f}',
        "{{CURRENT_CACHED}}": f'${current["cached_input"]:.2f}',
        "{{CURRENT_OUTPUT}}": f'${current["output"]:.2f}',
        "{{CURRENT_PHASE}}": current_phase,
        "{{PRICE_STATUS}}": ("Launch-period discounted rates apply through October 19, 2026." if current == intro else "Launch discount has ended; regular rates apply according to the tracked schedule."),
    }
    fragment = FRAGMENT.read_text(encoding="utf-8")
    for key, value in replacement.items():
        fragment = fragment.replace(key, value)
    if "{{" in fragment:
        raise ValueError("Unresolved Mistral Large 4 pricing placeholder")
    if page.count("</main>") != 1:
        raise ValueError("Expected one closing main tag")
    page = page.replace("</main>", fragment + "\n</main>", 1)
    page = page.replace("</head>", '<link rel="stylesheet" href="/models/mistral-large-4/reference.css" />\n</head>', 1)
    safe_title, safe_description = escape(TITLE, quote=True), escape(DESCRIPTION, quote=True)
    page = re.sub(r"<title>.*?</title>", "<title>" + safe_title + "</title>", page, count=1, flags=re.S)
    page = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m:m[1]+safe_description+m[2],page,count=1)
    for prop, value in (("og:title",safe_title),("twitter:title",safe_title),("og:description",safe_description),("twitter:description",safe_description)):
        page = re.sub(r'(<meta (?:property|name)="' + re.escape(prop) + r'" content=")[^"]*(")',lambda m:m[1]+value+m[2],page,count=1)
    page = page.replace("verified model reference.</span>", "pricing, API &amp; features.</span>", 1)
    faq = [
        ("What is Mistral Large 4?", "Mistral Large 4 is Mistral AI's October 2026 multimodal Mixture-of-Experts model in Public Preview. It supports text and image inputs, text outputs, reasoning, structured outputs and tool-connected workflows."),
        ("How much does Mistral Large 4 cost per million tokens?", "Launch-period Standard prices are $0.68 input, $0.07 cached input and $2.09 output per million tokens through October 19, 2026 in SXF's verified rate schedule. From October 20 the listed regular rates are $1.36, $0.14 and $4.18 respectively. Confirm current pricing with Mistral before purchase."),
        ("What is the Mistral Large 4 context window?", "The official model card lists a 1,000,000-token context window. This describes the model's context capacity, not a guarantee of perfect long-document recall or a separately published maximum output size."),
        ("What is the Mistral Large 4 API model ID?", "The public-preview API is listed as mistral-large-4 in Mistral's launch changelog and model card. Reasoning documentation also mentions a versioned mistral-large-4-0 identifier. Check availability in your own Mistral Studio account."),
        ("Is Mistral Large 4 open source or downloadable?", "Mistral announced open-weight plans for later in October 2026. At this review, the announcement is not proof of a downloadable release, and no license or hardware requirement should be assumed without an official weights publication."),
        ("Does Mistral Large 4 support images and PDF analysis?", "Yes. Mistral lists multimodal text-and-image understanding and document Q&A. Production PDF handling should follow the documented API input type, with extracted results validated against source documents."),
        ("Does Mistral Large 4 support function calling and JSON outputs?", "Yes. The official model card lists function calling, structured outputs, built-in tools and supported agent/conversation endpoints."),
        ("Can I use Mistral Large 4 from Python?", "Yes. Install the mistralai SDK, set your MISTRAL_API_KEY variable and use client.chat.complete with model=mistral-large-4. See the runnable example above."),
        ("What is the difference between Mistral Large 4 and Mistral Medium 3.5?", "Mistral Large 4 is a newer Public Preview model with a 1M context window. Mistral Medium 3.5 is a generally available coding and agent model with a 256K window. Compare cost, latency and task-level quality before choosing."),
        ("Is Mistral Large 4 ready for production?", "It is accessible as a public preview, but Mistral's lifecycle policy allows preview models to receive updates and does not guarantee a transition to general availability. Use regression tests, controlled rollouts and fallback strategies."),
    ]
    sources = ["https://docs.mistral.ai/models/mistral-large-4-0","https://mistral.ai/news/mistral-large-4/","https://docs.mistral.ai/resources/changelogs","https://docs.mistral.ai/inference/pricing","https://docs.mistral.ai/studio/conversations/reasoning","https://docs.mistral.ai/inference/model-lifecycle"]
    graph = [
        {"@type":"WebPage","@id":URL+"#webpage","url":URL,"name":TITLE,"description":DESCRIPTION,"inLanguage":"en","isPartOf":{"@id":"https://sxf.si/#website"},"mainEntity":{"@id":URL+"#article"},"breadcrumb":{"@id":URL+"#breadcrumb"}},
        {"@type":"TechArticle","@id":URL+"#article","headline":TITLE.split(" | ")[0],"description":DESCRIPTION,"url":URL,"mainEntityOfPage":{"@id":URL+"#webpage"},"dateModified":"2026-10-14","author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},"publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},"about":{"@type":"Thing","name":"Mistral Large 4","sameAs":sources[0]},"citation":sources,"inLanguage":"en"},
        {"@type":"BreadcrumbList","@id":URL+"#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},{"@type":"ListItem","position":2,"name":"Models","item":"https://sxf.si/models/"},{"@type":"ListItem","position":3,"name":"Mistral Large 4","item":URL}]},
        {"@type":"FAQPage","@id":URL+"#faq","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}
    ]
    schema = json.dumps({"@context":"https://schema.org","@graph":graph},ensure_ascii=False)
    page, count = re.subn(r'<script type="application/ld\+json">.*?</script>',lambda _: '<script type="application/ld+json">'+schema+'</script>',page,count=1,flags=re.S)
    if count != 1:
        raise ValueError("Mistral Large 4 JSON-LD block not found")
    return page
