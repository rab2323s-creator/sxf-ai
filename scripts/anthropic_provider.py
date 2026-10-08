"""Anthropic provider authority page. The generator calls this with its runtime globals."""
from html import escape
from datetime import date

def render_anthropic_provider_html(ctx, items):
    catalog = ctx["MODEL_PRICING_CATALOG"]
    models = [m for m in catalog["models"] if m["provider"] == "Anthropic"]
    assert models, "Anthropic missing from model pricing catalog"
    base = ctx["BASE_URL"]
    canonical = base + "/providers/anthropic/"
    verified = max(m["provenance"]["verified_at"] for m in models)
    docs = "https://platform.claude.com/docs/en/models/overview"
    pricing_url = "https://platform.claude.com/docs/en/about-claude/pricing"
    lifecycle = "https://platform.claude.com/docs/en/about-claude/model-deprecations"
    tools_url = "https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-reference"
    code_url = "https://code.claude.com/docs/en/overview"
    title = "Anthropic Claude Models: API Pricing & Comparison (2026) | SXF / AI"
    description = "Compare Anthropic Claude models, API token pricing, context windows, output limits and tools. Current vs legacy versions, use cases and official sources."
    def h(x): return escape(str(x), quote=True)
    def official(url, label):
        return f'<a href="{h(url)}" rel="noopener noreferrer">{h(label)} ↗</a>'
    def rate(m):
        for p in m.get("pricing", {}).get("standard", []):
            if p["start"] <= catalog["source_verified"] and (not p.get("end") or p["end"] >= catalog["source_verified"]):
                return p
        return {}
    def usd(x):
        return "$" + format(float(x), ".4f").rstrip("0").rstrip(".") if x is not None else "—"
    cards = []
    rows = []
    for m in models:
        p = rate(m)
        url = m.get("sxf_url", "")
        model_href = url if url.startswith("/models/") else None
        name = f'<a href="{h(model_href)}">{h(m["model"])}</a>' if model_href else h(m["model"])
        source = next((s for s in m.get("official_sources", []) if s.startswith("https://")), docs)
        status = "Restricted access" if "mythos" in m["model_id"] else m.get("lifecycle", {}).get("status", "Unverified")
        rows.append(f'<tr><th scope="row">{name}<small>{h(m["model_id"])}</small></th><td>{int(m["context_window"]):,}</td><td>{int(m["max_output"]):,}</td><td>{usd(p.get("input"))}</td><td>{usd(p.get("output"))}</td><td>{h(status)}</td><td>{official(source, "Specs")}</td></tr>')
        cards.append(f'<article class="model-family-card"><span>{h(m.get("family","Claude"))}</span><h3>{name}</h3><p>{h(m["positioning"])}</p><div class="model-family-spec"><b>{int(m["context_window"]):,} context</b><small>{int(m["max_output"]):,} output</small></div><div class="model-family-price"><strong>{usd(p.get("input"))} in / {usd(p.get("output"))} out per MTok</strong><small>{h(status)}</small></div></article>')
    faqs = [
        ("What is the best Claude model for most workloads?", "Anthropic's current model guide recommends Opus 5.5 as a starting point for most workloads. Sonnet 5.5 is the speed-and-intelligence choice, Fable 5.1 targets especially demanding reasoning, and current Haiku is intended for high-volume latency-sensitive tasks."),
        ("How much is Claude API pricing?", "Input and output are billed separately, generally per million tokens. Rates depend on the model and feature. Caching, batch, tools, inference geography and third-party cloud hosting can change total cost."),
        ("Does every Claude model support a million-token context?", "No. Limits vary by exact model ID and version. The catalog lists a million tokens for selected Claude 5 releases and 200,000 for Haiku 4.5. Anthropic's live Models API is the final authority."),
        ("Is Claude Code a Claude model?", "No. Claude Code is Anthropic's developer coding agent product. The Claude API provides model access and tool integration. Their pricing and usage arrangements should be reviewed separately."),
        ("Does Claude support web search, code execution or computer use?", "Anthropic documents tool-use patterns and specific hosted or client-side tools. Feature availability, tool versions and execution permissions depend on model and deployment; a tool-use-capable model does not directly execute arbitrary actions."),
        ("Are all Claude models generally available?", "No. Models like Mythos 5.1 have restricted access. Check the official model documentation and your own account or cloud platform before planning production usage."),
    ]
    faq_markup = "".join(f'<details><summary>{h(q)}</summary><p>{h(a)}</p></details>' for q,a in faqs)
    qa_schema = [{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]
    listing = [{"@type":"ListItem","position":i+1,"name":m["model"],"url":base + m["sxf_url"] if m.get("sxf_url","").startswith("/models/") else docs} for i,m in enumerate(models)]
    schema = {"@context":"https://schema.org","@graph":[
        {"@type":"CollectionPage","@id":canonical+"#page","name":title,"url":canonical,"description":description,"inLanguage":"en","dateModified":verified,"about":{"@type":"Organization","name":"Anthropic","url":"https://www.anthropic.com/"},"mainEntity":{"@id":canonical+"#models"}},
        {"@type":"ItemList","@id":canonical+"#models","name":"Anthropic models in SXF canonical catalog","numberOfItems":len(models),"itemListElement":listing},
        {"@type":"FAQPage","mainEntity":qa_schema},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":base+"/"},{"@type":"ListItem","position":2,"name":"Providers","item":base+"/providers/"},{"@type":"ListItem","position":3,"name":"Anthropic","item":canonical}]}
    ]}
    comparison_ids = {m["model_id"] for m in models}
    comparison_links = "".join(f'<a href="/compare/{h(c["slug"])}/">{h(c["title"])} ↗</a>' for c in ctx["MODEL_COMPARISON_CATALOG"]["comparisons"] if c.get("indexable") and comparison_ids.intersection(c.get("model_ids", [])))
    head = ctx["page_head"](title, description, canonical, schema)
    header = ctx["page_header"]("models")
    footer = ctx["page_footer"]()
    return f'''<!doctype html><html lang="en">{head}<body class="intel-page model-page">{header}<main>
    <section class="collection-hero shell">
      <nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><a href="/providers/">Providers</a><span>/</span>Anthropic</nav>
      <p class="eyebrow">PROVIDER INTELLIGENCE · VERIFIED {h(verified)}</p>
      <h1>Anthropic Claude models.<br><span>Pricing, capabilities and selection.</span></h1>
      <p>Anthropic develops Claude AI models and developer tools. Compare the published API model lineup, standard token economics, context limits, model lifecycles and deployment use cases. This source-backed guide explains what to pick and what to verify before building.</p>
      <div class="collection-stats"><div><strong>{len(models)}</strong><span>catalog entries</span></div><div><strong>{sum(bool(rate(m)) for m in models)}</strong><span>priced entries</span></div><div><strong>{h(verified)}</strong><span>latest catalog verification</span></div></div>
      <nav class="model-related-links" aria-label="On this page"><a href="#models"><strong>Models ↓</strong></a><a href="#pricing"><strong>Pricing ↓</strong></a><a href="#api"><strong>API ↓</strong></a><a href="#selection"><strong>Selection ↓</strong></a><a href="#faq"><strong>FAQ ↓</strong></a><a href="#sources"><strong>Sources ↓</strong></a></nav>
    </section>
    <section class="model-reference model-reference-deep shell" id="models"><div class="model-section-head"><p class="eyebrow">QUICK ANSWER</p><h2>Which Claude model should you choose?</h2></div>
      <p><strong>Start by testing Claude Opus 5.5</strong> for demanding general work, as Anthropic recommends. Sonnet 5.5 targets strong speed/intelligence economics, Fable 5.1 targets difficult long-horizon reasoning, and the latest Haiku model targets high-volume latency-sensitive tasks. Model names are not benchmark guarantees: measure your own quality, latency and failure rates.</p>
      <p><strong>Coverage disclosure:</strong> This comparison is generated from the SXF canonical pricing catalog, not a complete snapshot of Anthropic's live model registry. Anthropic's current model guide also lists <strong>Claude Haiku 5.5</strong>, which is not yet integrated in this catalog. Sonnet 5 and Haiku 4.5 remain shown for lifecycle/migration context. {official(docs, "Live official lineup")}</p>
      <h2>Claude model portfolio</h2><div class="model-family-grid">{"".join(cards)}</div>
      <h2>Claude context, output and price comparison</h2><p>Standard global API USD per one million tokens (MTok), separately billed for input and output. Max output is not the amount always generated. Check official sources for per-model feature and access differences.</p>
      <div style="overflow-x:auto"><table class="data-table"><thead><tr><th scope="col">Claude model</th><th scope="col">Context</th><th scope="col">Max output</th><th scope="col">Input / MTok</th><th scope="col">Output / MTok</th><th scope="col">Lifecycle / access</th><th scope="col">Primary source</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
    </section>
    <section class="model-reference model-reference-deep shell" id="pricing"><div class="model-section-head"><p class="eyebrow">API ECONOMICS</p><h2>Claude pricing: what the token rate means</h2></div>
      <p>A request consuming 100,000 input and 10,000 output tokens would cost about <strong>$0.60 with Opus 5.5</strong> ($0.40 + $0.20), <strong>$0.30 with Sonnet 5.5</strong>, or <strong>$1.50 with Fable 5.1</strong> at the listed standard global API rates. This is a simple token-only illustration, not an all-in quote.</p>
      <p>Prompt cache reads can be significantly cheaper than new input, but cache writes have separate rates and lifetimes. Batch usage, server-side tools (including web search), inference geography, enterprise terms and cloud marketplace endpoints may alter charges. A one-million-token context window is a capacity limit—not an included monthly allowance or flat fee. Compare real request distributions and output length before projecting production budgets.</p>
      <div class="model-related-links"><a href="/models/pricing/">SXF model pricing ↗</a>{official(pricing_url, "Official API pricing")}</div>
    </section>
    <section class="model-reference model-reference-deep shell" id="api"><div class="model-section-head"><p class="eyebrow">DEVELOPER PLATFORM</p><h2>Claude API capabilities, agents and coding</h2></div>
      <h3>Messages API and tool use</h3><p>Claude accepts text and image input and produces text. Developers can supply tool definitions; the model can request a call and the application executes the corresponding client tool. Supported Anthropic server tools include selected web search, web fetch and code-execution variants. Tool support is version- and model-specific: inspect the Models API capabilities object rather than assuming every tool works everywhere.</p>
      <h3>Computer use and browser automation</h3><p>Computer use and browser use are different tool interfaces. They require a runtime operated by the application with explicit permissions, safety boundaries and verification of actions. Automation quality should be evaluated by success rate, reversibility and human approval, not just the number of steps completed.</p>
      <h3>Claude Code</h3><p>Claude Code is Anthropic's agentic software-engineering product, not a separate underlying Claude model. It can be relevant when selecting models for terminal-first coding, repository exploration and code changes. Subscription eligibility and Claude API metered billing are distinct: check the latest product terms instead of equating API token prices with Claude Code plan costs.</p>
      <div class="model-related-links">{official(tools_url, "Official tool reference")}{official(code_url, "Claude Code docs")}<a href="/guides/best-ai-coding-tools/">AI coding tools compared ↗</a></div>
    </section>
    <section class="model-reference model-reference-deep shell" id="selection"><div class="model-section-head"><p class="eyebrow">DECISION FRAMEWORK</p><h2>Current Claude, legacy models and migration</h2></div>
      <h3>High-stakes reasoning and long-running tasks</h3><p>Evaluate Fable 5.1 against Opus 5.5 on difficult, verified tasks; pay for a premium model only when it materially improves outcomes. For long-context tasks, measure retrieval precision, end-to-end latency and effective cost across repeated turns.</p>
      <h3>Production apps and high-volume workflows</h3><p>Evaluate Sonnet 5.5 for balanced coding, knowledge work and agents. For classification, extraction, routing and brief responses, benchmark the current Haiku release directly. Do not select Haiku 4.5 from an older SXF row without checking newer models and API support.</p>
      <h3>Restricted and older releases</h3><p>Mythos 5.1 has limited-access specialist use cases and should not be offered as a generally accessible public API default. Sonnet 5 and Haiku 4.5 are older catalog records; their continued presence does not prove they are the preferred versions. Review Anthropic's release IDs, retirement dates and migration documentation before pinning or upgrading.</p>
      <p><strong>Practical migration checklist:</strong> confirm exact model ID and access; compare prompt quality using representative workloads; validate token limits, thinking controls, JSON/tool behavior and safety rules; retest price and caching; check your target cloud region; monitor deprecations.</p>
      <div class="model-related-links">{official(lifecycle, "Official lifecycle notices")}{official(docs, "Current model IDs")}<a href="/compare/">Compare models ↗</a><a href="/guides/gpt-6-vs-claude/">GPT-6 vs Claude: family comparison ↗</a>{comparison_links}</div>
    </section>
    <section class="model-reference model-reference-deep shell" id="faq"><div class="model-section-head"><p class="eyebrow">FAQ</p><h2>Anthropic Claude questions</h2></div>{faq_markup}</section>
    <section class="model-reference model-reference-deep shell" id="sources"><div class="model-section-head"><p class="eyebrow">SOURCE CHECK</p><h2>Primary documentation and methodology</h2></div>
      <p>The comparison table comes from the canonical SXF pricing catalog, with model-specific official URLs and recorded verification dates. Latest catalog verification: <strong>{h(verified)}</strong>. The actual Anthropic lineup can change before the local catalog is refreshed; omissions and legacy rows are disclosed rather than hidden.</p>
      <div class="model-related-links">{official(docs, "Models overview")}{official(pricing_url, "Pricing")}{official(lifecycle, "Deprecations")}{official(tools_url, "Tools")}{official(code_url, "Claude Code")}<a href="/models/">Model directory ↗</a><a href="/compare/">Comparison hub ↗</a></div>
    </section>
    </main>{footer}</body></html>'''
