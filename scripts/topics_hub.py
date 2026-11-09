"""The durable, intent-led discovery hub for SXF / AI topic coverage.

This directory is not a news feed or a replacement for evergreen guides.
Keep its navigation, editorial copy and schema in one generator-owned source.
"""
from __future__ import annotations

from html import escape
from typing import Callable

TITLE = "AI Topics: Agents, Coding, Security & Open Source | SXF / AI"
DESCRIPTION = (
    "Browse AI topics including agents, coding AI, security, open-source models "
    "and leading AI platforms. Find curated guides, research and topic updates."
)
CANONICAL = "https://sxf.si/topics/"

CARD_FOCUS = {
    "ai-agents": "Guides · Research · Developments",
    "coding-ai": "Tools · Workflows · Developments",
    "ai-security": "Threats · Controls · Resources",
    "open-source-ai": "Models · Runtimes · Releases",
    "multimodal-ai": "Vision · Audio · Video",
    "ai-safety": "Alignment · Evaluation · Risks",
    "openai": "Models · Products · Research",
    "google-ai": "Models · Products · Research",
    "github-copilot": "Features · Workflows · Integrations"
}

SUBJECT_ORDER = (
    "ai-agents", "coding-ai", "ai-security",
    "open-source-ai", "multimodal-ai", "ai-safety",
)
PLATFORM_ORDER = ("openai", "google-ai", "github-copilot")

# Short directory descriptions; in-depth keyword intent belongs to each topic / guide.
DIRECTORY_COPY = {
    "ai-agents": ("SYSTEMS & WORKFLOWS", "Explore agentic systems, tools, autonomy, evaluation and real-world use cases."),
    "coding-ai": ("DEVELOPER WORKFLOWS", "Explore AI coding assistants, software agents and developer tooling."),
    "ai-security": ("THREATS & DEFENSES", "Explore prompt injection, agent permissions, sandboxing and deployment security."),
    "open-source-ai": ("OPEN MODELS & RUNTIMES", "Explore open-weight models, local inference and open AI infrastructure."),
    "multimodal-ai": ("VOICE, IMAGE & VIDEO", "Explore AI that works across text, images, audio, video and other modalities."),
    "ai-safety": ("EVALUATION & ALIGNMENT", "Explore AI safety research, alignment, evaluation and deployment risks."),
    "openai": ("COMPANY & PLATFORM", "Follow OpenAI's model, product, platform and research developments."),
    "google-ai": ("COMPANY & PLATFORM", "Follow Google AI's models, research, products and developer platforms."),
    "github-copilot": ("PRODUCT & ECOSYSTEM", "Follow GitHub Copilot releases, coding workflows and developer integrations."),
}

