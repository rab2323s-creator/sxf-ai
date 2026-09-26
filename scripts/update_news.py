#!/usr/bin/env python3
from __future__ import annotations

import email.utils
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"
ARCHIVE_OUT = ROOT / "data" / "archive.json"
SLUG_ALIASES_PATH = ROOT / "data" / "slug_aliases.json"
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
SECTION_PAGES = {
    "Models": ROOT / "models" / "index.html",
    "Tools": ROOT / "tools" / "index.html",
    "Research": ROOT / "research" / "index.html",
    "Open Source": ROOT / "open-source" / "index.html",
}

SOURCES = [
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Google AI", "https://blog.google/technology/ai/rss/"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ("GitHub", "https://github.blog/changelog/feed/"),
]
USER_AGENT = "SXF-AI-Radar/1.1 (+https://sxf.si/)"
MAX_ITEMS = 80
MAX_AGE_DAYS = 21
MAX_META_ENRICH_PER_RUN = 8
INITIAL_ARCHIVE_DAYS = 35

def text(node, *names):
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""

def clean_title(title):
    return re.sub(r"\s+", " ", title).strip()[:240]

def clean_summary(value):
    if not value:
        return ""
    value = unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    # RSS feeds sometimes append publisher boilerplate that adds no editorial value.
    value = re.sub(r"\s*The post .+? appeared first on The GitHub Blog\s*\.?$", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:900]

def parse_date(value):
    if not value:
        return None
    try:
        d = email.utils.parsedate_to_datetime(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None

def categorize(title, source):
    t = title.replace("‑", "-").replace("–", "-").replace("—", "-").lower()

    # Product and developer surfaces beat incidental model mentions.
    if re.search(r"\bcopilot\b|\bchatgpt\b|\bagents? api\b|\bsandbox(?:ing)?\b|\bcode reviews?\b|\bgithub actions\b", t):
        if re.search(r"\bresearch\b|\bbenchmark\b|\bevaluation\b|\bstudy\b|\bsafety\b|\bmisalignment\b", t):
            return "Research"
        return "Tools"

    if re.search(r"\bresearch\b|\bpaper\b|\bstudy\b|\bbenchmark\b|\bevaluation\b|\bscience\b|\bsafety\b|\bmisalignment\b|\bassessment\b", t):
        return "Research"

    if re.search(r"\bopen[- ]source\b|\bopen weights?\b|\bweights\b|\bcheckpoint\b|\bllama\.cpp\b|\bmlx\b|\bquants?\b|\brepository release\b", t):
        return "Open Source"

    if re.search(r"\bgpt[- ]\d+(?:\.\d+)?\b|\bclaude(?:\s+[a-z]+)?\s+\d+(?:\.\d+)?\b|\bgemini(?:\s+\d+(?:\.\d+)?)?\b|\blfm\d+(?:\.\d+)?\b|\bllm\b|\bvision-language model\b|\bmultimodal model\b|\breasoning model\b|\bembedding model\b", t):
        return "Models"

    return "Tools"

def classify_tags(title, source, category):
    t = title.replace("‑", "-").replace("–", "-").replace("—", "-").lower()
    tags = []
    rules = [
        ("GitHub Copilot", r"\bcopilot\b"),
        ("Coding AI", r"\bcode\b|\bcoding\b|\bcodex\b|\bdeveloper\b|\brepository\b|\bjetbrains\b"),
        ("AI Agents", r"\bagents?\b|\bagentic\b"),
        ("Security", r"\bsecurity\b|\bsafety\b|\bsandbox(?:ing)?\b|\bcyber\b|\bproof of presence\b"),
        ("Multimodal AI", r"\bmultimodal\b|\bvision\b|\bimage\b|\bvideo\b|\bvoice\b|\baudio\b"),
        ("Open Source AI", r"\bopen[- ]source\b|\bopen weights?\b|\bweights\b|\bcheckpoint\b|\bllama\.cpp\b|\bmlx\b|\bquants?\b"),
        ("Research", r"\bresearch\b|\bpaper\b|\bstudy\b|\bbenchmark\b|\bevaluation\b|\bscience\b"),
    ]
    for label, pattern in rules:
        if re.search(pattern, t):
            tags.append(label)
    if source == "OpenAI":
        tags.append("OpenAI")
    elif source == "Google AI":
        tags.append("Google AI")
    if category == "Open Source" and "Open Source AI" not in tags:
        tags.append("Open Source AI")
    return list(dict.fromkeys(tags))

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def parse_feed(source, body):
    root = ET.fromstring(body)
    rows = []
    for item in root.findall(".//item"):
        title = clean_title(text(item, "title"))
        link = text(item, "link")
        published = parse_date(text(item, "pubDate", "date"))
        summary = clean_summary(text(item, "description", "summary", "content"))
        if title and link and published is not None:
            rows.append((title, link, published, summary))
    if not rows:
        for entry in root.findall(".//{*}entry"):
            title = clean_title(text(entry, "{*}title"))
            link = ""
            for ln in entry.findall("{*}link"):
                href = ln.attrib.get("href", "")
                rel = ln.attrib.get("rel", "alternate")
                if href and rel in ("alternate", ""):
                    link = href
                    break
            published = parse_date(text(entry, "{*}published", "{*}updated"))
            summary = clean_summary(text(entry, "{*}summary", "{*}content"))
            if title and link and published is not None:
                rows.append((title, link, published, summary))

    output = []
    for title, link, published, summary in rows:
        category = categorize(title, source)
        output.append({
            "title": title,
            "url": link,
            "source": source,
            "published": published.isoformat().replace("+00:00", "Z"),
            "category": category,
            "tags": classify_tags(title, source, category),
            "summary": summary,
        })
    return output

def fetch_meta_description(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
        with urllib.request.urlopen(req, timeout=12) as r:
            ctype = (r.headers.get("Content-Type") or "").lower()
            if "html" not in ctype:
                return ""
            raw = r.read(350000).decode("utf-8", "ignore")
        patterns = [
            r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\'](?:description|og:description)["\']',
        ]
        for pattern in patterns:
            m = re.search(pattern, raw, re.I | re.S)
            if m:
                value = clean_summary(m.group(1))
                if 40 <= len(value) <= 900:
                    return value
    except Exception:
        pass
    return ""

def enrich_summaries(items, existing_by_url):
    enriched = 0
    floor = datetime.min.replace(tzinfo=timezone.utc)
    for item in sorted(items, key=lambda x: parse_date(x["published"]) or floor, reverse=True):
        if enriched >= MAX_META_ENRICH_PER_RUN:
            break
        previous = existing_by_url.get(item["url"], {})
        if item.get("summary") or previous.get("summary"):
            continue
        summary = fetch_meta_description(item["url"])
        if summary:
            item["summary"] = summary
            item["summary_origin"] = "source-meta"
            enriched += 1
    return enriched

def valid_url(url):
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc)

def relative_time(date_str):
    d = parse_date(date_str)
    if d is None:
        return ""
    diff = max(timedelta(0), datetime.now(timezone.utc) - d)
    minutes = int(diff.total_seconds() // 60)
    if minutes < 2:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 7:
        return f"{days}d ago"
    return d.strftime("%b %-d")

def featured_html(item):
    href = item.get("signal_url", item["url"])
    return f'''<a class="featured-story" href="{escape(href, quote=True)}">
  <div class="featured-main">
    <div>
      <div class="featured-topline"><strong>{escape(item["source"])}</strong><i></i><span>{escape(relative_time(item["published"]))}</span></div>
      <h3 class="featured-title">{escape(item["title"])}</h3>
    </div>
    <div class="featured-footer"><span class="category-pill">{escape(item["category"])}</span><span class="open-label">Read signal <b>↗</b></span></div>
  </div>
  <div class="featured-visual" aria-hidden="true"><span class="signal-cross">+</span><span class="signal-number">01</span></div>
</a>'''

def cards_html(items):
    rows = []
    for item in items:
        href = item.get("signal_url", item["url"])
        rows.append(f'''<a class="story-card" href="{escape(href, quote=True)}">
  <div class="story-card-top"><span class="story-source">{escape(item["source"])}</span><span class="story-time">{escape(relative_time(item["published"]))}</span></div>
  <h3 class="story-title">{escape(item["title"])}</h3>
  <div class="story-card-bottom"><span class="category-pill">{escape(item["category"])}</span><span class="story-arrow" aria-hidden="true">↗</span></div>
</a>''')
    return "\n".join(rows)

def replace_block(source, start, end, body):
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    replacement = f"{start}\n{body}\n{end}"
    return pattern.sub(lambda _m: replacement, source, count=1)

def update_index(items):
    if not INDEX.exists() or not items:
        return
    page = INDEX.read_text(encoding="utf-8")
    page = replace_block(page, "<!-- SXF:FEATURED_START -->", "<!-- SXF:FEATURED_END -->", featured_html(items[0]))
    page = replace_block(page, "<!-- SXF:FEED_START -->", "<!-- SXF:FEED_END -->", cards_html(items[1:13]))
    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Latest AI signals",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": min(len(items), 10),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {"@type": "Thing", "name": item["title"], "url": item.get("signal_url", item["url"])},
            }
            for i, item in enumerate(items[:10])
        ],
    }
    schema = '<script type="application/ld+json" id="latest-signals-schema">' + json.dumps(item_list, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c") + "</script>"
    page = replace_block(page, "<!-- SXF:ITEMLIST_START -->", "<!-- SXF:ITEMLIST_END -->", schema)
    INDEX.write_text(page, encoding="utf-8")


def section_cards_html(items):
    rows = []
    for item in items[:12]:
        href = item.get("signal_url", item["url"])
        rows.append(f'''<a class="intel-card" href="{escape(href, quote=True)}">
  <div class="intel-meta"><strong>{escape(item["source"])}</strong><span>{escape(relative_time(item["published"]))}</span></div>
  <h3>{escape(item["title"])}</h3>
  <div class="intel-foot"><span>{escape(item["category"])}</span><b>↗</b></div>
</a>''')
    return "\n".join(rows)

def update_section_pages(items):
    for category, path in SECTION_PAGES.items():
        if not path.exists():
            continue
        filtered = [item for item in items if item["category"] == category]
        page = path.read_text(encoding="utf-8")
        page = page.replace('<a href="/open-source/">Open Source</a><a href="/brief/">Brief</a>', '<a href="/open-source/">Open Source</a><a href="/guides/">Guides</a><a href="/superintelligence/">Superintelligence</a><a href="/brief/">Brief</a>')
        page = page.replace('<a href="/guides/">Guides</a><a href="/brief/">Brief</a>', '<a href="/guides/">Guides</a><a href="/superintelligence/">Superintelligence</a><a href="/brief/">Brief</a>')
        page = replace_block(page, "<!-- SXF:SECTION_FEED_START -->", "<!-- SXF:SECTION_FEED_END -->", section_cards_html(filtered))
        schema = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"Latest {category} AI signals",
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": min(len(filtered), 10),
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "item": {"@type": "Thing", "name": item["title"], "url": item.get("signal_url", item["url"])}}
                for i, item in enumerate(filtered[:10])
            ],
        }
        schema_html = '<script type="application/ld+json" id="section-signals-schema">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c") + "</script>"
        page = replace_block(page, "<!-- SXF:SECTION_SCHEMA_START -->", "<!-- SXF:SECTION_SCHEMA_END -->", schema_html)
        if category == "Models":
            page = replace_block(page, "<!-- SXF:TRACKED_MODELS_START -->", "<!-- SXF:TRACKED_MODELS_END -->", tracked_models_html(items))
        path.write_text(page, encoding="utf-8")


BASE_URL = "https://sxf.si"
SIGNALS_DIR = ROOT / "signals"
TOPICS_DIR = ROOT / "topics"
BRIEF_DIR = ROOT / "brief"
COMPARE_DIR = ROOT / "compare"
GUIDES_DIR = ROOT / "guides"
SUPERINTELLIGENCE_DIR = ROOT / "superintelligence"
GPT6_COMPARE_SLUG = "gpt-6-astra-vs-sol-vs-luna"
GPT6_SOL_CLAUDE_COMPARE_SLUG = "gpt-6-sol-vs-claude-opus-5-5"

TOPICS = [
    {
        "slug": "openai",
        "name": "OpenAI",
        "description": "Product, model, research and platform signals published by OpenAI.",
        "source": "OpenAI",
    },
    {
        "slug": "google-ai",
        "name": "Google AI",
        "description": "AI product, research and developer signals published across Google's AI channels.",
        "source": "Google AI",
    },
    {
        "slug": "github-copilot",
        "name": "GitHub Copilot",
        "description": "Copilot product, coding workflow and developer tooling changes from GitHub.",
        "keywords": ["copilot"],
    },
    {
        "slug": "ai-agents",
        "name": "AI Agents",
        "description": "Agent systems, agentic workflows, APIs and products that act across multi-step tasks.",
        "keywords": ["agent", "agents", "agentic"],
    },
    {
        "slug": "coding-ai",
        "name": "Coding AI",
        "description": "AI coding systems, developer tools, code intelligence and software engineering workflows.",
        "keywords": ["code", "coding", "codex", "developer", "copilot", "repository"],
    },
    {
        "slug": "multimodal-ai",
        "name": "Multimodal AI",
        "description": "Vision, image, video, voice and multimodal model or product developments.",
        "keywords": ["multimodal", "vision", "image", "video", "voice", "audio"],
    },
    {
        "slug": "ai-safety",
        "name": "AI Safety",
        "description": "Safety, evaluation, alignment, risk and responsible deployment signals.",
        "keywords": ["safety", "alignment", "misalignment", "risk", "evaluation", "assessment"],
    },
    {
        "slug": "open-source-ai",
        "name": "Open Source AI",
        "description": "Open models, weights, runtimes, frameworks, repositories and local AI tooling.",
        "category": "Open Source",
        "keywords": ["open source", "open-source", "weights", "llama.cpp", "mlx", "repository"],
    },
    {
        "slug": "ai-security",
        "name": "AI Security",
        "description": "Security controls, sandboxing, cyber defense and deployment safeguards across AI products and infrastructure.",
        "keywords": ["security", "cyber", "sandbox", "sandboxing", "proof of presence"],
    },
]

MODEL_PATTERNS = [
    re.compile(r"\bGPT[- ]\d+(?:\.\d+)?(?:\s+(?:Astra|Sol|Luna|Live))?", re.I),
    re.compile(r"\bClaude\s+[A-Za-z]+\s+\d+(?:\.\d+)?", re.I),
    re.compile(r"\bGemini(?:\s+\d+(?:\.\d+)?)?(?:\s+(?:Pro|Flash|Ultra))?", re.I),
    re.compile(r"\bLFM\d+(?:\.\d+)?(?:[- ][A-Za-z0-9.]+)*", re.I),
]

STOPWORDS = {
    "the","a","an","and","or","to","of","for","with","in","on","at","is","are","by",
    "from","how","new","now","more","ai","using","use","your","its","into","as"
}

def slugify(value):
    value = value.replace("‑", "-").replace("–", "-").replace("—", "-")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:82] or "signal"

def load_slug_aliases():
    if not SLUG_ALIASES_PATH.exists():
        return {}
    try:
        data = json.loads(SLUG_ALIASES_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

SLUG_ALIASES = load_slug_aliases()

def signal_slug(item):
    digest = hashlib.sha1(item["url"].encode("utf-8")).hexdigest()[:7]
    return f'{slugify(item["title"])[:70]}-{digest}'

SIGNAL_SCORE_RULES = [
    (re.compile(r"\bintroducing\b|\blaunch(?:ed|es)?\b|\brelease(?:d|s)?\b|\bnow available\b", re.I), 18, "release"),
    (re.compile(r"\bGPT[- ]\d|\bClaude\b|\bGemini\b|\bLFM\d|\bmodel\b", re.I), 14, "model"),
    (re.compile(r"\bagents?\b|\bagentic\b|\bAPI\b|\bCopilot\b|\bdeveloper\b", re.I), 10, "developer"),
    (re.compile(r"\bresearch\b|\bbenchmark\b|\bevaluation\b|\bstudy\b|\bscience\b", re.I), 12, "research"),
    (re.compile(r"\bsafety\b|\balignment\b|\bmisalignment\b|\bassessment\b|\bcyber\b", re.I), 10, "safety"),
    (re.compile(r"\bopen[- ]source\b|\bweights\b|\brepository\b|\bllama\.cpp\b|\bMLX\b", re.I), 10, "open-source"),
    (re.compile(r"\bexpands?\b|\bnew features?\b|\bimproves?\b|\bfaster\b|\bbetter\b", re.I), 7, "product-change"),
]

def signal_score(item, now=None):
    title = item["title"]
    score = 24
    factors = []
    for pattern, points, label in SIGNAL_SCORE_RULES:
        if pattern.search(title):
            score += points
            factors.append(label)

    if item["category"] == "Models":
        score += 8
    elif item["category"] == "Research":
        score += 7
    elif item["category"] == "Open Source":
        score += 6
    else:
        score += 4
    return min(100, score), factors[:5]

def brief_priority(item, now=None):
    now = now or datetime.now(timezone.utc)
    base = item.get("signal_score", 0)
    published = parse_date(item.get("published", ""))
    if published is None:
        return base
    age_hours = max(0.0, (now - published).total_seconds() / 3600)
    freshness = 18 if age_hours <= 12 else 14 if age_hours <= 24 else 9 if age_hours <= 72 else 4 if age_hours <= 168 else 0
    return min(100, base + freshness)

def event_fingerprint(item):
    title = item["title"].replace("‑", "-").replace("–", "-").replace("—", "-").lower()
    models = sorted(set(slugify(name) for name in extract_models(item["title"])))
    if models and re.search(r"\bintroducing\b|\brelease(?:d|s)?\b|\bavailable\b|\blaunch(?:ed|es)?\b", title):
        return "model-release:" + "|".join(models)
    tokens = [
        token for token in re.findall(r"[a-z0-9]+", title)
        if len(token) > 3 and token not in STOPWORDS and token not in {"openai","github","google","hugging","face"}
    ]
    return "title:" + "-".join(tokens[:8])

def editorial_units(item):
    title = item["title"]
    source = item["source"]
    category = item["category"]
    summary = clean_summary(item.get("summary", ""))
    text_value = f"{title} {summary}".lower()
    models = extract_models(title)
    primary_model = models[0] if models else ""

    if summary:
        what_changed = summary
    elif re.search(r"\bintroducing\b|\blaunch(?:ed|es)?\b|\brelease(?:d|s)?\b", title, re.I):
        what_changed = f'{source} published a release-focused update titled “{title}.” SXF is tracking it as a {category.lower()} signal and keeps the original publication as the source of record.'
    elif re.search(r"\bnow available\b|\bavailable\b|\bexpands?\b|\benablement\b", title, re.I):
        what_changed = f'{source} published an availability or rollout update titled “{title}.” The signal is indexed here so changes in access, rollout scope and related product details can be followed over time.'
    elif re.search(r"\bbenchmark\b|\bevaluation\b|\bresearch\b|\bstudy\b|\bscience\b", title, re.I):
        what_changed = f'{source} published a research-oriented update titled “{title}.” SXF places it in the radar as a traceable research signal rather than treating the headline as an independently verified finding.'
    else:
        what_changed = f'{source} published an update titled “{title}.” SXF classifies it under {category} and preserves the direct path to the original publication for the complete context.'

    if re.search(r"\bno longer available\b|\bdeprecated\b|\bdeprecat(?:e|ed|ion)\b|\bremoved\b|\bend of support\b", text_value):
        why = "This is an operational change, not just a product update: existing workflows may stop working or require migration. The practical impact depends on which environments are affected, whether an opt-out exists, and how much lead time users have to move."
        verify = "Check the exact cutoff date, affected runtimes or products, migration path, temporary exceptions, and whether any existing workloads are grandfathered."
    elif re.search(r"\bpricing\b|\bprice\b|\bcost\b|\bdiscount\b|\bbilling\b", text_value):
        why = "Cost changes can alter which workloads are economical to run at scale, especially for high-volume or agentic use. The meaningful signal is not the headline price alone but how the new rates interact with caching, long context, tool use, and production volume."
        verify = "Check the billing unit, context thresholds, cached-input treatment, tool or service charges, regional differences, and the date the new pricing takes effect."
    elif re.search(r"\bbenchmark\b|\bevaluation\b|\bhalf the time\b|\bhalf the cost\b|\b\d+%\b|\bstate-of-the-art\b|\bsota\b", text_value):
        model_note = f" for {primary_model}" if primary_model else ""
        why = f"This update makes a measurable performance claim{model_note}, which is more useful than a generic capability statement if the comparison is reproducible. It can influence model or workflow selection only when the baseline, workload, and evaluation setup are comparable to real use."
        verify = "Check the baseline, sample size, task mix, model and effort settings, token or tool costs, evaluation harness, and whether the reported result comes from controlled testing or a single customer case study."
    elif re.search(r"\bsafety\b|\bmisalignment\b|\bsecurity\b|\bcyber\b|\byouth\b|\bteen\b|\bmental health\b|\bmentalhealth\b", text_value):
        why = "Safety and security updates can change how a system should be evaluated, deployed, or governed even when headline capability is unchanged. The useful signal is whether the work introduces a concrete framework, evidence base, control, or reporting standard that can be applied in practice."
        verify = "Check the scope of the evaluation or policy, who defined the criteria, the underlying evidence, known limitations, whether results were independently reviewed, and which safeguards are actually deployed versus proposed."
    elif category == "Open Source":
        if re.search(r"\bjoins?\b|\bmaintainer\b|\bcommunity\b", text_value):
            why = "Maintainer and stewardship changes can matter for open-source projects because roadmap continuity, review capacity, release cadence, and ecosystem support often depend on a small number of contributors."
            verify = "Check the maintainer’s ongoing role, repository ownership, release plans, governance changes, compatibility commitments, and whether support extends to the broader project or only selected components."
        else:
            why = "This can change what developers are able to run locally or integrate without depending on a hosted API. The practical value depends on whether the release includes usable artifacts, broad hardware or runtime support, and a license that fits real deployment."
            verify = "Check the released code or weights, license, supported quantization or model formats, hardware and memory requirements, runtime compatibility, benchmarks, and reproduction instructions."
    elif re.search(r"\bnow available\b|\bavailable in\b|\bexpands?\b|\benablement\b|\brollout\b|\baccess\b", text_value):
        target = primary_model or title
        why = f"The important change is broader access to {target}, which can move a capability from announcement to actual workflow use. The impact depends on who receives access, where it is available, and whether the release is general availability or a limited rollout."
        verify = "Check eligible plans or users, regions, product surfaces, default versus opt-in status, rollout timing, usage limits, and whether any capabilities remain preview-only."
    elif re.search(r"\bintroducing\b|\blaunch(?:ed|es)?\b|\brelease(?:d|s)?\b|\bnew features?\b|\bimprovements?\b", text_value):
        if category == "Models":
            model_name = primary_model or "the model"
            why = f"A new model release such as {model_name} can change capability, latency, cost, or deployment tradeoffs. The practical value comes from what is materially different from the prior generation and which workloads benefit enough to justify switching."
            verify = "Check model availability, context and output limits, pricing, supported modalities and tools, knowledge cutoff, migration guidance, benchmark methodology, and any stated safety or usage restrictions."
        elif category == "Research":
            why = "A new research release matters when it adds evidence, methodology, or reproducible tooling rather than only a headline conclusion. Its value depends on whether others can inspect the setup and test the result outside the original authors’ environment."
            verify = "Check the research question, dataset, methodology, baselines, statistical or evaluation procedure, limitations, artifacts or code, and whether independent reproduction is possible."
        else:
            why = "A product launch or feature release matters when it changes a workflow users can actually perform, not simply the product’s positioning. The impact depends on availability, permissions, integration depth, and whether the feature removes a real operational constraint."
            verify = "Check release status, supported plans and platforms, required permissions, limits or quotas, integration prerequisites, pricing impact, and whether the feature is generally available or still in preview."
    elif re.search(r"\bcase study\b|\bhelps?\b|\busing\b|\bwith gpt\b|\btrusts?\b|\bcuts?\b|\bboost(?:ing|s|ed)?\b", text_value):
        why = "This is primarily a deployment or customer-use signal. It is useful for understanding where the technology is being applied, but the result should not be generalized beyond the described workflow without comparable evidence."
        verify = "Check the customer’s baseline, workflow scope, measurement period, model configuration, human involvement, cost accounting, and whether the reported outcome was independently evaluated."
    elif category == "Models":
        model_name = primary_model or "the model"
        why = f"This signal may affect how {model_name} is positioned or deployed. The useful question is whether it changes capability, access, reliability, or economics enough to alter a real model-selection decision."
        verify = "Check the exact model version, availability, pricing, context and output limits, tool support, benchmark evidence, and differences from the previous release."
    elif category == "Research":
        why = "This research signal is useful if it changes the available evidence around capability, evaluation, safety, or scientific use. The strongest value comes from transparent methods and results that can be inspected or reproduced."
        verify = "Check methodology, dataset or sample selection, baselines, evaluation criteria, limitations, conflicts or vendor involvement, and whether code or data are available for reproduction."
    else:
        why = "This update matters if it changes a concrete workflow, permission boundary, integration, or user capability. The impact should be judged by what becomes possible in practice rather than by the announcement language alone."
        verify = "Check who can use the change, supported platforms and workflows, permissions, rollout status, limits, pricing implications, and any documented technical constraints."

    return {
        "what_changed": clean_summary(what_changed)[:1100],
        "why_it_matters": why,
        "what_to_verify": verify,
    }

def select_brief_items(items, limit=5):
    floor = datetime.min.replace(tzinfo=timezone.utc)
    ranked = sorted(
        items,
        key=lambda item: (brief_priority(item), parse_date(item["published"]) or floor),
        reverse=True,
    )
    selected = []
    source_counts = {}
    category_counts = {}
    events = set()

    for item in ranked:
        source = item["source"]
        category = item["category"]
        event = event_fingerprint(item)
        if event in events:
            continue
        if source_counts.get(source, 0) >= 2:
            continue
        if category_counts.get(category, 0) >= 2 and len(selected) < limit - 1:
            continue
        selected.append(item)
        events.add(event)
        source_counts[source] = source_counts.get(source, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
        if len(selected) == limit:
            return selected

    for item in ranked:
        event = event_fingerprint(item)
        if item in selected or event in events:
            continue
        selected.append(item)
        events.add(event)
        if len(selected) == limit:
            break
    return selected

def prepare_items(items):
    prepared = []
    for item in items:
        row = dict(item)
        row["summary"] = clean_summary(row.get("summary", ""))
        row["category"] = categorize(row["title"], row["source"])
        row["tags"] = classify_tags(row["title"], row["source"], row["category"])
        row["signal_slug"] = SLUG_ALIASES.get(row["url"]) or row.get("signal_slug") or signal_slug(row)
        row["signal_url"] = f'{BASE_URL}/signals/{row["signal_slug"]}/'
        score, factors = signal_score(row)
        row["signal_score"] = score
        row["score_factors"] = factors
        quality_score, quality_factors = seo_quality(row)
        row["seo_quality_score"] = quality_score
        row["seo_quality_factors"] = quality_factors
        row["seo_eligible"] = seo_signal_eligible(row, quality_score)
        row["editorial"] = editorial_units(row)
        prepared.append(row)
    return prepared

def load_items(path):
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("items", []) if isinstance(payload, dict) else []
    except Exception:
        return []

def merge_archive(existing_items, incoming_items):
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    by_url = {item.get("url"): dict(item) for item in existing_items if valid_url(item.get("url", ""))}

    for incoming in incoming_items:
        url = incoming["url"]
        previous = by_url.get(url, {})
        merged = dict(previous)
        merged.update(incoming)
        if not merged.get("summary") and previous.get("summary"):
            merged["summary"] = previous["summary"]
            merged["summary_origin"] = previous.get("summary_origin", "")
        merged["category"] = categorize(merged["title"], merged["source"])
        merged["tags"] = classify_tags(merged["title"], merged["source"], merged["category"])
        merged["first_seen"] = previous.get("first_seen") or now_iso

        before = {
            "title": previous.get("title"),
            "source": previous.get("source"),
            "published": previous.get("published"),
            "category": previous.get("category"),
            "summary": clean_summary(previous.get("summary", "")),
            "tags": previous.get("tags", []),
        }
        after = {
            "title": merged.get("title"),
            "source": merged.get("source"),
            "published": merged.get("published"),
            "category": merged.get("category"),
            "summary": clean_summary(merged.get("summary", "")),
            "tags": merged.get("tags", []),
        }
        merged["modified_at"] = now_iso if before != after else previous.get("modified_at", now_iso)
        merged["last_seen"] = now_iso
        by_url[url] = merged

    valid = []
    for item in by_url.values():
        if not valid_url(item.get("url", "")):
            continue
        if parse_date(item.get("published", "")) is None:
            continue
        if not item.get("first_seen"):
            item["first_seen"] = now_iso
        if not item.get("modified_at"):
            item["modified_at"] = now_iso
        valid.append(item)
    valid.sort(key=lambda x: parse_date(x["published"]), reverse=True)
    return prepare_items(valid)

def client_item(item):
    return {
        "title": item["title"],
        "url": item["url"],
        "signal_url": item["signal_url"],
        "source": item["source"],
        "published": item["published"],
        "category": item["category"],
        "tags": item.get("tags", []),
        "signal_score": item.get("signal_score", 0),
    }

def normalize_model_text(value):
    return value.replace("‑", "-").replace("–", "-").replace("—", "-")

def extract_models(title):
    text_value = normalize_model_text(title)
    found = []
    for pattern in MODEL_PATTERNS:
        for match in pattern.findall(text_value):
            name = re.sub(r"\s+", " ", match).strip()
            name = re.sub(r"gpt", "GPT", name, flags=re.I)
            name = re.sub(r"^GPT\s+(?=\d)", "GPT-", name)
            name = re.sub(r"claude", "Claude", name, flags=re.I)
            name = re.sub(r"gemini", "Gemini", name, flags=re.I)
            if name and name not in found:
                found.append(name)
                base = re.match(r"^(GPT-\d+(?:\.\d+)?)\s+", name, re.I)
                if base:
                    parent = re.sub(r"gpt", "GPT", base.group(1), flags=re.I)
                    if parent not in found:
                        found.append(parent)

    # Handle grouped family announcements such as "GPT-6 Sol and Luna".
    grouped = re.search(r"\b(GPT[- ]\d+(?:\.\d+)?)\s+(Astra|Sol|Luna)\s+(?:and|&)\s+(Astra|Sol|Luna)\b", text_value, re.I)
    if grouped:
        family = re.sub(r"^GPT\s+(?=\d)", "GPT-", grouped.group(1), flags=re.I)
        family = re.sub(r"gpt", "GPT", family, flags=re.I)
        for variant in (grouped.group(2), grouped.group(3)):
            full = f"{family} {variant.title()}"
            if full not in found:
                found.append(full)
        if family not in found:
            found.append(family)
    return found

SEO_MIN_SUMMARY_CHARS = 90
SEO_MIN_QUALITY_SCORE = 50
SEO_STRONG_EVENT = re.compile(
    r"\bintroducing\b|\blaunch(?:ed|es)?\b|\brelease(?:d|s)?\b|\bnow available\b|"
    r"\bavailable\b|\bbenchmark\b|\bevaluation\b|\bframework\b|\bpricing\b|"
    r"\bsafety overview\b|\bnew features?\b|\bimprovements?\b|\bexpands?\b|\bprompt caching\b",
    re.I,
)
SEO_HIGH_VALUE_TAGS = {
    "GitHub Copilot", "AI Agents", "Coding AI", "Multimodal AI",
    "Open Source AI", "Research", "Security",
}
MODEL_CASE_STUDY = re.compile(
    r"\bhelps?\b|\btrusts?\b|\bcuts?\b|\bboost(?:ing|s|ed)?\b|\busing\b|\bwith GPT\b",
    re.I,
)

MODEL_REFERENCE = {
    "GPT-6": {
        "provider": "OpenAI",
        "summary": "GPT-6 is OpenAI’s current flagship model family, spanning Astra for the hardest end-to-end work, Sol for demanding coding and agentic workflows, and Luna for efficient high-volume tasks.",
        "pricing_note": "Standard API pricing per 1M text tokens for prompts up to 272K input tokens. Longer prompts use higher rates.",
        "modalities": "Text and image input · text output",
        "variants": [
            {
                "name": "GPT-6 Astra",
                "model_id": "gpt-6-astra",
                "positioning": "Highest capability",
                "best_for": "Complex reasoning, coding, computer use, research and document creation",
                "context": "1,050,000",
                "max_output": "128,000",
                "knowledge_cutoff": "Apr 30, 2026",
                "input_price": "$10.00",
                "cached_price": "$1.00",
                "output_price": "$50.00",
                "released": "Sep 3, 2026",
                "source": "https://developers.openai.com/api/docs/models/gpt-6-astra",
            },
            {
                "name": "GPT-6 Sol",
                "model_id": "gpt-6-sol",
                "positioning": "Capability / cost balance",
                "best_for": "Complex coding and agentic workflows",
                "context": "1,050,000",
                "max_output": "128,000",
                "knowledge_cutoff": "Apr 20, 2026",
                "input_price": "$2.00",
                "cached_price": "$0.20",
                "output_price": "$10.00",
                "released": "Sep 22, 2026",
                "source": "https://developers.openai.com/api/docs/models/gpt-6-sol",
            },
            {
                "name": "GPT-6 Luna",
                "model_id": "gpt-6-luna",
                "positioning": "Efficiency",
                "best_for": "Focused, high-volume and cost-sensitive workloads",
                "context": "1,050,000",
                "max_output": "128,000",
                "knowledge_cutoff": "May 18, 2026",
                "input_price": "$0.10",
                "cached_price": "$0.01",
                "output_price": "$0.50",
                "released": "Sep 22, 2026",
                "source": "https://developers.openai.com/api/docs/models/gpt-6-luna",
            },
        ],
        "sources": [
            ("OpenAI model catalog", "https://developers.openai.com/api/docs/models"),
            ("OpenAI API pricing", "https://developers.openai.com/api/docs/pricing"),
            ("GPT-6 model guidance", "https://developers.openai.com/api/docs/guides/latest-model"),
            ("OpenAI API changelog", "https://developers.openai.com/api/docs/changelog"),
        ],
        "faq": [
            ("What models are in the GPT-6 family?", "OpenAI currently lists GPT-6 Astra, GPT-6 Sol and GPT-6 Luna as the flagship GPT-6 family."),
            ("What is the GPT-6 context window?", "Astra, Sol and Luna each have a 1,050,000-token context window and support up to 128,000 output tokens."),
            ("How much does GPT-6 cost in the API?", "For Standard API requests up to 272K input tokens, Astra is $10 input / $50 output per 1M tokens, Sol is $2 / $10, and Luna is $0.10 / $0.50. Cached-input rates are lower."),
            ("What is each GPT-6 model for?", "OpenAI positions Astra for the hardest end-to-end work, Sol for complex coding and agentic workflows, and Luna for efficient high-volume tasks."),
        ],
    }
}

def model_reference(name):
    if name == "GPT-6" or name.startswith("GPT-6 "):
        return MODEL_REFERENCE["GPT-6"]
    return None

def model_reference_html(name):
    ref = model_reference(name)
    if not ref:
        return ""

    variants = ref["variants"]
    selected = next((v for v in variants if v["name"].lower() == name.lower()), None)
    focus = selected or None
    verified = datetime.now(timezone.utc).date().isoformat()

    if focus:
        facts = f'''<div class="model-fact-grid">
          <div><span>MODEL ID</span><strong>{escape(focus["model_id"])}</strong></div>
          <div><span>CONTEXT WINDOW</span><strong>{escape(focus["context"])}</strong><small>tokens</small></div>
          <div><span>MAX OUTPUT</span><strong>{escape(focus["max_output"])}</strong><small>tokens</small></div>
          <div><span>KNOWLEDGE CUTOFF</span><strong>{escape(focus["knowledge_cutoff"])}</strong></div>
          <div><span>STANDARD INPUT</span><strong>{escape(focus["input_price"])}</strong><small>/ 1M tokens</small></div>
          <div><span>STANDARD OUTPUT</span><strong>{escape(focus["output_price"])}</strong><small>/ 1M tokens</small></div>
        </div>'''
        intro = f'''<div class="model-reference-copy"><p class="eyebrow">MODEL REFERENCE</p><h2>{escape(name)} at a glance.</h2>
          <p>{escape(focus["best_for"])}. OpenAI lists a {escape(focus["context"])}-token context window, up to {escape(focus["max_output"])} output tokens and a {escape(focus["knowledge_cutoff"])} knowledge cutoff.</p>
          <p class="reference-note">Released {escape(focus["released"])} · {escape(ref["modalities"])} · Last verified {escape(verified)}</p></div>'''
    else:
        facts = '''<div class="model-fact-grid">
          <div><span>FAMILY</span><strong>3</strong><small>flagship variants</small></div>
          <div><span>CONTEXT WINDOW</span><strong>1,050,000</strong><small>tokens across family</small></div>
          <div><span>MAX OUTPUT</span><strong>128,000</strong><small>tokens across family</small></div>
          <div><span>INPUT</span><strong>Text + image</strong></div>
          <div><span>OUTPUT</span><strong>Text</strong></div>
          <div><span>PROVIDER</span><strong>OpenAI</strong></div>
        </div>'''
        intro = f'''<div class="model-reference-copy"><p class="eyebrow">MODEL REFERENCE</p><h2>GPT-6 family at a glance.</h2>
          <p>{escape(ref["summary"])}</p>
          <p class="reference-note">{escape(ref["modalities"])} · Last verified {escape(verified)}</p></div>'''

    rows = "".join(
        f'''<tr class="{"is-current" if focus and v["name"] == focus["name"] else ""}">
          <th scope="row"><a href="/models/{escape(slugify(v["name"]), quote=True)}/">{escape(v["name"])}</a><small>{escape(v["model_id"])}</small></th>
          <td>{escape(v["positioning"])}</td><td>{escape(v["context"])}</td><td>{escape(v["max_output"])}</td>
          <td>{escape(v["input_price"])}</td><td>{escape(v["cached_price"])}</td><td>{escape(v["output_price"])}</td>
        </tr>''' for v in variants
    )
    sources = "".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(label)}</span><b>↗</b></a>'
        for label, url in ref["sources"]
    )
    faq = "".join(
        f'<details><summary>{escape(question)}</summary><p>{escape(answer)}</p></details>'
        for question, answer in ref["faq"]
    )
    return f'''<section class="model-reference shell">
      <div class="model-reference-intro">{intro}{facts}</div>
      <div class="model-comparison">
        <div class="intel-section-head"><div><p class="eyebrow">FAMILY COMPARISON</p><h2>Astra, Sol and Luna.</h2></div><a class="comparison-cta" href="/compare/{GPT6_COMPARE_SLUG}/">Full decision guide ↗</a></div>
        <div class="model-table-wrap"><table><thead><tr><th>Model</th><th>Positioning</th><th>Context</th><th>Max output</th><th>Input</th><th>Cached</th><th>Output</th></tr></thead><tbody>{rows}</tbody></table></div>
        <p class="reference-note">{escape(ref["pricing_note"])}</p>
      </div>
      <div class="model-reference-lower">
        <div class="model-sources"><p class="eyebrow">OFFICIAL SOURCES</p>{sources}</div>
        <div class="model-faq"><p class="eyebrow">QUICK ANSWERS</p>{faq}</div>
      </div>
    </section>'''

