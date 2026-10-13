"""Evergreen, search-intent-specific enrichment for Anthropic's provider portfolio.

The existing generator keeps all live catalog model cards, model IDs, pricing
provenance and canonical routing. Tiered prices are read from catalog data;
this module never manufactures a flat token rate for Haiku 5.5.
"""
from __future__ import annotations
import json
import re
from html import escape

TITLE = "Anthropic Models & Claude API Pricing | SXF / AI"
DESCRIPTION = "Compare Anthropic Claude models and API prices: Opus, Sonnet, Haiku and Fable, token costs, context limits, caching, model IDs and which to choose."
HERO = "Compare Anthropic's Claude language models by API price, context window, output limit, reasoning and real workloads. See the current Opus, Sonnet, Haiku and Fable lineup, historical releases, tiered Haiku pricing and links to verified model references."
QUICK = "\n      <h2 id=\"current-claude-models\">Current Anthropic Claude models: quick choice and price.</h2>\n      <p>For <strong>Claude models</strong> searches, start with the four families Anthropic identifies in its <a href=\"https://platform.claude.com/docs/en/models/overview\" rel=\"noopener noreferrer\">current model lineup</a>. These are direct <strong>Claude API</strong> list prices in USD per million input/output tokens; third-party hosting and optional tools can differ.</p>\n      <div class=\"model-family-grid\">\n        <article class=\"model-family-card\"><span>GENERAL FLAGSHIP</span><h3><a href=\"/models/claude-opus-5-5/\">Claude Opus 5.5</a></h3><p>Anthropic's starting recommendation for general demanding work, coding and agentic tasks.</p><div class=\"model-family-price\"><strong>$4 input / $20 output</strong><small>per million tokens · 1M context</small></div></article>\n        <article class=\"model-family-card\"><span>SPEED + CAPABILITY</span><h3><a href=\"/models/claude-sonnet-5-5/\">Claude Sonnet 5.5</a></h3><p>Test for production coding and applications balancing speed, capability and per-request cost.</p><div class=\"model-family-price\"><strong>$2 input / $10 output</strong><small>per million tokens · 1M context</small></div></article>\n        <article class=\"model-family-card\"><span>HIGH-VOLUME / LOW COST</span><h3><a href=\"/models/claude-haiku-5-5/\">Claude Haiku 5.5</a></h3><p>Classification, extraction and fast subagents. Price depends on total input prompt length.</p><div class=\"model-family-price\"><strong>From $0.10 input / $0.50 output</strong><small>per million tokens · prompts up to 100K</small></div></article>\n        <article class=\"model-family-card\"><span>DEMANDING REASONING</span><h3><a href=\"/models/claude-fable-5-1/\">Claude Fable 5.1</a></h3><p>Compare against Opus for exceptionally challenging long-horizon reasoning and agent work.</p><div class=\"model-family-price\"><strong>$10 input / $50 output</strong><small>per million tokens · 1M context</small></div></article>\n      </div>\n      <p><strong>Choose by measured task performance:</strong> the cheapest model is not always the cheapest successful solution. Include latency, tool reliability, revision count and output quality when comparing the models. <a href=\"/compare/claude-haiku-5-5-vs-claude-sonnet-5-5/\">Compare Haiku 5.5 vs Sonnet 5.5</a> for a more focused decision.</p>\n"
DETAIL = "\n    <section class=\"model-reference model-reference-deep shell\" id=\"haiku-pricing\"><div class=\"model-section-head\"><p class=\"eyebrow\">PRICING THAT CHANGES WITH PROMPT SIZE</p><h2>Claude Haiku 5.5 API pricing: short vs long prompts.</h2></div>\n      <p><strong>Haiku 5.5's advertised “from” price applies only when the input prompt is 100,000 tokens or shorter.</strong> If a prompt exceeds 100,000 input tokens, Anthropic applies the higher rate to its input and output tokens. This matters for teams processing long documents and agent context: a row that says “$0.10 input / $0.50 output” without the threshold would be misleading.</p>\n      <div style=\"overflow-x:auto\"><table class=\"data-table\">\n        <thead><tr><th scope=\"col\">Input prompt length</th><th scope=\"col\">Input per 1M tokens</th><th scope=\"col\">Output per 1M tokens</th><th scope=\"col\">5m cache write / 1M</th><th scope=\"col\">Cache read / 1M</th></tr></thead>\n        <tbody>\n          <tr><th scope=\"row\">Up to 100,000 tokens</th><td>$0.10</td><td>$0.50</td><td>$0.125</td><td>$0.01</td></tr>\n          <tr><th scope=\"row\">Over 100,000 tokens</th><td>$0.50</td><td>$2.50</td><td>$0.625</td><td>$0.05</td></tr>\n        </tbody>\n      </table></div>\n      <p><strong>Cost example:</strong> 20,000 input tokens and 2,000 output tokens cost about <strong>$0.003</strong> ($0.002 input + $0.001 output). A 120,000-input-token prompt and 10,000 output tokens cost about <strong>$0.085</strong> ($0.060 input + $0.025 output). These are uncached, real-time base API estimates; the full cost may also include tool use or other charges.</p>\n      <p><strong>Why this is useful:</strong> Haiku's short-prompt price is exceptionally low, but long document analysis can move into a different tier. Compare with <a href=\"/models/claude-sonnet-5-5/\">Sonnet 5.5</a> or <a href=\"/models/claude-opus-5-5/\">Opus 5.5</a> on the actual number of tokens processed, not just the headline model rate. <a href=\"https://platform.claude.com/docs/en/models/haiku-5-5/overview\" rel=\"noopener noreferrer\">Official Haiku 5.5 specifications and tiered pricing ↗</a></p>\n    </section>\n    <section class=\"model-reference model-reference-deep shell\" id=\"api-example\"><div class=\"model-section-head\"><p class=\"eyebrow\">DEVELOPER REFERENCE</p><h2>Anthropic Claude API example: make your first Messages request.</h2></div>\n      <p>The <strong>Claude Messages API</strong> uses a model ID (for example <code>claude-sonnet-5-5</code>) rather than the marketing family name. Keep your key server-side; set a maximum response length, then inspect returned usage before extrapolating cost. The sample below performs one text-only request.</p>\n      <pre style=\"white-space:pre-wrap;overflow-wrap:anywhere;overflow-x:auto\"><code>curl https://api.anthropic.com/v1/messages \\\n  -H \"x-api-key: $ANTHROPIC_API_KEY\" \\\n  -H \"anthropic-version: 2023-06-01\" \\\n  -H \"content-type: application/json\" \\\n  -d '{\n    \"model\": \"claude-sonnet-5-5\",\n    \"max_tokens\": 512,\n    \"messages\": [\n      {\"role\": \"user\", \"content\": \"Compare two approaches to retrying a failed API call.\"}\n    ]\n  }'</code></pre>\n      <p>The response includes generated message content and token-usage fields. For agents, tool-use or computer-use features require extra configuration and explicit authorization. See <a href=\"https://platform.claude.com/docs/en/api/messages\" rel=\"noopener noreferrer\">Anthropic Messages API docs</a>, <a href=\"/guides/ai-agent-authorization/\">agent authorization guidance</a> and the <a href=\"/tools/ai-model-cost-calculator/\">SXF model cost calculator</a> (for calculator-eligible fixed-rate models only).</p>\n    </section>\n    <section class=\"model-reference model-reference-deep shell\" id=\"claude-selection\"><div class=\"model-section-head\"><p class=\"eyebrow\">MODEL SELECTION AND MIGRATION</p><h2>Which Claude model should you use for coding, agents or bulk tasks?</h2></div>\n      <div class=\"model-family-grid\">\n        <article class=\"model-family-card\"><span>CODING / COMPLEX AGENTS</span><h3>Opus 5.5</h3><p>Start with the general flagship model, then benchmark Fable 5.1 only if harder reasoning or longer task chains justify the higher price. <a href=\"/models/claude-opus-5-5/\">Opus reference ↗</a></p></article>\n        <article class=\"model-family-card\"><span>DAILY PRODUCTION</span><h3>Sonnet 5.5</h3><p>Evaluate when you need strong coding and knowledge work with lower token expense than Opus. <a href=\"/models/claude-sonnet-5-5/\">Sonnet reference ↗</a></p></article>\n        <article class=\"model-family-card\"><span>CLASSIFICATION AND ROUTING</span><h3>Haiku 5.5</h3><p>Prefer for large volumes of short requests and low-latency subtasks; watch the 100K prompt threshold on long context. <a href=\"/models/claude-haiku-5-5/\">Haiku reference ↗</a></p></article>\n        <article class=\"model-family-card\"><span>LEGACY MAINTENANCE</span><h3>Sonnet 5 / Haiku 4.5</h3><p>Both are labeled legacy by Anthropic, though currently active in its model documentation. Test upgrades carefully; legacy does not automatically mean retired. <a href=\"https://platform.claude.com/docs/en/about-claude/model-deprecations\" rel=\"noopener noreferrer\">Deprecations ↗</a></p></article>\n      </div>\n      <p><strong>Evaluation approach:</strong> measure task success rate, median and tail latency, correction effort, effective cost after cache/Batch discounts, and permission failures for tools. This matters more than ranking by name or assumed benchmark superiority. For system-level costs, read <a href=\"/guides/ai-agent-cost/\">AI agent cost and ROI analysis</a>.</p>\n    </section>\n"
FAQS = [["Which Anthropic Claude models are current?","Anthropic's current model overview lists Claude Fable 5.1, Claude Opus 5.5, Claude Sonnet 5.5 and Claude Haiku 5.5. Older releases may remain available, while specialist Mythos access is restricted; check each model's live status."],["What is Anthropic Claude API pricing per million tokens?","Direct Anthropic API input/output base rates include Fable 5.1 $10/$50, Opus 5.5 $4/$20 and Sonnet 5.5 $2/$10 per million tokens. Haiku 5.5 has prompt-length tiers: $0.10/$0.50 at up to 100,000 input tokens and $0.50/$2.50 above 100,000. Caching, batch, tools and inference geography can change the bill."],["How much does Claude Haiku 5.5 cost?","For prompts containing at most 100,000 input tokens, Haiku 5.5 costs $0.10 per million input tokens and $0.50 per million output tokens on the standard Claude API. For prompts above 100,000 input tokens, the rates are $0.50 input and $2.50 output. The prompt-length threshold affects both rates."],["Which Claude model is best for coding or AI agents?","Start by evaluating Opus 5.5 for general demanding work, Sonnet 5.5 for a balance of speed and capability, and Fable 5.1 when measured harder reasoning or agent tasks justify the extra expense. Haiku 5.5 is optimized for fast low-cost subtasks. Use your own acceptance tests rather than a universal ranking."],["What is the difference between Claude Opus, Sonnet, Haiku and Fable?","Opus is Anthropic's general flagship choice, Sonnet emphasizes speed and intelligence balance, Haiku emphasizes throughput and lower prices, and Fable is a premium option for difficult reasoning and long-horizon agentic work. Exact features depend on the model version and endpoint."],["Does every Claude model have a one-million-token context window?","No. The current Fable 5.1, Opus 5.5, Sonnet 5.5 and Haiku 5.5 each list one million tokens, but older models such as Haiku 4.5 have a 200,000-token context. Context capacity is not a promise of perfect recall."],["How does Claude prompt caching pricing work?","Claude has separate prices for cache creation and cache reads. Haiku 5.5 cache reads start at $0.01 per million tokens for prompts up to 100,000 tokens and rise to $0.05 for longer prompts. Actual savings require cache reuse, and rates differ by model, duration and inference region."],["Does Anthropic offer Batch API discounts?","Anthropic documents a 50% discount on input and output token rates for eligible Message Batches API usage. Batch jobs are asynchronous; availability and tool or cache behavior can differ from real-time requests."],["Can developers use Claude models through Amazon Bedrock or Google Cloud?","Several Claude models are available through the Claude API and supported third-party cloud platforms, including Amazon Bedrock and Google Cloud. Model IDs, supported regions, prices and features can differ by platform. Verify the model page for your chosen runtime."],["Is Claude Code the same as the Claude API?","No. Claude Code is Anthropic's coding-agent product; Claude API offers model access for application development. Subscriptions and metered API billing are not interchangeable."],["Are older Claude models still usable?","Some earlier releases remain active as legacy models while newer versions are recommended. Claude Sonnet 5 and Claude Haiku 4.5 are marked legacy in Anthropic's documentation; do not assume their retirement or availability without checking the official deprecations list."],["How do I estimate Claude API costs?","Multiply input tokens by the model's per-million input rate and generated output tokens by its output rate, then include applicable cache writes, cache reads, tools, batch adjustments and region-specific pricing. For Haiku 5.5 check whether the entire prompt crosses 100,000 input tokens first."]]
SOURCES = ["https://platform.claude.com/docs/en/models/overview","https://platform.claude.com/docs/en/models/haiku-5-5/overview","https://platform.claude.com/docs/en/about-claude/pricing","https://platform.claude.com/docs/en/about-claude/model-deprecations"]
CANONICAL = "https://sxf.si/providers/anthropic/"


