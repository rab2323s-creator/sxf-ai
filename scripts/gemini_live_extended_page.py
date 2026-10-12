"""Editorial enrichment for one verified Gemini Live model reference.

Applied after catalog rendering; keeps the existing slug, facts, and history.
"""
import json
import re
from html import escape

TITLE = "Gemini 3.8 Live Extended Thinking: API, Pricing & Voice Agents | SXF / AI"
DESCRIPTION = "Gemini 3.8 Live Extended Thinking guide: Live API model ID, 131K context, voice pricing, async tools, thinking levels and Gemini 3.8 Live comparison."
HERO = "Google's real-time voice model for complex agent conversations: background reasoning, streaming speech and non-blocking function calls. Explore Live API setup, pricing, limits and when to use it."
CANONICAL = "https://sxf.si/models/gemini-3-8-live-extended-thinking/"
FAQS = [["What is Gemini 3.8 Live Extended Thinking?","It is Google's high-reasoning Live API audio-to-audio model for real-time voice agents that plan multi-step work and call asynchronous tools while continuing the conversation."],["What is the exact API model ID?","Use gemini-3.8-live-extended-thinking in the Gemini Live API. It is a separate endpoint from gemini-3.8-live."],["What is its context window?","Google publishes a 131,072-token input limit and a 65,536-token output limit."],["How much does Gemini 3.8 Live Extended Thinking cost?","Google's paid Standard rates are $0.75 per million text input tokens and $4.50 per million text output tokens; audio costs $3 input and $12 output per million audio tokens. Image/video input is $1 per million tokens. The output rates include thinking tokens."],["Does it support background thinking and async tools?","Yes. Set thinking_level to low, medium or high; minimal is unsupported. Function declarations must use NON_BLOCKING behavior."],["How is Extended Thinking different from Gemini 3.8 Live?","Gemini 3.8 Live prioritizes low-latency direct dialogue. Extended Thinking adds configurable background reasoning and requires interaction_status to decide whether the entire request has finished."],["Does turnComplete mean the session is idle?","Not necessarily. During background reasoning an utterance may finish while interaction_status remains IN_PROGRESS; wait for IDLE before treating the full task as complete."],["Does the model support caching, Batch API or structured outputs?","No. Google's model card lists caching, Batch API and structured outputs as unsupported for this endpoint."]]
SECTIONS = "\n        <section class=\"model-deep-section\" id=\"overview\" data-gemini-live-extended-guide>\n          <div class=\"model-section-head\"><p class=\"eyebrow\">QUICK ANSWER</p><h2>What is Gemini 3.8 Live Extended Thinking?</h2></div>\n          <p>Gemini 3.8 Live Extended Thinking is Google's high-reasoning, real-time voice model for conversations that need more than quick spoken answers. It streams audio while working through multi-step requests and executing asynchronous functions in the background. Developers access it through the Gemini Live API using the model ID <code>gemini-3.8-live-extended-thinking</code>.</p>\n          <p>The main distinction is <strong>background reasoning without treating every spoken pause as the end of a request</strong>. A voice agent can acknowledge the user, call an external tool, and continue speaking as results arrive. Google's model card lists a 131,072-token input limit, 65,536-token output limit, text/image/audio/video input and text/audio output.</p>\n          <nav class=\"model-related-links\" aria-label=\"Page sections\">\n            <a href=\"#pricing-breakdown\"><span>PRICING</span><strong>Text, audio and video rates</strong><b>↗</b></a>\n            <a href=\"#live-api-integration\"><span>LIVE API</span><strong>Async setup and session status</strong><b>↗</b></a>\n            <a href=\"#live-model-comparison\"><span>COMPARISON</span><strong>Extended Thinking vs Live</strong><b>↗</b></a>\n          </nav>\n        </section>\n\n        <section class=\"model-deep-section\" id=\"features\">\n          <div class=\"model-section-head\"><p class=\"eyebrow\">CORE CAPABILITIES</p><h2>How background reasoning changes a voice agent.</h2></div>\n          <div class=\"model-capability-grid\">\n            <article><span>CONTINUOUS SPEECH</span><h3>Audio while work continues</h3><p>Intermediate spoken updates can keep a user informed while the model reasons or waits for an external service, instead of forcing a silent pause for every tool call.</p></article>\n            <article><span>THINKING LEVELS</span><h3>Low, medium or high</h3><p>Configure reasoning depth with <code>thinking_config</code> and <code>thinking_level</code>. The <code>minimal</code> level is not supported for this model.</p></article>\n            <article><span>TOOL EXECUTION</span><h3>Async-only function calling</h3><p>Declare functions with <code>behavior: NON_BLOCKING</code>. Synchronous blocking declarations are not supported, which matters when migrating an existing Live integration.</p></article>\n            <article><span>SESSION LIFECYCLE</span><h3>Watch interaction status</h3><p>An audio message ending with <code>turnComplete</code> does not always mean the full job is finished. <code>IN_PROGRESS</code> and <code>IDLE</code> identify active background work and true completion.</p></article>\n          </div>\n        </section>\n\n        <section class=\"model-deep-section\" id=\"pricing-breakdown\">\n          <div class=\"model-section-head\"><p class=\"eyebrow\">GEMINI LIVE API PRICING</p><h2>Gemini 3.8 Live Extended Thinking pricing by modality.</h2><p>Google lists Standard paid API rates in USD. A voice session can combine audio, text, and image/video usage, so a text-only calculator does not reflect the whole bill.</p></div>\n          <div class=\"model-capability-grid\">\n            <article><span>TEXT TOKENS</span><h3>$0.75 in / $4.50 out</h3><p>Per one million text tokens. Output pricing includes thinking tokens, so deeper reasoning can affect usage.</p></article>\n            <article><span>AUDIO TOKENS</span><h3>$3 in / $12 out</h3><p>Per one million audio tokens. Google's pricing page also gives $0.005 per minute of input audio and $0.018 per minute of output audio.</p></article>\n            <article><span>IMAGE / VIDEO INPUT</span><h3>$1 per million tokens</h3><p>Image and video inputs have their own rate; Google also lists an approximate $0.002-per-minute equivalent. These are not text-token rates.</p></article>\n          </div>\n          <p>Google lists a free tier subject to its usage limits. Search grounding may incur separate charges according to the <a href=\"https://ai.google.dev/gemini-api/docs/pricing\" target=\"_blank\" rel=\"noopener noreferrer\">official Gemini pricing documentation</a>. Check current provider rates before estimating production costs; caching and Batch API are not supported for this endpoint.</p>\n        </section>\n\n        <section class=\"model-deep-section\" id=\"live-model-comparison\">\n          <div class=\"model-section-head\"><p class=\"eyebrow\">MODEL COMPARISON</p><h2>Gemini 3.8 Live vs Live Extended Thinking: which should you use?</h2></div>\n          <div class=\"model-capability-grid\">\n            <article><span>FASTER DIRECT CONVERSATIONS</span><h3><a href=\"/models/gemini-3-8-live/\">Gemini 3.8 Live</a></h3><p>Better suited to quick voice commands, immediate back-and-forth and simpler tool flows. It does not accept a <code>thinking_level</code> setting and supports both blocking and non-blocking tools.</p></article>\n            <article><span>COMPLEX MULTI-STEP TASKS</span><h3>Gemini 3.8 Live Extended Thinking</h3><p>Designed for spoken assistants that plan, research or troubleshoot across several tools. It offers low/medium/high background reasoning, async-only tools and <code>interaction_status</code>-based completion.</p></article>\n          </div>\n          <p><strong>Practical choice:</strong> start with the standard Live endpoint for low-latency dialogue. Choose Extended Thinking when the quality of multi-step reasoning and non-blocking background work matters more than the simplest turn-taking flow.</p>\n        </section>\n\n        <section class=\"model-deep-section\" id=\"live-api-integration\">\n          <div class=\"model-section-head\"><p class=\"eyebrow\">API INTEGRATION</p><h2>How to use Gemini 3.8 Live Extended Thinking in the Live API.</h2></div>\n          <div class=\"model-caveat-list\">\n            <div><span>01</span><p><strong>Select the endpoint.</strong> Connect through the Gemini Live API using <code>gemini-3.8-live-extended-thinking</code>, not <code>gemini-3.8-live</code>. This is a streaming, bidirectional session rather than an ordinary one-shot text request.</p></div>\n            <div><span>02</span><p><strong>Configure background reasoning.</strong> Set <code>thinking_config</code> to <code>low</code>, <code>medium</code> or <code>high</code>; declare any callable functions with <code>NON_BLOCKING</code> behavior. Google documents that blocking functions produce an error for Extended Thinking.</p></div>\n            <div><span>03</span><p><strong>Handle the full interaction lifecycle.</strong> When your client receives <code>interactionStatus: IN_PROGRESS</code>, keep the session active even if <code>turnComplete: true</code> arrives for an interim utterance. Treat <code>interactionStatus: IDLE</code> as completion of the background task.</p></div>\n            <div><span>04</span><p><strong>Test streaming and interruption.</strong> Google states that <code>send_client_content</code> works throughout the session with explicit user/model roles, and sending <code>turn_complete=true</code> interrupts active generation. Proactive audio is permanently enabled.</p></div>\n          </div>\n          <p>For complete SDK and WebSocket examples, see Google's <a href=\"https://ai.google.dev/gemini-api/docs/live-api/thinking\" target=\"_blank\" rel=\"noopener noreferrer\">Thinking in the Live API guide</a> and <a href=\"https://ai.google.dev/gemini-api/docs/live-api/capabilities\" target=\"_blank\" rel=\"noopener noreferrer\">Live API capabilities documentation</a>.</p>\n        </section>\n\n        <section class=\"model-deep-section\" id=\"use-cases\">\n          <div class=\"model-section-head\"><p class=\"eyebrow\">USE CASES &amp; LIMITATIONS</p><h2>Best use cases for Extended Thinking voice agents.</h2></div>\n          <div class=\"model-capability-grid\">\n            <article><span>SUPPORT</span><h3>Multi-step troubleshooting</h3><p>Guide a caller through diagnostics while checking logs, account systems or several possible causes using asynchronous tools.</p></article>\n            <article><span>AGENT WORKFLOWS</span><h3>Coordinated information retrieval</h3><p>Discuss options aloud while a travel or booking assistant checks availability, compares results and completes a multi-step research task.</p></article>\n            <article><span>EDUCATION</span><h3>Reasoning-heavy tutoring</h3><p>Explain STEM problems or code debugging steps in speech while verifying calculations and gathering additional context.</p></article>\n          </div>\n          <p><strong>Important limits:</strong> this model's published feature list does not include context caching, Batch API, code execution, file search, structured outputs or URL context. Google lists Search grounding and asynchronous function calling as supported. Developers should not assume standard text API features automatically carry over to Live audio sessions.</p>\n        </section>\n"
FAQ_HTML = "\n        <section class=\"model-deep-section\" id=\"faq\">\n          <div class=\"model-section-head\"><p class=\"eyebrow\">FAQ</p><h2>Gemini 3.8 Live Extended Thinking FAQ.</h2></div>\n          <div class=\"model-caveat-list\">\n            <div><span>01</span><p><strong>What is Gemini 3.8 Live Extended Thinking?</strong> It is Google's high-reasoning Live API audio-to-audio model for real-time voice agents that plan multi-step work and call asynchronous tools while continuing the conversation.</p></div>\n            <div><span>02</span><p><strong>What is the exact API model ID?</strong> Use gemini-3.8-live-extended-thinking in the Gemini Live API. It is a separate endpoint from gemini-3.8-live.</p></div>\n            <div><span>03</span><p><strong>What is its context window?</strong> Google publishes a 131,072-token input limit and a 65,536-token output limit.</p></div>\n            <div><span>04</span><p><strong>How much does Gemini 3.8 Live Extended Thinking cost?</strong> Google's paid Standard rates are $0.75 per million text input tokens and $4.50 per million text output tokens; audio costs $3 input and $12 output per million audio tokens. Image/video input is $1 per million tokens. The output rates include thinking tokens.</p></div>\n            <div><span>05</span><p><strong>Does it support background thinking and async tools?</strong> Yes. Set thinking_level to low, medium or high; minimal is unsupported. Function declarations must use NON_BLOCKING behavior.</p></div>\n            <div><span>06</span><p><strong>How is Extended Thinking different from Gemini 3.8 Live?</strong> Gemini 3.8 Live prioritizes low-latency direct dialogue. Extended Thinking adds configurable background reasoning and requires interaction_status to decide whether the entire request has finished.</p></div>\n            <div><span>07</span><p><strong>Does turnComplete mean the session is idle?</strong> Not necessarily. During background reasoning an utterance may finish while interaction_status remains IN_PROGRESS; wait for IDLE before treating the full task as complete.</p></div>\n            <div><span>08</span><p><strong>Does the model support caching, Batch API or structured outputs?</strong> No. Google's model card lists caching, Batch API and structured outputs as unsupported for this endpoint.</p></div>\n          </div>\n        </section>\n"
MARKER = '<section class="model-deep-section"><div class="model-section-head"><p class="eyebrow">CAVEATS</p>'
SOURCES = [
    "https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live-extended-thinking",
    "https://ai.google.dev/gemini-api/docs/pricing",
    "https://ai.google.dev/gemini-api/docs/live-api/thinking",
    "https://ai.google.dev/gemini-api/docs/live-api/capabilities",
]