def seo_quality(item):
    summary_len = len(clean_summary(item.get("summary", "")))
    score = 30 if summary_len >= 120 else 24 if summary_len >= 90 else 14 if summary_len >= 60 else 0
    factors = []

    if summary_len >= SEO_MIN_SUMMARY_CHARS:
        factors.append("substantive-source-summary")
    if SEO_STRONG_EVENT.search(item["title"]):
        score += 18
        factors.append("search-worthy-event")
    if extract_models(item["title"]):
        score += 18
        factors.append("named-model")

    signal = item.get("signal_score", 0)
    score += 15 if signal >= 55 else 12 if signal >= 45 else 9 if signal >= 38 else 3

    if item["category"] in {"Models", "Research", "Open Source"}:
        score += 8
        factors.append("durable-intelligence-layer")
    if SEO_HIGH_VALUE_TAGS.intersection(item.get("tags", [])):
        score += 10
        factors.append("high-value-topic")

    if item["category"] == "Models" and not SEO_STRONG_EVENT.search(item["title"]) and MODEL_CASE_STUDY.search(item["title"]):
        score -= 20
        factors.append("case-study-penalty")

    return max(0, min(100, score)), factors

def seo_signal_eligible(item, quality_score=None):
    summary_len = len(clean_summary(item.get("summary", "")))
    if summary_len < SEO_MIN_SUMMARY_CHARS:
        return False
    if quality_score is None:
        quality_score, _ = seo_quality(item)
    return quality_score >= SEO_MIN_QUALITY_SCORE

def model_page_indexable(name, items):
    substantive = [item for item in items if len(clean_summary(item.get("summary", ""))) >= SEO_MIN_SUMMARY_CHARS]
    if len(items) >= 2 and len(substantive) >= 2:
        return True
    return any(
        item.get("seo_eligible", seo_signal_eligible(item))
        and SEO_STRONG_EVENT.search(item["title"])
        for item in items
    )

def topic_page_indexable(items):
    substantive = sum(
        1 for item in items
        if len(clean_summary(item.get("summary", ""))) >= SEO_MIN_SUMMARY_CHARS
    )
    return len(items) >= 3 and substantive >= 2

def model_groups(items):
    groups = {}
    for item in items:
        for name in extract_models(item["title"]):
            groups.setdefault(name, []).append(item)
    return dict(sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0].lower())))

def tracked_models_html(items):
    groups = model_groups(items)
    cards = []
    for name, matched in list(groups.items())[:12]:
        cards.append(
            f'<a class="tracked-model" href="/models/{escape(slugify(name), quote=True)}/">'
            f'<span>{len(matched):02d}</span><strong>{escape(name)}</strong>'
            f'<small>{len(matched)} signal{"s" if len(matched) != 1 else ""}</small><b>↗</b></a>'
        )
    return "".join(cards)

def topic_matches(item, topic):
    if topic.get("source") and item["source"] == topic["source"]:
        return True
    tags = set(item.get("tags", []))
    if topic["name"] in tags:
        return True
    if topic.get("category") and item["category"] == topic["category"]:
        return True
    haystack = f'{item["title"]} {item.get("summary","")}'.lower()
    for keyword in topic.get("keywords", []):
        key = keyword.lower()
        if (" " in key and key in haystack) or (" " not in key and re.search(rf"\b{re.escape(key)}\b", haystack)):
            return True
    return False

def topic_groups(items):
    result = {}
    for topic in TOPICS:
        matches = [item for item in items if topic_matches(item, topic)]
        if matches:
            result[topic["slug"]] = (topic, matches)
    return result

def item_topics(item):
    return [topic for topic in TOPICS if topic_matches(item, topic)]

def display_date(value):
    d = parse_date(value)
    return d.strftime("%B %-d, %Y") if d is not None else "Unknown date"

def compact_description(item):
    editorial = item.get("editorial") or editorial_units(item)
    return editorial["what_changed"]

def category_context(category):
    return {
        "Models": "Tracked in the Models layer for model releases, capability shifts and deployment changes.",
        "Tools": "Tracked in the Tools layer for products, APIs, agents and practical AI workflows.",
        "Research": "Tracked in the Research layer for studies, evaluations, benchmarks, safety and scientific work.",
        "Open Source": "Tracked in the Open Source layer for repositories, weights, runtimes, frameworks and local AI.",
    }.get(category, "Tracked as part of the SXF AI signal layer.")

def category_path(category):
    return {
        "Models": "/models/",
        "Tools": "/tools/",
        "Research": "/research/",
        "Open Source": "/open-source/",
    }.get(category, "/signals/")

def page_header(active=""):
    links = [
        ("/models/", "Models", "models"),
        ("/tools/", "Tools", "tools"),
        ("/research/", "Research", "research"),
        ("/open-source/", "Open Source", "open-source"),
        ("/guides/", "Guides", "guides"),
        ("/superintelligence/", "Superintelligence", "superintelligence"),
        ("/brief/", "Brief", "brief"),
        ("/about/", "About", "about"),
    ]
    nav_parts = []
    for href, label, key in links:
        current = ' aria-current="page"' if key == active else ""
        nav_parts.append(f'<a href="{href}"{current}>{label}</a>')
    nav = "".join(nav_parts)
    return f'''<header class="site-header"><div class="header-inner">
      <a class="brand" href="/" aria-label="SXF AI home"><span class="brand-mark">SXF</span><span class="brand-divider">/</span><span class="brand-ai">AI</span></a>
      <nav class="top-nav" aria-label="Primary navigation">{nav}</nav>
      <div class="header-status"><span class="pulse-dot"></span>LIVE</div>
    </div></header>'''

def page_footer():
    return '''<footer class="footer shell">
      <div class="footer-main">
        <div class="footer-identity">
          <a class="brand footer-brand" href="/" aria-label="SXF AI home"><span class="brand-mark">SXF</span><span class="brand-divider">/</span><span class="brand-ai">AI</span></a>
          <p class="footer-statement">AI intelligence,<br><span>mapped in motion.</span></p>
          <p class="footer-description">Primary-source signals, model intelligence, expert guides and research context — organized for fast understanding.</p>
          <a class="footer-contact" href="mailto:info@sxf.si" aria-label="Email SXF at info@sxf.si"><span class="footer-contact-dot" aria-hidden="true"></span><span class="footer-contact-label">CONTACT</span><strong>info@sxf.si</strong><b aria-hidden="true">↗</b></a>
        </div>
        <nav class="footer-nav" aria-label="Footer navigation">
          <div class="footer-nav-group"><p>INTELLIGENCE</p><a href="/models/">Models <span>↗</span></a><a href="/signals/">Signals <span>↗</span></a><a href="/topics/">Topics <span>↗</span></a><a href="/research/">Research <span>↗</span></a></div>
          <div class="footer-nav-group"><p>EXPLORE</p><a href="/guides/">Guides <span>↗</span></a><a href="/superintelligence/">Superintelligence <span>↗</span></a><a href="/open-source/">Open Source <span>↗</span></a><a href="/brief/">SXF Brief <span>↗</span></a></div>
          <div class="footer-nav-group"><p>SXF</p><a href="/about/">About & Method <span>↗</span></a><a href="mailto:info@sxf.si">Contact <span>↗</span></a><a href="https://vivamediacreative.com/labs/">VMC Labs <span>↗</span></a><a href="https://vivamediacreative.com/">Viva Media Creative <span>↗</span></a></div>
        </nav>
      </div>
      <div class="footer-bottom"><span>© <span id="year"></span> SXF / AI</span><span>Curated AI intelligence · Built for signal.</span><span>Developed within <a href="https://vivamediacreative.com/labs/">VMC Labs</a></span></div>
    </footer><script>document.getElementById("year").textContent=new Date().getFullYear();</script>'''

def page_head(title, description, canonical, schema, page_type="website", robots="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"):
    safe_description = escape(description[:180], quote=True)
    if page_type == "article":
        social_image_meta = '<meta name="twitter:card" content="summary" />'
    else:
        social_image_meta = '''<meta property="og:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:image:alt" content="SXF / AI — The AI Signals Hub" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />
      <meta name="twitter:image:alt" content="SXF / AI — The AI Signals Hub" />'''
    return f'''<head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="color-scheme" content="dark" />
      <title>{escape(title)}</title>
      <meta name="description" content="{safe_description}" />
      <meta name="robots" content="{escape(robots, quote=True)}" />
      <meta name="googlebot" content="{escape(robots, quote=True)}" />
      <meta name="theme-color" content="#07090d" />
      <link rel="canonical" href="{escape(canonical, quote=True)}" />
      <link rel="alternate" hreflang="en" href="{escape(canonical, quote=True)}" />
      <link rel="alternate" hreflang="x-default" href="{escape(canonical, quote=True)}" />
      <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      <meta property="og:type" content="{escape(page_type, quote=True)}" />
      <meta property="og:site_name" content="SXF / AI" />
      <meta property="og:title" content="{escape(title, quote=True)}" />
      <meta property="og:description" content="{safe_description}" />
      <meta property="og:url" content="{escape(canonical, quote=True)}" />
      {social_image_meta}
      <meta name="twitter:title" content="{escape(title, quote=True)}" />
      <meta name="twitter:description" content="{safe_description}" />
      <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")}</script>
      <link rel="stylesheet" href="/styles.css" />
      <link rel="stylesheet" href="/intelligence.css" />
    </head>'''

def related_items(item, items, limit=5):
    base_tokens = set(re.findall(r"[a-z0-9]+", normalize_model_text(item["title"]).lower())) - STOPWORDS
    scored = []
    for other in items:
        if other["url"] == item["url"]:
            continue
        other_tokens = set(re.findall(r"[a-z0-9]+", normalize_model_text(other["title"]).lower())) - STOPWORDS
        score = len(base_tokens & other_tokens)
        if other["source"] == item["source"]:
            score += 2
        if other["category"] == item["category"]:
            score += 1
        if score:
            scored.append((score, parse_date(other["published"]), other))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [row[2] for row in scored[:limit]]

def signal_row(item):
    return f'''<a class="signal-row" href="/signals/{escape(item["signal_slug"], quote=True)}/">
      <div class="signal-row-meta"><span>{escape(item["source"])}</span><time datetime="{escape(item["published"], quote=True)}">{escape(display_date(item["published"]))}</time></div>
      <h3>{escape(item["title"])}</h3>
      <div class="signal-row-foot"><span>{escape(item["category"])}</span><b>Open signal ↗</b></div>
    </a>'''

def signal_page_html(item, items):
    canonical = item["signal_url"]
    description = compact_description(item)
    modified = item.get("modified_at") or item["published"]
    indexable = bool(item.get("seo_eligible", seo_signal_eligible(item)))
    robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" if indexable else "noindex,follow"
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "@id": canonical + "#article",
                "headline": item["title"],
                "datePublished": item["published"],
                "dateModified": modified,
                "mainEntityOfPage": canonical,
                "url": canonical,
                "articleSection": item["category"],
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "author": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "creator": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "citation": item["url"],
                "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Signals", "item": BASE_URL + "/signals/"},
                    {"@type": "ListItem", "position": 3, "name": item["category"], "item": BASE_URL + category_path(item["category"])},
                ],
            },
        ],
    }
    topics = item_topics(item)
    models = extract_models(item["title"])
    topic_links = "".join(
        f'<a href="/topics/{escape(t["slug"], quote=True)}/">{escape(t["name"])}</a>' for t in topics[:4]
    )
    model_links = "".join(
        f'<a href="/models/{escape(slugify(name), quote=True)}/">{escape(name)}</a>' for name in models[:4]
    )
    related = "".join(signal_row(x) for x in related_items(item, items))
    editorial = item.get("editorial") or editorial_units(item)
    summary_label = "Source summary" if item.get("summary") else "SXF signal note"
    return f'''<!doctype html><html lang="en">
    {page_head(item["title"] + " | SXF / AI", description, canonical, schema, "article", robots)}
    <body class="intel-page signal-page">
      <a class="skip-link" href="#signal-main">Skip to signal</a>
      <div class="ambient ambient-one" aria-hidden="true"></div><div class="ambient ambient-two" aria-hidden="true"></div>
      {page_header()}
      <main id="signal-main">
        <section class="intel-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/signals/">Signals</a><span>/</span><a href="{escape(category_path(item["category"]), quote=True)}">{escape(item["category"])}</a></nav>
          <div class="intel-kicker"><span class="pulse-dot"></span> SIGNAL / {escape(item["category"].upper())}</div>
          <h1>{escape(item["title"])}</h1>
          <div class="signal-meta-strip">
            <div><span>SOURCE</span><strong>{escape(item["source"])}</strong></div>
            <div><span>PUBLISHED</span><strong>{escape(display_date(item["published"]))}</strong></div>
            <div><span>LAYER</span><strong>{escape(item["category"])}</strong></div>
            <div><span>SIGNAL SCORE</span><strong>{item.get("signal_score", 0):02d}/100</strong></div>
          </div>
        </section>
        <section class="signal-layout shell">
          <article class="signal-brief">
            <p class="eyebrow">{summary_label.upper()}</p>
            <p class="signal-summary">{escape(editorial["what_changed"])}</p>
            <div class="signal-context"><span>WHY IT MATTERS</span><p>{escape(editorial["why_it_matters"])}</p></div>
            <div class="signal-context"><span>WHAT TO VERIFY</span><p>{escape(editorial["what_to_verify"])}</p></div>
          </article>
          <aside class="source-card">
            <span class="source-card-label">SOURCE OF RECORD</span><strong>{escape(item["source"])}</strong>
            <p>Read the original publication for the complete context behind this signal.</p>
            <a href="{escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">Open original source <b>↗</b></a>
          </aside>
        </section>
        <section class="signal-taxonomy shell">
          <div><span>TOPICS</span>{topic_links or '<small>No topic tag yet</small>'}</div>
          <div><span>MODELS</span>{model_links or '<small>No named model detected</small>'}</div>
        </section>
        <section class="related-signals shell">
          <div class="intel-section-head"><div><p class="eyebrow">RELATED SIGNALS</p><h2>Keep the context connected.</h2></div><a href="/signals/">All signals ↗</a></div>
          <div class="signal-list">{related}</div>
        </section>
      </main>
      {page_footer()}
    </body></html>'''
def signals_index_html(items):
    canonical = f"{BASE_URL}/signals/"
    description = "Latest AI signals tracked by SXF / AI across models, tools, research and open source, with direct links to primary sources."
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "AI Signals | SXF / AI",
        "url": canonical,
        "isPartOf": {"@id": "https://sxf.si/#website"},
        "inLanguage": "en",
    }
    rows = "".join(signal_row(item) for item in items[:40])
    return f'''<!doctype html><html lang="en">{page_head("AI Signals — Latest Primary-Source AI Updates | SXF / AI", description, canonical, schema)}
    <body class="intel-page collection-page"><a class="skip-link" href="#signals-main">Skip to signals</a>
    {page_header()}<main id="signals-main">
      <section class="collection-hero shell">
        <p class="eyebrow">SXF SIGNAL INDEX</p><h1>The AI changes<br><span>worth opening.</span></h1>
        <p>Models, tools, research and open-source developments organized as traceable signals with the primary source kept one click away.</p>
        <div class="collection-stats"><div><strong>{len(items)}</strong><span>tracked signals</span></div><div><strong>4</strong><span>intelligence layers</span></div><div><strong>3h</strong><span>refresh cycle</span></div></div>
      </section>
      <section class="topic-reference shell"><a class="guide-inline-cta" href="/guides/ai-agent-security/"><div><span>REFERENCE GUIDE</span><strong>AI Agent Security in 2026</strong><p>Understand prompt injection, MCP, permissions and sandboxing behind the security signals in the radar.</p></div><b>Read security guide ↗</b></a></section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">LATEST</p><h2>Signal stream.</h2></div><a href="/brief/">Read today’s brief ↗</a></div><div class="signal-list">{rows}</div></section>
    </main>{page_footer()}</body></html>'''

def topic_page_html(topic, items):
    canonical = f'{BASE_URL}/topics/{topic["slug"]}/'
    latest = items[0]
    latest_summary = clean_summary(latest.get("summary", "")) or compact_description(latest)
    first_date = display_date(items[-1]["published"])
    latest_date = display_date(latest["published"])
    source_count = len({item["source"] for item in items})
    robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" if topic_page_indexable(items) else "noindex,follow"
    schema = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": f'{topic["name"]} AI Signals | SXF / AI', "url": canonical,
        "description": topic["description"], "isPartOf": {"@id": "https://sxf.si/#website"}, "inLanguage": "en"
    }
    rows = "".join(signal_row(item) for item in items[:30])
    security_reference = ""
    if topic["slug"] == "ai-security":
        security_reference = '''<section class="topic-reference shell"><div class="guide-choice-grid"><article><span>AGENT SECURITY</span><p>Permissions, MCP, sandboxing, memory integrity and production controls.</p><div class="tool-links"><a href="/guides/ai-agent-security/">AI Agent Security ↗</a></div></article><article><span>PROMPT INJECTION</span><p>Direct vs indirect injection, agent hijacking, RAG, browser and tool defenses.</p><div class="tool-links"><a href="/guides/prompt-injection/">Prompt Injection guide ↗</a></div></article></div></section>'''
    elif topic["slug"] == "github-copilot":
        security_reference = '''<section class="topic-reference shell"><a class="guide-inline-cta" href="/guides/github-copilot-alternatives/"><div><span>DEEP COMPARISON</span><strong>Best GitHub Copilot Alternatives in 2026</strong><p>Cursor, Claude Code, Codex, Cline, JetBrains AI, OpenCode and Devin Desktop compared by workflow and cost.</p></div><b>Compare alternatives ↗</b></a></section>'''
    elif topic["slug"] == "coding-ai":
        security_reference = '''<section class="topic-reference shell"><div class="guide-choice-grid"><article><span>SECURITY GUIDE</span><p>Prompt injection, MCP, permissions, sandboxing and production controls.</p><div class="tool-links"><a href="/guides/ai-agent-security/">AI Agent Security ↗</a></div></article><article><span>COPILOT ALTERNATIVES</span><p>Compare Cursor, Claude Code, Codex, Cline, JetBrains AI, OpenCode and Devin Desktop.</p><div class="tool-links"><a href="/guides/github-copilot-alternatives/">Open comparison ↗</a></div></article></div></section>'''
    elif topic["slug"] == "ai-agents":
        security_reference = '''<section class="topic-reference shell"><div class="guide-choice-grid"><article><span>AGENT SECURITY</span><p>Identity, tool boundaries, MCP, sandboxing and human approval.</p><div class="tool-links"><a href="/guides/ai-agent-security/">Open security guide ↗</a></div></article><article><span>PROMPT INJECTION</span><p>Understand direct and indirect injection before expanding agent autonomy.</p><div class="tool-links"><a href="/guides/prompt-injection/">Open prompt injection guide ↗</a></div></article></div></section>'''
    return f'''<!doctype html><html lang="en">{page_head(topic["name"] + " — AI Signals | SXF / AI", topic["description"], canonical, schema, robots=robots)}
    <body class="intel-page topic-page">{page_header()}<main>
      <section class="collection-hero shell"><nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><a href="/topics/">Topics</a><span>/</span><span>{escape(topic["name"])}</span></nav>
      <p class="eyebrow">TOPIC INTELLIGENCE</p><h1>{escape(topic["name"])}<br><span>signal history.</span></h1><p>{escape(topic["description"])}</p>
      <div class="collection-stats"><div><strong>{len(items)}</strong><span>tracked signals</span></div><div><strong>{source_count}</strong><span>primary sources</span></div><div><strong>{escape(latest_date)}</strong><span>latest tracked</span></div></div></section>
      <section class="signal-layout shell"><article class="signal-brief"><p class="eyebrow">LATEST DEVELOPMENT</p><h2>{escape(latest["title"])}</h2><p class="signal-summary">{escape(latest_summary)}</p><a class="brief-open" href="/signals/{escape(latest["signal_slug"], quote=True)}/">Open latest signal ↗</a></article>
      <aside class="source-card"><span class="source-card-label">COVERAGE WINDOW</span><strong>{escape(topic["name"])}</strong><p>Tracked from {escape(first_date)} through {escape(latest_date)} across {source_count} primary source{"s" if source_count != 1 else ""}.</p></aside></section>
      {security_reference}
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">RECENT</p><h2>Latest in {escape(topic["name"])}.</h2></div><a href="/topics/">All topics ↗</a></div><div class="signal-list">{rows}</div></section>
    </main>{page_footer()}</body></html>'''

def topics_index_html(groups):
    canonical = f"{BASE_URL}/topics/"
    description = "Explore SXF / AI topic intelligence across companies, agents, coding AI, multimodal systems, safety and open-source AI."
    schema = {"@context":"https://schema.org","@type":"CollectionPage","name":"AI Topics | SXF / AI","url":canonical,"isPartOf":{"@id":"https://sxf.si/#website"},"inLanguage":"en"}
    cards = "".join(
        f'''<a class="topic-card" href="/topics/{escape(slug, quote=True)}/"><span>{len(items):02d}</span><h2>{escape(topic["name"])}</h2><p>{escape(topic["description"])}</p><b>Open topic ↗</b></a>'''
        for slug,(topic,items) in groups.items()
    )
    return f'''<!doctype html><html lang="en">{page_head("AI Topics — Companies, Agents, Safety & Open Source | SXF / AI", description, canonical, schema)}
    <body class="intel-page topics-page">{page_header()}<main>
    <section class="collection-hero shell"><p class="eyebrow">TOPIC MAP</p><h1>Follow the subject,<br><span>not just the headline.</span></h1><p>Persistent topic pages turn individual releases into a navigable signal history.</p></section>
    <section class="topic-grid shell">{cards}</section></main>{page_footer()}</body></html>'''