PAGE_TEMPLATE = r'''
<section class="topics-hub-hero shell" aria-labelledby="topics-hub-title">
  <nav class="intel-breadcrumb topics-hub-breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><span aria-current="page">AI Topics</span></nav>
  <div class="topics-hub-hero-layout">
    <div>
      <p class="eyebrow">AI KNOWLEDGE MAP / SXF</p>
      <h1 id="topics-hub-title">Explore AI <span>topics.</span></h1>
      <p class="topics-hub-lead">Find your way through artificial intelligence: AI agents, coding tools, security, open-source models and the platforms shaping the field.</p>
      <p class="topics-hub-support">Each topic connects trusted updates with relevant guides and research. Start with a subject; go deeper on its dedicated page.</p>
      <div class="topics-hub-actions"><a class="topics-hub-primary-link" href="#browse-by-topic">Browse topics <span aria-hidden="true">↗</span></a><a class="topics-hub-secondary-link" href="#start-here">Where to start <span aria-hidden="true">↗</span></a></div>
    </div>
    <aside class="topics-hub-promise" aria-label="How the topic map works">
      <span class="topics-hub-mono">01 / DISCOVER</span>
      <strong>One subject.<br>Connected intelligence.</strong>
      <p>Topics organize the subject. Guides explain it. Research tests it. Signals track what changes.</p>
      <span class="topics-hub-promise-foot">__TOPIC_COUNT__ topic hubs · Maintained from primary-source coverage</span>
    </aside>
  </div>
</section>
<section class="topics-hub-section shell" id="browse-by-topic" aria-labelledby="topics-subject-heading">
  <div class="topics-hub-heading"><div><p class="eyebrow">01 / FIELDS & CAPABILITIES</p><h2 id="topics-subject-heading">Browse by subject.</h2><p>Choose a field to explore its concepts, practical guidance and ongoing developments.</p></div><span class="topics-hub-section-count">__SUBJECT_COUNT__ subjects</span></div>
  <div class="topics-hub-grid">__SUBJECT_CARDS__</div>
</section>
<section class="topics-hub-section topics-hub-platforms shell" aria-labelledby="topics-platform-heading">
  <div class="topics-hub-heading"><div><p class="eyebrow">02 / COMPANIES & PLATFORMS</p><h2 id="topics-platform-heading">Follow the ecosystem.</h2><p>Looking for a particular company or product? Start with its dedicated coverage.</p></div><span class="topics-hub-section-count">__PLATFORM_COUNT__ platforms</span></div>
  <div class="topics-hub-grid topics-hub-grid-platforms">__PLATFORM_CARDS__</div>
</section>
<section class="topics-hub-section shell" id="start-here" aria-labelledby="topics-start-heading">
  <div class="topics-hub-heading"><div><p class="eyebrow">03 / START WITH A QUESTION</p><h2 id="topics-start-heading">Find the right starting point.</h2><p>For a specific question, use the focused guide. For the full landscape, explore the topic hub.</p></div></div>
  <div class="topics-hub-paths">
    <article class="topics-hub-path"><span class="topics-hub-mono">UNDERSTAND AGENTS</span><h3>What is agentic AI?</h3><p>Start with the definition and real examples, then explore the wider AI agents landscape.</p><div class="topics-hub-path-links"><a href="/guides/what-is-agentic-ai/">Read the agentic AI guide ↗</a><a href="/topics/ai-agents/">Explore AI Agents ↗</a></div></article>
    <article class="topics-hub-path"><span class="topics-hub-mono">CHOOSE DEVELOPER TOOLS</span><h3>Which AI coding tools fit your workflow?</h3><p>Compare coding tools in a dedicated guide, or follow the broader coding AI ecosystem.</p><div class="topics-hub-path-links"><a href="/guides/best-ai-coding-tools/">Explore the coding tools guide ↗</a><a href="/topics/coding-ai/">Explore Coding AI ↗</a></div></article>
    <article class="topics-hub-path"><span class="topics-hub-mono">MANAGE AGENT RISKS</span><h3>How do you secure an AI agent?</h3><p>Use the practical security guide for defenses; follow the topic for risks and standards.</p><div class="topics-hub-path-links"><a href="/guides/ai-agent-security/">Read the agent security guide ↗</a><a href="/topics/ai-security/">Explore AI Security ↗</a></div></article>
  </div>
</section>
<section class="topics-hub-section topics-hub-method shell" aria-labelledby="topics-method-heading">
  <div class="topics-hub-method-layout"><div><p class="eyebrow">04 / NAVIGATE SXF</p><h2 id="topics-method-heading">A map, not another feed.</h2><p>Topics connect SXF's different content types around a subject. They do not replace deep-dive guides or duplicate the chronological Signals feed.</p><a class="topics-hub-text-link" href="/about/#method">How we select and verify sources ↗</a></div>
  <div class="topics-hub-layers"><a href="/guides/"><span>GUIDES</span><strong>Learn how something works</strong><span aria-hidden="true">↗</span></a><a href="/research/"><span>RESEARCH</span><strong>Examine evidence and analysis</strong><span aria-hidden="true">↗</span></a><a href="/models/"><span>MODELS</span><strong>Explore model capabilities</strong><span aria-hidden="true">↗</span></a><a href="/signals/"><span>SIGNALS</span><strong>Track what changed</strong><span aria-hidden="true">↗</span></a></div></div>
</section>
<section class="topics-hub-outro shell" aria-label="Explore AI knowledge"><p>Follow the subject, not just the headline.</p><a href="#browse-by-topic">Back to all AI topics ↑</a></section>
'''