def _replace_meta(page, key, value):
    pattern = r'(<meta (?:name|property)="' + re.escape(key) + r'" content=")[^"]*(" />)'
    page, count = re.subn(
        pattern,
        lambda match: match.group(1) + escape(value, quote=True) + match.group(2),
        page,
        count=1,
    )
    if count != 1:
        raise ValueError("Gemini Live page missing expected meta field: " + key)
    return page


def enrich_gemini_live_extended_page(page):
    """Enrich an individual generated model page without changing its canonical URL."""
    if "data-gemini-live-extended-guide" in page:
        return page
    old_title = re.search(r"<title>.*?</title>", page)
    if not old_title:
        raise ValueError("Gemini Live page missing title")
    page = page.replace(old_title.group(0), "<title>" + escape(TITLE) + "</title>", 1)
    for key, value in (
        ("description", DESCRIPTION),
        ("og:title", TITLE),
        ("og:description", DESCRIPTION),
        ("twitter:title", TITLE),
        ("twitter:description", DESCRIPTION),
    ):
        page = _replace_meta(page, key, value)

    old_h1 = "<h1>Gemini 3.8 Live Extended Thinking<br><span>verified model reference.</span></h1>"
    if page.count(old_h1) != 1:
        raise ValueError("Gemini Live hero heading has changed")
    page = page.replace(
        old_h1,
        "<h1>Gemini 3.8 Live Extended Thinking<br><span>Live API, pricing &amp; background reasoning.</span></h1>",
        1,
    )
    old_hero = "<p>Google Live voice endpoint with continuous audio, background thinking and asynchronous agent tool use.</p>"
    if page.count(old_hero) != 1:
        raise ValueError("Gemini Live hero summary has changed")
    page = page.replace(old_hero, "<p>" + escape(HERO) + "</p>", 1)

    schema_match = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.DOTALL)
    if not schema_match:
        raise ValueError("Gemini Live page missing JSON-LD")
    schema = json.loads(schema_match.group(2))
    article = next((obj for obj in schema.get("@graph", []) if obj.get("@type") == "TechArticle"), None)
    if article is None:
        raise ValueError("Gemini Live page missing TechArticle schema")
    article["headline"] = TITLE.removesuffix(" | SXF / AI")
    article["description"] = DESCRIPTION
    article["citation"] = SOURCES
    article["mainEntityOfPage"] = {"@type": "WebPage", "@id": CANONICAL}
    article["publisher"] = {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"}
    schema["@graph"].append({
        "@type": "FAQPage",
        "@id": CANONICAL + "#faq",
        "url": CANONICAL + "#faq",
        "mainEntity": [
            {"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}}
            for question, answer in FAQS
        ],
    })
    jsonld = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    page = page[:schema_match.start(2)] + jsonld + page[schema_match.end(2):]

    if page.count(MARKER) != 1:
        raise ValueError("Gemini Live page missing canonical catalog caveats section")
    page = page.replace(MARKER, SECTIONS + FAQ_HTML + "\n\n        " + MARKER, 1)
    return page