def model_page_html(name, items):
    slug = slugify(name)
    canonical = f"{BASE_URL}/models/{slug}/"
    ref = model_reference(name)
    if ref:
        description = (
            f"{name} reference: pricing, context window, API specifications, model family details "
            f"and the latest primary-source updates tracked by SXF / AI."
        )
        title = f"{name} — Pricing, Context Window, API & Updates | SXF / AI" if name != "GPT-6" else "GPT-6 Models — Pricing, Context Window & Updates | SXF / AI"
    else:
        description = f"Track {name} releases, capability changes and related primary-source signals on SXF / AI."
        title = name + " — Releases & Signals | SXF / AI"
    latest = items[0]
    latest_summary = clean_summary(latest.get("summary", "")) or compact_description(latest)
    first_date = display_date(items[-1]["published"])
    latest_date = display_date(latest["published"])
    source_count = len({item["source"] for item in items})
    robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" if model_page_indexable(name, items) else "noindex,follow"
    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"CollectionPage","name":f"{name} reference and updates | SXF / AI","url":canonical,
                "description":description,"isPartOf":{"@id":"https://sxf.si/#website"},
                "about":{"@type":"Thing","name":name},"inLanguage":"en"
            },
            {
                "@type":"BreadcrumbList",
                "itemListElement":[
                    {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL + "/"},
                    {"@type":"ListItem","position":2,"name":"Models","item":BASE_URL + "/models/"},
                    {"@type":"ListItem","position":3,"name":name,"item":canonical},
                ]
            }
        ]
    }
    rows = "".join(signal_row(item) for item in items[:30])
    reference = model_reference_html(name)
    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema, robots=robots)}
    <body class="intel-page model-page">{page_header("models")}<main>
      <section class="collection-hero shell"><nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><a href="/models/">Models</a><span>/</span><span>{escape(name)}</span></nav>
      <p class="eyebrow">MODEL INTELLIGENCE</p><h1>{escape(name)}<br><span>{"reference & signals." if ref else "release signals."}</span></h1><p>{escape(description)}</p>
      <div class="collection-stats"><div><strong>{len(items)}</strong><span>tracked signals</span></div><div><strong>{source_count}</strong><span>primary sources</span></div><div><strong>{escape(latest_date)}</strong><span>latest tracked</span></div></div></section>
      {reference}
      <section class="signal-layout shell"><article class="signal-brief"><p class="eyebrow">LATEST DEVELOPMENT</p><h2>{escape(latest["title"])}</h2><p class="signal-summary">{escape(latest_summary)}</p><a class="brief-open" href="/signals/{escape(latest["signal_slug"], quote=True)}/">Open latest signal ↗</a></article>
      <aside class="source-card"><span class="source-card-label">MODEL TIMELINE</span><strong>{escape(name)}</strong><p>Tracked from {escape(first_date)} through {escape(latest_date)} across {source_count} primary source{"s" if source_count != 1 else ""}.</p></aside></section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">MODEL TIMELINE</p><h2>Recent {escape(name)} signals.</h2></div><a href="/models/">All models ↗</a></div><div class="signal-list">{rows}</div></section>
    </main>{page_footer()}</body></html>'''




def best_ai_coding_tools_html(items):
    canonical = f"{BASE_URL}/guides/best-ai-coding-tools/"
    published = "2026-09-25"
    verified = "2026-09-25"
    title = "Best AI Coding Tools in 2026: Features, Pricing & Comparison | SXF / AI"
    description = "Compare Claude Code, OpenAI Codex, GitHub Copilot, Cursor and Windsurf/Devin Desktop in 2026 by agent workflow, pricing, IDE support, autonomy and team fit."

    tools = [
        {
            "name": "Claude Code",
            "best": "Terminal-first autonomous engineering",
            "surface": "CLI + IDE",
            "agent": "High",
            "free": "No",
            "starting": "$20/mo",
            "pricing": "Claude Pro is $20/month ($17/month equivalent on annual billing); Max starts at $100/month. Claude Code is included in paid Claude plans.",
            "source": "https://claude.com/pricing",
            "internal": "/topics/coding-ai/",
        },
        {
            "name": "OpenAI Codex",
            "best": "OpenAI / ChatGPT coding workflows",
            "surface": "Desktop + CLI + IDE + cloud",
            "agent": "High",
            "free": "Yes",
            "starting": "$0",
            "pricing": "Codex is available across ChatGPT plans. Free access exists for short coding tasks; Plus is $20/month, with higher-capacity Pro plans starting at $100/month. API-key usage is billed separately.",
            "source": "https://developers.openai.com/docs/pricing",
            "internal": "/topics/coding-ai/",
        },
        {
            "name": "GitHub Copilot",
            "best": "GitHub-native teams and broad IDE coverage",
            "surface": "IDE + GitHub + CLI + cloud",
            "agent": "High",
            "free": "Yes",
            "starting": "$0",
            "pricing": "Free includes limited usage. Individual paid plans currently start at Pro $10/month, with Pro+ at $39 and Max at $100.",
            "source": "https://github.com/features/copilot/plans",
            "internal": "/topics/github-copilot/",
        },
        {
            "name": "Cursor",
            "best": "AI-native editor with local and cloud agents",
            "surface": "AI IDE + cloud agents",
            "agent": "High",
            "free": "Yes",
            "starting": "$0",
            "pricing": "Hobby is free. Cursor Pro is $20/month and Teams starts at $40/user/month. Cloud Agents are billed using the selected model's API pricing.",
            "source": "https://cursor.com/pricing",
            "internal": "/topics/coding-ai/",
        },
        {
            "name": "Windsurf / Devin Desktop",
            "best": "Multi-agent command-center workflows",
            "surface": "AI IDE + local/cloud agents",
            "agent": "High",
            "free": "Yes",
            "starting": "$0",
            "pricing": "Windsurf has been renamed Devin Desktop. Current listed plans are Free $0, Pro $20/month and Max $200/month; team pricing is separate.",
            "source": "https://windsurf.com/editor",
            "internal": "/topics/coding-ai/",
        },
    ]

    rows = "".join(
        f'''<tr>
          <th scope="row"><a href="#{escape(slugify(t["name"]), quote=True)}">{escape(t["name"])}</a></th>
          <td>{escape(t["best"])}</td><td>{escape(t["surface"])}</td><td>{escape(t["agent"])}</td>
          <td>{escape(t["free"])}</td><td>{escape(t["starting"])}</td>
        </tr>'''
        for t in tools
    )

    toc = [
        ("quick-comparison", "Quick comparison"),
        ("how-we-evaluated", "How we evaluated"),
        ("claude-code", "Claude Code"),
        ("openai-codex", "OpenAI Codex"),
        ("github-copilot", "GitHub Copilot"),
        ("cursor", "Cursor"),
        ("windsurf-devin-desktop", "Windsurf / Devin Desktop"),
        ("large-codebases", "Best for large codebases"),
        ("autonomous-agents", "Best autonomous coding agent"),
        ("github-workflows", "Best for GitHub workflows"),
        ("free-tools", "Best free option"),
        ("claude-code-vs-cursor-vs-copilot", "Claude Code vs Cursor vs Copilot"),
        ("agent-vs-autocomplete", "AI agent vs autocomplete"),
        ("pricing", "Pricing explained"),
        ("faq", "FAQ"),
    ]
    toc_html = "".join(f'<a href="#{escape(anchor, quote=True)}">{escape(label)}</a>' for anchor,label in toc)

    source_links = "".join(
        f'<a href="{escape(t["source"], quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(t["name"])} official pricing/product page</span><b>↗</b></a>'
        for t in tools
    )

    faq = [
        ("What is the best AI coding tool in 2026?", "There is no universal winner because the products optimize different workflows. Claude Code is strongest as a terminal-first agent, Codex spans local and cloud OpenAI workflows, GitHub Copilot is deeply integrated with GitHub and many IDEs, Cursor is an AI-native editor with cloud agents, and Devin Desktop builds on Windsurf as a multi-agent command center."),
        ("What is the best AI coding tool for large codebases?", "For large repositories, the critical factors are context retrieval, environment setup, test execution and the ability to keep long tasks coherent. Claude Code, Codex and Cursor Cloud Agents are especially relevant when the task requires multi-file planning and verification rather than just completion."),
        ("Which AI coding tool is best for GitHub?", "GitHub Copilot has the most native GitHub surface area because it is built directly into GitHub workflows, including code review and cloud-agent features. Codex, Cursor and Claude Code can also work with GitHub repositories, but through different delegation models."),
        ("Are free AI coding tools good enough?", "Yes for evaluation and light work. GitHub Copilot, Cursor, Codex and Devin Desktop all have free entry points as of the verification date. Heavy agent sessions, premium models and team workflows usually require paid usage."),
        ("Is an AI coding agent the same as autocomplete?", "No. Autocomplete predicts or generates code around the current edit. An agent can inspect a repository, plan work, edit multiple files, run commands and tests, use tools, and sometimes continue remotely in its own development environment."),
        ("Should teams use one coding agent for everything?", "Usually not. The better architecture is to standardize security, review and repository rules, then choose the agent surface that fits each workflow. Inline coding, local debugging, cloud delegation and pull-request review have different operational requirements."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq)

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "TechArticle",
                "@id": canonical + "#article",
                "headline": "Best AI Coding Tools in 2026: Features, Pricing & Comparison",
                "description": description,
                "url": canonical,
                "mainEntityOfPage": canonical,
                "datePublished": published,
                "dateModified": verified,
                "author": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "creator": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "articleSection": "AI Coding",
                "keywords": [
                    "best AI coding tools 2026", "AI coding agents", "Claude Code", "OpenAI Codex",
                    "GitHub Copilot", "Cursor", "Windsurf", "Devin Desktop"
                ],
                "about": [{"@type": "SoftwareApplication", "name": t["name"], "url": t["source"]} for t in tools],
                "citation": [t["source"] for t in tools],
                "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Guides", "item": BASE_URL + "/guides/"},
                    {"@type": "ListItem", "position": 3, "name": "Best AI Coding Tools in 2026", "item": canonical},
                ],
            },
            {
                "@type": "ItemList",
                "name": "AI coding tools compared",
                "numberOfItems": len(tools),
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "name": t["name"], "url": t["source"]}
                    for i,t in enumerate(tools)
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q,a in faq
                ],
            },
        ],
    }

    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema, page_type="article")}
    <body class="intel-page guide-article-page">{page_header("guides")}<main>
      <article>
        <header class="guide-article-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span>AI Coding Tools</span></nav>
          <p class="eyebrow">SXF GUIDE / AI CODING</p>
          <h1>Best AI Coding Tools in 2026:<br><span>Features, Pricing & Comparison</span></h1>
          <p class="guide-deck">Claude Code, Codex, GitHub Copilot, Cursor and Windsurf have converged on the same destination — agentic software development — but they approach the job from very different surfaces. This guide compares the architecture of the workflow, not just the model name in the picker.</p>
          <div class="guide-byline">
            <div><span>Published</span><strong>September 25, 2026</strong></div>
            <div><span>Last verified</span><strong>September 25, 2026</strong></div>
            <div><span>Reading time</span><strong>18 min</strong></div>
            <div><span>Research standard</span><strong>Primary-source first</strong></div>
          </div>
        </header>

        <section class="guide-answer shell">
          <div class="guide-answer-label">QUICK ANSWER</div>
          <div><h2>There is no single “best” AI coding tool. The best choice depends on where you want the agent to work.</h2>
          <p><strong>Claude Code</strong> is the cleanest terminal-first agent. <strong>Codex</strong> is strongest when you want OpenAI’s coding stack across desktop, CLI, IDE and cloud. <strong>GitHub Copilot</strong> is the natural fit for GitHub-centric organizations. <strong>Cursor</strong> is the most integrated AI-first editor in this group, with local and cloud agents in one product. <strong>Windsurf, now Devin Desktop,</strong> is evolving toward a command center for managing multiple agents while retaining a full IDE.</p></div>
        </section>

        <div class="guide-reading shell">
          <aside class="guide-toc"><span>IN THIS GUIDE</span>{toc_html}<a class="guide-toc-top" href="#top">Back to top ↑</a></aside>

          <div class="guide-prose" id="top">
            <section id="quick-comparison">
              <p class="eyebrow">QUICK COMPARISON</p>
              <h2>Best AI coding tools in 2026 at a glance</h2>
              <p>The coding-tool market has moved beyond autocomplete. The important distinction in 2026 is whether a product can <em>close the loop</em>: understand the repository, make coordinated edits, execute tools, run tests, inspect failures and keep working until a task is actually verified.</p>
              <div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>Tool</th><th>Best fit</th><th>Main surface</th><th>Agentic workflow</th><th>Free entry</th><th>Starts at</th></tr></thead><tbody>{rows}</tbody></table></div>
              <p class="guide-fact-note">Pricing and product availability verified September 25, 2026. Subscription limits, model availability and usage-based charges can change independently of base plan prices.</p>
            </section>

            <section id="how-we-evaluated">
              <p class="eyebrow">METHODOLOGY</p>
              <h2>How we evaluated the best AI coding tools</h2>
              <p>A useful coding agent is not just a model wrapped in a chat panel. SXF evaluates the system around the model. We focus on seven things that determine whether an agent survives real engineering work:</p>
              <div class="guide-criteria">
                <article><span>01</span><h3>Repository understanding</h3><p>Can it retrieve the right files, symbols and history without flooding the context window?</p></article>
                <article><span>02</span><h3>Execution loop</h3><p>Can it edit, run commands, test, inspect failures and iterate instead of stopping after code generation?</p></article>
                <article><span>03</span><h3>Autonomy</h3><p>Can work continue across many steps or in a remote environment without constant human prompting?</p></article>
                <article><span>04</span><h3>Reviewability</h3><p>Can engineers see diffs, logs, test results and artifacts before accepting changes?</p></article>
                <article><span>05</span><h3>Workflow fit</h3><p>Does it live where the developer already works: terminal, IDE, GitHub, cloud or all four?</p></article>
                <article><span>06</span><h3>Cost model</h3><p>Is the economics predictable for daily use, or does heavy agent activity become usage-based?</p></article>
                <article><span>07</span><h3>Team controls</h3><p>Does it support policy, permissions, secrets, auditability and repeatable engineering instructions?</p></article>
              </div>
              <div class="guide-callout"><strong>Expert note</strong><p>We do not rank tools by vendor benchmark charts alone. Coding benchmarks can use different models, harnesses, reasoning settings and evaluation rules. Product architecture matters because the same model can perform very differently when retrieval, tools and verification loops change.</p></div>
            </section>

            <section class="tool-review" id="claude-code">
              <div class="tool-review-head"><span>01</span><div><p class="eyebrow">ANTHROPIC</p><h2>Claude Code: best for terminal-first autonomous engineering</h2></div></div>
              <p>Claude Code is fundamentally different from an editor assistant. Its center of gravity is the terminal and the repository, which makes it feel closer to a software-engineering agent than an AI feature inside an IDE. Anthropic also supports Claude Code in IDEs, but the mental model remains task delegation with tools rather than inline completion.</p>
              <p>That architecture is particularly effective for work that crosses many files: migrations, debugging, dependency changes, test repair, refactors and implementation tasks where the agent needs to inspect the codebase before it can decide what to change. Anthropic has also expanded the product with agent management, scheduled routines, computer use and multi-agent workflows.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>Repo-scale terminal workflows</strong></div><div><span>Primary surface</span><strong>CLI + IDE</strong></div><div><span>Paid access</span><strong>Pro from $20/mo</strong></div><div><span>Workflow style</span><strong>Agent-first</strong></div></div>
              <h3>Where Claude Code is strongest</h3>
              <p>Its advantage is not that “Claude writes better code” in every scenario. The advantage is that the product is comfortable operating as a long-running collaborator with direct access to development tools. For engineers who already live in a shell, that reduces interface friction and makes complex tasks feel natural.</p>
              <h3>What to watch</h3>
              <p>Usage limits are shared across Claude products on subscription plans, and heavy coding can consume capacity quickly. Teams should also design permission boundaries carefully because terminal agents become more useful as they receive more command, network and credential access.</p>
              <div class="tool-links"><a href="https://claude.com/product/claude-code" target="_blank" rel="noopener noreferrer">Claude Code official page ↗</a><a href="https://claude.com/pricing" target="_blank" rel="noopener noreferrer">Official pricing ↗</a><a href="/topics/coding-ai/">SXF Coding AI signals ↗</a></div>
            </section>

            <section class="tool-review" id="openai-codex">
              <div class="tool-review-head"><span>02</span><div><p class="eyebrow">OPENAI</p><h2>OpenAI Codex: best for OpenAI-native coding across local and cloud workflows</h2></div></div>
              <p>Codex is no longer one interface. It spans the desktop app, CLI, IDE extension and cloud execution, and OpenAI exposes related automation surfaces such as the Codex SDK, GitHub Action and cloud agent infrastructure. That makes Codex less like a single editor plugin and more like a coding layer across local and remote environments.</p>
              <p>The important architectural point is delegation. You can work interactively when the problem needs steering, or hand off a task to a cloud environment when you want the agent to keep running, test its changes and return with results. For teams already using ChatGPT and OpenAI models, this lowers the operational cost of introducing a separate coding stack.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>OpenAI / ChatGPT workflows</strong></div><div><span>Primary surface</span><strong>Desktop + CLI + IDE + cloud</strong></div><div><span>Entry</span><strong>Free plan available</strong></div><div><span>Workflow style</span><strong>Local + delegated cloud</strong></div></div>
              <h3>Where Codex is strongest</h3>
              <p>Codex makes sense when software work is part of a broader OpenAI workflow rather than an isolated coding feature. The product can move between interactive development, remote execution and automation, and API-key users can also build Codex into CI or shared engineering systems.</p>
              <h3>What to watch</h3>
              <p>There are two economics to understand: subscription usage when signing in with ChatGPT, and token/API pricing when using an API key. Those are not interchangeable. Teams should decide which path they are standardizing before they compare headline subscription prices.</p>
              <div class="tool-links"><a href="https://developers.openai.com/docs/" target="_blank" rel="noopener noreferrer">Codex documentation ↗</a><a href="https://developers.openai.com/docs/pricing" target="_blank" rel="noopener noreferrer">Official pricing ↗</a><a href="/topics/openai/">OpenAI intelligence ↗</a></div>
            </section>

            <section class="tool-review" id="github-copilot">
              <div class="tool-review-head"><span>03</span><div><p class="eyebrow">GITHUB</p><h2>GitHub Copilot: best for GitHub-native teams and broad IDE coverage</h2></div></div>
              <p>Copilot has evolved from completion into a portfolio of coding surfaces: inline suggestions, chat, agent mode, CLI, code review and cloud agents. Its structural advantage is GitHub itself. Repository hosting, pull requests, code review and agent delegation can live inside the same platform that already owns the team’s development workflow.</p>
              <p>GitHub also offers model choice and access to third-party coding agents on higher plans, so Copilot increasingly acts as an orchestration layer rather than a bet on one model. For organizations with many developers and mixed IDE preferences, that breadth is difficult to ignore.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>GitHub-centric organizations</strong></div><div><span>Primary surface</span><strong>IDE + GitHub + CLI</strong></div><div><span>Entry</span><strong>Free · Pro $10/mo</strong></div><div><span>Workflow style</span><strong>Assist + review + agents</strong></div></div>
              <h3>Where GitHub Copilot is strongest</h3>
              <p>The product is strongest when the organization wants one coding layer that follows developers from the editor to pull requests and review. It also has a lower individual paid entry price than several AI-first editors in this comparison.</p>
              <h3>What to watch</h3>
              <p>The new AI-credit model means “subscription price” is not the complete cost story for agent-heavy usage. Code completions remain unlimited on paid plans, but chats, agents and other AI features draw from credits depending on model and task complexity.</p>
              <div class="tool-links"><a href="https://github.com/features/copilot" target="_blank" rel="noopener noreferrer">GitHub Copilot ↗</a><a href="https://github.com/features/copilot/plans" target="_blank" rel="noopener noreferrer">Official plans ↗</a><a href="/topics/github-copilot/">SXF GitHub Copilot intelligence ↗</a></div>
            </section>

            <section class="tool-review" id="cursor">
              <div class="tool-review-head"><span>04</span><div><p class="eyebrow">CURSOR</p><h2>Cursor: best AI coding editor for integrated local and cloud agent workflows</h2></div></div>
              <p>Cursor’s advantage is product coherence. The editor, agent, model selection, codebase search and cloud agents are designed as one system. That matters because agentic development creates context switching: inspect locally, delegate remotely, review results, continue debugging. Cursor tries to keep those modes inside the same interface and account model.</p>
              <p>Its Cloud Agents run in isolated development environments with repositories, dependencies, secrets and network access. They can build, test and create pull requests without keeping your laptop online, and can be started from the editor, web, mobile, Slack, GitHub, Linear or API.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>AI-first editor workflows</strong></div><div><span>Primary surface</span><strong>Editor + cloud agents</strong></div><div><span>Entry</span><strong>Free · Pro $20/mo</strong></div><div><span>Cloud agent cost</span><strong>Model API pricing</strong></div></div>
              <h3>Where Cursor is strongest</h3>
              <p>Cursor is compelling for developers who want the AI agent to be the editor experience rather than an extension layered on top of an existing IDE. The cloud-agent system also makes parallel work and remote delegation a first-class workflow instead of an add-on.</p>
              <h3>What to watch</h3>
              <p>Cloud-agent economics can differ from the base subscription because remote runs are billed at the selected model’s API rate. Teams should measure real token use on their repositories rather than assume the $20 subscription is the ceiling.</p>
              <div class="tool-links"><a href="https://cursor.com/" target="_blank" rel="noopener noreferrer">Cursor ↗</a><a href="https://cursor.com/pricing" target="_blank" rel="noopener noreferrer">Official pricing ↗</a><a href="https://cursor.com/docs/cloud-agent" target="_blank" rel="noopener noreferrer">Cloud Agents docs ↗</a></div>
            </section>

            <section class="tool-review" id="windsurf-devin-desktop">
              <div class="tool-review-head"><span>05</span><div><p class="eyebrow">COGNITION</p><h2>Windsurf / Devin Desktop: best for managing multiple coding agents from one editor</h2></div></div>
              <p>There is an important naming change in 2026: Windsurf is now called <strong>Devin Desktop</strong>. The underlying IDE experience remains, but the product direction is explicitly moving toward an agent command center where engineers plan, delegate, review and manage local and cloud agents from one surface.</p>
              <p>This makes it less useful to think of Windsurf as “another AI editor.” The strategic idea is multi-agent supervision: the developer stays in a full IDE while several agents can do implementation work around them. Cognition also highlights Fast Context for codebase retrieval and unlimited access to its SWE-1.7 model on the current product page.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>Multi-agent supervision</strong></div><div><span>Primary surface</span><strong>IDE + agent command center</strong></div><div><span>Entry</span><strong>Free · Pro $20/mo</strong></div><div><span>Current name</span><strong>Devin Desktop</strong></div></div>
              <h3>Where Devin Desktop is strongest</h3>
              <p>The product is interesting for engineers who expect the future workflow to involve several agents rather than one chat session. The IDE stays available for deep inspection while the command-center layer is designed for delegation and review.</p>
              <h3>What to watch</h3>
              <p>The rebrand is recent, so search results, documentation and user language still mix “Windsurf” and “Devin Desktop.” For discovery, both names matter. For purchasing decisions, use the current Devin Desktop pricing and documentation rather than older Windsurf plan comparisons.</p>
              <div class="tool-links"><a href="https://windsurf.com/editor" target="_blank" rel="noopener noreferrer">Devin Desktop / Windsurf official page ↗</a><a href="/topics/coding-ai/">SXF Coding AI signals ↗</a></div>
            </section>

            <section id="large-codebases">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best AI coding tool for large codebases?</h2>
              <p>Large repositories expose the weakness of simplistic “context window” comparisons. A coding agent rarely succeeds by loading the entire repository into one prompt. It succeeds by retrieving the right slices of code, preserving task state, running the software and validating its own edits.</p>
              <p>For that reason, <strong>Claude Code, Codex and Cursor Cloud Agents</strong> are the most relevant tools in this group for repo-scale implementation work. Claude Code is attractive when the terminal and local environment are central. Codex is attractive when you want to move between local interaction and delegated cloud work. Cursor is attractive when the editor itself should coordinate both local and remote agents.</p>
              <div class="guide-callout"><strong>What to test on your own repository</strong><p>Give each tool the same multi-file bug or migration. Measure files inspected, unnecessary edits, test execution, recovery from a failing test, total review time and how often a human must re-explain repository context. That tells you more than a generic leaderboard.</p></div>
            </section>

            <section id="autonomous-agents">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>Which AI coding tool is best for autonomous coding agents?</h2>
              <p>All five products now have agentic capabilities, so “has agent mode” is no longer a meaningful differentiator. The useful question is where the agent runs and what verification loop surrounds it.</p>
              <p><strong>Cursor</strong> and <strong>Codex</strong> have clear local-to-cloud delegation stories. <strong>Claude Code</strong> is strong when autonomy lives close to the terminal and development environment. <strong>GitHub Copilot</strong> is compelling when delegation should start from issues, pull requests or the GitHub platform. <strong>Devin Desktop</strong> is explicitly designed around supervising multiple agents.</p>
            </section>

            <section id="github-workflows">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best AI coding tool for GitHub workflows and pull requests?</h2>
              <p>For a team whose engineering system already revolves around GitHub, <strong>GitHub Copilot</strong> has the structural advantage. Code review, cloud-agent work, repository context and account governance live inside the same platform. That reduces integration work and gives organizations a single control plane.</p>
              <p>The alternative is not “GitHub or another tool.” Codex, Cursor and Claude Code can all work with GitHub repositories. The tradeoff is whether GitHub should be the agent interface itself or simply the source-control system the agent hands work back to.</p>
            </section>

            <section id="free-tools">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best free AI coding tool in 2026?</h2>
              <p>If the goal is to evaluate the category before paying, there are multiple credible free entry points. <strong>GitHub Copilot Free</strong> includes limited completions and agent/chat usage. <strong>Cursor Hobby</strong> is free with limited agent requests. <strong>Codex</strong> has a free-plan entry for short coding tasks. <strong>Devin Desktop</strong> lists a free plan. Claude Code, by contrast, is included in paid Claude plans rather than Claude Free.</p>
              <p>Free tiers are useful for testing interaction design, but they are poor proxies for the economics of daily autonomous work. Agent sessions consume more model inference, tools and execution time than autocomplete, so serious evaluation should include a paid month and a real repository.</p>
            </section>

            <section id="claude-code-vs-cursor-vs-copilot">
              <p class="eyebrow">CHOOSING BETWEEN LEADERS</p>
              <h2>Claude Code vs Cursor vs GitHub Copilot: how should developers choose?</h2>
              <div class="guide-choice-grid">
                <article><span>Choose Claude Code when…</span><p>You want the terminal to be the primary interface, you delegate complex multi-file work, and you value an agent that feels close to the development environment.</p></article>
                <article><span>Choose Cursor when…</span><p>You want an AI-native editor where chat, editing, model selection and cloud agents feel like one integrated product.</p></article>
                <article><span>Choose GitHub Copilot when…</span><p>Your organization is standardized on GitHub, developers use mixed IDEs, and you want AI assistance, agents and review to share the existing repository platform.</p></article>
              </div>
              <p>Many advanced teams will use more than one. The key is to avoid overlapping tools without a reason. Define which tool owns inline assistance, which owns delegated implementation and which owns automated review.</p>
            </section>

            <section id="agent-vs-autocomplete">
              <p class="eyebrow">FOUNDATION</p>
              <h2>AI coding agent vs autocomplete: what changed?</h2>
              <p>Autocomplete answers a local question: <em>what code probably comes next?</em> An agent answers a systems question: <em>what sequence of actions completes this engineering task?</em></p>
              <div class="guide-difference">
                <div><span>AUTOCOMPLETE</span><strong>Predict → suggest → accept</strong><p>Fast, low-friction and ideal for local edits, boilerplate and repetitive code.</p></div>
                <div><span>CODING AGENT</span><strong>Inspect → plan → edit → run → verify</strong><p>Higher cost and more operational risk, but able to handle tasks that span files, tools and time.</p></div>
              </div>
              <p>This distinction explains why pricing is changing across the category. A completion can be measured as a short inference. An agent may use a frontier model repeatedly, search a repository, call tools, create environments and run tests. The product economics increasingly look like compute orchestration rather than a simple IDE subscription.</p>
            </section>

            <section id="pricing">
              <p class="eyebrow">PRICING GUIDE</p>
              <h2>AI coding tool pricing in 2026: why the monthly fee is only part of the cost</h2>
              <p>The headline subscription price is useful for lightweight interactive coding, but autonomous work introduces a second layer: usage. GitHub uses AI credits for many agent interactions. Cursor Cloud Agents are billed at model API pricing. Codex can run against a ChatGPT allowance or an API key. Claude paid plans share usage across Claude and Claude Code, with optional usage credits. The result is that two developers on the same $20 plan can have very different effective costs.</p>
              <div class="guide-pricing-list">
                {"".join(f'<div><strong>{escape(t["name"])}</strong><p>{escape(t["pricing"])}</p><a href="{escape(t["source"], quote=True)}" target="_blank" rel="noopener noreferrer">Verify pricing ↗</a></div>' for t in tools)}
              </div>
              <div class="guide-callout"><strong>SXF cost rule</strong><p>For teams, compare cost per accepted engineering task — not cost per seat. Include agent usage, review time, failed runs and the human time required to recover from wrong changes.</p></div>
            </section>

            <section class="guide-faq-section" id="faq">
              <p class="eyebrow">FAQ</p>
              <h2>Frequently asked questions about AI coding tools</h2>
              <div class="model-faq">{faq_html}</div>
            </section>

            <section class="guide-sources">
              <p class="eyebrow">PRIMARY SOURCES</p>
              <h2>Official documentation used for this guide</h2>
              <p>Pricing and product capabilities change quickly. SXF links directly to the vendor pages used for verification so readers can check the current state before purchasing.</p>
              <div class="model-sources">{source_links}</div>
            </section>
          </div>
        </div>
      </article>
    </main>{page_footer()}</body></html>'''