def topic_directory_groups(groups):
    return {slug: (topic, items) for slug, (topic, items) in groups.items()}


def topic_card(slug: str, topic: dict, items: list) -> str:
    label, summary = DIRECTORY_COPY.get(slug, ("TOPIC HUB", topic["description"]))
    return (
        f'<a class="topics-hub-card" href="/topics/{escape(slug, quote=True)}/">'
        f'<span class="topics-hub-card-label">{escape(label)}</span>'
        f'<h3>{escape(topic["name"])}</h3>'
        f'<p>{escape(summary)}</p>'
        f'<span class="topics-hub-card-foot"><span>{escape(CARD_FOCUS.get(slug, "Explore the coverage"))}</span>'
        f'<b>Explore topic <span aria-hidden="true">↗</span></b></span></a>'
    )


def topic_schema(groups: dict) -> dict:
    order = [slug for slug in (*SUBJECT_ORDER, *PLATFORM_ORDER) if slug in groups]
    entries = [
        {
            "@type": "ListItem", "position": pos,
            "name": groups[slug][0]["name"],
            "url": CANONICAL + slug + "/",
        }
        for pos, slug in enumerate(order, 1)
    ]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": CANONICAL + "#webpage",
                "url": CANONICAL,
                "name": "AI Topics: Agents, Coding, Security & Open Source",
                "description": DESCRIPTION,
                "inLanguage": "en",
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "publisher": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "breadcrumb": {"@id": CANONICAL + "#breadcrumb"},
                "mainEntity": {"@id": CANONICAL + "#topic-list"},
                "about": [{"@type": "Thing", "name": "Artificial intelligence"}],
            },
            {
                "@type": "ItemList",
                "@id": CANONICAL + "#topic-list",
                "name": "Browse SXF artificial intelligence topics",
                "numberOfItems": len(entries),
                "itemListOrder": "https://schema.org/ItemListOrderAscending",
                "itemListElement": entries,
            },
            {
                "@type": "BreadcrumbList",
                "@id": CANONICAL + "#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sxf.si/"},
                    {"@type": "ListItem", "position": 2, "name": "AI Topics", "item": CANONICAL},
                ],
            },
        ],
    }


def render_topics_hub(groups: dict, *, page_head: Callable, page_header: Callable, page_footer: Callable) -> str:
    groups = topic_directory_groups(groups)
    subjects = [slug for slug in SUBJECT_ORDER if slug in groups]
    platforms = [slug for slug in PLATFORM_ORDER if slug in groups]
    def cards(slugs):
        return "".join(topic_card(slug, *groups[slug]) for slug in slugs)
    main = (PAGE_TEMPLATE
        .replace("__TOPIC_COUNT__", str(len(subjects) + len(platforms)))
        .replace("__SUBJECT_COUNT__", str(len(subjects)))
        .replace("__PLATFORM_COUNT__", str(len(platforms)))
        .replace("__SUBJECT_CARDS__", cards(subjects))
        .replace("__PLATFORM_CARDS__", cards(platforms)))
    return (
        '<!doctype html><html lang="en">'
        + page_head(TITLE, DESCRIPTION, CANONICAL, topic_schema(groups))
        + '<body class="intel-page topics-page topics-hub-page">'
        + page_header("topics") + '<main id="main-content">' + main
        + '</main>' + page_footer()
        + '<script src="/assets/topic-navigation.js" defer></script></body></html>'
    )
