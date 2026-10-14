"""Durable AWS-sourced SEO guide for Amazon Nova 2 Lite."""
import json
import re
from html import escape
from pathlib import Path

FRAGMENT = Path(__file__).resolve().parents[1] / "data/model-page-content/amazon-nova-2-lite-seo.html"
URL = "https://sxf.si/models/amazon-nova-2-lite/"
TITLE = "Amazon Nova 2 Lite: Pricing, 1M Context & Bedrock API | SXF / AI"
DESCRIPTION = "Amazon Nova 2 Lite guide: AWS Bedrock API pricing, 1M context, 64K output, Boto3 Python example, extended thinking, multimodal limits and Nova 1 comparison."

def enrich_amazon_nova_2_lite(page, model):
    if page.count("</main>") != 1:
        raise ValueError("Unexpected Amazon Nova 2 Lite HTML main tag")
    rates = model["pricing"]["standard"][-1]
    ip, op = float(rates["input"]), float(rates["output"])
    input_price = "$" + format(ip, ".2f")
    output_price = "$" + format(op, ".2f")
    cost_example = "$" + format((50000 * ip + 10000 * op) / 1000000, ".3f")
    fragment = FRAGMENT.read_text(encoding="utf-8").replace("{{INPUT_PRICE}}", input_price).replace("{{OUTPUT_PRICE}}", output_price).replace("{{COST_EXAMPLE}}", cost_example)
    if "{{" in fragment or "}}" in fragment:
        raise ValueError("Unresolved Nova 2 Lite placeholder")
    page = page.replace("</main>", fragment + "\n</main>", 1)
    safe_title, safe_description = escape(TITLE, quote=True), escape(DESCRIPTION, quote=True)
    page = re.sub(r"<title>.*?</title>", "<title>" + safe_title + "</title>", page, count=1, flags=re.S)
    page = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m[1]+safe_description+m[2], page, count=1)
    for prop, val in (("og:title",safe_title),("twitter:title",safe_title),("og:description",safe_description),("twitter:description",safe_description)):
        page = re.sub(r'(<meta (?:property|name)="' + re.escape(prop) + r'" content=")[^"]*(")', lambda m: m[1]+val+m[2], page, count=1)
    page = page.replace("verified model reference.</span>", "pricing, context &amp; API guide.</span>", 1)
    faq_pairs = [
        ("What is Amazon Nova 2 Lite?", "Amazon Nova 2 Lite is a multimodal, text-output reasoning model available through Amazon Bedrock. It handles text, images, documents and video for automation, analysis and agentic workloads."),
        ("How much does Amazon Nova 2 Lite cost?", "SXF's tracked Standard reference rates are "+input_price+" per million input tokens and "+output_price+" per million output tokens. Actual AWS prices vary by routing, Region, service tier and caching, so confirm the applicable Amazon Bedrock pricing table."),
        ("What is the Amazon Nova 2 Lite model ID?", "The base model ID is amazon.nova-2-lite-v1:0. Amazon Bedrock also offers inference profile IDs including global.amazon.nova-2-lite-v1:0 and us.amazon.nova-2-lite-v1:0, depending on regional availability."),
        ("What are the context window and maximum output?", "AWS lists 1 million context tokens and 64K maximum output tokens for Amazon Nova 2 Lite on its Bedrock model card. Application settings and service constraints may impose lower effective limits."),
        ("Does Nova 2 Lite understand video and audio?", "Nova 2 Lite analyzes video visually along with text, images and documents, but does not provide general audio-track transcription or native audio output. Use a speech model for audio-specific tasks."),
        ("Does Amazon Nova 2 Lite support reasoning?", "Yes. Extended thinking is disabled by default and can be enabled with low, medium or high reasoning effort. Reasoning tokens may be billed even when reasoning content is redacted."),
        ("Can I call Amazon Nova 2 Lite with Python?", "Yes. Use boto3 with the Amazon Bedrock Runtime Converse API, your AWS credentials and an available model inference profile. The Python example above provides a minimal request."),
        ("Is Nova 2 Lite better than Nova 1 Lite?", "Nova 2 Lite expands the context window from 300K to 1M tokens, adds extended thinking and built-in tools, and increases the documented output capacity. Whether it performs better for your application should be determined with a representative test set."),
    ]
    sources = [
        "https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html",
        "https://aws.amazon.com/bedrock/pricing/",
        "https://docs.aws.amazon.com/nova/latest/nova2-userguide/using-converse-api.html",
        "https://docs.aws.amazon.com/nova/latest/nova2-userguide/reasoning-capabilities.html",
        "https://aws.amazon.com/blogs/machine-learning/migrate-from-amazon-nova-1-to-amazon-nova-2-on-amazon-bedrock/",
        "https://aws.amazon.com/blogs/machine-learning/pair-nova-2-lite-with-claude-for-cost-optimized-document-processing/",
    ]
    graph = [
        {"@type":"WebPage","@id":URL+"#webpage","url":URL,"name":TITLE,"description":DESCRIPTION,"inLanguage":"en","isPartOf":{"@id":"https://sxf.si/#website"},"mainEntity":{"@id":URL+"#article"},"breadcrumb":{"@id":URL+"#breadcrumb"}},
        {"@type":"TechArticle","@id":URL+"#article","headline":TITLE.split(" | ")[0],"description":DESCRIPTION,"url":URL,"mainEntityOfPage":{"@id":URL+"#webpage"},"dateModified":"2026-10-14","author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},"publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},"about":{"@type":"Thing","name":"Amazon Nova 2 Lite","sameAs":sources[0]},"citation":sources,"inLanguage":"en"},
        {"@type":"BreadcrumbList","@id":URL+"#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},{"@type":"ListItem","position":2,"name":"Models","item":"https://sxf.si/models/"},{"@type":"ListItem","position":3,"name":"Amazon Nova 2 Lite","item":URL}]},
        {"@type":"FAQPage","@id":URL+"#faq","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_pairs]},
    ]
    schema = json.dumps({"@context":"https://schema.org","@graph":graph}, ensure_ascii=False)
    page,count = re.subn(r'<script type="application/ld\+json">.*?</script>',lambda _: '<script type="application/ld+json">'+schema+'</script>',page,count=1,flags=re.S)
    if count != 1:
        raise ValueError("Nova 2 Lite JSON-LD not found")
    return page