def gpt6_vs_claude_guide_html(items):
    canonical = f"{BASE_URL}/guides/gpt-6-vs-claude/"
    published = "2026-09-25"
    verified = "2026-09-25"
    title = "GPT-6 vs Claude in 2026: Models, Pricing, Coding, Context & API Comparison | SXF / AI"
    description = "GPT-6 vs Claude in 2026: compare Astra, Sol and Luna with Claude Fable 5.1, Opus 5.5, Sonnet 5 and Haiku 4.5 on pricing, context, coding, agents and APIs."

    openai_models = [
        {
            "name":"GPT-6 Astra","id":"gpt-6-astra","role":"Highest capability","context":"1.05M","output":"128K",
            "input":"$10","cached":"$1","output_price":"$50","reasoning":"Low → Max",
            "best":"Hardest end-to-end reasoning, coding, research and computer use",
            "source":"https://developers.openai.com/api/docs/models/gpt-6-astra",
            "internal":"/models/gpt-6-astra/"
        },
        {
            "name":"GPT-6 Sol","id":"gpt-6-sol","role":"Capability / cost balance","context":"1.05M","output":"128K",
            "input":"$2","cached":"$0.20","output_price":"$10","reasoning":"None → Max",
            "best":"Complex coding and agentic workflows",
            "source":"https://developers.openai.com/api/docs/models/gpt-6-sol",
            "internal":"/models/gpt-6-sol/"
        },
        {
            "name":"GPT-6 Luna","id":"gpt-6-luna","role":"Efficiency","context":"1.05M","output":"128K",
            "input":"$0.10","cached":"$0.01","output_price":"$0.50","reasoning":"None → Max",
            "best":"Focused, high-volume and cost-sensitive work",
            "source":"https://developers.openai.com/api/docs/models/gpt-6-luna",
            "internal":"/models/gpt-6-luna/"
        },
    ]
    claude_models = [
        {
            "name":"Claude Fable 5.1","id":"claude-fable-5-1","role":"Demanding reasoning","context":"1M","output":"128K",
            "input":"$10","cached":"$0.25","output_price":"$50","reasoning":"Adaptive · always on",
            "best":"Long-horizon agentic work and demanding reasoning",
            "source":"https://platform.claude.com/docs/en/models/fable-5-1/overview"
        },
        {
            "name":"Claude Opus 5.5","id":"claude-opus-5-5","role":"Agentic coding / knowledge work","context":"1M","output":"128K",
            "input":"$4","cached":"$0.20","output_price":"$20","reasoning":"Adaptive · always on",
            "best":"Long-running agentic coding and knowledge work",
            "source":"https://platform.claude.com/docs/en/models/opus-5-5/overview",
            "internal":"/models/claude-opus-5-5/"
        },
        {
            "name":"Claude Sonnet 5","id":"claude-sonnet-5","role":"Speed / intelligence balance","context":"1M","output":"128K",
            "input":"$2","cached":"$0.20","output_price":"$10","reasoning":"Adaptive",
            "best":"Everyday coding, agents, analysis and enterprise work",
            "source":"https://platform.claude.com/docs/en/models/sonnet-5/whats-new-sonnet-5"
        },
        {
            "name":"Claude Haiku 4.5","id":"claude-haiku-4-5","role":"Lowest latency / cost","context":"200K","output":"64K",
            "input":"$1","cached":"$0.10","output_price":"$5","reasoning":"Extended thinking",
            "best":"Real-time and high-volume cost-sensitive workloads",
            "source":"https://platform.claude.com/docs/en/models/haiku-4-5/overview"
        },
    ]

    all_models = openai_models + claude_models
    rows = "".join(
        f'''<tr>
          <th scope="row">{f'<a href="{escape(m.get("internal"), quote=True)}">{escape(m["name"])}</a>' if m.get("internal") else escape(m["name"])}<small>{escape(m["id"])}</small></th>
          <td>{escape("OpenAI" if m in openai_models else "Anthropic")}</td>
          <td>{escape(m["role"])}</td><td>{escape(m["context"])}</td><td>{escape(m["output"])}</td>
          <td>{escape(m["reasoning"])}</td><td>{escape(m["input"])}</td><td>{escape(m["cached"])}</td><td>{escape(m["output_price"])}</td>
        </tr>'''
        for m in all_models
    )

    def cost(input_rate, output_rate, in_m, out_m):
        value = input_rate * in_m + output_rate * out_m
        return ("$" + f"{value:,.4f}").rstrip("0").rstrip(".")

    # Standard short-context example: 100K input + 10K output.
    short = [
        ("GPT-6 Astra", cost(10,50,.1,.01)),
        ("Claude Fable 5.1", cost(10,50,.1,.01)),
        ("GPT-6 Sol", cost(2,10,.1,.01)),
        ("Claude Sonnet 5", cost(2,10,.1,.01)),
        ("Claude Opus 5.5", cost(4,20,.1,.01)),
        ("GPT-6 Luna", cost(.1,.5,.1,.01)),
        ("Claude Haiku 4.5", cost(1,5,.1,.01)),
    ]
    short_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>100K input + 10K output</small></div>' for n,c in short)

    # Long-context example: 500K input + 50K output.
    # GPT-6 uses 2x input and 1.5x output above 272K input; Claude 1M models keep standard token pricing.
    long = [
        ("GPT-6 Astra", cost(20,75,.5,.05)),
        ("Claude Fable 5.1", cost(10,50,.5,.05)),
        ("GPT-6 Sol", cost(4,15,.5,.05)),
        ("Claude Sonnet 5", cost(2,10,.5,.05)),
        ("Claude Opus 5.5", cost(4,20,.5,.05)),
        ("GPT-6 Luna", cost(.2,.75,.5,.05)),
    ]
    long_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>500K input + 50K output</small></div>' for n,c in long)

    toc = [
        ("quick-answer","Quick answer"),
        ("family-map","GPT-6 and Claude model map"),
        ("pricing","GPT-6 vs Claude pricing"),
        ("context-window","Context window and long context"),
        ("coding","Coding"),
        ("reasoning","Reasoning"),
        ("agents","Agents and tool use"),
        ("api","API differences"),
        ("multimodal","Multimodal capabilities"),
        ("speed","Speed and latency"),
        ("research-writing","Research and writing"),
        ("business","Business and enterprise"),
        ("which-model","Which model should you use?"),
        ("gpt6-vs-claude-opus","GPT-6 vs Claude Opus 5.5"),
        ("faq","FAQ"),
    ]
    toc_html = "".join(f'<a href="#{escape(a, quote=True)}">{escape(label)}</a>' for a,label in toc)

    sources = [
        ("OpenAI GPT-6 model catalog","https://developers.openai.com/api/docs/models"),
        ("OpenAI GPT-6 guidance","https://developers.openai.com/api/docs/guides/latest-model"),
        ("OpenAI GPT-6 Astra","https://developers.openai.com/api/docs/models/gpt-6-astra"),
        ("OpenAI GPT-6 Sol","https://developers.openai.com/api/docs/models/gpt-6-sol"),
        ("OpenAI GPT-6 Luna","https://developers.openai.com/api/docs/models/gpt-6-luna"),
        ("Anthropic current models","https://platform.claude.com/docs/en/models/overview"),
        ("Claude Fable 5.1","https://platform.claude.com/docs/en/models/fable-5-1/overview"),
        ("Claude Opus 5.5","https://platform.claude.com/docs/en/models/opus-5-5/overview"),
        ("Claude Sonnet 5","https://platform.claude.com/docs/en/models/sonnet-5/whats-new-sonnet-5"),
        ("Claude context windows","https://platform.claude.com/docs/en/build-with-claude/context-windows"),
        ("Claude API pricing","https://platform.claude.com/docs/en/about-claude/pricing"),
    ]
    source_links = "".join(f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(label)}</span><b>↗</b></a>' for label,url in sources)

    faq = [
        ("Is GPT-6 better than Claude?", "There is no defensible universal answer from vendor specifications alone. GPT-6 and Claude each contain several models optimized for different capability, latency and cost targets. The useful comparison is workload-specific: model tier, token economics, tool stack, reasoning controls and your own evaluation results."),
        ("Which is cheaper, GPT-6 or Claude?", "At standard short-context rates, GPT-6 Astra and Claude Fable 5.1 both list $10 input and $50 output per million tokens, while GPT-6 Sol and Claude Sonnet 5 both list $2 and $10. GPT-6 Luna is much cheaper than Claude Haiku 4.5 at $0.10/$0.50 versus $1/$5. Long-context economics differ because GPT-6 applies higher rates above 272K input tokens while Claude's 1M models keep standard token pricing."),
        ("Which has the larger context window, GPT-6 or Claude?", "GPT-6 Astra, Sol and Luna each list 1,050,000 tokens. Claude Fable 5.1, Opus 5.5 and Sonnet 5 list 1,000,000 tokens. Claude Haiku 4.5 lists 200,000 tokens. Maximum output is 128K on the GPT-6 family and the three larger Claude models, while Haiku 4.5 lists 64K."),
        ("Which is better for coding, GPT-6 or Claude?", "Both vendors explicitly position current models for coding. OpenAI describes GPT-6 Sol as built for complex coding and agentic workflows and Astra for the hardest end-to-end work. Anthropic positions Opus 5.5 for long-running agentic coding, Sonnet 5 for everyday coding and Fable 5.1 for demanding long-horizon work. The better choice depends on your repository, tools, latency target and cost profile."),
        ("Which is better for AI agents?", "Both platforms now expose serious agent tool stacks. GPT-6 through the Responses API supports built-in tools including web search, file search, code interpreter, hosted shell, computer use and MCP. Claude supports server and client tools including web search, web fetch, code execution, computer use, browser use, tool search and MCP. Tool architecture and operational fit matter as much as the base model."),
        ("Is GPT-6 vs Claude the same as ChatGPT vs Claude?", "No. GPT-6 and Claude refer to model families and APIs. ChatGPT and the Claude app are consumer or workplace products with their own plan limits, interface features, connectors and routing behavior. An API comparison should not be treated as a complete comparison of the apps."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq)

    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"TechArticle","@id":canonical+"#article","url":canonical,"mainEntityOfPage":canonical,
                "headline":"GPT-6 vs Claude in 2026: Models, Pricing, Coding, Context & API Comparison",
                "description":description,"datePublished":published,"dateModified":verified,
                "author":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "creator":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "isPartOf":{"@id":"https://sxf.si/#website"},
                "articleSection":"AI Models",
                "keywords":["GPT-6 vs Claude","GPT-6 vs Claude 2026","GPT-6 vs Claude pricing","GPT-6 vs Claude coding","GPT-6 vs Claude API","GPT-6 vs Claude context window","GPT-6 vs Claude Opus 5.5"],
                "about":[{"@type":"Thing","name":"GPT-6"},{"@type":"Thing","name":"Claude"}],
                "citation":[url for _label,url in sources],
                "inLanguage":"en"
            },
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},
                {"@type":"ListItem","position":2,"name":"Guides","item":BASE_URL+"/guides/"},
                {"@type":"ListItem","position":3,"name":"GPT-6 vs Claude","item":canonical}
            ]},
            {"@type":"ItemList","name":"GPT-6 and Claude models compared","numberOfItems":len(all_models),"itemListElement":[
                {"@type":"ListItem","position":i+1,"name":m["name"],"url":m["source"]} for i,m in enumerate(all_models)
            ]},
            {"@type":"FAQPage","mainEntity":[
                {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq
            ]}
        ]
    }

    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema, page_type="article")}
    <body class="intel-page guide-article-page">{page_header("guides")}<main>
      <article>
        <header class="guide-article-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span>GPT-6 vs Claude</span></nav>
          <p class="eyebrow">SXF GUIDE / FRONTIER MODELS</p>
          <h1>GPT-6 vs Claude in 2026:<br><span>Models, Pricing, Coding, Context & API</span></h1>
          <p class="guide-deck">GPT-6 and Claude are no longer single-model comparisons. They are model families with different tiers, reasoning controls, long-context economics and agent stacks. This guide compares the systems layer by layer so you can choose for a real workload instead of comparing brand names.</p>
          <div class="guide-byline">
            <div><span>Published</span><strong>September 25, 2026</strong></div>
            <div><span>Last verified</span><strong>September 25, 2026</strong></div>
            <div><span>Reading time</span><strong>22 min</strong></div>
            <div><span>Evidence</span><strong>Official model docs</strong></div>
          </div>
        </header>

        <section class="guide-answer shell" id="quick-answer">
          <div class="guide-answer-label">QUICK ANSWER</div>
          <div><h2>GPT-6 vs Claude is really a question of model tier, workload shape and agent architecture.</h2>
          <p>At the top end, <strong>GPT-6 Astra</strong> and <strong>Claude Fable 5.1</strong> carry the same listed $10/$50 standard token price and nearly the same context size. In the balanced tier, <strong>GPT-6 Sol</strong> and <strong>Claude Sonnet 5</strong> are both $2/$10. Anthropic inserts <strong>Claude Opus 5.5</strong> between those tiers for long-running agentic coding at $4/$20. At the efficiency end, <strong>GPT-6 Luna</strong> is dramatically cheaper than Claude Haiku 4.5 on listed token rates. The biggest hidden difference is long context: GPT-6 applies higher pricing above 272K input tokens, while Anthropic bills its 1M-context Claude models at standard token rates.</p></div>
        </section>

        <div class="guide-reading shell">
          <aside class="guide-toc"><span>IN THIS GUIDE</span>{toc_html}<a class="guide-toc-top" href="#top">Back to top ↑</a></aside>

          <div class="guide-prose" id="top">
            <section id="family-map">
              <p class="eyebrow">MODEL FAMILY MAP</p>
              <h2>GPT-6 and Claude are families, not one-to-one models</h2>
              <p>The first mistake in a GPT-6 vs Claude comparison is treating each brand as one model. OpenAI currently splits GPT-6 into Astra, Sol and Luna. Anthropic's current lineup includes Fable 5.1, Opus 5.5, Sonnet 5 and Haiku 4.5. Those tiers do not map perfectly, but their pricing and positioning reveal useful comparison pairs.</p>
              <div class="guide-matchup-grid">
                <article><span>TOP-END</span><h3>GPT-6 Astra ↔ Claude Fable 5.1</h3><p>Both list $10 input / $50 output per million tokens and roughly one million tokens of context. OpenAI positions Astra for its hardest end-to-end work; Anthropic reserves Fable for demanding reasoning and long-horizon agents.</p></article>
                <article><span>EVERYDAY / BALANCED</span><h3>GPT-6 Sol ↔ Claude Sonnet 5</h3><p>Both list $2 input / $10 output. Sol is positioned around complex coding and agents; Sonnet 5 around speed plus intelligence for everyday coding, agents and enterprise tasks.</p></article>
                <article><span>AGENTIC CODING</span><h3>GPT-6 Sol ↔ Claude Opus 5.5</h3><p>This is the more interesting coding comparison. Opus 5.5 costs twice Sol at standard token rates, but Anthropic specifically targets long-running agentic coding and keeps standard rates across its 1M context.</p></article>
                <article><span>EFFICIENCY</span><h3>GPT-6 Luna ↔ Claude Haiku 4.5</h3><p>Both target efficient, high-volume work, but their economics are far apart: Luna lists $0.10/$0.50 while Haiku lists $1/$5, and Luna also has a much larger context window.</p></article>
              </div>

              <div class="guide-table-wrap"><table class="guide-table family-table"><thead><tr><th>Model</th><th>Provider</th><th>Positioning</th><th>Context</th><th>Max output</th><th>Thinking</th><th>Input</th><th>Cached</th><th>Output</th></tr></thead><tbody>{rows}</tbody></table></div>
              <p class="guide-fact-note">Prices are USD per 1M text tokens at standard listed rates. GPT-6 long-context pricing changes above 272K input tokens; Claude's 1M-context models use standard token pricing across that context window.</p>
            </section>

            <section id="pricing">
              <p class="eyebrow">GPT-6 VS CLAUDE PRICING</p>
              <h2>Which is cheaper: GPT-6 or Claude?</h2>
              <p>At short context, the answer depends entirely on tier. Astra and Fable 5.1 have identical headline input/output prices. Sol and Sonnet 5 also have identical headline prices. Opus 5.5 occupies a higher-cost coding tier. Luna is the outlier: its token price is one-tenth of Haiku 4.5's listed rate.</p>
              <h3>Example: 100K input tokens + 10K output tokens</h3>
              <div class="cost-grid guide-cost-grid">{short_cards}</div>
              <p>The short-context numbers expose why brand-level statements like “Claude is cheaper” or “GPT is cheaper” are misleading. The model tier matters more than the logo.</p>

              <h3>Long-context economics change the comparison</h3>
              <p>OpenAI states that GPT-6 requests above 272K input tokens are billed at <strong>2× input/cache rates and 1.5× output rates for the full request</strong>. Anthropic states that its 1M-context models use 1M as the default and that long-context requests are billed at standard pricing.</p>
              <h3>Example: 500K input tokens + 50K output tokens</h3>
              <div class="cost-grid guide-cost-grid">{long_cards}</div>
              <p class="guide-fact-note">Claude Haiku 4.5 is excluded from the 500K example because its context window is 200K. These examples cover token charges only; tools, regional processing, fast tiers, caching and other platform charges can alter total cost.</p>
              <div class="guide-callout"><strong>SXF analysis</strong><p>For short prompts, GPT-6 Sol and Claude Sonnet 5 have essentially the same headline token economics. For very long prompts, Claude Sonnet 5 becomes materially cheaper than Sol because Anthropic does not add a long-context multiplier. That is a workload-level difference, not a generic statement that one vendor is cheaper.</p></div>
            </section>

            <section id="context-window">
              <p class="eyebrow">CONTEXT WINDOW</p>
              <h2>GPT-6 vs Claude context window: 1.05M vs 1M is not the whole story</h2>
              <p>GPT-6 Astra, Sol and Luna each list a <strong>1,050,000-token</strong> context window and <strong>128,000 max output tokens</strong>. Claude Fable 5.1, Opus 5.5 and Sonnet 5 each list <strong>1,000,000 tokens</strong> of context and <strong>128,000 max output</strong>. Claude Haiku 4.5 is smaller at 200K context and 64K max output.</p>
              <p>The raw 50K-token difference between 1.05M and 1M is unlikely to be the deciding factor for most systems. Retrieval quality, prompt structure, tool results, cached prefixes and how much context remains after reasoning tokens often matter more. The pricing rule above 272K is more operationally important than the 5% difference in nominal context.</p>
              <h3>Which is better for long documents and giant codebases?</h3>
              <p>For a one-shot request that genuinely needs 500K–1M tokens, Claude's standard long-context billing is economically attractive. For agentic systems, the better design may be to avoid repeatedly sending huge contexts at all: use retrieval, caching, compaction and tools to keep the active working set smaller.</p>
            </section>

            <section id="coding">
              <p class="eyebrow">GPT-6 VS CLAUDE FOR CODING</p>
              <h2>Which is better for coding: GPT-6 or Claude?</h2>
              <p>Both vendors explicitly optimize current models for software engineering, but they emphasize different tiers. OpenAI calls GPT-6 Sol a model built for complex coding and agentic workflows and positions Astra above it for the hardest end-to-end work. Anthropic positions Opus 5.5 for long-running agentic coding, Sonnet 5 for everyday coding and Fable 5.1 for demanding long-horizon work.</p>
              <p>That means the useful comparison is not “GPT-6 vs Claude coding score.” It is <strong>Sol vs Sonnet for everyday economics</strong>, <strong>Sol vs Opus 5.5 for long-running agents</strong>, and <strong>Astra vs Fable 5.1 when capability matters more than latency or token cost</strong>.</p>
              <div class="guide-choice-grid">
                <article><span>Use GPT-6 Sol when…</span><p>You want OpenAI's complex coding/agent tier at $2/$10 and your workflow benefits from explicit reasoning-effort controls and the Responses API tool stack.</p></article>
                <article><span>Use Claude Opus 5.5 when…</span><p>Your workload is long-running agentic coding and you value Anthropic's 1M context at standard rates, adaptive thinking and Claude's tool ecosystem.</p></article>
                <article><span>Use Astra or Fable when…</span><p>The task is difficult enough that cost and latency are secondary to getting a stronger end-to-end result. Test both on your own repository rather than extrapolating from vendor charts.</p></article>
              </div>
              <p>For product-level coding workflows, also separate the models from the coding tools around them. A developer using Claude Code is evaluating a different system than someone calling Claude through a raw API; the same is true for Codex versus a direct GPT-6 API call.</p>
              <div class="tool-links"><a href="/guides/best-ai-coding-tools/">Best AI Coding Tools in 2026 ↗</a><a href="/compare/gpt-6-sol-vs-claude-opus-5-5/">Sol vs Opus 5.5 deep dive ↗</a><a href="/topics/coding-ai/">Coding AI signals ↗</a></div>
            </section>

            <section id="reasoning">
              <p class="eyebrow">REASONING CONTROLS</p>
              <h2>GPT-6 vs Claude reasoning: explicit effort vs adaptive thinking</h2>
              <p>OpenAI exposes a broad reasoning-effort ladder on GPT-6. Astra supports low through max. Sol and Luna additionally support <strong>none</strong>, which lets applications trade reasoning depth for latency and cost on simpler requests.</p>
              <p>Claude's newest models lean more heavily on adaptive thinking. Fable 5.1 and Opus 5.5 keep adaptive thinking always on, with default effort levels of high and medium respectively. Sonnet 5 uses adaptive thinking and allows it to be disabled; Haiku 4.5 uses the older extended-thinking model.</p>
              <div class="guide-callout"><strong>Why this matters</strong><p>Reasoning controls affect more than benchmark quality. They change latency, output-token consumption, cache behavior and how deterministic your cost envelope feels. For production systems, the ability to route easy work to lighter reasoning can be as valuable as peak capability.</p></div>
            </section>

            <section id="agents">
              <p class="eyebrow">AGENTS & TOOL USE</p>
              <h2>GPT-6 vs Claude for AI agents: both are now full agent platforms</h2>
              <p>The agent comparison is no longer “which model can call a function.” Both ecosystems expose substantial tool infrastructure.</p>
              <div class="guide-difference agent-platform-grid">
                <div><span>OPENAI / RESPONSES API</span><strong>Built-in execution surfaces</strong><p>GPT-6 model pages list support for web search, file search, image generation, code interpreter, hosted shell, apply patch, skills, computer use, MCP and tool search, in addition to function calling and structured outputs.</p></div>
                <div><span>ANTHROPIC / MESSAGES API</span><strong>Server + client tool architecture</strong><p>Claude supports server tools such as web search, web fetch, code execution, advisor and tool search, plus MCP. Anthropic also defines client toolsets for computer use, browser use, bash, text editing and memory.</p></div>
              </div>
              <h3>Which agent stack is better?</h3>
              <p>That cannot be answered responsibly from a feature checklist. The engineering questions are: where tools execute, how credentials are isolated, how state persists, how failures are retried, what is billed separately, and how easy it is to inspect what the agent actually did. The right answer can change by deployment architecture even when the model quality is similar.</p>
            </section>

            <section id="api">
              <p class="eyebrow">API COMPARISON</p>
              <h2>GPT-6 vs Claude API: Responses API vs Messages API</h2>
              <p>OpenAI recommends the <strong>Responses API</strong> as the primary path for new GPT-6 applications. It combines model output with built-in tools, stateful workflows and agent features. Claude's core interface is the <strong>Messages API</strong>, with tool calls represented as structured content blocks and an expanding set of Anthropic-hosted server tools.</p>
              <p>Both platforms support function/tool calling, vision, streaming and MCP-based integration. The deeper difference is interface philosophy. OpenAI increasingly bundles execution primitives directly around Responses. Anthropic distinguishes server tools from client tools more explicitly and gives developers detailed control over where execution occurs.</p>
              <h3>Migration cost matters more than syntax</h3>
              <p>If your application already depends on one provider's prompt caching, reasoning format, tool schemas, safety handling or streaming events, switching is not just replacing a model ID. The model may be API-compatible at the HTTP level while the surrounding control plane is not.</p>
            </section>

            <section id="multimodal">
              <p class="eyebrow">MULTIMODAL</p>
              <h2>GPT-6 vs Claude multimodal capabilities</h2>
              <p>Current GPT-6 models accept <strong>text and image input</strong> and return text. OpenAI's model pages list audio and video as unsupported for these GPT-6 text models. Anthropic's current Claude lineup also supports text and image input with text output, plus vision across the family.</p>
              <p>If your application needs speech, realtime audio or native image generation, the comparison moves beyond GPT-6 vs Claude base models and into each vendor's specialized model and tool ecosystem. Do not infer multimodal breadth from the flagship language-model name alone.</p>
            </section>

            <section id="speed">
              <p class="eyebrow">SPEED & LATENCY</p>
              <h2>Which is faster: GPT-6 or Claude?</h2>
              <p>There is no clean cross-vendor answer in the official documentation. Anthropic publishes relative latency labels inside its own lineup: Fable 5.1 is slower, Opus 5.5 moderate, Sonnet 5 fast and Haiku 4.5 fastest. OpenAI exposes model-specific speed characteristics but does not provide a directly comparable, standardized latency number against Claude.</p>
              <p>A serious latency test should measure <strong>time to first token, total completion time, output tokens per second, tool-call round trips and p95/p99 latency</strong> from the region where your application actually runs. Reasoning effort must be held constant enough to make the comparison meaningful.</p>
              <div class="guide-callout"><strong>Do not benchmark the brand</strong><p>“GPT-6 vs Claude speed” is too broad. Benchmark the exact model, effort setting, service tier, prompt length, output length and tool path you plan to deploy.</p></div>
            </section>

            <section id="research-writing">
              <p class="eyebrow">RESEARCH & WRITING</p>
              <h2>GPT-6 vs Claude for research, writing and knowledge work</h2>
              <p>OpenAI positions Astra for research and document creation and describes Sol as a strong everyday driver for writing, coding and work that needs judgment. Anthropic positions Opus 5.5 for long-running knowledge work, Fable 5.1 for multi-step research and demanding reasoning, and Sonnet 5 for everyday content creation and analysis.</p>
              <p>For research systems, the surrounding tools again matter. Both providers offer web access and code execution paths. Citation quality, source-selection behavior and document handling should be tested on the actual research workflow rather than assumed from generic model intelligence.</p>
              <h3>What about long reports?</h3>
              <p>Both top families can emit up to 128K tokens in a single response under their documented limits, although practical applications usually benefit from structured generation, intermediate validation and section-by-section review. Anthropic additionally documents a 300K max-output beta for Opus 5.5 in the Batch API.</p>
            </section>

            <section id="business">
              <p class="eyebrow">ENTERPRISE</p>
              <h2>GPT-6 vs Claude for business and enterprise AI</h2>
              <p>Enterprise choice should not start with “which chatbot feels smarter.” It should start with deployment requirements: data residency, cloud availability, identity and governance, auditability, tool permissions, rate limits, procurement and the cost of operating agents at scale.</p>
              <p>Anthropic distributes current Claude models through the Claude API and major cloud platforms including Amazon Bedrock, Google Cloud and Microsoft Foundry. OpenAI exposes GPT-6 through its API platform with data-residency options that vary by model and processing tier. For regulated workloads, verify the exact model, region and service tier rather than assuming a family-wide policy.</p>
              <h3>Multi-model routing may be better than choosing one vendor model</h3>
              <p>Both companies' own guidance points toward workload-specific model selection. In practice, a robust system often routes easy/high-volume requests to an efficient model and escalates difficult tasks to a stronger one. The unit of optimization is therefore the <em>workflow</em>, not the prestige of the default model.</p>
            </section>

            <section id="which-model">
              <p class="eyebrow">DECISION GUIDE</p>
              <h2>Which GPT-6 or Claude model should you use?</h2>
              <div class="guide-decision-table">
                <div><span>Hardest end-to-end work</span><strong>GPT-6 Astra or Claude Fable 5.1</strong><p>Both occupy the $10/$50 top tier. Run your own evals on the exact task.</p></div>
                <div><span>Everyday coding and agents</span><strong>GPT-6 Sol or Claude Sonnet 5</strong><p>Both list $2/$10 standard pricing; ecosystem and long-context behavior become key differentiators.</p></div>
                <div><span>Long-running agentic coding</span><strong>Claude Opus 5.5 or GPT-6 Sol</strong><p>Opus is explicitly positioned for this workload; Sol is half the standard token price and built for complex coding/agents.</p></div>
                <div><span>Huge prompts above 272K</span><strong>Claude 1M models deserve a close look</strong><p>Anthropic keeps standard token pricing across 1M context; GPT-6 raises rates once input exceeds 272K.</p></div>
                <div><span>High-volume low-cost automation</span><strong>GPT-6 Luna</strong><p>Its $0.10/$0.50 listed rate is materially below Claude Haiku 4.5's $1/$5, while also offering a larger context window.</p></div>
                <div><span>Lowest latency inside Claude</span><strong>Claude Haiku 4.5</strong><p>Anthropic labels it the fastest current Claude model; test against Luna if cross-vendor latency matters.</p></div>
              </div>
            </section>

            <section id="gpt6-vs-claude-opus">
              <p class="eyebrow">DEEP DIVE</p>
              <h2>GPT-6 vs Claude Opus 5.5: which comparison matters most?</h2>
              <p>“GPT-6 vs Claude Opus” can refer to several different pairings. If the question is cost-balanced coding, GPT-6 Sol is the logical OpenAI comparison. If the question is absolute capability, Astra is the higher OpenAI tier. That distinction matters because Sol is $2/$10 while Opus 5.5 is $4/$20, whereas Astra is $10/$50.</p>
              <p>For a detailed Sol-specific comparison—including cache pricing, long-context cost examples and reasoning controls—use the dedicated SXF comparison below.</p>
              <div class="guide-inline-cta"><div><span>SXF DEEP DIVE</span><strong>GPT-6 Sol vs Claude Opus 5.5</strong><p>Pricing, context, reasoning controls and long-context economics using official vendor specifications.</p></div><a href="/compare/gpt-6-sol-vs-claude-opus-5-5/">Open comparison ↗</a></div>
            </section>

            <section class="guide-faq-section" id="faq">
              <p class="eyebrow">FAQ</p>
              <h2>Frequently asked questions about GPT-6 vs Claude</h2>
              <div class="model-faq">{faq_html}</div>
            </section>

            <section class="guide-sources">
              <p class="eyebrow">PRIMARY SOURCES</p>
              <h2>Official sources used for this comparison</h2>
              <p>This guide separates vendor-documented specifications from SXF analysis. Pricing, context windows, reasoning controls and product positioning were checked against the official documentation linked below.</p>
              <div class="model-sources">{source_links}</div>
            </section>
          </div>
        </div>
      </article>
    </main>{page_footer()}</body></html>'''


def open_source_ai_models_guide_html(items):
    canonical = f"{BASE_URL}/guides/open-source-ai-models/"
    published = "2026-09-26"
    verified = "2026-09-26"
    title = "Best Open-Source AI Models in 2026: Licenses, Hardware & Local Use | SXF / AI"
    description = "Compare the best open-source and open-weight AI models in 2026: DeepSeek V4-Pro, Qwen3.5, GLM-5, Mistral Small 4, Gemma 4 and Kimi K3 by license, size, context and local use."

    models = [
        {
            "name":"DeepSeek V4-Pro","publisher":"DeepSeek","license":"MIT","openness":"Permissive weights",
            "params":"1.6T / 49B active","context":"1M","modalities":"Text","local":"Datacenter / multi-node",
            "footprint":"865 GB repository","best":"Frontier reasoning, coding and million-token text workloads",
            "source":"https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro",
        },
        {
            "name":"Qwen3.5-397B-A17B","publisher":"Qwen","license":"Apache 2.0","openness":"Permissive weights",
            "params":"397B / 17B active","context":"262K native · ~1.01M extended","modalities":"Text + image","local":"Multi-GPU / server",
            "footprint":"94 weight shards","best":"Multilingual multimodal agents and general-purpose deployment",
            "source":"https://huggingface.co/Qwen/Qwen3.5-397B-A17B",
        },
        {
            "name":"GLM-5","publisher":"Z.ai","license":"MIT","openness":"Permissive weights",
            "params":"744B / 40B active","context":"202,752 config","modalities":"Text","local":"Multi-GPU / server",
            "footprint":"744B-parameter MoE","best":"Systems engineering, coding and long-horizon agents",
            "source":"https://huggingface.co/zai-org/GLM-5",
        },
        {
            "name":"Mistral Small 4","publisher":"Mistral AI","license":"Apache 2.0","openness":"Permissive weights",
            "params":"119B / 6.5B active","context":"256K","modalities":"Text + image","local":"High-memory workstation / server",
            "footprint":"242 GB full · 70.8 GB NVFP4","best":"Efficient reasoning, coding, agents and multimodal enterprise use",
            "source":"https://huggingface.co/mistralai/Mistral-Small-4-119B-2603",
        },
        {
            "name":"Gemma 4 12B","publisher":"Google DeepMind","license":"Apache 2.0","openness":"Permissive weights",
            "params":"~12B dense","context":"256K","modalities":"Text + image + audio","local":"Yes · laptop-class",
            "footprint":"23.9 GB weights · 16 GB-class local target",
            "best":"Local multimodal AI, private assistants and on-device experimentation",
            "source":"https://huggingface.co/google/gemma-4-12B",
        },
        {
            "name":"Kimi K3","publisher":"Moonshot AI","license":"Kimi K3 License","openness":"Custom-license open weights",
            "params":"2.8T / 104B active","context":"1M","modalities":"Text + image","local":"Datacenter-class",
            "footprint":"96 large weight shards","best":"Frontier multimodal agents, long-context knowledge work and coding",
            "source":"https://huggingface.co/moonshotai/Kimi-K3",
        },
    ]

    rows = "".join(
        f'''<tr>
          <th scope="row"><a href="#{escape(slugify(m["name"]), quote=True)}">{escape(m["name"])}</a><small>{escape(m["publisher"])}</small></th>
          <td><span class="license-badge {"license-permissive" if m["license"] in {"MIT","Apache 2.0"} else "license-custom"}">{escape(m["license"])}</span></td>
          <td>{escape(m["params"])}</td><td>{escape(m["context"])}</td><td>{escape(m["modalities"])}</td>
          <td>{escape(m["local"])}</td><td>{escape(m["best"])}</td>
        </tr>'''
        for m in models
    )

    toc = [
        ("quick-answer","Quick answer"),
        ("open-source-vs-open-weights","Open source vs open weights"),
        ("comparison","Model comparison"),
        ("deepseek-v4-pro","DeepSeek V4-Pro"),
        ("qwen3-5-397b-a17b","Qwen3.5"),
        ("glm-5","GLM-5"),
        ("mistral-small-4","Mistral Small 4"),
        ("gemma-4-12b","Gemma 4 12B"),
        ("kimi-k3","Kimi K3"),
        ("local-use","Best model for local use"),
        ("hardware","Hardware requirements"),
        ("coding","Best open model for coding"),
        ("agents","Best open model for agents"),
        ("commercial-use","Commercial use and licenses"),
        ("benchmarks","How to read benchmarks"),
        ("how-to-choose","How to choose"),
        ("faq","FAQ"),
    ]
    toc_html = "".join(f'<a href="#{escape(a, quote=True)}">{escape(label)}</a>' for a,label in toc)

    faq = [
        ("What is the best open-source AI model in 2026?", "There is no single best model across every deployment. DeepSeek V4-Pro, Qwen3.5-397B-A17B and GLM-5 target frontier-scale server workloads; Mistral Small 4 is a more deployable 119B MoE; Gemma 4 12B is the practical local multimodal choice in this shortlist; and Kimi K3 is a frontier open-weight model under a custom license."),
        ("What is the best open-source AI model to run locally?", "Gemma 4 12B is the clearest local choice in this shortlist. Google explicitly targets dedicated-GPU laptops with about 16 GB VRAM or unified memory, and the official checkpoint is about 23.9 GB. Mistral Small 4 can be self-hosted, but even its official NVFP4 checkpoint is about 70.8 GB and is better suited to high-memory workstations or servers."),
        ("What is the difference between open-source AI and open-weight AI?", "Open weights means the trained parameters are downloadable. The Open Source Initiative's Open Source AI Definition requires more: freedoms to use, study, modify and share, plus the preferred form for modification, including sufficient training-data information, training and inference code, and model parameters. A permissive weight license alone does not prove the full AI system meets that definition."),
        ("Which open AI model has the largest context window?", "DeepSeek V4-Pro and Kimi K3 list 1M-token context windows. Qwen3.5-397B-A17B has 262,144 tokens natively and can be extended to roughly 1.01M. Gemma 4 12B and Mistral Small 4 list 256K, while GLM-5's released configuration lists 202,752 positions."),
        ("Which open model is best for coding?", "For frontier-scale coding, DeepSeek V4-Pro and GLM-5 are designed around reasoning, coding and agentic engineering. Qwen3.5 and Mistral Small 4 add strong multimodal or deployment advantages. For local coding assistants, Gemma 4 12B is much easier to run than the frontier-scale MoE models."),
        ("Can open-source AI models be used commercially?", "MIT and Apache 2.0 are permissive software licenses commonly compatible with commercial use, subject to their terms and applicable law. Kimi K3 uses a custom license, so commercial deployments should review that license directly. Also distinguish a model-weight license from whether the entire AI system qualifies as Open Source AI under the OSI definition."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq)

    sources = [
        ("Open Source AI Definition 1.0","https://opensource.org/ai/open-source-ai-definition"),
        ("DeepSeek V4-Pro model card","https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro"),
        ("DeepSeek V4-Pro model downloads","https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/README.md"),
        ("Qwen3.5-397B-A17B model card","https://huggingface.co/Qwen/Qwen3.5-397B-A17B"),
        ("GLM-5 model card","https://huggingface.co/zai-org/GLM-5"),
        ("Mistral Small 4 announcement","https://mistral.ai/news/mistral-small-4/"),
        ("Mistral Small 4 weights","https://huggingface.co/mistralai/Mistral-Small-4-119B-2603"),
        ("Mistral Small 4 NVFP4 weights","https://huggingface.co/mistralai/Mistral-Small-4-119B-2603-NVFP4"),
        ("Gemma 4 12B model card","https://huggingface.co/google/gemma-4-12B"),
        ("Gemma 4 12B developer guide","https://developers.googleblog.com/gemma-4-12b-the-developer-guide/"),
        ("Kimi K3 model card","https://huggingface.co/moonshotai/Kimi-K3"),
    ]
    source_links = "".join(f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(label)}</span><b>↗</b></a>' for label,url in sources)

    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"TechArticle","@id":canonical+"#article","url":canonical,"mainEntityOfPage":canonical,
                "headline":"Best Open-Source AI Models in 2026: Licenses, Hardware & Local Use",
                "description":description,"datePublished":published,"dateModified":verified,
                "author":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "creator":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "isPartOf":{"@id":"https://sxf.si/#website"},
                "articleSection":"Open Source AI",
                "keywords":[
                    "best open source AI models 2026","best open weight models","local AI models",
                    "DeepSeek V4 Pro","Qwen3.5","GLM-5","Mistral Small 4","Gemma 4","Kimi K3",
                    "open source LLM","AI model hardware requirements"
                ],
                "about":[{"@type":"Thing","name":m["name"],"url":m["source"]} for m in models],
                "citation":[url for _label,url in sources],
                "inLanguage":"en"
            },
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},
                {"@type":"ListItem","position":2,"name":"Guides","item":BASE_URL+"/guides/"},
                {"@type":"ListItem","position":3,"name":"Best Open-Source AI Models in 2026","item":canonical}
            ]},
            {"@type":"ItemList","name":"Open and open-weight AI models compared","numberOfItems":len(models),"itemListElement":[
                {"@type":"ListItem","position":i+1,"name":m["name"],"url":m["source"]} for i,m in enumerate(models)
            ]},
            {"@type":"FAQPage","mainEntity":[
                {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq
            ]}
        ]
    }

    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema, page_type="article")}
    <body class="intel-page guide-article-page">{page_header("guides")}<main>
      <article>
        <header class="guide-article-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span>Open-Source AI Models</span></nav>
          <p class="eyebrow">SXF GUIDE / OPEN MODELS</p>
          <h1>Best Open-Source AI Models in 2026:<br><span>Licenses, Hardware & Local Use</span></h1>
          <p class="guide-deck">The open-model market now spans laptop-sized multimodal models and multi-trillion-parameter systems that need datacenter hardware. This guide separates license reality from marketing, then compares the models by architecture, context, deployment footprint and the workloads they are actually practical for.</p>
          <div class="guide-byline">
            <div><span>Published</span><strong>September 26, 2026</strong></div>
            <div><span>Last verified</span><strong>September 26, 2026</strong></div>
            <div><span>Reading time</span><strong>24 min</strong></div>
            <div><span>Evidence</span><strong>Official weights & docs</strong></div>
          </div>
        </header>

        <section class="guide-answer shell" id="quick-answer">
          <div class="guide-answer-label">QUICK ANSWER</div>
          <div><h2>The best open model depends more on hardware and license constraints than on a single benchmark score.</h2>
          <p><strong>Gemma 4 12B</strong> is the most practical local multimodal model in this shortlist because Google explicitly targets 16 GB-class laptops. <strong>Mistral Small 4</strong> is a strong self-hosted middle ground with Apache 2.0 licensing, 119B total / 6.5B active parameters and an official 70.8 GB NVFP4 checkpoint. <strong>Qwen3.5-397B-A17B</strong> is a compelling multilingual multimodal MoE for large deployments. <strong>DeepSeek V4-Pro</strong> and <strong>GLM-5</strong> target frontier-scale reasoning and coding on server infrastructure. <strong>Kimi K3</strong> is the largest model here at 2.8T parameters with a 1M context window, but it uses a custom Kimi K3 license rather than MIT or Apache 2.0.</p></div>
        </section>

        <div class="guide-reading shell">
          <aside class="guide-toc"><span>IN THIS GUIDE</span>{toc_html}<a class="guide-toc-top" href="#top">Back to top ↑</a></aside>

          <div class="guide-prose" id="top">
            <section id="open-source-vs-open-weights">
              <p class="eyebrow">DEFINITION FIRST</p>
              <h2>Open-source AI vs open weights: the distinction most model lists skip</h2>
              <p>The search phrase “open-source AI model” is useful, but technically it collapses several different ideas. A downloadable checkpoint is an <strong>open-weight release</strong>. A model carrying an MIT or Apache 2.0 license has permissive legal terms around the released artifacts. Neither fact, by itself, proves that the full AI system satisfies the Open Source Initiative's Open Source AI Definition.</p>
              <p>OSI's definition asks whether users can use, study, modify and share the system and whether the preferred form for modification is available. For machine-learning systems, that includes sufficient information about training data, the code used to train and run the system, and the model parameters. That is a higher bar than “weights are on Hugging Face.”</p>
              <div class="guide-difference">
                <div><span>OPEN WEIGHTS</span><strong>You can download the trained parameters.</strong><p>Useful for self-hosting, fine-tuning and research, but the license may be custom and the training recipe may still be incomplete.</p></div>
                <div><span>OPEN SOURCE AI</span><strong>The system is modifiable in its preferred form.</strong><p>Under OSAID 1.0, that means freedoms plus the relevant data information, code and parameters needed to study and modify the system.</p></div>
              </div>
              <div class="guide-callout"><strong>SXF terminology</strong><p>This page targets the common search term “open-source AI models,” but the comparison table reports the actual model-weight license. We avoid claiming that every downloadable model is an OSI-compliant Open Source AI system.</p></div>
            </section>

            <section id="comparison">
              <p class="eyebrow">QUICK COMPARISON</p>
              <h2>Best open-source and open-weight AI models in 2026 at a glance</h2>
              <div class="guide-table-wrap"><table class="guide-table open-model-table"><thead><tr><th>Model</th><th>License</th><th>Parameters</th><th>Context</th><th>Modalities</th><th>Local fit</th><th>Best fit</th></tr></thead><tbody>{rows}</tbody></table></div>
              <p class="guide-fact-note">“Local fit” means practical deployment class, not whether a framework can technically load the checkpoint. Exact RAM/VRAM requirements depend on precision, quantization, KV cache, context length, batching and runtime.</p>

              <div class="guide-criteria open-model-criteria">
                <article><span>01</span><h3>License</h3><p>Can you modify, redistribute or commercialize the released artifacts under clear terms?</p></article>
                <article><span>02</span><h3>Active parameters</h3><p>For MoE models, active parameters matter for compute per token, while total parameters still matter for storage and memory distribution.</p></article>
                <article><span>03</span><h3>Context</h3><p>Long context can help research and agents, but KV-cache memory and retrieval quality often become the real bottlenecks.</p></article>
                <article><span>04</span><h3>Deployment footprint</h3><p>A model is only “local” in a useful sense if your hardware can run it at acceptable speed and context size.</p></article>
                <article><span>05</span><h3>Tool use</h3><p>Agentic workloads need reliable structured outputs, function calling and compatibility with serving stacks.</p></article>
                <article><span>06</span><h3>Multimodality</h3><p>Vision and audio can eliminate separate models, but may increase memory and preprocessing complexity.</p></article>
              </div>
            </section>

            <section class="tool-review" id="deepseek-v4-pro">
              <div class="tool-review-head"><span>01</span><div><p class="eyebrow">DEEPSEEK</p><h2>DeepSeek V4-Pro: frontier open weights for reasoning, coding and 1M-token text context</h2></div></div>
              <p>DeepSeek V4-Pro is the largest MIT-licensed checkpoint in this shortlist by total storage footprint. DeepSeek lists <strong>1.6 trillion total parameters with 49 billion activated per token</strong> and a <strong>1M-token context window</strong>. The Hugging Face repository is roughly <strong>865 GB</strong>, with FP4 used for MoE expert parameters and FP8 for most other weights.</p>
              <p>The MoE design is important. Only a fraction of the 1.6T parameters are active for each token, reducing inference compute compared with a dense model of the same total size. But sparsity does not magically make the full model laptop-sized: the weights still have to live somewhere, and distributed serving becomes part of the deployment architecture.</p>
              <div class="tool-facts"><div><span>Total / active</span><strong>1.6T / 49B</strong></div><div><span>Context</span><strong>1M tokens</strong></div><div><span>License</span><strong>MIT</strong></div><div><span>Repository</span><strong>~865 GB</strong></div></div>
              <h3>Who should use DeepSeek V4-Pro?</h3>
              <p>It makes sense for teams that want frontier-class open weights and already operate serious GPU infrastructure. It is especially relevant to coding, reasoning and long-context systems where self-hosting control matters more than minimizing infrastructure complexity.</p>
              <h3>Who should not use it?</h3>
              <p>If your requirement is “run a strong model on one workstation” or “ship offline AI to end users,” V4-Pro is the wrong deployment class. Use a smaller model or a managed inference provider rather than turning model hosting into the main engineering project.</p>
              <div class="tool-links"><a href="https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro" target="_blank" rel="noopener noreferrer">Official weights ↗</a><a href="/open-source/">SXF Open Source signals ↗</a></div>
            </section>

            <section class="tool-review" id="qwen3-5-397b-a17b">
              <div class="tool-review-head"><span>02</span><div><p class="eyebrow">QWEN</p><h2>Qwen3.5-397B-A17B: best fit for multilingual multimodal open deployment at scale</h2></div></div>
              <p>Qwen3.5-397B-A17B combines a vision encoder with a sparse MoE language model. Qwen documents <strong>397B total parameters and 17B activated</strong>, a <strong>262,144-token native context window</strong> extensible to roughly <strong>1,010,000 tokens</strong>, and support for <strong>201 languages and dialects</strong>.</p>
              <p>The architecture is attractive because the active parameter count is much smaller than the total parameter pool. For serving, Qwen documents compatibility with Transformers, vLLM, SGLang and KTransformers. The model still consists of dozens of large weight shards, so “17B active” should not be confused with “17B model footprint.”</p>
              <div class="tool-facts"><div><span>Total / active</span><strong>397B / 17B</strong></div><div><span>Context</span><strong>262K native · ~1.01M extended</strong></div><div><span>License</span><strong>Apache 2.0</strong></div><div><span>Modality</span><strong>Text + image</strong></div></div>
              <h3>Why Qwen3.5 stands out</h3>
              <p>Its combination of multilingual coverage, multimodality, sparse compute and permissive Apache 2.0 weights makes it a strong platform model for organizations building international assistants, multimodal agents or their own managed inference layer.</p>
              <h3>Deployment reality</h3>
              <p>This is still a large-model deployment. Plan for multi-GPU or server infrastructure, especially at long context. Extending to ~1M context also increases KV-cache pressure; the advertised maximum is not a free operating point.</p>
              <div class="tool-links"><a href="https://huggingface.co/Qwen/Qwen3.5-397B-A17B" target="_blank" rel="noopener noreferrer">Official model card ↗</a><a href="/topics/open-source-ai/">Open-source AI topic ↗</a></div>
            </section>

            <section class="tool-review" id="glm-5">
              <div class="tool-review-head"><span>03</span><div><p class="eyebrow">Z.AI</p><h2>GLM-5: an MIT-licensed MoE built for systems engineering and long-horizon agents</h2></div></div>
              <p>GLM-5 targets a different center of gravity: complex systems engineering and long-horizon agentic tasks. Z.ai lists <strong>744B total parameters with 40B active</strong>, trained on 28.5T tokens, and uses DeepSeek Sparse Attention to reduce long-context deployment cost. The released configuration exposes <strong>202,752 maximum positions</strong>.</p>
              <p>Z.ai publishes extensive coding, terminal, browser and tool-use evaluations. Those results are useful evidence about the model's intended workload, but they should not be merged mechanically with numbers from other vendors because harnesses, prompts, context strategies and tool environments differ.</p>
              <div class="tool-facts"><div><span>Total / active</span><strong>744B / 40B</strong></div><div><span>Context config</span><strong>202,752</strong></div><div><span>License</span><strong>MIT</strong></div><div><span>Focus</span><strong>Systems + agents</strong></div></div>
              <h3>Best use case for GLM-5</h3>
              <p>Choose it when open deployment and agentic engineering are the priority and you have infrastructure for a very large MoE. It is particularly interesting for coding-agent research because the official evaluation suite includes SWE-bench, terminal and browser tasks rather than only general chat benchmarks.</p>
              <div class="tool-links"><a href="https://huggingface.co/zai-org/GLM-5" target="_blank" rel="noopener noreferrer">Official model card ↗</a><a href="https://github.com/zai-org/GLM-5" target="_blank" rel="noopener noreferrer">Official GitHub ↗</a></div>
            </section>

            <section class="tool-review" id="mistral-small-4">
              <div class="tool-review-head"><span>04</span><div><p class="eyebrow">MISTRAL AI</p><h2>Mistral Small 4: the strongest middle ground between frontier capability and self-hosting practicality</h2></div></div>
              <p>Mistral Small 4 is a <strong>119B-parameter MoE with 6.5B activated per token</strong>, a <strong>256K context window</strong>, text-and-image input, configurable reasoning and native function calling. Mistral releases it under Apache 2.0 and explicitly supports both instruct and reasoning modes.</p>
              <p>Its deployment story is unusually clear. The full Hugging Face repository is about <strong>242 GB</strong>, while Mistral also publishes an official <strong>NVFP4 checkpoint of about 70.8 GB</strong>. That does not make it a normal laptop model, but it puts serious self-hosting within reach of high-memory workstations and smaller multi-GPU servers instead of requiring datacenter-scale model parallelism.</p>
              <div class="tool-facts"><div><span>Total / active</span><strong>119B / 6.5B</strong></div><div><span>Context</span><strong>256K</strong></div><div><span>License</span><strong>Apache 2.0</strong></div><div><span>NVFP4 checkpoint</span><strong>~70.8 GB</strong></div></div>
              <h3>Why Mistral Small 4 is strategically interesting</h3>
              <p>It combines four things that often require separate models: general instruction following, reasoning, coding/agent behavior and vision. For enterprises that want to keep inference under their control without hosting a 400B–2.8T model, that balance can matter more than a narrow benchmark lead.</p>
              <div class="tool-links"><a href="https://mistral.ai/news/mistral-small-4/" target="_blank" rel="noopener noreferrer">Official announcement ↗</a><a href="https://huggingface.co/mistralai/Mistral-Small-4-119B-2603-NVFP4" target="_blank" rel="noopener noreferrer">Official NVFP4 weights ↗</a></div>
            </section>

            <section class="tool-review" id="gemma-4-12b">
              <div class="tool-review-head"><span>05</span><div><p class="eyebrow">GOOGLE DEEPMIND</p><h2>Gemma 4 12B: best open model in this list for practical local multimodal AI</h2></div></div>
              <p>Gemma 4 12B is the model in this shortlist that changes the hardware conversation. Google describes it as a dense, unified multimodal model with <strong>256K context</strong> and native text, image and audio input. The Hugging Face weight file is about <strong>23.9 GB</strong>.</p>
              <p>More importantly, Google's developer guide explicitly targets <strong>dedicated-GPU laptops with about 16 GB VRAM or unified memory</strong>. That is possible through optimized local inference rather than by loading a full 24 GB BF16 checkpoint naively into a 16 GB GPU. It is the kind of distinction that matters when “runs locally” is the purchase criterion.</p>
              <div class="tool-facts"><div><span>Architecture</span><strong>~12B dense</strong></div><div><span>Context</span><strong>256K</strong></div><div><span>License</span><strong>Apache 2.0</strong></div><div><span>Local target</span><strong>16 GB-class laptop</strong></div></div>
              <h3>Best use cases for Gemma 4 12B</h3>
              <p>Private desktop assistants, local document analysis, speech/image understanding, coding experiments and applications that cannot send data to a hosted API. It is not the largest or most expensive model here—and that is precisely why it is useful.</p>
              <h3>What Gemma 4 12B is not</h3>
              <p>It should not be compared with DeepSeek V4-Pro or Kimi K3 as if parameter scale were equal. The value proposition is deployment efficiency and multimodal local use, not replacing datacenter-scale models on every frontier reasoning task.</p>
              <div class="tool-links"><a href="https://huggingface.co/google/gemma-4-12B" target="_blank" rel="noopener noreferrer">Official weights ↗</a><a href="https://developers.googleblog.com/gemma-4-12b-the-developer-guide/" target="_blank" rel="noopener noreferrer">Google local deployment guide ↗</a></div>
            </section>

            <section class="tool-review" id="kimi-k3">
              <div class="tool-review-head"><span>06</span><div><p class="eyebrow">MOONSHOT AI</p><h2>Kimi K3: frontier open weights at 2.8T parameters with a custom license</h2></div></div>
              <p>Kimi K3 is the scale outlier. Moonshot lists <strong>2.8 trillion total parameters, 104 billion activated per token</strong>, native multimodality and a <strong>1,048,576-token context window</strong>. The published weights use MXFP4 with MXFP8 activations and are split across 96 large shards.</p>
              <p>The licensing distinction is equally important: Kimi K3 uses the <strong>Kimi K3 License</strong>, not MIT or Apache 2.0. The weights are openly downloadable, but any commercial or redistribution decision should be based on the actual custom license rather than assuming “open weights” means standard permissive terms.</p>
              <div class="tool-facts"><div><span>Total / active</span><strong>2.8T / 104B</strong></div><div><span>Context</span><strong>1M</strong></div><div><span>License</span><strong>Kimi K3 License</strong></div><div><span>Deployment</span><strong>Datacenter-class</strong></div></div>
              <h3>Who is Kimi K3 for?</h3>
              <p>Organizations and researchers exploring frontier-scale multimodal agents, long-context knowledge work and coding where model ownership matters and distributed infrastructure is already available. It is not a realistic “download and run on my gaming PC” model.</p>
              <div class="tool-links"><a href="https://huggingface.co/moonshotai/Kimi-K3" target="_blank" rel="noopener noreferrer">Official model card ↗</a></div>
            </section>

            <section id="local-use">
              <p class="eyebrow">LOCAL AI</p>
              <h2>What is the best open-source AI model to run locally in 2026?</h2>
              <p><strong>Gemma 4 12B is the practical answer in this shortlist.</strong> It is the only model here whose publisher explicitly targets dedicated-GPU laptops around the 16 GB VRAM/unified-memory class. Mistral Small 4 is the next step up if you have a high-memory workstation or multi-GPU server and want much more model capacity.</p>
              <div class="guide-decision-table">
                <div><span>Laptop / 16 GB-class</span><strong>Gemma 4 12B</strong><p>Google provides a local deployment path and targets consumer-grade devices.</p></div>
                <div><span>High-memory workstation</span><strong>Mistral Small 4 NVFP4</strong><p>The official quantized checkpoint is ~70.8 GB before runtime overhead and KV cache.</p></div>
                <div><span>Multi-GPU server</span><strong>Qwen3.5 or GLM-5</strong><p>Useful when model scale and agent capability justify distributed serving complexity.</p></div>
                <div><span>Datacenter / multi-node</span><strong>DeepSeek V4-Pro or Kimi K3</strong><p>Frontier-scale weights whose storage and memory footprint dominate deployment design.</p></div>
              </div>
              <div class="guide-callout"><strong>Local does not mean offline laptop</strong><p>Every model with downloadable weights is technically self-hostable. That does not make every model practical on a single machine. “Local AI” should describe the hardware you actually control, from a laptop to a private GPU cluster.</p></div>
            </section>

            <section id="hardware">
              <p class="eyebrow">HARDWARE REQUIREMENTS</p>
              <h2>How much RAM or VRAM do open-source AI models need?</h2>
              <p>There is no single VRAM number that follows directly from parameter count. Precision determines weight memory; MoE routing determines active compute; context length determines KV-cache growth; and runtimes may split weights across GPU, CPU and multiple nodes. The same model can therefore have very different hardware requirements at 4-bit quantization and 8K context versus BF16 and 256K context.</p>
              <div class="hardware-ladder">
                <div><span>~16 GB class</span><strong>Gemma 4 12B</strong><p>Google explicitly targets optimized local execution on dedicated-GPU laptops with 16 GB VRAM or unified memory.</p></div>
                <div><span>~70+ GB checkpoint</span><strong>Mistral Small 4 NVFP4</strong><p>Official quantized files total about 70.8 GB, before runtime buffers and context cache.</p></div>
                <div><span>Hundreds of GB</span><strong>Qwen3.5 / GLM-5</strong><p>Large MoE models where multi-GPU serving is a realistic baseline rather than an edge case.</p></div>
                <div><span>~865 GB repository</span><strong>DeepSeek V4-Pro</strong><p>Distributed deployment territory even though only 49B parameters are activated per token.</p></div>
                <div><span>Multi-terabyte-scale parameter pool</span><strong>Kimi K3</strong><p>2.8T total parameters and 104B active: architect for datacenter serving, not desktop inference.</p></div>
              </div>
              <h3>Why active parameters do not equal VRAM requirements</h3>
              <p>In an MoE model, active parameters tell you roughly how much expert compute is used per token. They do <em>not</em> tell you how much memory is needed to store the expert pool. A 397B model with 17B active still has hundreds of billions of learned parameters that must be stored or distributed across devices.</p>
            </section>

            <section id="coding">
              <p class="eyebrow">OPEN MODELS FOR CODING</p>
              <h2>What is the best open-source AI model for coding?</h2>
              <p>For frontier-scale coding, <strong>DeepSeek V4-Pro</strong> and <strong>GLM-5</strong> deserve evaluation because both are explicitly aimed at difficult coding and agentic engineering. <strong>Qwen3.5</strong> is attractive when coding sits inside a multilingual or multimodal agent. <strong>Mistral Small 4</strong> is easier to self-host and includes native function calling with configurable reasoning. <strong>Gemma 4 12B</strong> is the practical local coding option when hardware limits matter.</p>
              <p>SXF does not declare a benchmark winner from vendor cards because coding evaluations are extremely harness-sensitive. A SWE-bench result obtained with one agent framework, context policy and retry budget is not automatically comparable with a number produced under another setup.</p>
              <div class="tool-links"><a href="/guides/best-ai-coding-tools/">Best AI Coding Tools in 2026 ↗</a><a href="/topics/coding-ai/">Coding AI signals ↗</a></div>
            </section>

            <section id="agents">
              <p class="eyebrow">OPEN MODELS FOR AGENTS</p>
              <h2>Which open model is best for AI agents and tool use?</h2>
              <p>Agent models need more than reasoning scores. They need stable structured outputs, tool-call accuracy, context management and affordable repeated inference. GLM-5 is explicitly trained and evaluated for long-horizon agents; Qwen3.5 emphasizes agent scaffolds and multilingual multimodality; Mistral Small 4 exposes native function calling and JSON output; Gemma 4 adds native function calling in a much smaller deployment envelope.</p>
              <p>For autonomous systems, deployment reliability may matter more than another few benchmark points. A model that fits comfortably in your infrastructure, supports your serving stack and has predictable tool behavior can outperform a larger model operationally because you can run more parallel agents, keep latency under control and inspect failures.</p>
            </section>

            <section id="commercial-use">
              <p class="eyebrow">LICENSES & COMMERCIAL USE</p>
              <h2>Can you use open-source AI models commercially?</h2>
              <p><strong>MIT and Apache 2.0 are permissive licenses commonly used for commercial software</strong>, but you still need to comply with their notice, attribution and other terms. DeepSeek V4-Pro and GLM-5 publish MIT metadata; Qwen3.5, Mistral Small 4 and Gemma 4 12B publish Apache 2.0 metadata.</p>
              <p><strong>Kimi K3 is different.</strong> It uses a custom Kimi K3 License. A custom license can still permit broad deployment, but you should read its actual conditions before building a commercial product, redistributing derivatives or offering the model as a service.</p>
              <h3>Model license vs application compliance</h3>
              <p>A permissive model license does not resolve every legal issue around your application. Training-data rights, output usage, privacy, sector regulation, export controls and downstream datasets can create separate obligations. Treat the model license as one layer of compliance, not the whole answer.</p>
              <div class="guide-callout"><strong>Important distinction</strong><p>“Apache 2.0 weights” is a precise statement about released artifacts. “Fully open-source AI system” is a broader claim. SXF keeps those statements separate.</p></div>
            </section>

            <section id="benchmarks">
              <p class="eyebrow">BENCHMARKS</p>
              <h2>How should you compare open-source AI model performance without fooling yourself?</h2>
              <p>Official model cards are useful, but they are not a neutral league table. Vendors may use different prompt templates, reasoning budgets, tool harnesses, maximum context, judge models and retry policies. This is especially visible in agentic coding, where the surrounding harness can change the result as much as the base model.</p>
              <div class="guide-criteria">
                <article><span>01</span><h3>Match the harness</h3><p>Do not compare two benchmark numbers unless model settings, tools and evaluation rules are materially equivalent.</p></article>
                <article><span>02</span><h3>Measure cost</h3><p>A higher score may require much longer reasoning traces or more agent steps. Track tokens, wall time and GPU cost.</p></article>
                <article><span>03</span><h3>Use your data</h3><p>Build a private eval set from real tickets, documents, languages and failure modes rather than optimizing for public benchmarks only.</p></article>
                <article><span>04</span><h3>Measure reliability</h3><p>For agents, pass rate across repeated runs matters more than one impressive output.</p></article>
              </div>
              <p>The right question is not “which model has the highest global score?” It is “which model meets our quality threshold at the latency, hardware, licensing and cost envelope we can operate?”</p>
            </section>

            <section id="how-to-choose">
              <p class="eyebrow">DECISION FRAMEWORK</p>
              <h2>How to choose an open-source AI model in 2026</h2>
              <div class="guide-decision-table">
                <div><span>You need local multimodal AI</span><strong>Start with Gemma 4 12B</strong><p>Small enough for optimized laptop-class deployment, 256K context, audio/image input and Apache 2.0 weights.</p></div>
                <div><span>You need a self-hosted enterprise middle tier</span><strong>Evaluate Mistral Small 4</strong><p>Apache 2.0, 119B/6.5B MoE, vision, reasoning, coding and a 70.8 GB official NVFP4 checkpoint.</p></div>
                <div><span>You need multilingual multimodal scale</span><strong>Evaluate Qwen3.5-397B-A17B</strong><p>201-language coverage, image input, Apache 2.0 and an efficient 17B-active MoE architecture.</p></div>
                <div><span>You need coding / systems agents</span><strong>Evaluate GLM-5 and DeepSeek V4-Pro</strong><p>Both target difficult reasoning and engineering workloads, but require substantial serving infrastructure.</p></div>
                <div><span>You need frontier open-weight scale</span><strong>Evaluate Kimi K3</strong><p>2.8T total, 104B active and 1M context—if the custom license and datacenter footprint fit your deployment.</p></div>
                <div><span>You need commercial simplicity</span><strong>Prefer clear MIT or Apache 2.0 releases</strong><p>Then separately verify whether the overall system meets your organization's definition of open source and compliance requirements.</p></div>
              </div>
            </section>

            <section class="guide-faq-section" id="faq">
              <p class="eyebrow">FAQ</p>
              <h2>Frequently asked questions about open-source AI models</h2>
              <div class="model-faq">{faq_html}</div>
            </section>

            <section class="guide-sources">
              <p class="eyebrow">PRIMARY SOURCES</p>
              <h2>Official sources used for this guide</h2>
              <p>SXF verifies licenses, parameter counts, context limits and deployment details against official model cards, vendor documentation and the Open Source Initiative. Vendor benchmark claims are treated as attributed evidence, not independent SXF measurements.</p>
              <div class="model-sources">{source_links}</div>
            </section>
          </div>
        </div>
      </article>
    </main>{page_footer()}</body></html>'''