def _replace_once(page, old, new):
    if page.count(old) != 1:
        raise ValueError("Anthropic provider generation template drift: " + old[:80])
    return page.replace(old, new, 1)


def _rewrite_meta(page, name, content):
    pattern = r'(<meta (?:name|property)="' + re.escape(name) + r'" content=")[^"]*(" />)'
    page, count = re.subn(
        pattern, lambda m: m.group(1) + escape(content, quote=True) + m.group(2),
        page, count=1,
    )
    if count != 1:
        raise ValueError("Anthropic provider meta missing: " + name)
    return page


def _modify_model_block(page, slug, tag, modify):
    if tag == "card":
        pattern = r'<article class="model-family-card">(?:(?!</article>).)*?<h3><a href="/models/' + re.escape(slug) + r'/">.*?</article>'
    else:
        pattern = r'<tr><th scope="row"><a href="/models/' + re.escape(slug) + r'/">.*?</tr>'
    matches = list(re.finditer(pattern, page, re.DOTALL))
    if len(matches) != 1:
        raise ValueError("Anthropic expected one " + tag + " block for " + slug)
    match = matches[0]
    block = modify(match.group())
    return page[:match.start()] + block + page[match.end():]


def enrich_anthropic_provider_page(page, models, verified):
    if 'data-anthropic-evergreen-guide' in page:
        return page
    if f'<link rel="canonical" href="{CANONICAL}"' not in page:
        raise ValueError("Anthropic provider canonical URL changed")
    haiku = next((m for m in models if m.get("model_id") == "claude-haiku-5-5"), None)
    if not haiku:
        raise ValueError("Haiku 5.5 missing from authoritative Anthropic catalog")
    scopes = haiku.get("pricing", {}).get("tiered", {}).get("scopes", [])
    tiers = scopes[0].get("tiers", []) if scopes else []
    if len(tiers) != 2 or tiers[0].get("max_input_tokens") != 100000 or tiers[1].get("min_input_tokens") != 100001:
        raise ValueError("Haiku 5.5 official tiered pricing changed: review the page")
    low, high = tiers
    lowin, lowout = f'\x24{low["input"]:.2f}', f'\x24{low["output"]:.2f}'
    highin, highout = f'\x24{high["input"]:.2f}', f'\x24{high["output"]:.2f}'

    page, count = re.subn(r"<title>.*?</title>", "<title>" + escape(TITLE) + "</title>", page, count=1)
    if count != 1:
        raise ValueError("Anthropic provider title missing")
    for name, content in (
        ("description", DESCRIPTION), ("og:title", TITLE),
        ("og:description", DESCRIPTION), ("twitter:title", TITLE),
        ("twitter:description", DESCRIPTION),
    ):
        page = _rewrite_meta(page, name, content)
    page = _replace_once(page, '<h1>Anthropic Claude models.<br><span>Pricing, capabilities and selection.</span></h1>', '<h1>Anthropic Claude models.<br><span>API pricing, comparison and model selection.</span></h1>')
    page = _replace_once(
        page,
        '<p>Anthropic develops Claude AI models and developer tools. Compare the published API model lineup, standard token economics, context limits, model lifecycles and deployment use cases. This source-backed guide explains what to pick and what to verify before building.</p>',
        '<p>' + escape(HERO) + '</p>',
    )
    page, count = re.subn(
        r'<p><strong>Coverage disclosure:</strong>.*?</p>',
        '<p><strong>Coverage and freshness:</strong> the SXF catalog contains the four current Claude model families as well as older and restricted releases. Haiku 5.5 uses prompt-length pricing rather than one flat rate. The official <a href="https://platform.claude.com/docs/en/models/overview" rel="noopener noreferrer">Anthropic model overview</a> remains the authority for new releases, availability and migrations.</p>',
        page, count=1, flags=re.DOTALL,
    )
    if count != 1:
        raise ValueError("Anthropic provider coverage disclosure missing")
    page = _replace_once(page, '<h2>Claude model portfolio</h2>', '<div data-anthropic-evergreen-guide>' + QUICK + '</div><h2>Claude model portfolio</h2>')

    def haiku_card(block):
        old = '<strong>— in / — out per MTok</strong>'
        if old not in block:
            raise ValueError("Haiku 5.5 old card missing placeholder")
        return block.replace(old, f'<strong>From {lowin} in / {lowout} out per MTok</strong>').replace('<small>current</small>', '<small>Up to 100K prompt tokens · tiered pricing</small>')
    page = _modify_model_block(page, 'claude-haiku-5-5', 'card', haiku_card)

    def haiku_row(block):
        if '<td>—</td><td>—</td>' not in block:
            raise ValueError("Haiku 5.5 missing price cells")
        return block.replace('<td>—</td><td>—</td>', f'<td>From {lowin}</td><td>From {lowout}</td>').replace('<td>current</td>', '<td>Current · prompt-length tiers</td>')
    page = _modify_model_block(page, 'claude-haiku-5-5', 'row', haiku_row)

    for slug in ['claude-sonnet-5', 'claude-haiku-4-5']:
        page = _modify_model_block(page, slug, 'card', lambda b: b.replace('<small>current</small>', '<small>Legacy · active (check migration)</small>'))
        page = _modify_model_block(page, slug, 'row', lambda b: b.replace('<td>current</td>', '<td>Legacy · active</td>'))

    catalog_priced = sum(
        bool(m.get('pricing', {}).get('standard') or m.get('pricing', {}).get('tiered'))
        for m in models
    )
    page, count = re.subn(r'(<strong>)\d+(</strong><span>priced entries</span>)', lambda m: m.group(1) + str(catalog_priced) + m.group(2), page, count=1)
    if count != 1:
        raise ValueError("Anthropic provider pricing count missing")
    page = _replace_once(
        page, '<h2>Claude context, output and price comparison</h2>',
        '<h2>Claude context, output and price comparison</h2><p><strong>Haiku 5.5 note:</strong> “From” rates below apply to prompts with at most 100K input tokens. For longer prompts, its input price is ' + highin + ' and its output price is ' + highout + ' per million tokens. <a href="#haiku-pricing">Full tier and caching details ↓</a></p>',
    )

    anchor = '    <section class="model-reference model-reference-deep shell" id="api">'
    page = _replace_once(page, anchor, DETAIL + '\n' + anchor)

    faq_markup = ''.join('<details><summary>' + escape(q) + '</summary><p>' + escape(a) + '</p></details>' for q,a in FAQS)
    faqs_old = r'(<section class="model-reference model-reference-deep shell" id="faq">.*?<div class="model-section-head">.*?</div>).*?(</section>)'
    page, count = re.subn(faqs_old, lambda m: m.group(1) + faq_markup + m.group(2), page, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError("Anthropic FAQ section changed")

    match = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.DOTALL)
    if not match:
        raise ValueError("Anthropic schema missing")
    schema = json.loads(match.group(2))
    nodes = schema['@graph']
    collection = next(n for n in nodes if n.get('@type') == 'CollectionPage')
    listing = next(n for n in nodes if n.get('@type') == 'ItemList')
    faq = next(n for n in nodes if n.get('@type') == 'FAQPage')
    crumb = next(n for n in nodes if n.get('@type') == 'BreadcrumbList')
    collection.update({
        'name': TITLE, 'description': DESCRIPTION,
        'dateModified': max(verified, '2026-10-13'),
        'isPartOf': {'@id': 'https://sxf.si/#website'},
        'publisher': {'@id': 'https://sxf.si/#organization'},
        'breadcrumb': {'@id': CANONICAL + '#breadcrumb'},
        'hasPart': {'@id': CANONICAL + '#faq'},
        'keywords': ['Anthropic models', 'Claude models', 'Anthropic API pricing', 'Claude model pricing', 'Claude API token costs', 'Opus Sonnet Haiku Fable comparison'],
    })
    listing['name'] = 'Anthropic Claude models with source-backed reference pages'
    crumb['@id'] = CANONICAL + '#breadcrumb'
    faq['@id'] = CANONICAL + '#faq'
    faq['mainEntity'] = [{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in FAQS]
    nodes.append({'@type':'WebSite','@id':'https://sxf.si/#website','name':'SXF / AI','url':'https://sxf.si/','publisher':{'@id':'https://sxf.si/#organization'}})
    nodes.append({'@type':'Organization','@id':'https://sxf.si/#organization','name':'SXF / AI','url':'https://sxf.si/'})
    encoded = json.dumps(schema, ensure_ascii=False, separators=(',', ':'))
    page = page[:match.start(2)] + encoded + page[match.end(2):]
    return page