def best_ai_agents_guide_html(items):
    canonical = f"{BASE_URL}/guides/best-ai-agents/"
    published = "2026-09-26"
    verified = "2026-09-26"
    title = "Best AI Agents in 2026: Work, Research, Coding & Automation | SXF / AI"
    description = "Compare the best AI agents in 2026: ChatGPT Work, Claude Cowork, Manus, Zapier Agents and Devin Desktop by autonomy, browser and computer use, integrations, pricing and best use."

    agents = [
        {
            "name":"ChatGPT Work","company":"OpenAI","best":"General-purpose work across apps, files and the web",
            "surface":"ChatGPT + cloud computer/browser","automation":"Scheduled and triggered tasks","free":"No",
            "entry":"Plus $20/mo","human":"Approvals for important actions",
            "source":"https://openai.com/index/chatgpt-for-your-most-ambitious-work/",
            "pricing":"https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus",
        },
        {
            "name":"Claude Cowork","company":"Anthropic","best":"Long-form knowledge work and file-based desktop tasks",
            "surface":"Desktop + web/mobile beta","automation":"Multi-step work in chosen files/tools","free":"No",
            "entry":"Pro $20/mo","human":"Permission-gated access",
            "source":"https://claude.com/product/cowork",
            "pricing":"https://support.claude.com/en/articles/11049762-choose-a-claude-plan",
        },
        {
            "name":"Manus","company":"Manus AI","best":"Cloud research, reports, slides, websites and parallel tasks",
            "surface":"Web + desktop + browser operator","automation":"Scheduled tasks + concurrent cloud tasks","free":"Yes",
            "entry":"Free · Pro from $20/mo","human":"Task-level steering / approvals",
            "source":"https://manus.im/",
            "pricing":"https://help.manus.im/en/articles/11711111-what-is-the-current-membership-pricing-for-manus",
        },
        {
            "name":"Zapier Agents","company":"Zapier","best":"Repeatable business automation across connected apps",
            "surface":"Web + Chrome extension + app integrations","automation":"Agent behaviors and app actions","free":"Yes",
            "entry":"Free · Pro $33.33/mo annual","human":"Workflow and app permissions",
            "source":"https://zapier.com/agents",
            "pricing":"https://zapier.com/pricing",
        },
        {
            "name":"Devin Desktop","company":"Cognition","best":"Software engineering and multi-agent coding workflows",
            "surface":"AI IDE + local/cloud agents","automation":"Delegated coding tasks and parallel agents","free":"Yes",
            "entry":"Free · Pro $20/mo","human":"Code review and repository controls",
            "source":"https://devin.ai/desktop",
            "pricing":"https://devin.ai/desktop",
        },
    ]

    rows = "".join(
        f'''<tr>
          <th scope="row"><a href="#{escape(slugify(a["name"]), quote=True)}">{escape(a["name"])}</a><small>{escape(a["company"])}</small></th>
          <td>{escape(a["best"])}</td><td>{escape(a["surface"])}</td><td>{escape(a["automation"])}</td>
          <td>{escape(a["free"])}</td><td>{escape(a["entry"])}</td><td>{escape(a["human"])}</td>
        </tr>'''
        for a in agents
    )

    toc = [
        ("quick-answer","Quick answer"),
        ("what-is-an-ai-agent","What is an AI agent?"),
        ("comparison","AI agent comparison"),
        ("how-we-evaluate","How we evaluate agents"),
        ("chatgpt-work","ChatGPT Work"),
        ("claude-cowork","Claude Cowork"),
        ("manus","Manus"),
        ("zapier-agents","Zapier Agents"),
        ("devin-desktop","Devin Desktop"),
        ("research","Best AI agent for research"),
        ("work","Best AI agent for work"),
        ("automation","Best AI agent for automation"),
        ("coding","Best AI agent for coding"),
        ("browser-computer-use","Browser & computer use"),
        ("pricing","AI agent pricing"),
        ("security","AI agent security"),
        ("how-to-choose","How to choose"),
        ("agent-vs-chatbot","AI agent vs chatbot"),
        ("faq","FAQ"),
    ]
    toc_html = "".join(f'<a href="#{escape(a, quote=True)}">{escape(label)}</a>' for a,label in toc)

    faq = [
        ("What is the best AI agent in 2026?", "There is no universal best agent because the products operate in different environments. ChatGPT Work is the broadest general-work agent in this shortlist; Claude Cowork is strong for file-heavy knowledge work; Manus is optimized for cloud research and deliverables; Zapier Agents is built for repeatable cross-app automation; and Devin Desktop is specialized for software engineering."),
        ("What is the best AI agent for research?", "ChatGPT Work and Manus are the strongest general research candidates in this shortlist because both can browse, gather information and produce finished deliverables. Claude Cowork is especially useful when research depends heavily on local files and long-form knowledge work. The best choice depends on source access, citation requirements and whether the final output must be a report, spreadsheet, slide deck or another artifact."),
        ("What is the best AI agent for business automation?", "Zapier Agents is the clearest fit when the goal is repeatable actions across business apps because its product and pricing are organized around agent activities, connected data sources and automated behaviors. ChatGPT Work can also run scheduled or triggered tasks, but it is a broader work agent rather than a dedicated automation platform."),
        ("What is the best AI agent for coding?", "Devin Desktop is the specialized coding agent in this comparison. ChatGPT includes Codex as a separate software-development mode, while Claude's coding-specific product is Claude Code. For a coding-only decision, compare dedicated coding agents rather than general-purpose work agents."),
        ("Is ChatGPT Agent still available?", "No. OpenAI's current help documentation says ChatGPT Agent is no longer available and directs users to ChatGPT Work for longer multi-step tasks and finished deliverables."),
        ("Are AI agents safe to run without supervision?", "Not for every action. Agents can misread intent, encounter prompt injection, expose data through over-broad permissions or take an irreversible action in the wrong context. High-impact actions such as sending, purchasing, deleting, publishing or changing production systems should use explicit permissions, scoped credentials and human approval."),
        ("What is the difference between an AI agent and a chatbot?", "A chatbot primarily generates responses. An agent operates a loop: it interprets a goal, plans or chooses actions, uses tools or a computer, observes the result, adapts and continues until it finishes, fails or asks for human input. Autonomy is a spectrum rather than an all-or-nothing property."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq)

    sources = [
        ("OpenAI · Introducing ChatGPT Work","https://openai.com/index/chatgpt-for-your-most-ambitious-work/"),
        ("OpenAI · ChatGPT Work and Codex","https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex"),
        ("OpenAI · retired ChatGPT Agent documentation","https://help.openai.com/en/articles/11752874-chatgpt-agent"),
        ("OpenAI · ChatGPT Business pricing","https://openai.com/business/pricing/"),
        ("Anthropic · Claude Cowork","https://claude.com/product/cowork"),
        ("Anthropic · Trustworthy agents in practice","https://www.anthropic.com/research/trustworthy-agents"),
        ("Anthropic · agent containment engineering","https://www.anthropic.com/engineering/how-we-contain-claude"),
        ("Manus · plans and pricing","https://help.manus.im/en/articles/11711111-what-is-the-current-membership-pricing-for-manus"),
        ("Manus · credit consumption","https://help.manus.im/en/articles/11711097-what-are-the-rules-for-credits-consumption-and-how-can-i-obtain-them"),
        ("Zapier · Agents pricing","https://zapier.com/pricing"),
        ("Zapier · Agent activity metering","https://help.zapier.com/hc/en-us/articles/26559132765325-How-is-Zapier-Agents-usage-measured"),
        ("Cognition · Devin Desktop","https://devin.ai/desktop"),
    ]
    source_links = "".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(label)}</span><b>↗</b></a>'
        for label,url in sources
    )

    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"TechArticle","@id":canonical+"#article","url":canonical,"mainEntityOfPage":canonical,
                "headline":"Best AI Agents in 2026: Work, Research, Coding & Automation",
                "description":description,"datePublished":published,"dateModified":verified,
                "author":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "creator":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "isPartOf":{"@id":"https://sxf.si/#website"},
                "articleSection":"AI Agents",
                "keywords":[
                    "best AI agents 2026","best autonomous AI agents","AI agent tools","AI agents for work",
                    "AI agents for research","AI agents for automation","ChatGPT Work","Claude Cowork",
                    "Manus AI agent","Zapier Agents","Devin Desktop"
                ],
                "about":[{"@type":"SoftwareApplication","name":a["name"],"url":a["source"]} for a in agents],
                "citation":[url for _label,url in sources],
                "inLanguage":"en"
            },
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},
                {"@type":"ListItem","position":2,"name":"Guides","item":BASE_URL+"/guides/"},
                {"@type":"ListItem","position":3,"name":"Best AI Agents in 2026","item":canonical}
            ]},
            {"@type":"ItemList","name":"AI agents compared","numberOfItems":len(agents),"itemListElement":[
                {"@type":"ListItem","position":i+1,"name":a["name"],"url":a["source"]} for i,a in enumerate(agents)
            ]},
            {"@type":"FAQPage","mainEntity":[
                {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq
            ]}
        ]
    }

    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema, page_type="article")}
    <body class="intel-page guide-article-page">{page_header("guides")}<main>
      <article>
        <header class="guide-article-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span>AI Agents</span></nav>
          <p class="eyebrow">SXF GUIDE / AGENTIC AI</p>
          <h1>Best AI Agents in 2026:<br><span>Work, Research, Coding & Automation</span></h1>
          <p class="guide-deck">AI agents are no longer one category. Some operate a cloud computer, some work inside your files, some orchestrate business apps and some are specialized software engineers. This guide compares the systems by where they act, how far they can run, how they are billed and where a human should remain in the loop.</p>
          <div class="guide-byline">
            <div><span>Published</span><strong>September 26, 2026</strong></div>
            <div><span>Last verified</span><strong>September 26, 2026</strong></div>
            <div><span>Reading time</span><strong>25 min</strong></div>
            <div><span>Research standard</span><strong>Primary-source first</strong></div>
          </div>
        </header>

        <section class="guide-answer shell" id="quick-answer">
          <div class="guide-answer-label">QUICK ANSWER</div>
          <div><h2>The best AI agent is the one whose execution environment matches the work you actually want to delegate.</h2>
          <p><strong>ChatGPT Work</strong> is the broadest general-purpose work agent in this shortlist, built to operate across apps, files, the web and finished deliverables. <strong>Claude Cowork</strong> is especially strong when the task starts from files and desktop knowledge work. <strong>Manus</strong> is designed for cloud-based research and artifact creation with parallel and scheduled tasks. <strong>Zapier Agents</strong> is the clearest choice for repeatable business automation across connected apps. <strong>Devin Desktop</strong> is the specialized option for software engineering and supervising coding agents. The important comparison is not “which agent is smartest?” but “what can it access, what can it execute, how is it governed and what does failure cost?”</p></div>
        </section>

        <div class="guide-reading shell">
          <aside class="guide-toc"><span>IN THIS GUIDE</span>{toc_html}<a class="guide-toc-top" href="#top">Back to top ↑</a></aside>

          <div class="guide-prose" id="top">
            <section id="what-is-an-ai-agent">
              <p class="eyebrow">DEFINITION</p>
              <h2>What is an AI agent in 2026?</h2>
              <p>An AI agent is a system that can move beyond generating an answer and <strong>take a sequence of actions toward a goal</strong>. A useful agent can inspect context, decide what to do next, call tools or operate software, observe the result, recover from some failures and continue until the task is complete or human input is needed.</p>
              <p>That definition is deliberately operational. “Agent” has become a marketing label for everything from a chatbot with one API call to a system that works for hours on a cloud computer. SXF treats autonomy as a spectrum and asks what the system can actually do without a human clicking every step.</p>
              <div class="agent-loop">
                <div><span>01</span><strong>Understand</strong><p>Interpret the goal, constraints and available context.</p></div>
                <div><span>02</span><strong>Plan</strong><p>Choose a next action or decompose the task.</p></div>
                <div><span>03</span><strong>Act</strong><p>Use an app, API, browser, shell, file or computer.</p></div>
                <div><span>04</span><strong>Observe</strong><p>Read the outcome instead of assuming the action worked.</p></div>
                <div><span>05</span><strong>Adapt</strong><p>Retry, change strategy or ask for approval when needed.</p></div>
              </div>
              <div class="guide-callout"><strong>Agent test</strong><p>If the system only writes instructions for you to execute, it is an assistant. If it can execute the work, inspect the result and continue through multiple steps, it is operating as an agent.</p></div>
            </section>

            <section id="comparison">
              <p class="eyebrow">QUICK COMPARISON</p>
              <h2>Best AI agents in 2026 at a glance</h2>
              <div class="guide-table-wrap"><table class="guide-table agent-table"><thead><tr><th>Agent</th><th>Best fit</th><th>Execution surface</th><th>Automation</th><th>Free</th><th>Entry price</th><th>Human control</th></tr></thead><tbody>{rows}</tbody></table></div>
              <p class="guide-fact-note">Prices and product availability verified September 26, 2026. Agent pricing is unusually difficult to compare because some products bundle usage into subscriptions, some meter credits or activities, and some consume model/API usage separately.</p>
            </section>

            <section id="how-we-evaluate">
              <p class="eyebrow">METHODOLOGY</p>
              <h2>How SXF evaluates AI agents</h2>
              <p>A model benchmark is not enough to evaluate an agent. The agent is the whole execution system around the model. SXF separates seven layers that determine whether delegation is actually useful:</p>
              <div class="guide-criteria agent-criteria">
                <article><span>01</span><h3>Execution environment</h3><p>Does the agent operate in a cloud computer, local desktop, browser, business apps, terminal or a controlled sandbox?</p></article>
                <article><span>02</span><h3>Tool breadth</h3><p>Can it work with files, websites, code, APIs and connected services without fragile manual handoffs?</p></article>
                <article><span>03</span><h3>Autonomy horizon</h3><p>How many steps can it complete before it loses state, needs clarification or requires human intervention?</p></article>
                <article><span>04</span><h3>Verification loop</h3><p>Can it check that the outcome is correct, or does it merely report that it completed an action?</p></article>
                <article><span>05</span><h3>Permissions</h3><p>Can access be scoped by app, file, credential, action or workspace rather than granting a broad blast radius?</p></article>
                <article><span>06</span><h3>Observability</h3><p>Can a human review steps, artifacts, logs or changes before trusting the result?</p></article>
                <article><span>07</span><h3>Economics</h3><p>Does a plan price include useful work, or do credits, activities, tool calls and long runs dominate the real cost?</p></article>
              </div>
              <p>SXF does not publish a single numerical score here because these systems are not interchangeable. A Zapier agent that executes a reliable CRM workflow and a Devin agent that fixes a repository issue solve different classes of work.</p>
            </section>

            <section class="tool-review" id="chatgpt-work">
              <div class="tool-review-head"><span>01</span><div><p class="eyebrow">OPENAI</p><h2>ChatGPT Work: best general-purpose AI agent for multi-step knowledge work</h2></div></div>
              <p>OpenAI describes ChatGPT Work as an agent for longer, multi-step work and finished deliverables. It can gather information across connected apps and files, use a cloud computer and browser for supported web workflows, and produce documents, spreadsheets, presentations, reports and web outputs rather than stopping at a chat response.</p>
              <p>The product is strategically important because it combines research, app context, browser action and artifact creation inside the same ChatGPT workspace. Scheduled Tasks can also run once, repeat on a schedule or react to a trigger, which moves Work from one-off delegation toward ongoing workflows.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>General multi-step work</strong></div><div><span>Environment</span><strong>Apps + files + cloud browser</strong></div><div><span>Entry plan</span><strong>Plus $20/mo</strong></div><div><span>Automation</span><strong>Scheduled / triggered tasks</strong></div></div>
              <h3>Where ChatGPT Work is strongest</h3>
              <p>It is strongest when a task crosses formats and information sources: research a market, inspect connected documents, calculate or structure data, navigate a web workflow and return a polished deliverable. That breadth is more important than any single browser benchmark.</p>
              <h3>Important 2026 change: ChatGPT Agent is retired</h3>
              <p>Older comparisons often list “ChatGPT Agent” or agent mode as the product. OpenAI's current documentation says <strong>ChatGPT Agent is no longer available</strong> and directs users to ChatGPT Work for longer multi-step tasks. A current buying guide should compare Work, not treat the retired product as the present-day option.</p>
              <h3>What to watch</h3>
              <p>Broad access creates broad risk. The useful question is not whether Work can connect to more data, but whether the minimum necessary apps, files and actions are exposed for the task. Important actions should remain approval-gated.</p>
              <div class="tool-links"><a href="https://openai.com/index/chatgpt-for-your-most-ambitious-work/" target="_blank" rel="noopener noreferrer">ChatGPT Work official page ↗</a><a href="https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex" target="_blank" rel="noopener noreferrer">Work documentation ↗</a><a href="/topics/openai/">SXF OpenAI intelligence ↗</a></div>
            </section>

            <section class="tool-review" id="claude-cowork">
              <div class="tool-review-head"><span>02</span><div><p class="eyebrow">ANTHROPIC</p><h2>Claude Cowork: best AI agent for file-heavy desktop and knowledge work</h2></div></div>
              <p>Claude Cowork is Anthropic's general work-agent surface. Anthropic describes it as a place where you hand Claude real work: Cowork operates in files and tools you choose and completes multi-step tasks from start to finish. It runs on desktop, with web and mobile in beta.</p>
              <p>The product's strongest conceptual advantage is controlled context. Instead of assuming an agent should see an entire digital life, Cowork starts from the files and tools a user selects. That is a useful pattern for document-heavy work where local files, reports, folders and structured deliverables matter more than broad browser automation.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>Files + knowledge work</strong></div><div><span>Environment</span><strong>Desktop + selected tools</strong></div><div><span>Entry plan</span><strong>Pro $20/mo</strong></div><div><span>Included in</span><strong>Pro · Max · Team · Enterprise</strong></div></div>
              <h3>Where Claude Cowork is strongest</h3>
              <p>Organizing and transforming files, assembling reports, synthesizing material across documents and completing tasks where the human wants to define the workspace before delegating. For software engineering, Claude Code is the more specialized product; Cowork belongs in the broader knowledge-work comparison.</p>
              <h3>Why Anthropic's safety work matters here</h3>
              <p>Anthropic explicitly frames agent risk around intent errors and prompt injection, and has published engineering work on containment and reducing an agent's blast radius. Those are not abstract concerns once an agent can touch real files and tools.</p>
              <div class="tool-links"><a href="https://claude.com/product/cowork" target="_blank" rel="noopener noreferrer">Claude Cowork ↗</a><a href="https://www.anthropic.com/research/trustworthy-agents" target="_blank" rel="noopener noreferrer">Trustworthy agents research ↗</a></div>
            </section>

            <section class="tool-review" id="manus">
              <div class="tool-review-head"><span>03</span><div><p class="eyebrow">MANUS</p><h2>Manus: best cloud AI agent for research, reports and parallel deliverables</h2></div></div>
              <p>Manus is built around handing work to an agent that runs in cloud environments rather than keeping a chat session open. Its current product includes advanced research, Wide Research, website deployment, slides, a browser operator, integrations and scheduled tasks.</p>
              <p>The pricing system reflects that architecture. Manus credits are consumed by LLM tokens, virtual machines and third-party APIs, so a task's cost depends on complexity and duration rather than a fixed “one prompt = one unit” rule. Free users receive limited agent access, while paid Pro tiers add larger monthly credit pools and more concurrency.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>Cloud research + artifacts</strong></div><div><span>Free plan</span><strong>300 daily Lite credits</strong></div><div><span>Pro</span><strong>From $20/mo</strong></div><div><span>Paid concurrency</span><strong>Up to 20 tasks</strong></div></div>
              <h3>Where Manus is strongest</h3>
              <p>Research or production work where parallelism matters: collecting information, producing a report, creating slides or a website, or letting several cloud tasks run without tying execution to the user's machine.</p>
              <h3>What to watch</h3>
              <p>Credits are a compute abstraction, not a fixed number of finished tasks. A short lookup and a long browser/code workflow can consume very different amounts. The right way to evaluate Manus cost is to record credits consumed by your recurring task types.</p>
              <div class="tool-links"><a href="https://manus.im/" target="_blank" rel="noopener noreferrer">Manus ↗</a><a href="https://help.manus.im/en/articles/11711111-what-is-the-current-membership-pricing-for-manus" target="_blank" rel="noopener noreferrer">Official pricing ↗</a></div>
            </section>

            <section class="tool-review" id="zapier-agents">
              <div class="tool-review-head"><span>04</span><div><p class="eyebrow">ZAPIER</p><h2>Zapier Agents: best AI agents for repeatable business automation</h2></div></div>
              <p>Zapier Agents sits closer to automation infrastructure than a general-purpose cloud coworker. The agent can use live data sources, browse the web and take actions across connected applications, with usage metered in <strong>activities</strong>—billable actions the agent performs.</p>
              <p>The Free plan includes 400 activities per month. The current Pro plan lists 1,500 activities per month at $400 billed annually, equivalent to $33.33 per month, with up to 40 activities in a single run. Enterprise adds organization-level sharing, audit logs and restricted-app controls.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>Cross-app business workflows</strong></div><div><span>Free usage</span><strong>400 activities/mo</strong></div><div><span>Pro</span><strong>1,500 activities/mo</strong></div><div><span>Per-run cap</span><strong>40 activities on Pro</strong></div></div>
              <h3>Where Zapier Agents is strongest</h3>
              <p>When the process is recurring and app-centric: qualify information, look up records, update systems, summarize data and trigger downstream steps. The strength is less about a giant context window and more about an existing integration graph plus repeatable execution.</p>
              <h3>Agent automation vs traditional automation</h3>
              <p>A deterministic Zap should still handle a deterministic workflow when possible. An agent earns its cost when judgment is needed inside the process: interpreting unstructured input, choosing among tools or adapting the next action to context.</p>
              <div class="tool-links"><a href="https://zapier.com/agents" target="_blank" rel="noopener noreferrer">Zapier Agents ↗</a><a href="https://zapier.com/pricing" target="_blank" rel="noopener noreferrer">Official pricing ↗</a></div>
            </section>

            <section class="tool-review" id="devin-desktop">
              <div class="tool-review-head"><span>05</span><div><p class="eyebrow">COGNITION</p><h2>Devin Desktop: best specialized AI agent for software engineering delegation</h2></div></div>
              <p>Devin Desktop is not a general office agent. It is an AI software-engineering environment built around coding agents, an IDE and the ability to manage development work across local and cloud contexts. That specialization is exactly why it belongs in the agent landscape but should not be judged by the same criteria as a research or CRM agent.</p>
              <p>The current Devin Desktop page lists Free, Pro at $20 per month and Max at $200 per month. The product also exposes integrations and MCP servers for developer infrastructure such as GitHub-adjacent services, deployment platforms and observability tools.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>Software engineering</strong></div><div><span>Environment</span><strong>AI IDE + agents</strong></div><div><span>Entry</span><strong>Free</strong></div><div><span>Pro</span><strong>$20/mo</strong></div></div>
              <h3>Where Devin Desktop is strongest</h3>
              <p>Delegating implementation work while preserving an engineer's ability to inspect code, diffs and the environment. For organizations evaluating coding agents specifically, it should be compared with Claude Code, Codex, Cursor and GitHub Copilot—not just with general AI agents.</p>
              <div class="tool-links"><a href="https://devin.ai/desktop" target="_blank" rel="noopener noreferrer">Devin Desktop ↗</a><a href="/guides/best-ai-coding-tools/">Best AI Coding Tools in 2026 ↗</a><a href="/topics/coding-ai/">Coding AI signals ↗</a></div>
            </section>

            <section id="research">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best AI agent for research in 2026?</h2>
              <p><strong>ChatGPT Work and Manus are the strongest general research candidates in this shortlist, but for different reasons.</strong> Work is attractive when research must combine connected company context, web work and polished artifacts inside one workspace. Manus is attractive when cloud execution, parallel tasks and dedicated research/report generation are central to the job.</p>
              <p>Claude Cowork becomes especially relevant when the research corpus is already sitting in local files and folders. In all three cases, “research agent” quality should be measured by source selection, traceability, contradictory-evidence handling and whether the final artifact preserves enough provenance for a human to audit it.</p>
              <div class="guide-callout"><strong>Research rule</strong><p>An agent that produces a beautiful report without traceable sources has automated writing, not research. Require source links, verify high-impact claims and separate observed evidence from the agent's synthesis.</p></div>
            </section>

            <section id="work">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best AI agent for work and productivity?</h2>
              <p>For broad knowledge work, <strong>ChatGPT Work</strong> has the widest role in this comparison: it is explicitly designed for multi-step tasks across apps and files and for producing finished deliverables. <strong>Claude Cowork</strong> is a strong alternative when the job is file-centric and the user wants to scope the tools and files Claude can work with.</p>
              <p>The decision should follow your information architecture. If important work lives across SaaS apps and web workflows, integration breadth matters. If the work lives in documents, folders and local knowledge, file control and document reasoning matter more.</p>
            </section>

            <section id="automation">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best AI agent for business automation?</h2>
              <p><strong>Zapier Agents is the clearest purpose-built choice here</strong> because the product is designed around automated behaviors, connected data sources and app actions. The monthly unit—activities—also maps more directly to automation volume than a conversational message limit.</p>
              <p>ChatGPT Work's scheduled and triggered tasks make it capable of recurring work too. The architectural distinction is that Zapier begins with workflow infrastructure and adds agent judgment, while Work begins with a general agent and expands into recurring execution.</p>
              <h3>When should you use a workflow instead of an agent?</h3>
              <p>If every step and branch is known in advance, deterministic automation is easier to test and cheaper to govern. Add an agent where the workflow requires interpretation, tool selection, unstructured data or recovery from variable inputs.</p>
            </section>

            <section id="coding">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best autonomous AI agent for coding?</h2>
              <p>For coding, use a coding agent rather than asking a general office agent to behave like one. <strong>Devin Desktop</strong> is the specialized agent in this article, but the category also includes Claude Code, OpenAI Codex, Cursor and GitHub Copilot. These systems understand repositories, edit multiple files, execute commands and return code changes instead of simply generating snippets.</p>
              <p>The dedicated SXF coding guide compares that category in depth, including workflow architecture, free tiers and repo-scale work.</p>
              <div class="guide-inline-cta"><div><span>SXF GUIDE</span><strong>Best AI Coding Tools in 2026</strong><p>Claude Code, Codex, GitHub Copilot, Cursor and Devin Desktop compared by workflow and autonomy.</p></div><a href="/guides/best-ai-coding-tools/">Open coding guide ↗</a></div>
            </section>

            <section id="browser-computer-use">
              <p class="eyebrow">BROWSER & COMPUTER USE</p>
              <h2>Which AI agents can browse the web or use a computer?</h2>
              <p>Computer-use capability is one of the most important boundaries between assistants and action-taking agents. ChatGPT Work can use a cloud computer and browser for supported workflows. Manus includes browser automation and virtual-machine-backed tasks. Zapier Agents includes web browsing alongside app actions. Claude's broader agent stack includes computer-use capabilities, while Cowork focuses on work in selected files and tools.</p>
              <p>Browser control should not be evaluated only by “can it click?” Real reliability comes from recognizing state changes, handling authentication, stopping at sensitive decisions and recovering when the page differs from what the model expected.</p>
              <div class="guide-difference">
                <div><span>API / TOOL ACTION</span><strong>Preferred when a reliable API exists.</strong><p>Structured inputs and outputs are easier to validate, authorize and audit.</p></div>
                <div><span>COMPUTER / BROWSER USE</span><strong>Useful when software has no suitable API.</strong><p>More general, but also more exposed to visual ambiguity, prompt injection and unexpected interface states.</p></div>
              </div>
            </section>

            <section id="pricing">
              <p class="eyebrow">PRICING</p>
              <h2>How much do AI agents cost in 2026?</h2>
              <p>Agent pricing is moving away from one simple subscription metric because an agent consumes several resources: model inference, tool calls, browsers or virtual machines, third-party APIs and sometimes long-lived execution environments.</p>
              <div class="guide-pricing-list">
                <div><strong>ChatGPT Work</strong><p>Included on eligible paid ChatGPT plans; Plus is $20/month. Business Standard is $20/user/month annual or $25 monthly, with flexible credits available beyond included usage.</p><a href="https://openai.com/business/pricing/" target="_blank" rel="noopener noreferrer">Verify pricing ↗</a></div>
                <div><strong>Claude Cowork</strong><p>Included with Claude Pro at $20/month ($17/month equivalent annually), Max tiers, Team and Enterprise. Usage limits apply and heavy Cowork work consumes capacity faster than ordinary chat.</p><a href="https://claude.com/product/cowork" target="_blank" rel="noopener noreferrer">Verify pricing ↗</a></div>
                <div><strong>Manus</strong><p>Free plan available. Pro starts at $20/month with 4,000 monthly credits; a $40 tier starts at 8,000 credits. Credits reflect model tokens, virtual machines and third-party APIs.</p><a href="https://help.manus.im/en/articles/11711111-what-is-the-current-membership-pricing-for-manus" target="_blank" rel="noopener noreferrer">Verify pricing ↗</a></div>
                <div><strong>Zapier Agents</strong><p>Free includes 400 activities/month. Pro is listed at $400 billed annually ($33.33/month equivalent) with 1,500 activities/month.</p><a href="https://zapier.com/pricing" target="_blank" rel="noopener noreferrer">Verify pricing ↗</a></div>
                <div><strong>Devin Desktop</strong><p>Current self-serve desktop tiers list Free, Pro at $20/month and Max at $200/month. Team and enterprise economics can differ.</p><a href="https://devin.ai/desktop" target="_blank" rel="noopener noreferrer">Verify pricing ↗</a></div>
              </div>
              <div class="guide-callout"><strong>Measure cost per completed task</strong><p>Seat price is a weak agent metric. Track the total cost of a verified outcome: subscription or credits + compute/tool usage + human review time + retries + recovery from incorrect actions.</p></div>
            </section>

            <section id="security">
              <p class="eyebrow">SAFETY & GOVERNANCE</p>
              <h2>Are autonomous AI agents safe?</h2>
              <p>Agents introduce a different security problem from chatbots because they combine model uncertainty with real permissions. Anthropic's agent-safety work highlights two central risks: the agent may misunderstand the user's intent, and external content can attempt <strong>prompt injection</strong> that manipulates the agent into taking an unintended action.</p>
              <p>The risk grows with blast radius. Giving an agent access to read a report is different from giving it permission to send email, spend money, delete cloud resources or deploy code. Mature agent deployments therefore treat permissions as part of the product architecture.</p>
              <div class="security-principles">
                <article><span>01</span><h3>Least privilege</h3><p>Give the agent only the apps, files, secrets and actions necessary for the current workflow.</p></article>
                <article><span>02</span><h3>Approval gates</h3><p>Require human confirmation before sending, purchasing, deleting, publishing or modifying critical systems.</p></article>
                <article><span>03</span><h3>Isolation</h3><p>Use sandboxes or dedicated environments so a failure cannot freely propagate into production resources.</p></article>
                <article><span>04</span><h3>Observability</h3><p>Keep logs, diffs and artifacts so a reviewer can understand what happened and why.</p></article>
                <article><span>05</span><h3>Prompt-injection defense</h3><p>Treat external webpages, documents and messages as potentially hostile input rather than trusted instructions.</p></article>
                <article><span>06</span><h3>Reversibility</h3><p>Prefer actions that can be reviewed, rolled back or staged before they become externally visible.</p></article>
              </div>
              <p>An agent should earn autonomy by proving reliability inside a bounded workflow. Do not start by handing it the maximum permissions and hoping the model behaves.</p>
            </section>

            <section id="how-to-choose">
              <p class="eyebrow">DECISION FRAMEWORK</p>
              <h2>How to choose the best AI agent for your workflow</h2>
              <div class="guide-decision-table">
                <div><span>Cross-app knowledge work</span><strong>Start with ChatGPT Work</strong><p>Broad general-work scope, connected context, browser workflows, finished artifacts and scheduled execution.</p></div>
                <div><span>File-heavy desktop work</span><strong>Start with Claude Cowork</strong><p>Strong fit when the working set is local documents, folders and selected tools.</p></div>
                <div><span>Cloud research and parallel tasks</span><strong>Start with Manus</strong><p>Research, reports, slides, websites, browser operator and concurrent cloud execution.</p></div>
                <div><span>Repeatable SaaS automation</span><strong>Start with Zapier Agents</strong><p>Built around app actions and recurring agent behaviors with explicit activity metering.</p></div>
                <div><span>Software engineering</span><strong>Start with Devin Desktop, then compare coding agents</strong><p>Specialized development environment; evaluate against Claude Code, Codex, Cursor and Copilot for your repository.</p></div>
                <div><span>High-risk operations</span><strong>Start with governance, not a product</strong><p>Define permissions, approval gates, auditability and failure recovery before selecting the agent.</p></div>
              </div>
            </section>

            <section id="agent-vs-chatbot">
              <p class="eyebrow">FOUNDATION</p>
              <h2>AI agent vs chatbot: what is the real difference?</h2>
              <div class="guide-difference">
                <div><span>CHATBOT</span><strong>Prompt → response</strong><p>Optimized for conversation, explanation, drafting and answering questions. Tools may exist, but the interaction is usually centered on each user turn.</p></div>
                <div><span>AI AGENT</span><strong>Goal → actions → observations → outcome</strong><p>Optimized for delegation. The system can continue through multiple steps, use tools and environments, and return after work has been executed.</p></div>
              </div>
              <p>The boundary is not binary. Modern products can behave like a chatbot in one mode and an agent in another. The useful test is how much responsibility the system can take for the execution loop while remaining observable and controllable.</p>
            </section>

            <section class="guide-faq-section" id="faq">
              <p class="eyebrow">FAQ</p>
              <h2>Frequently asked questions about AI agents</h2>
              <div class="model-faq">{faq_html}</div>
            </section>

            <section class="guide-sources">
              <p class="eyebrow">PRIMARY SOURCES</p>
              <h2>Official sources used for this guide</h2>
              <p>SXF verifies product availability, pricing and agent capabilities against vendor documentation. Where vendors describe their own product as safer, smarter or more capable, this guide treats that as an attributed claim rather than an independent benchmark result.</p>
              <div class="model-sources">{source_links}</div>
            </section>
          </div>
        </div>
      </article>
    </main>{page_footer()}</body></html>'''


def ai_super_agents_guide_html(items):
    canonical = f"{BASE_URL}/guides/ai-super-agents/"
    published = "2026-09-26"
    verified = "2026-09-26"
    title = "AI Super Agents in 2026: What They Are, How They Work, Examples & Risks | SXF / AI"
    description = "A complete guide to AI super agents in 2026: definitions, architecture, orchestration, multi-agent systems, real examples, enterprise use cases, safety, governance and the difference from AGI."

    examples = [
        {
            "name":"Marshall","company":"Salesforce","type":"Business-process orchestrator",
            "does":"Builds and runs end-to-end supply-chain and finance processes, deploying specialized back-office agents inside each step.",
            "pattern":"Super agent above specialized agents",
            "source":"https://www.salesforce.com/blog/regrello/",
        },
        {
            "name":"H2O AI Super Agent","company":"H2O.ai","type":"Enterprise AI orchestration layer",
            "does":"Plans from a natural-language goal and orchestrates predictive, generative and agentic systems with built-in tools, MCP and agent-to-agent calls.",
            "pattern":"Orchestrator across models, agents and tools",
            "source":"https://h2o.ai/platform/overview/",
        },
        {
            "name":"ChipStack AI Super Agent","company":"Cadence","type":"Domain-specific engineering super agent",
            "does":"Coordinates design, verification, regression, debug and RTL-generation workflows across semiconductor engineering tools and specialized agents.",
            "pattern":"Domain super agent with EDA execution",
            "source":"https://www.cadence.com/en_US/home/company/newsroom/press-releases/pr/2026/cadence-unleashes-chipstack-ai-super-agent-pioneering-a-new.html",
        },
        {
            "name":"AuraStack AI Super Agent","company":"Cadence","type":"Systems-design super agent",
            "does":"Coordinates domain-specific agents across PCB planning, implementation and multiphysics analysis.",
            "pattern":"Cross-domain design orchestrator",
            "source":"https://www.cadence.com/ko_KR/home/company/newsroom/press-releases/pr/2026/cadence-introduces-aurastack-ai-super-agent-the-worlds-first.html",
        },
        {
            "name":"Gupshup Superagent","company":"Gupshup","type":"Customer-experience orchestrator",
            "does":"Coordinates customer journeys, messaging and voice infrastructure, transactions and optimization from one conversational interface.",
            "pattern":"Full-stack conversational orchestrator",
            "source":"https://www.prnewswire.com/news-releases/gupshup-launches-superagent-the-autonomous-ai-agent-for-customer-conversations-at-scale-302742192.html",
        },
    ]

    rows = "".join(
        f'''<tr>
          <th scope="row"><a href="{escape(e["source"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(e["name"])}</a><small>{escape(e["company"])}</small></th>
          <td>{escape(e["type"])}</td><td>{escape(e["does"])}</td><td>{escape(e["pattern"])}</td>
        </tr>'''
        for e in examples
    )

    toc = [
        ("quick-answer","Quick answer"),
        ("what-is-a-super-agent","What is an AI super agent?"),
        ("not-a-standard","Is 'super agent' a technical standard?"),
        ("architecture","Super agent architecture"),
        ("examples","Real super agents in 2026"),
        ("vs-ai-agent","Super agent vs AI agent"),
        ("vs-multi-agent","Super agent vs multi-agent system"),
        ("vs-agent-swarm","Super agent vs agent swarm"),
        ("vs-agi","Super agent vs AGI / superintelligence"),
        ("orchestration","How orchestration works"),
        ("memory-context","Memory and context"),
        ("tools-protocols","Tools, MCP and A2A"),
        ("enterprise","Enterprise use cases"),
        ("coding-engineering","Engineering super agents"),
        ("research","Research and forecasting super agents"),
        ("economics","Cost and economics"),
        ("security","Safety and governance"),
        ("failure-modes","Failure modes"),
        ("when-to-use","When do you need a super agent?"),
        ("future","Where super agents are going"),
        ("faq","FAQ"),
    ]
    toc_html = "".join(f'<a href="#{escape(a, quote=True)}">{escape(label)}</a>' for a,label in toc)

    faq = [
        ("What is an AI super agent?", "AI super agent is an emerging, non-standard term for an agentic system that operates above a broader execution stack than a typical single agent. In current products, it usually means an orchestrator that can decompose a high-level goal, coordinate specialized agents and tools, maintain state across a longer workflow, and govern execution across multiple systems."),
        ("Is a super agent the same as a multi-agent system?", "No. A multi-agent system describes an architecture with multiple agents. A super agent is usually the higher-level orchestrator or user-facing control layer that decides how those agents, tools and models should be used. Some products called super agents may contain a multi-agent system internally."),
        ("Is a super agent the same as AGI?", "No. A super agent is a software architecture or product pattern for orchestrating tasks, agents and tools. AGI is a much broader concept about general intelligence across domains. A system can be called a super agent while still depending on narrow tools, fixed permissions, human approvals and current foundation models."),
        ("Is a super agent the same as superintelligence?", "No. Superintelligence refers to intelligence that exceeds human capability across very broad domains. 'Super agent' currently refers to agent orchestration and autonomy. The similar wording can be misleading, but the concepts are fundamentally different."),
        ("What companies are building AI super agents in 2026?", "Examples include Salesforce's Marshall for business processes, H2O.ai's H2O AI Super Agent for enterprise orchestration, Cadence's ChipStack and AuraStack for electronic design automation, and Gupshup's Superagent for customer-experience workflows. The term is used differently by each company."),
        ("What makes a super agent different from an ordinary AI agent?", "The recurring pattern is breadth of orchestration. A normal agent may own one workflow. A super agent typically accepts a higher-level goal, delegates to multiple specialized capabilities, coordinates state and dependencies, and returns one governed outcome."),
        ("Do super agents need multiple AI models?", "Not necessarily, but many architectures benefit from model routing. A super agent can use a stronger model for planning, smaller models for high-volume steps, predictive models for forecasting, and specialized tools or agents for execution."),
        ("Are AI super agents safe?", "They can be made safer, but greater autonomy increases the blast radius of mistakes. Production deployments need least-privilege permissions, sandboxing, approval gates, audit logs, tool isolation, prompt-injection defenses, evaluation and rollback paths."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq)

    sources = [
        ("Salesforce · Marshall super agent","https://www.salesforce.com/blog/regrello/"),
        ("H2O.ai · AI Platform and Super Agent","https://h2o.ai/platform/overview/"),
        ("H2O.ai · enterprise deployment at AT&T","https://h2o.ai/company/press-media/2026/h20-ai-super-agent-is-added-by-att-to-power-enterprise-agentic-ai/"),
        ("H2O.ai · Super Agent architecture documentation","https://docs.h2oai.com/enterprise-h2ogpte/guide/agents"),
        ("H2O.ai · long-running agents with NVIDIA","https://h2o.ai/blog/2026/deep-long-running-agents-built-on-h2oai-super-agent-with-nvidia-runai-and-aiq/"),
        ("Cadence · ChipStack AI Super Agent","https://www.cadence.com/en_US/home/company/newsroom/press-releases/pr/2026/cadence-unleashes-chipstack-ai-super-agent-pioneering-a-new.html"),
        ("Cadence · ChipStack RTL Generation Agent update","https://newsroom.cadence.com/press-releases/press-release-details/2026/Cadence-Expands-ChipStack-AI-Super-Agent-with-a-New-Agent-for-RTL-Generation-and-Early-PPA-Optimization/default.aspx"),
        ("Cadence · AuraStack AI Super Agent","https://www.cadence.com/ko_KR/home/company/newsroom/press-releases/pr/2026/cadence-introduces-aurastack-ai-super-agent-the-worlds-first.html"),
        ("Cadence + Google Cloud · ChipStack with Gemini","https://www.cadence.com/en_US/home/company/newsroom/press-releases/pr/2026/cadence-and-google-collaborate-to-scale-ai-driven-chip-design.html"),
        ("Gupshup · Superagent launch","https://www.prnewswire.com/news-releases/gupshup-launches-superagent-the-autonomous-ai-agent-for-customer-conversations-at-scale-302742192.html"),
    ]
    source_links = "".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(label)}</span><b>↗</b></a>'
        for label,url in sources
    )

    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"TechArticle","@id":canonical+"#article","url":canonical,"mainEntityOfPage":canonical,
                "headline":"AI Super Agents in 2026: What They Are, How They Work, Examples & Risks",
                "description":description,"datePublished":published,"dateModified":verified,
                "author":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "creator":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "isPartOf":{"@id":"https://sxf.si/#website"},
                "articleSection":"AI Agents",
                "keywords":[
                    "AI super agents","super agent AI","what is an AI super agent","super agent vs AI agent",
                    "super agent vs multi agent system","AI agent orchestration","agent swarm vs super agent",
                    "super agent vs AGI","AI super agents 2026","enterprise super agents"
                ],
                "about":[
                    {"@type":"Thing","name":"AI agents"},
                    {"@type":"Thing","name":"Multi-agent systems"},
                    {"@type":"Thing","name":"Agent orchestration"},
                    {"@type":"Thing","name":"Artificial general intelligence"},
                    {"@type":"Thing","name":"Artificial superintelligence"}
                ],
                "citation":[url for _label,url in sources],
                "inLanguage":"en"
            },
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},
                {"@type":"ListItem","position":2,"name":"Guides","item":BASE_URL+"/guides/"},
                {"@type":"ListItem","position":3,"name":"AI Super Agents in 2026","item":canonical}
            ]},
            {"@type":"ItemList","name":"AI super agent examples in 2026","numberOfItems":len(examples),"itemListElement":[
                {"@type":"ListItem","position":i+1,"name":e["name"],"url":e["source"]} for i,e in enumerate(examples)
            ]},
            {"@type":"FAQPage","mainEntity":[
                {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq
            ]}
        ]
    }

    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema, page_type="article")}
    <body class="intel-page guide-article-page">{page_header("guides")}<main>
      <article>
        <header class="guide-article-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span>AI Super Agents</span></nav>
          <p class="eyebrow">SXF GUIDE / NEXT-GENERATION AGENTS</p>
          <h1>AI Super Agents in 2026:<br><span>What They Are, How They Work, Examples & Risks</span></h1>
          <p class="guide-deck">“Super agent” is becoming a real product category before it has become a formal technical standard. Salesforce, H2O.ai, Cadence and other companies are using the term for systems that sit above ordinary agents: accepting broad goals, coordinating specialized workers, routing tools and models, preserving state and governing execution across an entire workflow. This guide explains the emerging architecture without turning marketing language into a fake consensus.</p>
          <div class="guide-byline">
            <div><span>Published</span><strong>September 26, 2026</strong></div>
            <div><span>Last verified</span><strong>September 26, 2026</strong></div>
            <div><span>Reading time</span><strong>26 min</strong></div>
            <div><span>Evidence</span><strong>Primary-source examples</strong></div>
          </div>
        </header>

        <section class="guide-answer shell" id="quick-answer">
          <div class="guide-answer-label">QUICK ANSWER</div>
          <div><h2>An AI super agent is best understood as an orchestration layer above ordinary agents, models and tools—not as a new form of superintelligence.</h2>
          <p>There is no industry-standard definition yet. But the strongest 2026 examples share a pattern: the super agent receives a high-level objective, decomposes it into sub-tasks, chooses specialized agents or tools, coordinates dependencies, keeps track of progress, adapts when execution changes and returns one governed outcome. Salesforce's Marshall dispatches back-office agents inside business processes; H2O's Super Agent orchestrates predictive, generative and agentic systems; Cadence's Super Agents coordinate specialist engineering agents across chip and system design. The label varies, but <strong>hierarchical orchestration</strong> is the recurring architectural idea.</p></div>
        </section>

        <div class="guide-reading shell">
          <aside class="guide-toc"><span>IN THIS GUIDE</span>{toc_html}<a class="guide-toc-top" href="#top">Back to top ↑</a></aside>

          <div class="guide-prose" id="top">
            <section id="what-is-a-super-agent">
              <p class="eyebrow">CORE DEFINITION</p>
              <h2>What is an AI super agent?</h2>
              <p>An <strong>AI super agent</strong> is an emerging name for an agentic system whose responsibility is broader than executing one task or workflow. Instead of acting as a single specialist, it typically behaves as a <strong>manager, router and orchestrator</strong>: it accepts an outcome-level goal, decides how the work should be decomposed, calls agents or tools with narrower skills and keeps the overall workflow coherent.</p>
              <p>The important word is not <em>super</em>. It is <em>scope</em>. A super agent usually owns more of the control plane: planning, delegation, routing, state, error handling, policy and synthesis. That can make the user experience feel like one agent even when the system underneath contains many models, agents, workflows and deterministic services.</p>
              <div class="super-agent-stack">
                <div class="super-agent-layer super-agent-goal"><span>01</span><strong>Goal layer</strong><p>One high-level objective from a human or system.</p></div>
                <div class="super-agent-layer"><span>02</span><strong>Orchestrator</strong><p>Decomposes, routes, schedules and changes the plan.</p></div>
                <div class="super-agent-layer"><span>03</span><strong>Specialist agents</strong><p>Research, coding, finance, design, forecasting or domain work.</p></div>
                <div class="super-agent-layer"><span>04</span><strong>Tools & systems</strong><p>APIs, browser, shell, databases, MCP servers and enterprise software.</p></div>
                <div class="super-agent-layer"><span>05</span><strong>Governance</strong><p>Permissions, approvals, logs, evaluation, cost and rollback.</p></div>
              </div>
              <div class="guide-callout"><strong>SXF definition</strong><p>Until a formal standard exists, SXF uses “super agent” to describe a higher-level agentic orchestrator that owns an end-to-end objective and coordinates multiple specialized capabilities under one control loop.</p></div>
            </section>

            <section id="not-a-standard">
              <p class="eyebrow">TERMINOLOGY</p>
              <h2>Is “super agent” a technical standard?</h2>
              <p><strong>No.</strong> As of September 2026, “AI super agent” is not a standardized architecture, protocol or capability class. Different vendors use the term for related but distinct systems.</p>
              <div class="guide-matchup-grid">
                <article><span>SALESFORCE</span><h3>Process orchestrator</h3><p>Marshall creates and runs business processes, routing items and deploying specialized back-office agents inside the workflow.</p></article>
                <article><span>H2O.AI</span><h3>Enterprise AI control layer</h3><p>The Super Agent sits above predictive, generative and agentic capabilities, choosing tools and agents and keeping an auditable execution trail.</p></article>
                <article><span>CADENCE</span><h3>Domain engineering orchestrator</h3><p>ChipStack and AuraStack coordinate specialized engineering agents and native EDA tools across complex design stages.</p></article>
                <article><span>GUPSHUP</span><h3>Customer-experience orchestrator</h3><p>Superagent coordinates campaigns, customer journeys, transactions, messaging infrastructure and optimization from one interface.</p></article>
              </div>
              <p>This lack of standardization is not necessarily a problem. New software categories often appear in products before terminology settles. But it means any article claiming “a super agent must have exactly X features” is describing an opinion, not an established specification.</p>
              <h3>Why the term is appearing now</h3>
              <p>Single-agent systems are hitting coordination limits. As organizations add more agents, tools and models, somebody—or something—has to decide which capability should run, in what order, under which permissions and how the results should be combined. “Super agent” is one emerging name for that control layer.</p>
            </section>

            <section id="architecture">
              <p class="eyebrow">ARCHITECTURE</p>
              <h2>How does a super agent work?</h2>
              <p>A mature super-agent architecture usually has two loops running at once: an <strong>execution loop</strong> that gets work done, and a <strong>control loop</strong> that decides whether the execution is still on track.</p>
              <div class="agent-loop super-loop">
                <div><span>01</span><strong>Interpret</strong><p>Translate the user goal into constraints, success criteria and required context.</p></div>
                <div><span>02</span><strong>Decompose</strong><p>Break a broad outcome into tasks, dependencies and parallelizable branches.</p></div>
                <div><span>03</span><strong>Route</strong><p>Select the right model, specialist agent, deterministic service or tool for each step.</p></div>
                <div><span>04</span><strong>Execute</strong><p>Run agents and tools, sometimes in parallel and sometimes sequentially.</p></div>
                <div><span>05</span><strong>Observe</strong><p>Collect tool results, errors, artifacts, costs and environment state.</p></div>
                <div><span>06</span><strong>Re-plan</strong><p>Retry, switch tools, escalate models, request approval or change the workflow.</p></div>
                <div><span>07</span><strong>Verify</strong><p>Check success criteria instead of assuming that tool completion equals task completion.</p></div>
                <div><span>08</span><strong>Synthesize</strong><p>Return one coherent result and preserve the audit trail behind it.</p></div>
              </div>
              <h3>The planner should not do everything</h3>
              <p>A common design mistake is using the strongest model for every step. A better super agent can route: a high-capability model may plan the workflow, a small model may classify hundreds of records, a predictive system may estimate risk, a deterministic rule engine may enforce policy and a specialized agent may execute a domain task. H2O's public architecture explicitly combines generative, predictive and agentic AI in this way.</p>
            </section>

            <section id="examples">
              <p class="eyebrow">REAL EXAMPLES / 2026</p>
              <h2>Which AI super agents exist today?</h2>
              <p>The category is no longer hypothetical. Multiple companies are shipping systems they explicitly call Super Agents, although their architectures and markets differ substantially.</p>
              <div class="guide-table-wrap"><table class="guide-table super-agent-table"><thead><tr><th>System</th><th>Type</th><th>What it does</th><th>Architectural pattern</th></tr></thead><tbody>{rows}</tbody></table></div>

              <h3>Salesforce Marshall: the super agent as a business-process manager</h3>
              <p>Salesforce describes Marshall as a super agent for supply chain and finance. The important architectural detail is that Marshall is not simply another back-office worker. It builds a process from a conversation, runs it, routes items, handles stalls and escalations, then deploys specialized agents inside individual steps. That is a hierarchical manager-worker pattern.</p>

              <h3>H2O AI Super Agent: the super agent as an enterprise AI control plane</h3>
              <p>H2O's definition is broader. Its Super Agent sits above predictive AI, generative AI, agentic AI and observability. H2O says it can create and orchestrate agents, use 27 built-in tools, connect over MCP and make agent-to-agent calls over A2A. AT&T is using the system in workflows including customer experience, fraud, field operations, security and research. H2O's public architecture is one of the clearest examples of a super agent as a general enterprise orchestration layer.</p>

              <h3>Cadence ChipStack and AuraStack: super agents as domain operating systems</h3>
              <p>Cadence applies the term to engineering workflows with deep domain structure. ChipStack coordinates front-end chip design and verification; AuraStack spans PCB and advanced-packaging design. These are important examples because they show that a super agent does not have to be general-purpose. It can be narrow in domain yet broad in workflow ownership.</p>
              <p>Cadence expanded ChipStack on September 22, 2026 with an RTL Generation Agent for spec-to-RTL creation and PPA optimization. That update illustrates how a super-agent architecture can evolve: new specialist agents are added under the existing orchestrator instead of rebuilding the user-facing system.</p>
            </section>

            <section id="vs-ai-agent">
              <p class="eyebrow">SUPER AGENT VS AI AGENT</p>
              <h2>What is the difference between a super agent and a normal AI agent?</h2>
              <div class="guide-difference">
                <div><span>AI AGENT</span><strong>Owns a task or bounded workflow.</strong><p>It can reason, use tools and iterate, but its responsibility is usually limited to one domain or execution loop.</p></div>
                <div><span>SUPER AGENT</span><strong>Owns the outcome and coordinates the system.</strong><p>It decides which agents, models and tools should work, tracks dependencies and manages the end-to-end objective.</p></div>
              </div>
              <p>An ordinary agent might “investigate this account.” A super agent might “reduce churn this quarter,” then dispatch research, forecasting, outreach and operations agents, monitor results and escalate exceptions. The difference is not magic intelligence. It is <strong>organizational scope inside the software architecture</strong>.</p>
            </section>

            <section id="vs-multi-agent">
              <p class="eyebrow">SUPER AGENT VS MULTI-AGENT SYSTEM</p>
              <h2>Is a super agent the same as a multi-agent system?</h2>
              <p>No. <strong>Multi-agent system</strong> describes a system containing multiple autonomous or semi-autonomous agents. <strong>Super agent</strong> usually describes a role in that architecture: the coordinator, supervisor or user-facing orchestrator.</p>
              <p>You can build a multi-agent system without a super agent—for example, peer agents that negotiate directly. You can also build a product marketed as a super agent that calls tools and deterministic workflows without spawning many independent agents. The terms overlap, but they are not synonyms.</p>
              <div class="guide-callout"><strong>Architecture test</strong><p>Ask: “Who owns the global plan?” If one agent maintains the high-level objective and delegates work to others, that component is functioning as a super-agent-style orchestrator regardless of what the vendor calls it.</p></div>
            </section>

            <section id="vs-agent-swarm">
              <p class="eyebrow">SUPER AGENT VS AGENT SWARM</p>
              <h2>What is the difference between a super agent and an agent swarm?</h2>
              <p>An <strong>agent swarm</strong> generally emphasizes many agents coordinating through decentralized or loosely centralized interaction. A super-agent architecture is usually more hierarchical: one control layer holds the objective and assigns or routes work.</p>
              <p>The two patterns can coexist. A super agent may delegate one branch of a plan to a swarm, then combine the swarm's result with outputs from deterministic tools or other specialist agents. The important distinction is control topology, not the number of model calls.</p>
              <div class="control-topology">
                <article><span>HIERARCHY</span><h3>Super-agent pattern</h3><p>Goal → orchestrator → specialists → tools. Clear global owner, easier policy and audit.</p></article>
                <article><span>PEER NETWORK</span><h3>Swarm pattern</h3><p>Goal → many interacting agents. Potentially flexible and parallel, but harder to govern and debug.</p></article>
                <article><span>HYBRID</span><h3>Orchestrated swarm</h3><p>A super agent assigns a subproblem to a swarm and remains responsible for the final outcome.</p></article>
              </div>
            </section>

            <section id="vs-agi">
              <p class="eyebrow">SUPER AGENT VS AGI</p>
              <h2>Is an AI super agent AGI or superintelligence?</h2>
              <p><strong>No.</strong> The words sound related, but current super agents are software architectures built from today's models, tools, permissions and workflows. They can be highly autonomous inside a bounded environment without possessing human-level general intelligence.</p>
              <div class="guide-choice-grid">
                <article><span>Super Agent</span><p>An orchestration pattern: coordinates agents, models and tools around a high-level objective.</p></article>
                <article><span>AGI</span><p>A debated concept describing broadly general intelligence that can learn and perform across domains at or around human-level breadth.</p></article>
                <article><span>Superintelligence</span><p>A hypothetical intelligence that substantially exceeds human capability across very broad cognitive domains.</p></article>
              </div>
              <p>A super agent may look more capable than its base model because orchestration gives it memory, tools, parallel workers and persistence. That is <strong>system-level capability amplification</strong>, not evidence that the underlying model has become superintelligent.</p>
            </section>

            <section id="orchestration">
              <p class="eyebrow">ORCHESTRATION</p>
              <h2>How do super agents coordinate other AI agents?</h2>
              <p>There are several orchestration strategies, and robust systems often combine them.</p>
              <div class="guide-criteria">
                <article><span>01</span><h3>Hierarchical delegation</h3><p>A supervisor decomposes work and assigns tasks to specialists. This is the clearest super-agent pattern.</p></article>
                <article><span>02</span><h3>Capability routing</h3><p>The orchestrator chooses a model or agent based on cost, modality, latency, permissions or expertise.</p></article>
                <article><span>03</span><h3>Parallel execution</h3><p>Independent branches run simultaneously, then the super agent resolves conflicts and synthesizes results.</p></article>
                <article><span>04</span><h3>Deterministic stages</h3><p>Critical rules remain hard-coded while agents handle ambiguous reasoning inside safe boundaries.</p></article>
                <article><span>05</span><h3>Escalation</h3><p>A cheap worker can hand difficult cases to a stronger model or request human review.</p></article>
                <article><span>06</span><h3>Evaluator loops</h3><p>Separate checks score or critique outputs before downstream actions are allowed.</p></article>
              </div>
              <p>The architectural goal is not to maximize the number of agents. It is to minimize unnecessary cognitive work while assigning each step to the cheapest reliable capability.</p>
            </section>

            <section id="memory-context">
              <p class="eyebrow">MEMORY & CONTEXT</p>
              <h2>Why memory becomes critical in a super-agent system</h2>
              <p>A normal agent can sometimes keep a task inside one model context. A super agent may coordinate work that lasts hours or days and produces far more state than any one context window should carry. It therefore needs explicit memory architecture.</p>
              <div class="memory-grid">
                <article><span>Working memory</span><p>The current plan, unresolved dependencies and recent observations.</p></article>
                <article><span>Artifact memory</span><p>Documents, code, reports, datasets and files produced by workers.</p></article>
                <article><span>Operational state</span><p>Which jobs ran, failed, retried or are waiting for approval.</p></article>
                <article><span>Long-term memory</span><p>Stable preferences, learned procedures and organization knowledge where policy permits.</p></article>
              </div>
              <p>The system should not treat “put everything in the prompt” as memory. Good orchestration retrieves only the state needed for the next decision and keeps authoritative data in external stores where it can be versioned and audited.</p>
            </section>

            <section id="tools-protocols">
              <p class="eyebrow">TOOLS & PROTOCOLS</p>
              <h2>How MCP and agent-to-agent protocols fit into super agents</h2>
              <p>Super agents become more useful as integrations become standardized. <strong>MCP</strong> gives agents a common pattern for discovering and invoking tools and data sources. <strong>Agent-to-agent communication</strong> allows one agentic system to delegate work to another without pretending that every capability is a simple function.</p>
              <p>H2O's current platform is a concrete example: its Super Agent exposes built-in tools, MCP connectivity and A2A calls. The important shift is architectural. The super agent no longer has to own every capability—it can orchestrate an ecosystem of services that advertise what they can do.</p>
              <div class="guide-callout"><strong>Protocol ≠ governance</strong><p>A common tool protocol makes connection easier. It does not decide whether the agent should be allowed to call the tool, whether the data is trusted or whether the action needs approval. Permission and policy layers remain necessary.</p></div>
            </section>

            <section id="enterprise">
              <p class="eyebrow">ENTERPRISE USE CASES</p>
              <h2>What are AI super agents used for in business?</h2>
              <p>The strongest current use cases have one thing in common: the goal crosses several systems and specialist functions.</p>
              <div class="guide-decision-table">
                <div><span>Supply chain & finance</span><strong>End-to-end process orchestration</strong><p>Salesforce's Marshall routes work, chases stalled items, escalates exceptions and deploys back-office agents inside process steps.</p></div>
                <div><span>Telecommunications</span><strong>Research, fraud, field operations</strong><p>AT&T is using H2O's Super Agent across customer experience, fraud prevention, field operations, security and enterprise research.</p></div>
                <div><span>Semiconductors</span><strong>Design + verification</strong><p>Cadence coordinates specialist agents across RTL creation, test planning, regressions, debugging and optimization.</p></div>
                <div><span>Customer experience</span><strong>Journey orchestration</strong><p>Gupshup positions Superagent as a layer that coordinates campaigns, conversations, transactions and infrastructure.</p></div>
              </div>
              <h3>Why enterprises need an orchestrator</h3>
              <p>Large organizations already have models, rules, databases, SaaS products and automation. A useful super agent does not replace all of that. It becomes a goal-driven interface over the existing system, deciding what should be used and preserving governance across the chain.</p>
            </section>

            <section id="coding-engineering">
              <p class="eyebrow">ENGINEERING</p>
              <h2>What does a super agent look like in coding and engineering?</h2>
              <p>Engineering is where the distinction between agent and super agent becomes easiest to see. A coding agent can implement a feature. An engineering super agent can coordinate specification interpretation, design, implementation, simulation, testing, optimization and review across specialist tools.</p>
              <p>Cadence's ChipStack is a strong domain example. Its September 2026 RTL Generation Agent expanded the existing super-agent system into spec-to-RTL creation and power/performance/area optimization. Instead of one model trying to imitate every EDA tool, the architecture combines agentic reasoning with native engineering systems.</p>
              <p>The same pattern is likely to appear in software engineering: a high-level orchestrator coordinating architecture, coding, security, testing, deployment and observability agents while maintaining one objective and one audit trail.</p>
              <div class="tool-links"><a href="/guides/best-ai-coding-tools/">Best AI Coding Tools in 2026 ↗</a><a href="/guides/best-ai-agents/">Best AI Agents in 2026 ↗</a><a href="/topics/ai-agents/">AI Agents topic ↗</a></div>
            </section>

            <section id="research">
              <p class="eyebrow">RESEARCH & FORECASTING</p>
              <h2>Can super agents improve research and forecasting?</h2>
              <p>Potentially, because research naturally decomposes into heterogeneous tasks: search, retrieval, source validation, coding, statistical analysis, forecasting, critique and synthesis. H2O's Super Agent is an example of this composition: the company describes a reasoning pipeline with multi-source research, self-critique and predictive modeling rather than search alone.</p>
              <p>H2O reports strong results on the live FutureX forecasting benchmark, but those scores are vendor-reported evidence about one system, not proof that “super agents” as a category are inherently better forecasters. The transferable architectural lesson is that prediction may benefit from combining language-model reasoning with actual predictive systems instead of asking a language model to guess a probability from prose.</p>
            </section>

            <section id="economics">
              <p class="eyebrow">ECONOMICS</p>
              <h2>Are super agents more expensive than normal AI agents?</h2>
              <p>They can be—sometimes dramatically—because one user request may trigger many model calls, tools, sandboxes, searches and specialist agents. But orchestration can also reduce cost if it routes each step intelligently.</p>
              <div class="economics-grid">
                <article><span>Cost multipliers</span><h3>Parallel agents, retries, long context, browsers and premium models</h3><p>Every autonomous branch consumes compute and often creates additional verification work.</p></article>
                <article><span>Cost reducers</span><h3>Routing, caching, deterministic tools and small models</h3><p>Use a frontier model only where reasoning justifies it; route routine work to cheaper systems.</p></article>
              </div>
              <h3>The right unit is cost per verified outcome</h3>
              <p>Token cost is insufficient. Measure model inference, tools, infrastructure, external APIs, retries and human review against the value of the completed workflow. H2O explicitly advertises cost attribution per user and task, which is the kind of observability super-agent systems need.</p>
            </section>

            <section id="security">
              <p class="eyebrow">SECURITY & GOVERNANCE</p>
              <h2>Are AI super agents safe?</h2>
              <p>Super agents amplify both capability and blast radius. If one orchestrator can command many tools and specialist agents, a planning error, poisoned context or compromised credential can propagate through an entire workflow.</p>
              <div class="security-principles">
                <article><span>01</span><h3>Least privilege</h3><p>Each worker should receive only the credentials and tools required for its sub-task.</p></article>
                <article><span>02</span><h3>Approval boundaries</h3><p>Irreversible or externally visible actions should require explicit human or policy approval.</p></article>
                <article><span>03</span><h3>Agent isolation</h3><p>Run specialists in sandboxes or separated identities so one failure cannot inherit the entire system's permissions.</p></article>
                <article><span>04</span><h3>Typed delegation</h3><p>Pass structured tasks and expected outputs between agents instead of unrestricted natural-language authority.</p></article>
                <article><span>05</span><h3>Auditability</h3><p>Record who delegated what, which tool ran, which model made the decision and what changed.</p></article>
                <article><span>06</span><h3>Cost controls</h3><p>Set budgets, concurrency limits and stop conditions so runaway planning cannot consume unlimited compute.</p></article>
              </div>
              <h3>Prompt injection becomes a systems problem</h3>
              <p>A super agent may read webpages, documents and messages, then pass extracted information to other agents with stronger permissions. That makes context provenance critical. Untrusted text should be treated as data, not as instructions that automatically inherit the orchestrator's authority.</p>
            </section>

            <section id="failure-modes">
              <p class="eyebrow">FAILURE MODES</p>
              <h2>How do AI super agents fail?</h2>
              <div class="failure-grid">
                <article><span>Goal drift</span><p>The orchestrator optimizes a proxy and loses the user's actual objective after many delegated steps.</p></article>
                <article><span>Coordination tax</span><p>Adding agents creates more messages, latency and contradictions than useful specialization.</p></article>
                <article><span>Authority leakage</span><p>A low-trust worker indirectly causes a high-privilege action through the supervisor.</p></article>
                <article><span>State divergence</span><p>Parallel agents act on different versions of the world and return mutually inconsistent results.</p></article>
                <article><span>Verification collapse</span><p>The same family of models generates and judges the work, allowing shared blind spots to pass.</p></article>
                <article><span>Runaway economics</span><p>Retries, recursive planning or agent spawning consume more compute than the task is worth.</p></article>
              </div>
              <p>The best super-agent systems therefore look less like “one brilliant autonomous AI” and more like carefully engineered distributed systems with explicit policies, state and observability.</p>
            </section>

            <section id="when-to-use">
              <p class="eyebrow">DECISION FRAMEWORK</p>
              <h2>When do you actually need a super agent?</h2>
              <div class="guide-decision-table">
                <div><span>One bounded task</span><strong>Use one agent</strong><p>Do not add orchestration when a single agent can complete and verify the workflow reliably.</p></div>
                <div><span>Many deterministic steps</span><strong>Use workflow automation</strong><p>If the branches are known in advance, a workflow engine is easier to test and govern.</p></div>
                <div><span>Several specialized agents</span><strong>Consider a supervisor</strong><p>A super-agent pattern helps when work requires dynamic delegation and synthesis.</p></div>
                <div><span>Cross-system outcome</span><strong>Super-agent architecture becomes valuable</strong><p>Especially when the objective spans research, prediction, software, business systems and human approvals.</p></div>
                <div><span>High-risk environment</span><strong>Governance first</strong><p>Do not increase autonomy until permissions, logging, rollback and evaluation exist.</p></div>
              </div>
              <p>The simplest architecture that reliably solves the problem is usually the best one. “Super agent” should describe needed orchestration—not become a reason to turn every workflow into a society of models.</p>
            </section>

            <section id="future">
              <p class="eyebrow">WHAT COMES NEXT</p>
              <h2>Where are AI super agents heading after 2026?</h2>
              <p>The likely direction is not one giant model controlling everything. It is increasingly compositional: <strong>strong planners + specialist agents + deterministic systems + shared protocols + governance</strong>. Models will continue improving, but production systems will still need routing, memory, permission boundaries and observability.</p>
              <p>Three changes matter most. First, tool and agent protocols such as MCP and A2A reduce integration friction. Second, model routing makes it economical to mix frontier and smaller models inside one workflow. Third, domain super agents like Cadence's show that high-value autonomy may emerge fastest in industries where the toolchain and success criteria are already well defined.</p>
              <h3>Will super agents lead to superintelligence?</h3>
              <p>Super agents can amplify what current models can accomplish by giving them persistence, tools and coordination. That may produce systems that appear dramatically more capable on real tasks. But architectural amplification should not be confused with evidence of AGI or superintelligence. Those are separate scientific and philosophical questions.</p>
              <div class="guide-inline-cta"><div><span>RELATED SXF GUIDE</span><strong>Best AI Agents in 2026</strong><p>Compare today's deployed work, research, coding and automation agents before looking at the emerging super-agent layer above them.</p></div><a href="/guides/best-ai-agents/">Open guide ↗</a></div>
            </section>

            <section class="guide-faq-section" id="faq">
              <p class="eyebrow">FAQ</p>
              <h2>Frequently asked questions about AI super agents</h2>
              <div class="model-faq">{faq_html}</div>
            </section>

            <section class="guide-sources">
              <p class="eyebrow">PRIMARY SOURCES</p>
              <h2>Primary sources used for this guide</h2>
              <p>Because “super agent” is not yet a standard term, this guide grounds the definition in how companies are actually using it in deployed 2026 systems. Vendor productivity and benchmark claims are attributed as vendor evidence, not treated as independent SXF measurements.</p>
              <div class="model-sources">{source_links}</div>
            </section>
          </div>
        </div>
      </article>
    </main>{page_footer()}</body></html>'''


def superintelligence_index_html(items, current_items):
    canonical = f"{BASE_URL}/superintelligence/"
    verified = "2026-09-26"
    title = "Superintelligence (ASI): What It Is, AGI vs ASI, Risks & Latest Research | SXF / AI"
    description = "A living guide to artificial superintelligence (ASI): definition, AGI vs ASI, paths to superintelligence, capabilities, recursive self-improvement, risks, control and research."

    source_records = [
        ("Google DeepMind", "From AGI to ASI", "Jun 12, 2026", "Research", "Four pathways: scaling AGI, paradigm shifts, recursive improvement and large-scale multi-agent collectives.", "https://deepmind.google/research/publications/239142/"),
        ("Google DeepMind", "Solipsistic superintelligence is unlikely to be cooperative", "Jun 4, 2026", "Cooperation", "Argues that highly capable task solvers need cooperation and institutions as design primitives rather than treating the world as stationary.", "https://deepmind.google/research/publications/231466/"),
        ("Google DeepMind", "Securing the future of AI agents", "Jun 18, 2026", "Control", "Describes an AI Control Roadmap for securing increasingly capable and imperfectly aligned agents.", "https://deepmind.google/blog/securing-the-future-of-ai-agents/"),
        ("OpenAI", "Industrial Policy for the Intelligence Age", "2026", "Transition", "Describes a transition toward systems that outperform the smartest humans even when those humans are AI-assisted, while emphasizing uncertainty about how the transition unfolds.", "https://openai.com/index/industrial-policy-for-the-intelligence-age/"),
        ("OpenAI", "Our principles", "Apr 26, 2026", "Governance", "Frames a future in which superintelligence could concentrate power or be distributed more broadly, and argues for democratization and human agency.", "https://openai.com/index/our-principles/"),
        ("Meta", "Personal superintelligence", "2026", "Vision", "Meta's stated vision is personal superintelligence directed by individuals toward goals they value.", "https://ai.meta.com/events/"),
        ("Meta", "Muse Spark 1.1", "Jul 9, 2026", "Models", "Meta Superintelligence Labs positions its multimodal reasoning work as progress toward its personal-superintelligence vision.", "https://ai.meta.com/blog/introducing-muse-spark-meta-model-api/"),
        ("Anthropic", "Automated Alignment Researchers", "Apr 14, 2026", "Alignment", "Studies whether frontier models can help scale alignment research and oversight as models become harder for humans to evaluate directly.", "https://www.anthropic.com/news/automated-alignment-researchers"),
        ("Anthropic", "Agentic Misalignment in Summer 2026", "Jul 13, 2026", "Agent safety", "Reports controlled simulations of frontier-agent failures and argues for measuring such failure modes before agents receive more authority.", "https://alignment.anthropic.com/2026/agentic-misalignment-summer-2026/"),
    ]

    research_cards = "".join(
        f'''<a class="si-research-card" href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">
          <div><span>{escape(org)}</span><small>{escape(date)} · {escape(kind)}</small></div>
          <h3>{escape(name)}</h3><p>{escape(copy)}</p><b>Primary source ↗</b>
        </a>'''
        for org,name,date,kind,copy,url in source_records
    )

    path_cards = [
        ("01","Scaling AGI","Continue scaling and improving broadly capable AGI systems until capability moves beyond human and organizational baselines.","DeepMind pathway"),
        ("02","AI paradigm shifts","A new architecture, learning paradigm or system design could unlock capabilities that scaling today's methods does not.","DeepMind pathway"),
        ("03","Recursive improvement","AI systems may contribute increasingly to AI research, improving the systems and processes used to build their successors.","DeepMind pathway"),
        ("04","Multi-agent collectives","Superhuman system-level capability could emerge from very large collections of interacting agents rather than one monolithic model.","DeepMind pathway"),
    ]
    paths_html = "".join(
        f'''<article class="si-path"><span>{num}</span><small>{escape(note)}</small><h3>{escape(name)}</h3><p>{escape(copy)}</p></article>'''
        for num,name,copy,note in path_cards
    )

    capabilities = [
        ("Scientific discovery","Projected ASI","Generate and test hypotheses across disciplines at a pace and breadth beyond human research organizations."),
        ("Software & AI R&D","Projected ASI","Design, implement and evaluate complex systems—including parts of the AI research process itself."),
        ("Mathematics & reasoning","Projected ASI","Solve novel formal and conceptual problems beyond the strongest human specialists."),
        ("Strategic planning","Projected ASI","Model long-horizon consequences and coordinate decisions across complex, changing environments."),
        ("Robotics & physical systems","Projected ASI","Pair advanced cognition with perception, planning and control in the physical world."),
        ("Collective coordination","Projected ASI","Coordinate many agents, tools or institutions at a scale that creates system-level cognitive capability."),
    ]
    capability_html = "".join(
        f'''<article><span>{escape(status)}</span><h3>{escape(name)}</h3><p>{escape(copy)}</p></article>'''
        for name,status,copy in capabilities
    )

    labs = [
        ("Google DeepMind","Research framing","Published a dedicated AGI→ASI report defining artificial general superintelligence and analyzing four possible pathways beyond AGI.","https://deepmind.google/research/publications/239142/"),
        ("OpenAI","Transition & governance","Public 2026 materials explicitly discuss a transition toward superintelligence, distribution of power, infrastructure and governance.","https://openai.com/index/our-principles/"),
        ("Meta Superintelligence Labs","Personal superintelligence","Meta frames its goal as personal superintelligence placed in individuals' hands and links Muse model development to that vision.","https://ai.meta.com/events/"),
        ("Anthropic","Alignment & oversight","Anthropic's public alignment work focuses on agentic failure modes, scalable oversight and using AI to help automate alignment research as capabilities grow.","https://www.anthropic.com/research/team/alignment"),
    ]
    labs_html = "".join(
        f'''<a class="si-lab" href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(angle)}</span><h3>{escape(name)}</h3><p>{escape(copy)}</p><b>Official source ↗</b></a>'''
        for name,angle,copy,url in labs
    )

    glossary = [
        ("AGI","Artificial general intelligence","A debated category for AI with broad, general capability across domains rather than a narrow specialist system."),
        ("ASI","Artificial superintelligence","AI that broadly exceeds human cognitive capability; current research sources treat it as a future state, not a demonstrated present-day system."),
        ("Artificial general superintelligence","DeepMind terminology","A post-AGI system more intelligent and cognitively capable than large organizations of humans."),
        ("Recursive self-improvement","AI improving AI","A pathway in which AI meaningfully contributes to improving models, training, research or the systems used to build successors."),
        ("Scalable oversight","Supervising stronger systems","Methods for evaluating and steering models on tasks that humans cannot reliably assess unaided."),
        ("Agentic AI","Action-taking AI","Systems that plan, use tools and execute multi-step tasks rather than only produce responses."),
        ("Multi-agent system","Collective architecture","Multiple agents with distinct roles or policies that communicate or coordinate toward goals."),
        ("AI control","Operational safeguards","Techniques for limiting, monitoring and containing advanced systems even when perfect alignment cannot be assumed."),
        ("Alignment","Intent and behavior","Work on making AI systems behave in ways that reliably reflect intended goals, constraints and human values."),
        ("Intelligence explosion","Hypothetical acceleration","A proposed feedback process where improvements to AI research capability accelerate further improvements."),
    ]
    glossary_html = "".join(
        f'''<article><span>{escape(label)}</span><h3>{escape(term)}</h3><p>{escape(copy)}</p></article>'''
        for term,label,copy in glossary
    )

    deep_guides = [
        ("/guides/ai-super-agents/","SUPER AGENTS","AI Super Agents in 2026","How higher-level agent orchestrators differ from ordinary agents, multi-agent systems, AGI and superintelligence."),
        ("/guides/best-ai-agents/","AGENTIC AI","Best AI Agents in 2026","Today's deployed work, research, coding and automation agents—the layer below the ASI question."),
        ("/guides/gpt-6-vs-claude/","FRONTIER MODELS","GPT-6 vs Claude in 2026","Current frontier model families, reasoning, agents, pricing and API architecture."),
        ("/guides/open-source-ai-models/","OPEN MODELS","Best Open-Source AI Models in 2026","Open and open-weight systems, deployment constraints and local AI."),
    ]
    guide_cards = "".join(
        f'''<a class="si-guide-card" href="{escape(href, quote=True)}"><span>{escape(kicker)}</span><h3>{escape(name)}</h3><p>{escape(copy)}</p><b>Read guide ↗</b></a>'''
        for href,kicker,name,copy in deep_guides
    )

    def is_frontier_signal(item):
        hay = " ".join([
            item.get("title",""), item.get("summary",""), item.get("category",""),
            " ".join(item.get("tags",[]) or [])
        ]).lower()
        terms = ("superintelligen","agi","alignment","agentic","agent ","agents","safety","reasoning","research","evaluation","misalignment","autonomous")
        return any(term in hay for term in terms)

    related = [item for item in current_items if is_frontier_signal(item)]
    if len(related) < 4:
        extras = [item for item in current_items if item not in related and (item.get("category") == "Research" or "Research" in (item.get("tags") or []))]
        related.extend(extras[:6-len(related)])
    signal_rows = "".join(signal_row(item) for item in related[:6])

    faq = [
        ("What is superintelligence?", "Artificial superintelligence (ASI) generally refers to AI that exceeds human cognitive capability across broad domains. Google DeepMind's 2026 AGI-to-ASI report describes artificial general superintelligence as a system more intelligent and cognitively capable than large organizations of humans."),
        ("Does artificial superintelligence exist today?", "The official research and company sources reviewed by SXF discuss ASI as a future or emerging target rather than a demonstrated existing system. Today's frontier models can already be superhuman on some narrow tasks, but narrow superhuman performance is not the same as broad artificial superintelligence."),
        ("What is the difference between AGI and ASI?", "AGI is generally used for broadly capable AI at roughly human-level generality or competence, although definitions vary. ASI refers to a further level where machine intelligence broadly exceeds humans, potentially including the collective capability of large human organizations."),
        ("Is GPT-6 or Claude superintelligent?", "No official source cited on this page classifies today's GPT-6 or Claude systems as artificial superintelligence. Frontier models can be highly capable and superhuman on selected tasks without meeting a broad ASI definition."),
        ("How could superintelligence emerge?", "Google DeepMind's 2026 report analyzes four possible paths from AGI to ASI: scaling AGI, shifts in AI paradigms, recursive improvement, and emergence from large-scale multi-agent collectives."),
        ("What is recursive self-improvement?", "Recursive self-improvement is the idea that AI could increasingly improve the models, algorithms, training methods, tools or research processes used to build more capable AI, creating a feedback loop. It is a proposed pathway, not a demonstrated inevitability."),
        ("Could multi-agent systems become superintelligent?", "DeepMind includes large-scale multi-agent collectives as one possible route from AGI to ASI. Whether collective systems would produce broad superintelligence depends on coordination, communication, specialization, governance and many unresolved research questions."),
        ("Can superintelligence be controlled?", "There is no demonstrated complete solution for controlling hypothetical ASI. Current research includes scalable oversight, alignment training, monitoring, containment, least-privilege tool access, AI control methods, cooperation and institutional safeguards."),
        ("When will superintelligence arrive?", "There is no reliable consensus date. OpenAI and other labs publish views and scenarios, but these are forecasts or strategic positions rather than established timelines. DeepMind's AGI-to-ASI report analyzes pathways instead of assigning a fixed arrival date."),
        ("Is a super agent the same as superintelligence?", "No. A super agent is an orchestration architecture that coordinates agents, models and tools. Superintelligence describes a level of broad cognitive capability. A system can be a powerful super agent without being AGI or ASI."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq)

    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"CollectionPage","@id":canonical+"#webpage","url":canonical,
                "name":"Superintelligence (ASI) — SXF / AI",
                "headline":"Superintelligence: The Intelligence Beyond AGI",
                "description":description,"dateModified":verified,
                "isPartOf":{"@id":"https://sxf.si/#website"},
                "about":[
                    {"@type":"Thing","name":"Artificial superintelligence"},
                    {"@type":"Thing","name":"Artificial general intelligence"},
                    {"@type":"Thing","name":"AI alignment"},
                    {"@type":"Thing","name":"Multi-agent systems"},
                    {"@type":"Thing","name":"Recursive self-improvement"}
                ],
                "citation":[url for _org,_name,_date,_kind,_copy,url in source_records],
                "hasPart":[{"@id":BASE_URL+href} for href,_k,_n,_c in deep_guides],
                "inLanguage":"en"
            },
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},
                {"@type":"ListItem","position":2,"name":"Superintelligence","item":canonical}
            ]},
            {"@type":"ItemList","name":"SXF superintelligence reference guides","numberOfItems":len(deep_guides),"itemListElement":[
                {"@type":"ListItem","position":i+1,"name":name,"url":BASE_URL+href}
                for i,(href,_k,name,_c) in enumerate(deep_guides)
            ]},
            {"@type":"FAQPage","mainEntity":[
                {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq
            ]}
        ]
    }

    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema)}
    <body class="intel-page si-page">{page_header("superintelligence")}<main>
      <section class="si-hero shell">
        <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><span>Superintelligence</span></nav>
        <div class="si-hero-grid">
          <div class="si-hero-copy">
            <p class="eyebrow">SXF / SUPERINTELLIGENCE INTELLIGENCE HUB</p>
            <h1>Superintelligence:<br><span>The intelligence beyond AGI.</span></h1>
            <p>Artificial superintelligence (ASI) is the idea of AI that broadly exceeds human cognitive capability. This living reference separates demonstrated AI from proposed pathways, company visions and unresolved research—then connects the evidence to the systems being built now.</p>
            <div class="hero-actions"><a class="primary-cta" href="#definition">Understand ASI <span>↓</span></a><a class="secondary-cta" href="#research">Latest research</a></div>
          </div>
          <div class="si-core" aria-label="Conceptual intelligence continuum">
            <div class="si-ring si-ring-outer"></div><div class="si-ring si-ring-mid"></div><div class="si-ring si-ring-inner"></div>
            <div class="si-core-center"><small>ARTIFICIAL</small><strong>ASI</strong><span>SUPERINTELLIGENCE</span></div>
            <span class="si-node si-node-a">AGI</span><span class="si-node si-node-b">AGENTS</span><span class="si-node si-node-c">RESEARCH</span><span class="si-node si-node-d">CONTROL</span>
          </div>
        </div>
        <div class="si-status-bar"><span>Last verified <strong>Sep 26, 2026</strong></span><span>Research-led reference</span><span>Living intelligence hub</span></div>
      </section>

      <section class="si-definition shell" id="definition">
        <div class="si-definition-label">QUICK DEFINITION</div>
        <div><h2>What is artificial superintelligence (ASI)?</h2><p><strong>Artificial superintelligence</strong> refers to AI that exceeds human cognitive capability across broad domains—not merely one benchmark or narrow task. DeepMind's 2026 framing goes further, describing artificial general superintelligence as a system more intelligent and cognitively capable than large organizations of humans.</p>
        <p>ASI is not a label SXF applies to current frontier models. In the official sources tracked here, it remains a future state, research target or strategic vision. The evidence today is about increasingly capable models, agents and AI-assisted research—not a demonstrated general superintelligence.</p></div>
      </section>

      <section class="si-continuum shell">
        <div class="intel-section-head"><div><p class="eyebrow">INTELLIGENCE CONTINUUM</p><h2>Current AI → AGI → ASI.</h2></div><span>Conceptual map, not a forecast</span></div>
        <div class="si-continuum-grid">
          <article><span>01 · NOW</span><h3>Frontier AI</h3><p>Broadly useful models and agents that can be superhuman on selected tasks but remain uneven, tool-dependent and failure-prone.</p><small>Demonstrated today</small></article>
          <article><span>02 · DEBATED THRESHOLD</span><h3>AGI</h3><p>A contested category for broadly general machine intelligence. Definitions differ across labs, researchers and policy discussions.</p><small>No universal definition</small></article>
          <article class="is-highlight"><span>03 · FUTURE STATE</span><h3>ASI</h3><p>Broad machine intelligence beyond human individuals—and in stronger definitions, beyond the cognitive capability of large human organizations.</p><small>Not demonstrated</small></article>
          <article><span>04 · THEORETICAL LIMITS</span><h3>Universal AI</h3><p>A theoretical endpoint used in research to reason about the upper continuum of machine intelligence beyond practical present-day systems.</p><small>Theoretical framing</small></article>
        </div>
        <div class="guide-callout"><strong>Do not collapse the categories</strong><p>A model can beat humans at coding, chess, retrieval or a scientific benchmark without being AGI or ASI. Narrow superhuman performance is evidence about a capability—not proof of general superintelligence.</p></div>
      </section>

      <section class="si-paths shell">
        <div class="intel-section-head"><div><p class="eyebrow">PATHS BEYOND AGI</p><h2>How could superintelligence emerge?</h2></div><a href="https://deepmind.google/research/publications/239142/" target="_blank" rel="noopener noreferrer">DeepMind primary source ↗</a></div>
        <p class="si-section-intro">Google DeepMind's 2026 <em>From AGI to ASI</em> report analyzes four broad pathways. They are scenarios for reasoning about a post-AGI future—not claims that any one path is inevitable.</p>
        <div class="si-path-grid">{paths_html}</div>
      </section>

      <section class="si-capabilities shell">
        <div class="intel-section-head"><div><p class="eyebrow">CAPABILITY MAP</p><h2>What could ASI actually be able to do?</h2></div><span>Projected capabilities, not present-day claims</span></div>
        <p class="si-section-intro">A useful ASI discussion must separate capabilities demonstrated by today's systems from capabilities implied by the definition of broad superintelligence. The cards below describe the latter.</p>
        <div class="si-capability-grid">{capability_html}</div>
      </section>

      <section class="si-rsi shell">
        <div class="si-split">
          <article><p class="eyebrow">RECURSIVE SELF-IMPROVEMENT</p><h2>Can AI improve itself?</h2><p>AI already contributes to coding, model evaluation and parts of AI research. Recursive self-improvement is the stronger hypothesis that those contributions could form a feedback loop: better AI improves the process used to create better AI, which then improves that process again.</p><p>That does <strong>not</strong> mean an intelligence explosion is automatic. Progress could bottleneck on experiments, compute, data, hardware, evaluation, coordination, physical infrastructure or human institutions. DeepMind treats recursive improvement as one possible ASI pathway, not a guaranteed outcome.</p></article>
          <article><p class="eyebrow">MULTI-AGENT SUPERINTELLIGENCE</p><h2>Could many agents become smarter than one model?</h2><p>Potentially. DeepMind includes large-scale multi-agent collectives as a possible route from AGI to ASI. Specialization and parallelism can create system-level capability that no single worker has.</p><p>But coordination creates its own limits: communication overhead, conflicting state, incentive problems, correlated failures and governance. Anthropic's 2026 work on AI organizations is an early warning that groups of agents can become more effective while also creating new alignment problems.</p></article>
        </div>
      </section>

      <section class="si-personal shell">
        <div class="si-personal-grid">
          <div><p class="eyebrow">PERSONAL SUPERINTELLIGENCE</p><h2>Meta uses the term differently.</h2></div>
          <div><p>Meta's public vision is <strong>“personal superintelligence”</strong>: advanced AI placed in individuals' hands to help them pursue goals they value. Meta Superintelligence Labs links Muse model development to that direction.</p><p>This is an important example of why terminology must be sourced. A company's product vision for “personal superintelligence” is not automatically the same thing as the broad ASI concept used in academic work.</p><a href="https://ai.meta.com/events/" target="_blank" rel="noopener noreferrer">Meta's stated vision ↗</a></div>
        </div>
      </section>

      <section class="si-labs shell">
        <div class="intel-section-head"><div><p class="eyebrow">LABS & RESEARCH DIRECTIONS</p><h2>Who is working on the path toward more powerful AI?</h2></div><span>Official positions · no ranking</span></div>
        <p class="si-section-intro">These organizations use different terminology and pursue different research programs. SXF reports their documented positions without treating them as equivalent claims or predicting which organization reaches any future threshold first.</p>
        <div class="si-lab-grid">{labs_html}</div>
      </section>

      <section class="si-safety shell">
        <div class="intel-section-head"><div><p class="eyebrow">ALIGNMENT & CONTROL</p><h2>Can superintelligence be controlled?</h2></div><span>Open research problem</span></div>
        <div class="si-safety-grid">
          <article><span>ALIGNMENT</span><h3>Will the system pursue what humans actually intend?</h3><p>Current alignment methods depend heavily on human feedback and evaluation. If future systems outperform humans on hard tasks, supervision itself becomes a technical bottleneck.</p></article>
          <article><span>SCALABLE OVERSIGHT</span><h3>How do humans evaluate work they cannot understand unaided?</h3><p>Research from Anthropic and others explores using AI to assist oversight and alignment research while testing whether those methods continue to generalize as capability rises.</p></article>
          <article><span>AI CONTROL</span><h3>Can dangerous actions be contained even if alignment is imperfect?</h3><p>Control research focuses on monitoring, sandboxing, permissions, tripwires, restricted access and system architectures that limit what a capable model can do.</p></article>
          <article><span>COOPERATION</span><h3>Will powerful systems act well in a world of other agents and institutions?</h3><p>DeepMind argues that a highly capable task solver is not automatically cooperative and that institutions and interdependence may need to be part of the design problem.</p></article>
          <article><span>HUMAN AGENCY</span><h3>Who retains meaningful decision power?</h3><p>Technical safety is incomplete if humans lose practical control over goals, institutions or resource allocation. Several current research and policy frameworks explicitly preserve human agency.</p></article>
          <article><span>GOVERNANCE</span><h3>Who gets to deploy, constrain or benefit from the most capable systems?</h3><p>Superintelligence raises questions beyond model behavior: concentration of power, access, accountability, infrastructure and democratic oversight.</p></article>
        </div>
      </section>

      <section class="si-timeline shell">
        <div class="intel-section-head"><div><p class="eyebrow">PATHWAY, NOT PREDICTION</p><h2>What would have to happen before ASI?</h2></div><span>No fixed arrival date</span></div>
        <div class="si-timeline-list">
          <div><span>NOW</span><strong>Frontier multimodal models and agents</strong><p>Systems increasingly reason, use tools, code, browse and act—but remain inconsistent and dependent on scaffolding.</p></div>
          <div><span>STEP 01</span><strong>Broader autonomous competence</strong><p>Agents become more reliable across longer tasks, environments and modalities with better verification and memory.</p></div>
          <div><span>STEP 02</span><strong>AGI-like breadth</strong><p>A debated threshold where machine capability becomes broadly general across major cognitive domains.</p></div>
          <div><span>STEP 03</span><strong>AI-accelerated AI research</strong><p>AI contributes materially to model design, experimentation, coding, evaluation and scientific discovery.</p></div>
          <div><span>STEP 04</span><strong>Post-AGI amplification</strong><p>Scaling, new paradigms, recursive improvement or collective intelligence could push system capability beyond human organizations.</p></div>
          <div><span>ASI</span><strong>Artificial general superintelligence</strong><p>A future state of broad cognitive capability beyond humans; timing and feasibility remain uncertain.</p></div>
        </div>
        <div class="guide-callout"><strong>When will superintelligence arrive?</strong><p>There is no reliable consensus date. Public lab statements are forecasts, goals or scenarios—not measurements of an established timeline. SXF therefore tracks milestones and evidence instead of publishing a countdown.</p></div>
      </section>

      <section class="si-research shell" id="research">
        <div class="intel-section-head"><div><p class="eyebrow">PRIMARY RESEARCH & POSITIONS</p><h2>The evidence layer.</h2></div><span>Official sources · 2026</span></div>
        <div class="si-research-grid">{research_cards}</div>
      </section>

      <section class="si-guides shell">
        <div class="intel-section-head"><div><p class="eyebrow">DEEP GUIDES</p><h2>Go deeper into the systems beneath ASI.</h2></div><a href="/guides/">All guides ↗</a></div>
        <div class="si-guide-grid">{guide_cards}</div>
      </section>

      <section class="si-glossary shell">
        <div class="intel-section-head"><div><p class="eyebrow">KEY TERMS</p><h2>Superintelligence glossary.</h2></div><span>Definitions used by SXF</span></div>
        <div class="si-glossary-grid">{glossary_html}</div>
      </section>

      <section class="si-faq shell">
        <div class="intel-section-head"><div><p class="eyebrow">QUICK ANSWERS</p><h2>Questions people ask about ASI.</h2></div><span>Direct answers · source-aware</span></div>
        <div class="model-faq">{faq_html}</div>
      </section>

      <section class="related-signals shell">
        <div class="intel-section-head"><div><p class="eyebrow">FRONTIER SIGNALS</p><h2>Research and agent signals feeding this hub.</h2></div><a href="/signals/">All signals ↗</a></div>
        <div class="signal-list">{signal_rows}</div>
      </section>
    </main>{page_footer()}</body></html>'''

def guides_index_html(items, current_items):
    canonical = f"{BASE_URL}/guides/"
    description = "In-depth AI guides covering models, coding tools, agents, open-source AI, research and superintelligence, built from primary sources and SXF intelligence."
    published = [
        {
            "href": "/guides/ai-agent-security/",
            "category": "Security · Agents",
            "categories": ["security", "agents", "research", "coding"],
            "kicker": "SECURITY REFERENCE",
            "title": "AI Agent Security in 2026",
            "description": "Prompt injection, MCP security, permissions, sandboxing, memory integrity, secrets, human approval and production controls.",
            "meta": "Prompt injection · MCP · Identity · Sandboxing",
            "updated": "Sep 26, 2026",
            "read_time": "30 min",
        },
        {
            "href": "/guides/prompt-injection/",
            "category": "Security · AI",
            "categories": ["security", "agents", "research"],
            "kicker": "PROMPT INJECTION",
            "title": "Prompt Injection in AI in 2026",
            "description": "Direct vs indirect prompt injection, agent hijacking, RAG and browser risks, MCP/tool exposure, layered defenses and production controls.",
            "meta": "Direct · Indirect · RAG · Agents",
            "updated": "Sep 26, 2026",
            "read_time": "26 min",
        },
        {
            "href": "/guides/github-copilot-alternatives/",
            "category": "Coding · Copilot",
            "categories": ["coding", "agents", "open-source"],
            "kicker": "COPILOT ALTERNATIVES",
            "title": "Best GitHub Copilot Alternatives in 2026",
            "description": "Cursor, Claude Code, Codex, Cline, JetBrains AI, OpenCode and Devin Desktop compared by workflow, pricing, agents, model choice and team fit.",
            "meta": "Cursor · Claude Code · Codex · Cline",
            "updated": "Sep 26, 2026",
            "read_time": "28 min",
        },
        {
            "href": "/guides/best-ai-coding-tools/",
            "category": "Coding",
            "categories": ["coding", "agents"],
            "kicker": "BUYING GUIDE",
            "title": "Best AI Coding Tools in 2026",
            "description": "Claude Code, Codex, GitHub Copilot, Cursor and Windsurf/Devin Desktop compared by workflow, pricing, autonomy and team fit.",
            "meta": "Coding agents · Pricing · Comparison",
            "updated": "Sep 25, 2026",
            "read_time": "18 min",
        },
        {
            "href": "/guides/gpt-6-vs-claude/",
            "category": "Models",
            "categories": ["models", "coding", "agents", "research"],
            "kicker": "FRONTIER MODEL GUIDE",
            "title": "GPT-6 vs Claude in 2026",
            "description": "A family-level comparison of models, pricing, coding, context windows, reasoning, agents and API architecture.",
            "meta": "Models · Pricing · API · Agents",
            "updated": "Sep 25, 2026",
            "read_time": "22 min",
        },
        {
            "href": "/guides/open-source-ai-models/",
            "category": "Open Source · Models",
            "categories": ["open-source", "models", "coding", "agents", "research"],
            "kicker": "OPEN MODEL GUIDE",
            "title": "Best Open-Source AI Models in 2026",
            "description": "DeepSeek, Qwen, GLM, Mistral, Gemma and Kimi compared by license, architecture, context, hardware and local deployment.",
            "meta": "Licenses · Hardware · Local AI",
            "updated": "Sep 26, 2026",
            "read_time": "24 min",
        },
        {
            "href": "/guides/best-ai-agents/",
            "category": "Agents · Automation",
            "categories": ["agents", "coding", "research"],
            "kicker": "AI AGENTS GUIDE",
            "title": "Best AI Agents in 2026",
            "description": "ChatGPT Work, Claude Cowork, Manus, Zapier Agents and Devin Desktop compared by autonomy, execution environment, pricing and best use.",
            "meta": "Work · Research · Coding · Automation",
            "updated": "Sep 26, 2026",
            "read_time": "25 min",
        },
        {
            "href": "/guides/ai-super-agents/",
            "category": "Agents · Superintelligence",
            "categories": ["agents", "research", "superintelligence"],
            "kicker": "EMERGING AI SYSTEMS",
            "title": "AI Super Agents in 2026",
            "description": "What super agents are, how orchestration works, real 2026 examples, multi-agent architecture, safety and the difference from AGI.",
            "meta": "Orchestration · Multi-agent · Safety · AGI",
            "updated": "Sep 26, 2026",
            "read_time": "26 min",
        },
        {
            "href": f"/compare/{GPT6_COMPARE_SLUG}/",
            "category": "Models",
            "categories": ["models"],
            "kicker": "MODEL SELECTION",
            "title": "GPT-6 Astra vs Sol vs Luna",
            "description": "Compare OpenAI’s GPT-6 family on capability positioning, context, API pricing and workload economics.",
            "meta": "Pricing · Context · Use cases",
            "updated": "Sep 25, 2026",
            "read_time": "6 min",
        },
        {
            "href": f"/compare/{GPT6_SOL_CLAUDE_COMPARE_SLUG}/",
            "category": "Models · Coding · Agents",
            "categories": ["models", "coding", "agents"],
            "kicker": "FRONTIER COMPARISON",
            "title": "GPT-6 Sol vs Claude Opus 5.5",
            "description": "A source-backed comparison of pricing, long-context economics, reasoning controls and agentic positioning.",
            "meta": "API · Agents · Long context",
            "updated": "Sep 25, 2026",
            "read_time": "7 min",
        },
    ]
    featured = published[:2]
    featured_cards = "".join(
        f'''<a class="guide-feature-card {"guide-feature-lead" if i == 0 else ""}" href="{escape(g["href"], quote=True)}">
          <div class="guide-card-top"><span class="guide-card-kicker">{escape(g["kicker"])}</span><small>{escape(g["updated"])}</small></div>
          <h2>{escape(g["title"])}</h2>
          <p>{escape(g["description"])}</p>
          <div class="guide-card-foot"><span>{escape(g["category"])} · {escape(g["read_time"])}</span><b>Read guide ↗</b></div>
        </a>'''
        for i, g in enumerate(featured)
    )
    library_cards = "".join(
        f'''<article class="guide-library-card" data-categories="{escape(" ".join(g["categories"]), quote=True)}" data-search="{escape((g["title"] + " " + g["description"] + " " + g["category"] + " " + g["meta"]).lower(), quote=True)}">
          <a href="{escape(g["href"], quote=True)}">
            <div class="guide-library-meta"><span>{escape(g["category"])}</span><span>Updated {escape(g["updated"])} · {escape(g["read_time"])}</span></div>
            <h3>{escape(g["title"])}</h3>
            <p>{escape(g["description"])}</p>
            <div class="guide-library-foot"><small>{escape(g["meta"])}</small><b>Open guide ↗</b></div>
          </a>
        </article>'''
        for g in published
    )
    tracks = [
        ("/models/", "01", "AI Models", "Capabilities, context windows, pricing, releases and persistent model reference pages.", "Explore models"),
        ("/topics/coding-ai/", "02", "AI Coding", "Coding agents, copilots, developer workflows and the tools changing software engineering.", "Track coding AI"),
        ("/topics/ai-agents/", "03", "AI Agents", "Agentic systems, APIs, orchestration and multi-step AI workflows.", "Explore agents"),
        ("/open-source/", "04", "Open-Source AI", "Open weights, runtimes, local inference, frameworks and deployable model ecosystems.", "Open-source layer"),
        ("/research/", "05", "Research & Safety", "Evaluations, benchmarks, alignment, security and evidence behind capability claims.", "Research layer"),
        ("/superintelligence/", "06", "Superintelligence", "ASI, paths beyond AGI, recursive improvement, multi-agent intelligence, alignment and control.", "Open the ASI hub"),
    ]
    track_cards = "".join(
        f'''<a class="guide-track" href="{escape(href, quote=True)}"><span>{num}</span><div><h3>{escape(title)}</h3><p>{escape(copy)}</p></div><b>{escape(cta)} ↗</b></a>'''
        for href, num, title, copy, cta in tracks
    )
    latest_rows = "".join(signal_row(item) for item in current_items[:6])
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": "AI Guides — Models, Agents, Coding & Superintelligence | SXF / AI",
                "description": description,
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "about": [
                    {"@type": "Thing", "name": "Artificial intelligence"},
                    {"@type": "Thing", "name": "Artificial superintelligence"},
                ],
                "hasPart": [{"@id": BASE_URL + g["href"]} for g in published],
                "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Guides", "item": canonical},
                ],
            },
            {
                "@type": "ItemList",
                "name": "SXF AI guides",
                "numberOfItems": len(published),
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "url": BASE_URL + g["href"], "name": g["title"]}
                    for i, g in enumerate(published)
                ],
            },
        ],
    }
    filters = [
        ("all", "All"),
        ("models", "Models"),
        ("coding", "Coding"),
        ("agents", "Agents"),
        ("security", "Security"),
        ("open-source", "Open Source"),
        ("research", "Research"),
        ("superintelligence", "Superintelligence"),
    ]
    filter_buttons = "".join(
        f'<button class="guide-filter{" is-active" if key == "all" else ""}" type="button" data-filter="{escape(key, quote=True)}">{escape(label)}</button>'
        for key, label in filters
    )
    library_script = '''<script>
    (() => {
      const input = document.getElementById("guideSearch");
      const cards = [...document.querySelectorAll(".guide-library-card")];
      const buttons = [...document.querySelectorAll(".guide-filter")];
      const empty = document.getElementById("guideEmpty");
      const count = document.getElementById("guideVisibleCount");
      let active = "all";
      const apply = () => {
        const q = (input.value || "").trim().toLowerCase();
        let visible = 0;
        cards.forEach(card => {
          const categories = (card.dataset.categories || "").split(" ");
          const categoryMatch = active === "all" || categories.includes(active);
          const searchMatch = !q || (card.dataset.search || "").includes(q);
          const show = categoryMatch && searchMatch;
          card.hidden = !show;
          if (show) visible += 1;
        });
        count.textContent = visible;
        empty.hidden = visible !== 0;
      };
      buttons.forEach(button => button.addEventListener("click", () => {
        buttons.forEach(x => x.classList.remove("is-active"));
        button.classList.add("is-active");
        active = button.dataset.filter || "all";
        apply();
      }));
      input.addEventListener("input", apply);
      apply();
    })();
    </script>'''
    return f'''<!doctype html><html lang="en">{page_head("AI Guides — Models, Agents, Coding & Superintelligence | SXF / AI", description, canonical, schema)}
    <body class="intel-page guides-page">{page_header("guides")}<main>
      <section class="guides-hero shell">
        <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><span>Guides</span></nav>
        <div class="guides-hero-grid">
          <div><p class="eyebrow">SXF GUIDES</p><h1>AI guides.<br><span>Built for decisions.</span></h1></div>
          <div class="guides-hero-copy"><p>Source-backed guides for choosing models, tools and AI systems — with pricing, capabilities, tradeoffs and live context from the SXF radar.</p></div>
        </div>
      </section>

      <section class="guides-featured shell">
        <div class="intel-section-head"><div><p class="eyebrow">FEATURED GUIDES</p><h2>Start here.</h2></div><span>Primary-source research · Living references</span></div>
        <div class="guide-feature-grid">{featured_cards}</div>
      </section>

      <section class="guide-library shell" id="all-guides">
        <div class="guide-library-heading">
          <div><p class="eyebrow">ALL GUIDES</p><h2>Browse the library.</h2><p>Find comparisons and reference guides by subject or search directly.</p></div>
          <div class="guide-library-count"><strong id="guideVisibleCount">{len(published)}</strong><span>guides shown</span></div>
        </div>
        <div class="guide-library-tools">
          <label class="guide-search"><span class="sr-only">Search SXF guides</span><input id="guideSearch" type="search" placeholder="Search guides, models, tools..." autocomplete="off" /></label>
          <div class="guide-filters" aria-label="Filter guides">{filter_buttons}</div>
        </div>
        <div class="guide-library-grid">{library_cards}</div>
        <div class="guide-empty" id="guideEmpty" hidden>No published guides match this filter yet.</div>
      </section>

      <section class="guides-map shell">
        <div class="intel-section-head"><div><p class="eyebrow">EXPLORE BY TOPIC</p><h2>Go deeper into the intelligence stack.</h2></div><span>Models · Tools · Research</span></div>
        <div class="guide-track-grid">{track_cards}</div>
      </section>

      <section class="guide-standard shell">
        <div class="guide-standard-head"><p class="eyebrow">EDITORIAL STANDARD</p><h2>Useful after the launch cycle ends.</h2></div>
        <div class="guide-standard-grid">
          <article><span>01</span><h3>Primary-source first</h3><p>Specifications, pricing, availability and release details trace back to vendor documentation whenever a primary source exists.</p></article>
          <article><span>02</span><h3>Facts before claims</h3><p>Directly comparable facts stay separate from vendor benchmarks, launch claims and interpretation.</p></article>
          <article><span>03</span><h3>Decision-oriented</h3><p>Guides answer practical questions: what changed, what it costs, what it is built for and where tradeoffs appear.</p></article>
          <article><span>04</span><h3>Living references</h3><p>Guides connect to Models, Topics and Signals so new developments update context instead of becoming isolated posts.</p></article>
        </div>
      </section>

      <section class="related-signals shell">
        <div class="intel-section-head"><div><p class="eyebrow">LATEST SIGNALS</p><h2>Live context behind the guides.</h2></div><a href="/signals/">All signals ↗</a></div>
        <div class="signal-list">{latest_rows}</div>
      </section>
    </main>{page_footer()}{library_script}</body></html>'''

def gpt6_comparison_html(items):
    canonical = f"{BASE_URL}/compare/{GPT6_COMPARE_SLUG}/"
    verified = datetime.now(timezone.utc).date().isoformat()
    ref = MODEL_REFERENCE["GPT-6"]
    variants = ref["variants"]
    family_signals = [item for item in items if any(name.startswith("GPT-6") for name in extract_models(item["title"]))][:10]

    def money(value):
        return ("$" + f"{value:,.3f}").rstrip("0").rstrip(".")

    short_examples, monthly_examples = [], []
    for v in variants:
        input_rate = float(v["input_price"].replace("$", ""))
        output_rate = float(v["output_price"].replace("$", ""))
        short_examples.append((v["name"], money(input_rate * 0.1 + output_rate * 0.01)))
        monthly_examples.append((v["name"], money(input_rate * 10 + output_rate)))

    short_cards = "".join(
        f'<div><span>{escape(name)}</span><strong>{escape(cost)}</strong><small>100K input + 10K output</small></div>'
        for name, cost in short_examples
    )
    monthly_cards = "".join(
        f'<div><span>{escape(name)}</span><strong>{escape(cost)}</strong><small>10M input + 1M output</small></div>'
        for name, cost in monthly_examples
    )
    rows = "".join(
        f'''<tr><th scope="row"><a href="/models/{escape(slugify(v["name"]), quote=True)}/">{escape(v["name"])}</a><small>{escape(v["model_id"])}</small></th>
        <td>{escape(v["positioning"])}</td><td>{escape(v["best_for"])}</td><td>{escape(v["context"])}</td><td>{escape(v["max_output"])}</td>
        <td>{escape(v["input_price"])}</td><td>{escape(v["cached_price"])}</td><td>{escape(v["output_price"])}</td></tr>'''
        for v in variants
    )
    source_links = "".join(
        f'<a href="{escape(v["source"], quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(v["name"])} model card</span><b>↗</b></a>'
        for v in variants
    ) + '<a href="https://developers.openai.com/api/docs/pricing" target="_blank" rel="noopener noreferrer"><span>OpenAI API pricing</span><b>↗</b></a>'
    signal_rows = "".join(signal_row(item) for item in family_signals)
    faq_items = [
        ("What is the difference between GPT-6 Astra, Sol and Luna?", "OpenAI positions Astra as its most capable model for the hardest end-to-end work, Sol for complex coding and agentic workflows, and Luna as its most efficient option for focused high-volume tasks."),
        ("Do GPT-6 Astra, Sol and Luna have the same context window?", "Yes. OpenAI lists a 1,050,000-token context window and a 128,000-token maximum output for all three models."),
        ("Which GPT-6 model is cheapest?", "GPT-6 Luna has the lowest listed token prices: $0.10 per 1M input tokens, $0.01 cached input and $0.50 output at the listed short-context rates."),
        ("When does GPT-6 long-context pricing apply?", "OpenAI states that prompts above 272K input tokens use higher rates for the full request: 2x input and cache rates and 1.5x output rates."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q, a in faq_items)
    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {"@type":"WebPage","@id":canonical+"#webpage","url":canonical,"name":"GPT-6 Astra vs Sol vs Luna: Pricing, Context & Use Cases","description":"Compare GPT-6 Astra, Sol and Luna on API pricing, context window, output limits and official use-case positioning.","dateModified":verified,"isPartOf":{"@id":"https://sxf.si/#website"},"about":[{"@type":"Thing","name":v["name"]} for v in variants],"citation":[v["source"] for v in variants]+["https://developers.openai.com/api/docs/pricing"],"inLanguage":"en"},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},{"@type":"ListItem","position":2,"name":"Models","item":BASE_URL+"/models/"},{"@type":"ListItem","position":3,"name":"GPT-6 comparison","item":canonical}]},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_items]},
        ],
    }
    description = "GPT-6 Astra vs Sol vs Luna: compare OpenAI API pricing, 1.05M context windows, 128K output limits and official use-case positioning."
    return f'''<!doctype html><html lang="en">{page_head("GPT-6 Astra vs Sol vs Luna — Pricing & Use Cases | SXF / AI", description, canonical, schema)}
    <body class="intel-page comparison-page">{page_header("models")}<main>
      <section class="comparison-hero shell"><nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/models/">Models</a><span>/</span><span>GPT-6 comparison</span></nav>
      <p class="eyebrow">MODEL COMPARISON / VERIFIED {escape(verified)}</p><h1>GPT-6 Astra<br><span>vs Sol vs Luna.</span></h1>
      <p>A decision-oriented comparison built from OpenAI’s official model cards and API pricing. Same 1.05M context window. Very different capability positioning and unit economics.</p>
      <div class="hero-actions"><a class="primary-cta" href="#decision">Choose by workload <span>↓</span></a><a class="secondary-cta" href="/models/gpt-6/">GPT-6 reference</a></div></section>

      <section id="decision" class="decision-grid shell">
        <article><span>ASTRA</span><h2>Maximize capability.</h2><p>For the hardest end-to-end work: complex reasoning, coding, computer use, research and document creation.</p><strong>$10 input · $50 output</strong><a href="/models/gpt-6-astra/">GPT-6 Astra reference ↗</a></article>
        <article><span>SOL</span><h2>Balance capability and cost.</h2><p>Built for complex coding and agentic workflows, at one-fifth of Astra’s listed short-context token rates.</p><strong>$2 input · $10 output</strong><a href="/models/gpt-6-sol/">GPT-6 Sol reference ↗</a></article>
        <article><span>LUNA</span><h2>Optimize for volume.</h2><p>OpenAI’s most efficient GPT-6 option for focused, high-volume tasks and cost-sensitive workloads.</p><strong>$0.10 input · $0.50 output</strong><a href="/models/gpt-6-luna/">GPT-6 Luna reference ↗</a></article>
      </section>

      <section class="comparison-table-section shell"><div class="intel-section-head"><div><p class="eyebrow">SPECIFICATIONS</p><h2>Side-by-side.</h2></div><span>Prices per 1M tokens</span></div>
      <div class="model-table-wrap"><table><thead><tr><th>Model</th><th>Positioning</th><th>Best fit</th><th>Context</th><th>Max output</th><th>Input</th><th>Cached</th><th>Output</th></tr></thead><tbody>{rows}</tbody></table></div>
      <p class="reference-note">Listed rates are the official short-context token prices shown on OpenAI’s model cards. Prompts above 272K input tokens use 2x input/cache rates and 1.5x output rates for the full request.</p></section>

      <section class="cost-section shell"><div class="intel-section-head"><div><p class="eyebrow">COST EXAMPLES</p><h2>What the price gap means.</h2></div><span>Token charges only</span></div>
      <h3>One short-context workload</h3><div class="cost-grid">{short_cards}</div><h3>Monthly volume</h3><div class="cost-grid">{monthly_cards}</div>
      <p class="reference-note">Monthly example assumes requests remain at or below 272K input tokens each. Tool calls, regional processing and other service tiers can change total cost.</p></section>

      <section class="comparison-notes shell"><article><p class="eyebrow">WHAT STAYS THE SAME</p><h2>Context is not the differentiator.</h2><p>All three official model cards list a 1,050,000-token context window and 128,000 maximum output tokens. The choice is driven more by capability needs, workload type and cost.</p></article>
      <article><p class="eyebrow">PRICE RATIO</p><h2>100× from Luna to Astra.</h2><p>At the listed short-context rates, Astra’s input and output token prices are 100× Luna’s. Sol sits at 20× Luna and one-fifth of Astra.</p></article></section>

      <section class="model-reference-lower shell"><div class="model-sources"><p class="eyebrow">OFFICIAL SOURCES</p>{source_links}</div><div class="model-faq"><p class="eyebrow">QUICK ANSWERS</p>{faq_html}</div></section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">LATEST GPT-6 SIGNALS</p><h2>What changed recently.</h2></div><a href="/models/gpt-6/">GPT-6 reference ↗</a></div><div class="signal-list">{signal_rows}</div></section>
    </main>{page_footer()}</body></html>'''


def gpt6_sol_vs_claude_opus_html(items):
    canonical = f"{BASE_URL}/compare/{GPT6_SOL_CLAUDE_COMPARE_SLUG}/"
    verified = datetime.now(timezone.utc).date().isoformat()
    sol = {
        "name": "GPT-6 Sol",
        "provider": "OpenAI",
        "model_id": "gpt-6-sol",
        "released": "Sep 22, 2026",
        "positioning": "Complex coding and agentic workflows",
        "context": "1,050,000",
        "max_output": "128,000",
        "knowledge_cutoff": "Apr 20, 2026",
        "thinking": "Optional; none through max",
        "input_price": "$2.00",
        "cached_price": "$0.20",
        "cache_write": "$2.50",
        "output_price": "$10.00",
        "source": "https://developers.openai.com/api/docs/models/gpt-6-sol",
    }
    claude = {
        "name": "Claude Opus 5.5",
        "provider": "Anthropic",
        "model_id": "claude-opus-5-5",
        "released": "Sep 22, 2026",
        "positioning": "Long-running agentic coding and knowledge work",
        "context": "1,000,000",
        "max_output": "128,000",
        "knowledge_cutoff": "Jun 2026",
        "thinking": "Adaptive; always on",
        "input_price": "$4.00",
        "cached_price": "$0.20",
        "cache_write": "$5.00 / $8.00",
        "output_price": "$20.00",
        "source": "https://platform.claude.com/docs/en/models/opus-5-5/overview",
    }

    rows = "".join([
        f'''<tr><th scope="row"><a href="/models/gpt-6-sol/">{escape(sol["name"])}</a><small>{escape(sol["model_id"])}</small></th>
        <td>{escape(sol["provider"])}</td><td>{escape(sol["positioning"])}</td><td>{escape(sol["context"])}</td><td>{escape(sol["max_output"])}</td>
        <td>{escape(sol["thinking"])}</td><td>{escape(sol["input_price"])}</td><td>{escape(sol["cached_price"])}</td><td>{escape(sol["cache_write"])}</td><td>{escape(sol["output_price"])}</td></tr>''',
        f'''<tr><th scope="row"><a href="/models/claude-opus-5-5/">{escape(claude["name"])}</a><small>{escape(claude["model_id"])}</small></th>
        <td>{escape(claude["provider"])}</td><td>{escape(claude["positioning"])}</td><td>{escape(claude["context"])}</td><td>{escape(claude["max_output"])}</td>
        <td>{escape(claude["thinking"])}</td><td>{escape(claude["input_price"])}</td><td>{escape(claude["cached_price"])}</td><td>{escape(claude["cache_write"])}</td><td>{escape(claude["output_price"])}</td></tr>''',
    ])

    def cost(input_rate, output_rate, input_m, output_m):
        value = input_rate * input_m + output_rate * output_m
        return ("$" + f"{value:,.3f}").rstrip("0").rstrip(".")

    standard_examples = [
        ("GPT-6 Sol", cost(2, 10, .1, .01)),
        ("Claude Opus 5.5", cost(4, 20, .1, .01)),
    ]
    monthly_examples = [
        ("GPT-6 Sol", cost(2, 10, 10, 1)),
        ("Claude Opus 5.5", cost(4, 20, 10, 1)),
    ]
    long_examples = [
        ("GPT-6 Sol", cost(4, 15, .5, .05)),
        ("Claude Opus 5.5", cost(4, 20, .5, .05)),
    ]
    standard_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>100K input + 10K output</small></div>' for n,c in standard_examples)
    monthly_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>10M input + 1M output</small></div>' for n,c in monthly_examples)
    long_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>500K input + 50K output</small></div>' for n,c in long_examples)

    relevant = [
        item for item in items
        if "GPT-6 Sol" in extract_models(item["title"]) or "Claude Opus 5.5" in extract_models(item["title"])
    ][:10]
    signal_rows = "".join(signal_row(item) for item in relevant)

    faq_items = [
        ("How much cheaper is GPT-6 Sol than Claude Opus 5.5 at standard token rates?",
         "At the official standard rates, GPT-6 Sol is priced at $2 input and $10 output per million tokens, while Claude Opus 5.5 is $4 input and $20 output. The uncached input and output rates are therefore half as high for Sol."),
        ("Do GPT-6 Sol and Claude Opus 5.5 have the same context window?",
         "No. OpenAI lists a 1,050,000-token context window for GPT-6 Sol. Anthropic lists 1,000,000 tokens for Claude Opus 5.5. Both list a 128,000-token maximum output."),
        ("How do long-context prices differ?",
         "OpenAI states that GPT-6 Sol requests above 272K input tokens use 2x input/cache rates and 1.5x output rates for the full request. Anthropic states that the 1M context window is standard and long-context requests are billed at standard pricing."),
        ("How does reasoning control differ?",
         "GPT-6 Sol supports reasoning effort from none through max. Claude Opus 5.5 uses adaptive thinking that is always on, with medium as the default effort."),
        ("Which model is positioned for coding and agents?",
         "Both vendors position these models for coding and agentic work. OpenAI describes Sol as built for complex coding and agentic workflows; Anthropic describes Opus 5.5 as built for long-running agentic coding and knowledge work."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq_items)

    sources = "".join([
        '<a href="https://developers.openai.com/api/docs/models/gpt-6-sol" target="_blank" rel="noopener noreferrer"><span>OpenAI · GPT-6 Sol model card</span><b>↗</b></a>',
        '<a href="https://developers.openai.com/api/docs/pricing" target="_blank" rel="noopener noreferrer"><span>OpenAI · API pricing</span><b>↗</b></a>',
        '<a href="https://platform.claude.com/docs/en/models/opus-5-5/overview" target="_blank" rel="noopener noreferrer"><span>Anthropic · Claude Opus 5.5 model card</span><b>↗</b></a>',
        '<a href="https://www.anthropic.com/claude-opus-5-5" target="_blank" rel="noopener noreferrer"><span>Anthropic · Opus 5.5 announcement</span><b>↗</b></a>',
    ])

    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"WebPage","@id":canonical+"#webpage","url":canonical,
                "name":"GPT-6 Sol vs Claude Opus 5.5: Pricing, Context & API Comparison",
                "description":"Compare GPT-6 Sol and Claude Opus 5.5 using official pricing, context, output limits, reasoning controls and long-context billing.",
                "dateModified":verified,"isPartOf":{"@id":"https://sxf.si/#website"},
                "about":[{"@type":"Thing","name":"GPT-6 Sol"},{"@type":"Thing","name":"Claude Opus 5.5"}],
                "citation":[sol["source"],"https://developers.openai.com/api/docs/pricing",claude["source"],"https://www.anthropic.com/claude-opus-5-5"],
                "inLanguage":"en"
            },
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},
                {"@type":"ListItem","position":2,"name":"Models","item":BASE_URL+"/models/"},
                {"@type":"ListItem","position":3,"name":"GPT-6 Sol vs Claude Opus 5.5","item":canonical}
            ]},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_items]},
        ]
    }
    description = "GPT-6 Sol vs Claude Opus 5.5: official API pricing, 1.05M vs 1M context, 128K output, reasoning controls and long-context costs."
    return f'''<!doctype html><html lang="en">{page_head("GPT-6 Sol vs Claude Opus 5.5 — Pricing & Context | SXF / AI", description, canonical, schema)}
    <body class="intel-page comparison-page">{page_header("models")}<main>
      <section class="comparison-hero shell">
        <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/models/">Models</a><span>/</span><span>Sol vs Opus 5.5</span></nav>
        <p class="eyebrow">MODEL COMPARISON / VERIFIED {escape(verified)}</p>
        <h1>GPT-6 Sol<br><span>vs Claude Opus 5.5.</span></h1>
        <p>Two models released on September 22, 2026 and aimed at serious coding and agentic work. This comparison separates official specifications and pricing from vendor performance claims.</p>
        <div class="hero-actions"><a class="primary-cta" href="#specs">Compare specs <span>↓</span></a><a class="secondary-cta" href="/models/gpt-6-sol/">GPT-6 Sol reference</a></div>
      </section>

      <section class="decision-grid duel-grid shell">
        <article><span>OPENAI · GPT-6 SOL</span><h2>Lower standard token rates.</h2><p>OpenAI positions Sol for complex coding and agentic workflows. It supports optional reasoning effort from none through max and a 1.05M context window.</p><strong>$2 input · $10 output / MTok</strong><a href="/models/gpt-6-sol/">Open Sol reference ↗</a></article>
        <article><span>ANTHROPIC · OPUS 5.5</span><h2>Long-running agentic work.</h2><p>Anthropic positions Opus 5.5 for long-running agentic coding and knowledge work. Adaptive thinking is always on and its 1M context is billed at standard rates.</p><strong>$4 input · $20 output / MTok</strong><a href="/models/claude-opus-5-5/">Open Opus 5.5 signals ↗</a></article>
      </section>

      <section id="specs" class="comparison-table-section shell">
        <div class="intel-section-head"><div><p class="eyebrow">OFFICIAL SPECIFICATIONS</p><h2>Side-by-side facts.</h2></div><span>Vendor documentation</span></div>
        <div class="model-table-wrap"><table><thead><tr><th>Model</th><th>Provider</th><th>Positioning</th><th>Context</th><th>Max output</th><th>Thinking</th><th>Input</th><th>Cache read</th><th>Cache write</th><th>Output</th></tr></thead><tbody>{rows}</tbody></table></div>
        <p class="reference-note">Prices shown are standard per 1M tokens. Claude cache-write pricing is $5 for a 5-minute cache and $8 for a 1-hour cache. GPT-6 Sol cache write is $2.50 per 1M tokens at the listed standard short-context rate.</p>
      </section>

      <section class="cost-section shell">
        <div class="intel-section-head"><div><p class="eyebrow">COST EXAMPLES</p><h2>Same tokens, different billing.</h2></div><span>Direct token charges</span></div>
        <h3>Short-context request</h3><div class="cost-grid two-up">{standard_cards}</div>
        <h3>Monthly standard volume</h3><div class="cost-grid two-up">{monthly_cards}</div>
        <h3>Single long-context request</h3><div class="cost-grid two-up">{long_cards}</div>
        <p class="reference-note">The 500K + 50K example applies OpenAI’s published long-context uplift to Sol and Anthropic’s standard Opus 5.5 rates. It excludes tool calls, regional processing and service-tier adjustments.</p>
      </section>

      <section class="comparison-notes shell">
        <article><p class="eyebrow">CONTEXT ECONOMICS</p><h2>The gap narrows on very long prompts.</h2><p>Sol’s standard uncached token prices are half of Opus 5.5. Above 272K input tokens, however, Sol’s full request moves to higher long-context rates while Anthropic says Opus 5.5 keeps standard pricing across its 1M context window.</p></article>
        <article><p class="eyebrow">CACHE READS</p><h2>Both list $0.20 / MTok.</h2><p>At standard rates, both vendors list $0.20 per million cached or cache-read input tokens. Their cache-write pricing and long-context billing differ, so agent cost depends on the shape of the workload rather than headline input price alone.</p></article>
      </section>

      <section class="comparison-notes shell">
        <article><p class="eyebrow">REASONING CONTROL</p><h2>Optional vs always-on thinking.</h2><p>GPT-6 Sol lets API users select reasoning effort from none to max. Claude Opus 5.5 uses adaptive thinking that cannot be disabled; Anthropic lists medium as its default effort.</p></article>
        <article><p class="eyebrow">BENCHMARK CAUTION</p><h2>Keep vendor claims attributable.</h2><p>Launch benchmark charts can use different harnesses, effort settings and comparison models. SXF keeps this page centered on directly comparable official specifications rather than declaring a benchmark winner from mismatched tests.</p></article>
      </section>

      <section class="model-reference-lower shell"><div class="model-sources"><p class="eyebrow">OFFICIAL SOURCES</p>{sources}</div><div class="model-faq"><p class="eyebrow">QUICK ANSWERS</p>{faq_html}</div></section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">RELATED SIGNALS</p><h2>Recent Sol and Opus 5.5 updates.</h2></div><a href="/signals/">All signals ↗</a></div><div class="signal-list">{signal_rows}</div></section>
    </main>{page_footer()}</body></html>'''

def brief_issue_html(items, issue_date):
    selected = select_brief_items(items)
    pretty = issue_date.strftime("%B %-d, %Y")
    slug = issue_date.isoformat()
    canonical = f"{BASE_URL}/brief/{slug}/"
    description = f"SXF Brief for {pretty}: five AI signals from primary sources across models, tools, research and open source."
    schema = {"@context":"https://schema.org","@type":"Article","headline":f"SXF Brief — {pretty}","datePublished":issue_date.isoformat(),"mainEntityOfPage":canonical,"isPartOf":{"@id":"https://sxf.si/#website"},"creator":{"@id":"https://vivamediacreative.com/labs/#organization"},"inLanguage":"en"}
    cards = ""
    for i,item in enumerate(selected, 1):
        cards += f'''<article class="brief-signal"><span class="brief-no">{i:02d}</span><div><div class="brief-meta"><strong>{escape(item["source"])}</strong><span>{escape(item["category"])}</span><span>SCORE {item.get("signal_score",0):02d}</span></div><h2><a href="/signals/{escape(item["signal_slug"], quote=True)}/">{escape(item["title"])}</a></h2><p>{escape(compact_description(item))}</p><a class="brief-open" href="/signals/{escape(item["signal_slug"], quote=True)}/">Open signal ↗</a></div></article>'''
    return f'''<!doctype html><html lang="en">{page_head("SXF Brief — " + pretty, description, canonical, schema, "article", "noindex,follow")}
    <body class="intel-page brief-page">{page_header("brief")}<main>
      <section class="brief-issue-hero shell"><div><p class="eyebrow">SXF BRIEF / {escape(slug)}</p><h1>Five signals.<br><span>Zero noise.</span></h1></div><p>Five high-priority signals selected by SXF’s internal scoring system, with source and category diversity built into the shortlist. Every item keeps the primary source attached.</p></section>
      <section class="brief-stack shell">{cards}</section>
      <section class="brief-note shell"><span>METHOD</span><p>The brief is a discovery layer, not a substitute for the source. Open each signal for attribution and the original publication.</p><a href="/about/">Read SXF methodology ↗</a></section>
    </main>{page_footer()}</body></html>'''

def brief_index_html(items, issue_date):
    selected = select_brief_items(items)
    current = issue_date.isoformat()
    canonical = f"{BASE_URL}/brief/"
    description = "SXF Brief: five primary-source AI signals to scan each day, selected from the live SXF radar."
    schema = {"@context":"https://schema.org","@type":"CollectionPage","name":"SXF Brief","url":canonical,"description":description,"isPartOf":{"@id":"https://sxf.si/#website"},"inLanguage":"en"}
    archive = []
    if BRIEF_DIR.exists():
        for p in sorted(BRIEF_DIR.iterdir(), reverse=True):
            if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name):
                archive.append(p.name)
    archive_html = "".join(f'<a href="/brief/{d}/"><span>{d}</span><b>Open issue ↗</b></a>' for d in archive[:14])
    return f'''<!doctype html><html lang="en">{page_head("SXF Brief — Five AI Signals, Zero Noise", description, canonical, schema)}
    <body class="intel-page brief-index">{page_header("brief")}<main>
      <section class="collection-hero shell"><p class="eyebrow">DAILY INTELLIGENCE</p><h1>Five signals.<br><span>Zero noise.</span></h1><p>A compact daily read built from SXF’s live primary-source radar.</p><div class="hero-actions"><a class="primary-cta" href="/brief/{current}/">Read latest brief <span>↗</span></a><a class="secondary-cta" href="/signals/">Browse all signals</a></div></section>
      <section class="brief-preview shell"><div class="intel-section-head"><div><p class="eyebrow">LATEST ISSUE</p><h2>{escape(issue_date.strftime("%B %-d, %Y"))}</h2></div><a href="/brief/{current}/">Open full issue ↗</a></div>
      <div class="brief-preview-grid">{"".join(f'<a href="/signals/{escape(x["signal_slug"], quote=True)}/"><span>{i:02d}</span><strong>{escape(x["title"])}</strong><small>{escape(x["source"])} · {escape(x["category"])}</small></a>' for i,x in enumerate(selected,1))}</div></section>
      <section class="brief-archive shell"><p class="eyebrow">ARCHIVE</p><div>{archive_html}</div></section>
    </main>{page_footer()}</body></html>'''

def build_discovery_pages(items, current_items):
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    BRIEF_DIR.mkdir(parents=True, exist_ok=True)
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)
    GUIDES_DIR.mkdir(parents=True, exist_ok=True)
    SUPERINTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)

    (SUPERINTELLIGENCE_DIR / "index.html").write_text(superintelligence_index_html(items, current_items), encoding="utf-8")
    (GUIDES_DIR / "index.html").write_text(guides_index_html(items, current_items), encoding="utf-8")
    coding_guide_path = GUIDES_DIR / "best-ai-coding-tools"
    coding_guide_path.mkdir(parents=True, exist_ok=True)
    (coding_guide_path / "index.html").write_text(best_ai_coding_tools_html(items), encoding="utf-8")
    model_guide_path = GUIDES_DIR / "gpt-6-vs-claude"
    model_guide_path.mkdir(parents=True, exist_ok=True)
    (model_guide_path / "index.html").write_text(gpt6_vs_claude_guide_html(items), encoding="utf-8")
    open_models_guide_path = GUIDES_DIR / "open-source-ai-models"
    open_models_guide_path.mkdir(parents=True, exist_ok=True)
    (open_models_guide_path / "index.html").write_text(open_source_ai_models_guide_html(items), encoding="utf-8")
    agents_guide_path = GUIDES_DIR / "best-ai-agents"
    agents_guide_path.mkdir(parents=True, exist_ok=True)
    (agents_guide_path / "index.html").write_text(best_ai_agents_guide_html(items), encoding="utf-8")
    super_agents_guide_path = GUIDES_DIR / "ai-super-agents"
    super_agents_guide_path.mkdir(parents=True, exist_ok=True)
    (super_agents_guide_path / "index.html").write_text(ai_super_agents_guide_html(items), encoding="utf-8")
    (SIGNALS_DIR / "index.html").write_text(signals_index_html(items), encoding="utf-8")
    for item in items:
        path = SIGNALS_DIR / item["signal_slug"]
        path.mkdir(parents=True, exist_ok=True)
        (path / "index.html").write_text(signal_page_html(item, items), encoding="utf-8")

    groups = topic_groups(items)
    (TOPICS_DIR / "index.html").write_text(topics_index_html(groups), encoding="utf-8")
    for slug, (topic, matched) in groups.items():
        path = TOPICS_DIR / slug
        path.mkdir(parents=True, exist_ok=True)
        (path / "index.html").write_text(topic_page_html(topic, matched), encoding="utf-8")

    for name, matched in model_groups(items).items():
        if not matched:
            continue
        path = ROOT / "models" / slugify(name)
        path.mkdir(parents=True, exist_ok=True)
        (path / "index.html").write_text(model_page_html(name, matched), encoding="utf-8")

    comparison_path = COMPARE_DIR / GPT6_COMPARE_SLUG
    comparison_path.mkdir(parents=True, exist_ok=True)
    (comparison_path / "index.html").write_text(gpt6_comparison_html(items), encoding="utf-8")

    duel_path = COMPARE_DIR / GPT6_SOL_CLAUDE_COMPARE_SLUG
    duel_path.mkdir(parents=True, exist_ok=True)
    (duel_path / "index.html").write_text(gpt6_sol_vs_claude_opus_html(items), encoding="utf-8")

    issue_date = datetime.now(timezone.utc).date()
    issue_dir = BRIEF_DIR / issue_date.isoformat()
    issue_dir.mkdir(parents=True, exist_ok=True)
    (issue_dir / "index.html").write_text(brief_issue_html(current_items, issue_date), encoding="utf-8")
    (BRIEF_DIR / "index.html").write_text(brief_index_html(current_items, issue_date), encoding="utf-8")
def sitemap_entry(url, lastmod):
    return f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>"

def content_lastmod(items, fallback="2026-09-26"):
    dates = []
    for item in items:
        modified = parse_date(item.get("modified_at", "")) or parse_date(item.get("published", ""))
        if modified is not None:
            dates.append(modified)
    return max(dates).date().isoformat() if dates else fallback

def update_sitemap(items):
    generated_today = datetime.now(timezone.utc).date().isoformat()
    global_lastmod = content_lastmod(items)
    category_lastmod = {
        category: content_lastmod([item for item in items if item["category"] == category], global_lastmod)
        for category in ("Models", "Tools", "Research", "Open Source")
    }
    model_collection_items = [
        item for item in items
        if item["category"] == "Models" or extract_models(item["title"])
    ]
    guide_lastmod = content_lastmod(items[:6], "2026-09-26")
    gpt6_compare_items = [
        item for item in items
        if {"GPT-6", "GPT-6 Astra", "GPT-6 Sol", "GPT-6 Luna"}.intersection(extract_models(item["title"]))
    ]
    sol_opus_items = [
        item for item in items
        if {"GPT-6 Sol", "Claude Opus 5.5"}.intersection(extract_models(item["title"]))
    ]

    rows = [
        sitemap_entry(f"{BASE_URL}/", global_lastmod),
        sitemap_entry(f"{BASE_URL}/models/", content_lastmod(model_collection_items, category_lastmod["Models"])),
        sitemap_entry(f"{BASE_URL}/tools/", category_lastmod["Tools"]),
        sitemap_entry(f"{BASE_URL}/research/", category_lastmod["Research"]),
        sitemap_entry(f"{BASE_URL}/open-source/", category_lastmod["Open Source"]),
        sitemap_entry(f"{BASE_URL}/signals/", global_lastmod),
        sitemap_entry(f"{BASE_URL}/topics/", global_lastmod),
        sitemap_entry(f"{BASE_URL}/brief/", generated_today),
        sitemap_entry(f"{BASE_URL}/about/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/", guide_lastmod),
        sitemap_entry(f"{BASE_URL}/superintelligence/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/best-ai-coding-tools/", "2026-09-25"),
        sitemap_entry(f"{BASE_URL}/guides/gpt-6-vs-claude/", "2026-09-25"),
        sitemap_entry(f"{BASE_URL}/guides/open-source-ai-models/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/best-ai-agents/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/ai-agent-security/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/github-copilot-alternatives/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/prompt-injection/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/ai-super-agents/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/compare/{GPT6_COMPARE_SLUG}/", content_lastmod(gpt6_compare_items, "2026-09-26")),
        sitemap_entry(f"{BASE_URL}/compare/{GPT6_SOL_CLAUDE_COMPARE_SLUG}/", content_lastmod(sol_opus_items, "2026-09-26")),
    ]

    for item in items:
        if not item.get("seo_eligible", seo_signal_eligible(item)):
            continue
        modified = parse_date(item.get("modified_at", "")) or parse_date(item["published"])
        rows.append(sitemap_entry(item["signal_url"], modified.date().isoformat()))

    for slug, (_topic, matched) in topic_groups(items).items():
        if topic_page_indexable(matched):
            rows.append(sitemap_entry(f"{BASE_URL}/topics/{slug}/", content_lastmod(matched)))

    for name, matched in model_groups(items).items():
        if model_page_indexable(name, matched):
            rows.append(sitemap_entry(f"{BASE_URL}/models/{slugify(name)}/", content_lastmod(matched)))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n"
    SITEMAP.write_text(xml, encoding="utf-8")
def main():
    incoming = []
    errors = []
    for source, url in SOURCES:
        try:
            incoming.extend(parse_feed(source, fetch(url)))
        except Exception as exc:
            errors.append(f"{source}: {exc}")

    existing = load_items(ARCHIVE_OUT)
    if not existing:
        existing = load_items(OUT)
    existing_by_url = {item.get("url"): item for item in existing if item.get("url")}
    ingest_cutoff = datetime.now(timezone.utc) - timedelta(days=INITIAL_ARCHIVE_DAYS)
    incoming = [
        item for item in incoming
        if parse_date(item.get("published", "")) is not None and parse_date(item["published"]) >= ingest_cutoff
    ]
    enriched = enrich_summaries(incoming, existing_by_url)

    archive = merge_archive(existing, incoming)
    if not archive:
        raise RuntimeError("No valid signals available after archive merge")

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    current = [
        item for item in archive
        if parse_date(item["published"]) is not None and parse_date(item["published"]) >= cutoff
    ][:MAX_ITEMS]
    if not current:
        current = archive[:MAX_ITEMS]

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    ARCHIVE_OUT.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_OUT.write_text(json.dumps({
        "updated_at": now_iso,
        "items": archive,
        "feed_errors": errors,
        "scoring_version": "sxf-signal-score-v2",
        "seo_quality_version": "sxf-seo-quality-v1",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    OUT.write_text(json.dumps({
        "updated_at": now_iso,
        "items": [client_item(item) for item in current],
        "feed_errors": errors,
        "scoring_version": "sxf-signal-score-v2",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    update_index(current)
    update_section_pages(current)
    build_discovery_pages(archive, current)
    update_sitemap(archive)
    print(
        f"Wrote {len(current)} current signals from {len(archive)} archived signals; "
        f"enriched {enriched} summaries; source errors: {len(errors)}"
    )
if __name__ == "__main__":
    main()
